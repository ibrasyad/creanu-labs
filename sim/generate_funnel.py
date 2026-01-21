import random
import numpy as np
import sys
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent

# Handle both module import and direct script execution
try:
    from .config import get_catalog, get_tiers, get_simulation, get_date_config, get_funnel_config
    from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, controlled_random, date_range
except ImportError:
    # Allow running as a script
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_catalog, get_tiers, get_simulation, get_date_config, get_funnel_config
    from utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, controlled_random, date_range

# Cache configs
_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()
_funnel = get_funnel_config()



def generate_visit(user_tier, current_date):
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

def generate_funnel(user_tier, is_continue):
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

def sample_hour_from_peak(peak_cfg):
    hour_cfg = peak_cfg["hour"]

    return int(
        controlled_random(
            mean=hour_cfg["avg"],
            min_val=hour_cfg["min"],
            max_val=hour_cfg["max"]
        )
    )

def generate_visit_hour(user_tier, step):
    tier_config = _tiers[user_tier]
    peak_config = tier_config.get("visit_hour_peak", _funnel.get("visit_hour_peak", {}))

    if not peak_config:
        return int(controlled_random(12, 0, 23))
    
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

def generate_funnel_table(current_date):
    import pandas as pd
    base_date = pd.to_datetime(current_date)

    funnel_df = pd.read_csv(BASE_DIR / "output/users_updated.csv")
    funnel_order = _funnel.get("funnel_order", [])

    # Determine who visits
    funnel_df[funnel_order[0]] = [
        generate_visit(tier, current_date) for tier in funnel_df["tier"]
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
            generate_funnel(tier, prev_value)
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