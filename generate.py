"""Generate reproducible, idempotent synthetic commerce data."""
from __future__ import annotations

import argparse
from pathlib import Path
import random

import pandas as pd

from sim.config import get_date_config, get_simulation, get_tiers
from sim.generate_basket import build_purchase_history, generate_basket, update_purchase_history
from sim.generate_funnel import funnel_wide_to_activity_log, generate_funnel_table
from sim.generate_user import generate_base_user_table, generate_new_users, roll_new_user_chance
from sim.utils import append_or_create_parquet, date_range, seed_for_date, set_random_seed

USER_COLUMNS = ["tier", "user_id", "city", "gender", "acquisition_channel", "registered_date", "last_active_date"]
FUNNEL_COLUMNS = ["session_id", "tier", "user_id", "activity", "activity_datetime"]
TRX_COLUMNS = ["session_id", "user_id", "trx_id", "date", "tier", "total_price"]
ITEM_COLUMNS = ["trx_id", "user_id", "tier", "date", "product", "quantity", "unit_price", "total_price"]
MANIFEST_COLUMNS = ["simulation_date", "seed"]


def _path(output_dir, name):
    return Path(output_dir) / name


def initial_run(output_dir="output", seed=None):
    """Create a new simulation dataset. This intentionally replaces its output directory files."""
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    (output / "csv-file").mkdir(exist_ok=True)
    seed = int(seed if seed is not None else get_simulation().get("random_seed", 20260101))
    set_random_seed(seed)
    from sim.utils import generate_catalog_parquet
    generate_catalog_parquet(str(_path(output, "catalog.parquet")))
    users = pd.DataFrame(generate_base_user_table(), columns=USER_COLUMNS)
    users["registered_date"] = pd.to_datetime(users["registered_date"])
    users["last_active_date"] = pd.to_datetime(users["last_active_date"])
    users.to_parquet(_path(output, "users_base.parquet"), index=False)
    users.to_parquet(_path(output, "users_updated.parquet"), index=False)
    pd.DataFrame(columns=USER_COLUMNS).to_parquet(_path(output, "users_new.parquet"), index=False)
    pd.DataFrame(columns=FUNNEL_COLUMNS).to_parquet(_path(output, "funnel.parquet"), index=False)
    pd.DataFrame(columns=TRX_COLUMNS).to_parquet(_path(output, "transaction.parquet"), index=False)
    pd.DataFrame(columns=ITEM_COLUMNS).to_parquet(_path(output, "transaction_item.parquet"), index=False)
    pd.DataFrame(columns=MANIFEST_COLUMNS).to_parquet(_path(output, "_simulation_runs.parquet"), index=False)


def _completed_dates(output_dir):
    path = _path(output_dir, "_simulation_runs.parquet")
    if not path.exists():
        return set()
    return set(pd.read_parquet(path)["simulation_date"].astype(str))


def _export_csv(output_dir):
    exports = {"users_updated.parquet": "user.csv", "transaction.parquet": "transaction.csv",
               "transaction_item.parquet": "transaction_item.csv", "funnel.parquet": "funnel.csv",
               "catalog.parquet": "catalog.csv"}
    for parquet_name, csv_name in exports.items():
        df = pd.read_parquet(_path(output_dir, parquet_name)).drop(columns=["tier"], errors="ignore")
        df.to_csv(_path(output_dir, "csv-file") / csv_name, index=False)


