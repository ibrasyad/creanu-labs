import random
import numpy as np
import sys
from pathlib import Path
import pandas as pd
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

# Handle both module import and direct script execution
try:
    from .config import get_catalog, get_tiers, get_simulation, get_date_config, get_funnel_config, get_growth_config, get_event_config
    from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, controlled_random, date_range
    from .growth import get_growth_multiplier
    from .event import get_event_multiplier
except ImportError:
    # Allow running as a script
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_catalog, get_tiers, get_simulation, get_date_config, get_funnel_config, get_growth_config, get_event_config
    from utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, controlled_random, date_range
    from growth import get_growth_multiplier
    from event import get_event_multiplier

# Cache configs
_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()
_funnel = get_funnel_config()
_growth = get_growth_config()
_event = get_event_config()


def generate_visit(user_tier, current_date, decay=1.0):
    """Generate whether a user visits on a given date."""
    # funnel_config = get_funnel_config()
    tier_config = _tiers[user_tier]
    # date_info = _date_config
    day_of_week = get_day_of_week(current_date)
    month_name = get_month_name(current_date)

    # Determine visit chance
    visit_chance = tier_config.get('visit_chance',{}).get(
        f"{day_of_week}",
        _sim.get('visit_chance',{}).get(f"{day_of_week}", 0.05)
    )

    visit_chance *= tier_config.get("monthly_visit_chance_multiplier", {}).get(month_name, 1.0)

    noise_cfg = tier_config.get("funnel_noise", None)
    if noise_cfg:
        noise_multiplier = apply_noise(visit_chance, noise_cfg)
        visit_chance = max(0, visit_chance * noise_multiplier)
    
    decay_multiplier = decay or 1.0
    visit_chance *= decay_multiplier

    # Apply Growth
    simulation_start = datetime.strptime(
        _date_config["start_date"], "%Y-%m-%d"
    )
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")

    growth_multiplier = get_growth_multiplier(
        date=date_obj,
        simulation_start=simulation_start,
        growth_cfg=_growth,
        tier_name=user_tier,
        metric="visit",
    )

    visit_chance *= growth_multiplier

    # Apply Event
    year = date_obj.year
    month = date_obj.month
    event_mult = get_event_multiplier(
        year, month,
        metric="visit",
        tier=user_tier
    )

    visit_chance *= event_mult

    random_num = random.random()
    # print(random_num)
    will_visit = random_num < visit_chance
    # print(user_tier, current_date, day_of_week, visit_chance, random_num, will_visit)
    return "landing_page" if will_visit is True else None

def generate_session_ids(df, current_date):
    date_str = pd.to_datetime(current_date).strftime("%Y%m%d")

    return [
        f"{date_str}-{i:08d}"
        for i in range(1, len(df) + 1)
    ]

def generate_funnel(user_tier, is_continue, current_date):
    if not is_continue:
        return None
    current_step = "landing_page" if is_continue is True else is_continue

    funnel_config = _funnel
    # print(funnel_config)
    funnel_order = funnel_config.get("funnel_order")
    tier_config = _tiers[user_tier]
    
    # tier_duration = tier_config.get(current_step, {}).get("duration", {})
    # base_duration = funnel_config.get(current_step, {}).get("duration", {})
    base_chance = tier_config.get(current_step, {}).get("conversion_rate", funnel_config.get(current_step, {}).get("conversion_rate", {}))

    noise_cfg = tier_config.get("funnel_noise", None)
    if noise_cfg:
        noise_multiplier = apply_noise(base_chance, noise_cfg)
        base_chance = max(0, base_chance * noise_multiplier)

    # Apply Growth
    simulation_start = datetime.strptime(
        _date_config["start_date"], "%Y-%m-%d"
    )
    date_obj = datetime.strptime(current_date, "%Y-%m-%d")

    growth_multiplier = get_growth_multiplier(
        date=date_obj,
        simulation_start=simulation_start,
        growth_cfg=_growth,
        tier_name=user_tier,
        metric="conversion",
    )

    base_chance *= growth_multiplier

    # Apply Event
    year = date_obj.year
    month = date_obj.month
    event_mult = get_event_multiplier(
        year, month,
        metric="conversion",
        tier=user_tier
    )

    base_chance *= event_mult
    
    random_num = random.random()
    # print(random_num)
    # print(base_chance)
    if random_num >= base_chance:
        return None

    # Move to next funnel step
    current_idx = funnel_order.index(current_step)
    next_step = funnel_order[current_idx+1]
    # print(current_idx)
    # print(next_step)
    return next_step

