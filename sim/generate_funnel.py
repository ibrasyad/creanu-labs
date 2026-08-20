"""Session and funnel-event generation."""
from datetime import datetime
from pathlib import Path
import random

import numpy as np
import pandas as pd

from .config import get_date_config, get_funnel_config, get_growth_config, get_simulation, get_tiers
from .event import get_event_multiplier
from .generate_basket import market_activity_multiplier
from .growth import get_growth_multiplier, get_simulation_year
from .utils import apply_noise, controlled_random, get_day_of_week, get_month_name, weighted_choice

BASE_DIR = Path(__file__).resolve().parent.parent
_tiers, _sim = get_tiers(), get_simulation()
_date_config, _funnel, _growth = get_date_config(), get_funnel_config(), get_growth_config()


def _rate(value):
    return min(1.0, max(0.0, float(value)))


def get_visit_decay_multiplier(days_since_last_visit, visit_decay):
    if not visit_decay:
        return 1.0
    multiplier = sorted(visit_decay, key=lambda rule: rule["days"])[0]["multiplier"]
    for rule in sorted(visit_decay, key=lambda rule: rule["days"]):
        if days_since_last_visit >= rule["days"]:
            multiplier = rule["multiplier"]
        else:
            break
    return float(multiplier)


def generate_visit(user_tier, current_date, decay=1.0):
    tier = _tiers[user_tier]
    weekday, month = get_day_of_week(current_date), get_month_name(current_date)
    chance = tier.get("visit_chance", _sim.get("visit_chance", {})).get(weekday, 0.05)
    chance *= tier.get("monthly_visit_chance_multiplier", {}).get(month, 1.0)
    chance *= market_activity_multiplier(current_date)
    chance *= apply_noise(chance, tier.get("funnel_noise"))
    chance *= decay
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")
    start = datetime.strptime(_date_config["start_date"], "%Y-%m-%d")
    chance *= get_growth_multiplier(date=date_obj, simulation_start=start, growth_cfg=_growth,
                                    tier_name=user_tier, metric="visit")
    chance *= get_event_multiplier(get_simulation_year(date_obj, start), date_obj.month,
                                   metric="visit", tier=user_tier)
    # Decay may reach zero, but a small configurable reactivation chance prevents permanent disappearance.
    if decay <= 0:
        chance = max(chance, float(_sim.get("reactivation_probability", 0.002)))
    return "landing_page" if random.random() < _rate(chance) else None


def generate_funnel(user_tier, previous_step, current_date):
    if not previous_step:
        return None
    order = _funnel["funnel_order"]
    if previous_step == order[-1]:
        return None
    tier = _tiers[user_tier]
    chance = tier.get(previous_step, {}).get("conversion_rate",
                                             _funnel.get(previous_step, {}).get("conversion_rate", 0.0))
    chance *= apply_noise(chance, tier.get("funnel_noise"))
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")
    start = datetime.strptime(_date_config["start_date"], "%Y-%m-%d")
    chance *= get_growth_multiplier(date=date_obj, simulation_start=start, growth_cfg=_growth,
                                    tier_name=user_tier, metric="conversion")
    chance *= get_event_multiplier(get_simulation_year(date_obj, start), date_obj.month,
                                   metric="conversion", tier=user_tier, funnel_step=previous_step)
    return order[order.index(previous_step) + 1] if random.random() < _rate(chance) else None


def generate_duration(user_tier, step):
    duration = _funnel.get(step, {}).get("duration", {}).copy()
    duration.update(_tiers[user_tier].get(step, {}).get("duration", {}))
    return controlled_random(duration.get("avg_duration", 10), duration.get("min_duration", 5),
                             duration.get("max_duration", 60))


def generate_landing_datetime(current_date, tier):
    peaks = _tiers[tier].get("visit_hour_peak", _funnel.get("visit_hour_peak", {}))
    if peaks:
        peak = peaks[weighted_choice({key: item["weight"] for key, item in peaks.items()})]
        hour = int(np.clip(round(np.random.normal(peak["hour"]["avg"], 2)), peak["hour"]["min"], peak["hour"]["max"]))
    else:
        hour = int(np.clip(round(np.random.normal(19, 2)), 0, 23))
    return pd.Timestamp(current_date) + pd.Timedelta(hours=hour, minutes=random.randint(0, 59), seconds=random.randint(0, 59))


def generate_session_ids(df, current_date):
    date_str = pd.Timestamp(current_date).strftime("%Y%m%d")
    return [f"{date_str}-{i:08d}" for i in range(1, len(df) + 1)]


def generate_funnel_table(current_date, users=None):
    users = pd.read_parquet(BASE_DIR / "output/users_updated.parquet") if users is None else users.copy()
    base_date = pd.Timestamp(current_date).normalize()
    users["last_active_date"] = pd.to_datetime(users["last_active_date"], errors="coerce").dt.normalize()
    users["recency"] = (base_date - users["last_active_date"]).dt.days.fillna(9999).clip(lower=0)
    users["visit_decay_multiplier"] = users["recency"].map(lambda days: get_visit_decay_multiplier(days, _sim.get("visit_decay", [])))
    users["landing_page"] = [generate_visit(tier, current_date, decay) for tier, decay in zip(users.tier, users.visit_decay_multiplier)]
    visitors = users.loc[users.landing_page.eq("landing_page"), ["tier", "user_id", "landing_page"]].copy()
    if visitors.empty:
        return pd.DataFrame(columns=["session_id", "tier", "user_id", "landing_page", "landing_page_datetime", "product_view", "product_view_datetime", "add_to_cart", "add_to_cart_datetime", "checkout", "checkout_datetime", "paid", "paid_datetime"])
    visitors["landing_page_datetime"] = [generate_landing_datetime(current_date, tier) for tier in visitors.tier]
    visitors = visitors.sort_values("landing_page_datetime").reset_index(drop=True)
    visitors["session_id"] = generate_session_ids(visitors, current_date)
    previous = "landing_page"
    for step in _funnel["funnel_order"][1:]:
        visitors[step] = [generate_funnel(tier, value, current_date) for tier, value in zip(visitors.tier, visitors[previous])]
        visitors[f"{step}_datetime"] = [prev + pd.Timedelta(seconds=generate_duration(tier, step)) if value else pd.NaT
                                          for prev, tier, value in zip(visitors[f"{previous}_datetime"], visitors.tier, visitors[step])]
        previous = step
    columns = ["session_id", "tier", "user_id"] + [item for step in _funnel["funnel_order"] for item in (step, f"{step}_datetime")]
    return visitors[columns]


def funnel_wide_to_activity_log(df):
    if df is None or df.empty:
        return pd.DataFrame(columns=["session_id", "tier", "user_id", "activity", "activity_datetime"])
    rows = []
    for row in df.itertuples(index=False):
        for step in _funnel["funnel_order"]:
            activity, timestamp = getattr(row, step), getattr(row, f"{step}_datetime")
            if pd.notna(activity) and pd.notna(timestamp):
                rows.append({"session_id": row.session_id, "tier": row.tier, "user_id": row.user_id,
                             "activity": activity, "activity_datetime": pd.Timestamp(timestamp)})
    return pd.DataFrame(rows)