def main(start_date=None, end_date=None, output_dir="output", seed=None):
    output = Path(output_dir)
    if not _path(output, "users_updated.parquet").exists():
        raise FileNotFoundError("Simulation is not initialized. Run initial_run() before main().")
    config = get_date_config()
    start_date, end_date = start_date or config["start_date"], end_date or config["end_date"]
    base_seed = int(seed if seed is not None else get_simulation().get("random_seed", 20260101))
    completed = _completed_dates(output)
    users = pd.read_parquet(_path(output, "users_updated.parquet"))
    existing_items = pd.read_parquet(_path(output, "transaction_item.parquet"))
    purchase_history = build_purchase_history(existing_items)
    tiers = get_tiers()

    for current_date in date_range(start_date, end_date):
        if current_date in completed:
            print(f"Skipping already generated date: {current_date}")
            continue
        day_seed = seed_for_date(base_seed, current_date)
        set_random_seed(day_seed)
        tier_names = list(tiers)
        random.shuffle(tier_names)
        new_rows = []
        current_user_count = len(users)
        for tier_name in tier_names:
            arrivals = roll_new_user_chance(tier_name, current_date)
            new_users = generate_new_users(arrivals, tier_name, current_date, current_user_count)
            new_rows.extend(new_users)
            current_user_count += len(new_users)
        new_users_df = pd.DataFrame(new_rows, columns=USER_COLUMNS[:-2])
        if not new_users_df.empty:
            new_users_df["registered_date"] = pd.Timestamp(current_date)
            new_users_df["last_active_date"] = pd.Timestamp(current_date)
            users = pd.concat([users, new_users_df], ignore_index=True)
        # users_new is an explicit daily delta snapshot, including an empty day.
        new_users_df.reindex(columns=USER_COLUMNS).to_parquet(_path(output, "users_new.parquet"), index=False)

        funnel_wide = generate_funnel_table(current_date, users=users)
        funnel_log = funnel_wide_to_activity_log(funnel_wide)
        append_or_create_parquet(str(_path(output, "funnel.parquet")), funnel_log)
        visitors = funnel_log.loc[funnel_log.activity.eq("landing_page"), "user_id"].unique()
        if len(visitors):
            users.loc[users.user_id.isin(visitors), "last_active_date"] = pd.Timestamp(current_date)
        users.to_parquet(_path(output, "users_updated.parquet"), index=False)

        paid = funnel_log.loc[funnel_log.activity.eq("paid"), ["session_id", "user_id", "tier", "activity_datetime"]].copy()
        transaction_rows, item_rows = [], []
        for paid_row in paid.itertuples(index=False):
            trx_id = f"trx-{paid_row.session_id}"  # stable and collision-free, even after midnight
            basket = generate_basket(paid_row.tier, paid_row.user_id, paid_row.activity_datetime, purchase_history)
            if not basket:
                continue
            transaction_rows.append({"session_id": paid_row.session_id, "user_id": paid_row.user_id,
                                     "trx_id": trx_id, "date": paid_row.activity_datetime, "tier": paid_row.tier,
                                     "total_price": sum(item["total_price"] for item in basket)})
            for item in basket:
                item_rows.append({"trx_id": trx_id, "user_id": paid_row.user_id, "tier": paid_row.tier,
                                  "date": paid_row.activity_datetime, **item})
            update_purchase_history(purchase_history, paid_row.user_id, paid_row.activity_datetime, basket)
        append_or_create_parquet(str(_path(output, "transaction.parquet")), pd.DataFrame(transaction_rows, columns=TRX_COLUMNS))
        append_or_create_parquet(str(_path(output, "transaction_item.parquet")), pd.DataFrame(item_rows, columns=ITEM_COLUMNS))
        append_or_create_parquet(str(_path(output, "_simulation_runs.parquet")),
                                 pd.DataFrame([{"simulation_date": current_date, "seed": day_seed}]))
        completed.add(current_date)
        print(f"Generated {current_date}: {len(funnel_log)} events, {len(transaction_rows)} transactions")
    _export_csv(output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate simulation data")
    parser.add_argument("--start-date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", help="End date (YYYY-MM-DD)")
    parser.add_argument("--seed", type=int, help="Base random seed")
    args = parser.parse_args()
    initial_run(seed=args.seed)
    main(start_date=args.start_date, end_date=args.end_date, seed=args.seed)