def generate_duration(user_tier, is_continue):
    if not is_continue:
        return None
    # current_step = "landing_page" if is_continue is True else is_continue
    current_step = is_continue
    
    tier_config = _tiers[user_tier]
    
    tier_duration = tier_config.get(current_step, {}).get("duration", {})
    base_duration = _funnel.get(current_step, {}).get("duration", {})

    mean_duration = tier_duration.get(
        "avg_duration",
        base_duration.get("avg_duration", 10)
    )
    min_duration = tier_duration.get(
        "min_duration",
        base_duration.get("min_duration", 5)
    )
    max_duration = tier_duration.get(
        "max_duration",
        base_duration.get("max_duration", 60)
    )
    duration_funnel = controlled_random(mean=mean_duration, min_val=min_duration, max_val=max_duration)
    # print(duration_funnel)
    return duration_funnel

def choose_visit_hour_peak(visit_hour_peak_cfg):
    weight_map = {
        k: v["weight"]
        for k, v in visit_hour_peak_cfg.items()
    }
    return weighted_choice(weight_map)

def sample_hour_from_peak(peak):
    avg = peak["hour"]["avg"]
    min_h = peak["hour"]["min"]
    max_h = peak["hour"]["max"]

    hour = np.random.normal(loc=avg, scale=2)
    return int(np.clip(round(hour), min_h, max_h))

def generate_visit_hour(user_tier, step):
    tier_config = _tiers[user_tier]
    peak_config = tier_config.get("visit_hour_peak", _funnel.get("visit_hour_peak", {}))

    if not peak_config:
        return int(np.clip(round(np.random.normal(loc=19, scale=2)), 0, 23))
    
    peak_key = choose_visit_hour_peak(peak_config)
    peak = peak_config[peak_key]

    return sample_hour_from_peak(peak)

def generate_landing_datetime(current_date, tier, step):
    base = pd.to_datetime(current_date)

    return (
        base
        + pd.to_timedelta(generate_visit_hour(tier, step), unit="h")
        + pd.to_timedelta(random.randint(0, 59), unit="m")
        + pd.to_timedelta(random.randint(0, 59), unit="s")
    )

def advance_datetime(prev_dt, tier, is_continue):
    if not is_continue or prev_dt is None:
        return None

    seconds = generate_duration(tier, is_continue)
    return prev_dt + pd.to_timedelta(seconds, unit="s")

def get_visit_decay_multiplier(days_since_last_visit: int, visit_decay: list) -> float:
    """
    Returns decay multiplier based on days since last visit.
    
    Logic:
    - Use the multiplier of the largest `days` threshold
      that is <= days_since_last_visit
    - If days_since_last_visit is below the first threshold,
      use the first multiplier
    """

    # Safety: sort by days ascending
    visit_decay = sorted(visit_decay, key=lambda x: x["days"])

    multiplier = visit_decay[0]["multiplier"]

    for rule in visit_decay:
        if days_since_last_visit >= rule["days"]:
            multiplier = rule["multiplier"]
        else:
            break

    return multiplier


