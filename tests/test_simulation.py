from datetime import datetime

import pandas as pd

from generate import initial_run, main
from sim.config import get_catalog, get_growth_config
from sim.event import get_event_multiplier
from sim.generate_basket import _available, build_purchase_history, market_activity_multiplier
from sim.growth import get_growth_multiplier


def test_events_use_simulation_year_profiles_and_funnel_stage():
    assert get_event_multiplier(1, 1, "visit", tier="family_shoppers") == 1.3
    assert get_event_multiplier(2, 1, "visit", tier="students") == 1.4
    assert get_event_multiplier(3, 5, "conversion", tier="young_professionals", funnel_step="landing_page") == 1.05
    assert get_event_multiplier(2023, 1, "visit", tier="family_shoppers") == 1.0


def test_growth_composes_base_and_yearly_profile_multipliers():
    result = get_growth_multiplier(date=datetime(2023, 6, 1), simulation_start=datetime(2023, 1, 1),
                                   growth_cfg=get_growth_config(), tier_name="young_professionals", metric="visit")
    assert result == 1.1 * 0.85 * 1.15


def test_market_volume_is_relative_behavioral_reference():
    assert market_activity_multiplier("2023-12-03") > market_activity_multiplier("2023-02-02")


def test_purchase_history_enforces_subcategory_cooldown():
    catalog = get_catalog()
    category, subcategory, product, cooldown = next(
        (category, subcategory, product, data.get("cooldown", config.get("cooldown", 1)))
        for category, subcategories in catalog.items()
        for subcategory, config in subcategories.items()
        for product, data in config["product"].items()
        if data.get("cooldown", config.get("cooldown", 1)) > 1
    )
    history = build_purchase_history(pd.DataFrame([{"user_id": "u", "product": product, "date": "2023-01-01"}]))
    assert not _available(category, subcategory, product, "u", "2023-01-02", history)
    assert _available(category, subcategory, product, "u", f"2023-02-01", history)


def test_generation_is_idempotent_and_transaction_ids_are_session_based(tmp_path):
    output = tmp_path / "output"
    initial_run(output, seed=99)
    main("2023-01-01", "2023-01-14", output, seed=99)
    funnel_before = pd.read_parquet(output / "funnel.parquet")
    transactions_before = pd.read_parquet(output / "transaction.parquet")
    main("2023-01-01", "2023-01-14", output, seed=99)
    assert len(pd.read_parquet(output / "funnel.parquet")) == len(funnel_before)
    transactions = pd.read_parquet(output / "transaction.parquet")
    assert len(transactions) == len(transactions_before)
    assert transactions.trx_id.is_unique
    assert transactions.trx_id.eq("trx-" + transactions.session_id).all()
