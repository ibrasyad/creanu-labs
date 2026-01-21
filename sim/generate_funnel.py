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
    current_step = "landing_page" if is_continue is True else is_continue
    
    funnel_config = get_funnel_config()
    tier_config = _tiers[user_tier]
    
    tier_duration = tier_config.get(current_step, {}).get("duration", {})
    base_duration = funnel_config.get(current_step, {}).get("duration", {})

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



# generate_funnel("budget_tier", True)

# def generate_funnel_table(current_date):
#     import pandas as pd

#     funnel_df = pd.read_csv(BASE_DIR / "output/users_updated.csv")
#     funnel_df["landing_page"] = funnel_df.apply(
#         lambda df: generate_visit(df["tier"], current_date), axis=1
#     )

#     funnel_df["landing_page_datetime"] = current_date

#     funnel_df = funnel_df[funnel_df["landing_page"] == "landing_page"].copy()

#     funnel_df["product_view"] = funnel_df.apply(
#         lambda df: generate_funnel(df["tier"], df["landing_page"]), axis=1
#     )

#     funnel_df["add_to_cart"] = funnel_df.apply(
#         lambda df: generate_funnel(df["tier"], df["product_view"]), axis=1
#     )

#     funnel_df["checkout"] = funnel_df.apply(
#         lambda df: generate_funnel(df["tier"], df["add_to_cart"]), axis=1
#     )

#     funnel_df["paid"] = funnel_df.apply(
#         lambda df: generate_funnel(df["tier"], df["checkout"]), axis=1
#     )

#     return funnel_df

def generate_funnel_table(current_date):
    import pandas as pd

    funnel_df = pd.read_csv(BASE_DIR / "output/users_updated.csv")

    # Determine who visits
    funnel_df["landing_page"] = [
        generate_visit(tier, current_date) for tier in funnel_df["tier"]
    ]

    # Set landing datetime (same for all rows that visited)
    funnel_df["landing_page_datetime"] = current_date

    # Keep only visitors
    funnel_df = funnel_df[funnel_df["landing_page"] == "landing_page"].copy()

    # If nobody visited, return an empty dataframe with the expected columns
    if funnel_df.empty:
        return pd.DataFrame(
            columns=[
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

    # Use list comprehensions to ensure scalar outputs (avoid .apply returning Series/DataFrame)
    funnel_df["product_view"] = [
        generate_funnel(tier, landing) for tier, landing in zip(funnel_df["tier"], funnel_df["landing_page"])
    ]

    funnel_df["add_to_cart"] = [
        generate_funnel(tier, pv) for tier, pv in zip(funnel_df["tier"], funnel_df["product_view"])
    ]

    funnel_df["checkout"] = [
        generate_funnel(tier, atc) for tier, atc in zip(funnel_df["tier"], funnel_df["add_to_cart"])
    ]

    funnel_df["paid"] = [
        generate_funnel(tier, out) for tier, out in zip(funnel_df["tier"], funnel_df["checkout"])
    ]

    # (Optionally) fill datetime columns for steps that happened. If your generate_duration returns durations,
    # you can compute datetimes here — for now set to current_date or None as in your original approach:
    funnel_df["product_view_datetime"] = funnel_df["product_view"].apply(lambda v: current_date if v else None)
    funnel_df["add_to_cart_datetime"] = funnel_df["add_to_cart"].apply(lambda v: current_date if v else None)
    funnel_df["checkout_datetime"] = funnel_df["checkout"].apply(lambda v: current_date if v else None)
    funnel_df["paid_datetime"] = funnel_df["paid"].apply(lambda v: current_date if v else None)

    column_list = ["tier",
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
            columns=["tier", "user_id", "activity", "activity_datetime"]
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
                    "tier": row["tier"],
                    "user_id": row["user_id"],
                    "activity": activity,
                    "activity_datetime": ts,
                })

    return pd.DataFrame(rows)

# date_here = date_range("2025-01-01","2025-02-01")
# for i in date_here:
#     generate_funnel_table(i)