def generate_funnel_table(current_date):
    import pandas as pd
    visit_decay = _sim.get("visit_decay", [])
    
    base_date = pd.to_datetime(current_date)

    funnel_df = pd.read_csv(BASE_DIR / "output/users_updated.csv")
    funnel_df["last_active_date"] = (
        pd.to_datetime(funnel_df["last_active_date"], format="mixed")
        .dt.normalize()
    )
    funnel_df["recency"] = (base_date - funnel_df["last_active_date"]).dt.days
    funnel_df["visit_decay_multiplier"] = funnel_df["recency"].apply(
        lambda r: get_visit_decay_multiplier(r, visit_decay)
    )

    funnel_order = _funnel.get("funnel_order", [])

    # Determine who visits
    funnel_df[funnel_order[0]] = [
        generate_visit(tier, current_date, decay)
        for tier, decay in zip(
            funnel_df["tier"],
            funnel_df["visit_decay_multiplier"]
        )
    ]

    # Set landing datetime (same for all rows that visited)
    funnel_df[f"{funnel_order[0]}_datetime"] = [
        generate_landing_datetime(base_date, tier, funnel_order[0]) if visited else None
        for tier, visited in zip(funnel_df["tier"], funnel_df[funnel_order[0]])
    ]

    # Keep only visitors
    funnel_df = funnel_df[funnel_df["landing_page"] == "landing_page"].copy()

    # Sort to make session_id deterministic (optional but recommended)
    funnel_df = funnel_df.sort_values("landing_page_datetime").reset_index(drop=True)

    # Generate session_id
    funnel_df["session_id"] = generate_session_ids(funnel_df, current_date)

    # If nobody visited, return an empty dataframe with the expected columns
    if funnel_df.empty:
        return pd.DataFrame(
            columns=[
                "session_id",
                "tier",
                "user_id",
                "landing_page",
                "landing_page_datetime",
                "product_view",
                "product_view_datetime",
                "add_to_cart",
                "add_to_cart_datetime",
                "checkout",
                "checkout_datetime",
                "paid",
                "paid_datetime",
            ]
        )

    funnel_order = _funnel.get("funnel_order", [])
    prev_step = funnel_order[0]

    for step in funnel_order[1:]:
        funnel_df[step] = [
            generate_funnel(tier, prev_value, current_date)
            for tier, prev_value in zip(
                funnel_df["tier"], funnel_df[prev_step]
            )
        ]

        funnel_df[f"{step}_datetime"] = [
            advance_datetime(prev_dt, tier, prev_value)
            for prev_dt, tier, prev_value in zip(
                funnel_df[f"{prev_step}_datetime"],
                funnel_df["tier"],
                funnel_df[prev_step]
            )
        ]

        prev_step = step

    column_list = [
        "session_id",
        "tier",
        "user_id",
        "landing_page",
        "landing_page_datetime",
        "product_view",
        "product_view_datetime",
        "add_to_cart",
        "add_to_cart_datetime",
        "checkout",
        "checkout_datetime",
        "paid",
        "paid_datetime"]
    
    funnel_df = funnel_df[column_list]

    return funnel_df

def funnel_wide_to_activity_log(df):
    if df is None or df.empty:
        return pd.DataFrame(
            columns=["session_id", "tier", "user_id", "activity", "activity_datetime"]
        )

    df = df.copy()

    steps = [
        ("landing_page", "landing_page_datetime"),
        ("product_view", "product_view_datetime"),
        ("add_to_cart", "add_to_cart_datetime"),
        ("checkout", "checkout_datetime"),
        ("paid", "paid_datetime"),
    ]

    rows = []

    for _, row in df.iterrows():
        for activity_col, datetime_col in steps:
            activity = row[activity_col]
            ts = row[datetime_col]

            if pd.notna(activity) and pd.notna(ts):
                rows.append({
                    "session_id": row["session_id"],
                    "tier": row["tier"],
                    "user_id": row["user_id"],
                    "activity": activity,
                    "activity_datetime": ts,
                })

    return pd.DataFrame(rows)

# date_here = date_range("2025-01-01","2025-02-01")
# for i in date_here:
#     generate_funnel_table(i)