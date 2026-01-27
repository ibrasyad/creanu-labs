import random
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Handle both module import and direct script execution
try:
    from .config import get_catalog, get_tiers, get_simulation, get_date_config, get_growth_config
    from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, date_range
    from .growth import get_growth_multiplier
except ImportError:
    # Allow running as a script
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_catalog, get_tiers, get_simulation, get_date_config, get_growth_config
    from utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, date_range
    from growth import get_growth_multiplier
    

# Cache configs
_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()
_growth = get_growth_config()

def get_base_user(tier_name):
    base_user = _tiers[tier_name]["base_user"]
    return base_user

def generate_user_id(date, user_counter):
    # Generate user_id as yyyymmddUUUUUU format
    date_str = date.replace("-", "")
    user_id = f"{date_str}-{user_counter:08d}"
    return user_id

def generate_base_user_table():
    rows = []

    # Build tier list
    tier_list = []
    for tier_name, tier in _tiers.items():
        base_user = tier.get("base_user", 0)
        if base_user > 0:
            tier_list.extend([tier_name] * base_user)

    # Shuffle tiers
    random.shuffle(tier_list)

    # Assign IDs sequentially
    for i, tier_name in enumerate(tier_list, start=1):
        user_id = generate_user_id(_date_config["start_date"], i)
        rows.append({
            "tier": tier_name,
            "user_id": user_id,
            "registered_date": _date_config["start_date"],
            "last_active_date": _date_config["start_date"]
        })

    return rows

def get_daily_new_user_chance(tier_name):
    tier_cfg = _tiers[tier_name]
    base_chance = tier_cfg.get("daily_new_user_chance", 0)
    noise_cfg = tier_cfg.get("daily_new_user_noise", None)
    if noise_cfg:
        noise_multiplier = apply_noise(base_chance, noise_cfg)
        return max(0, base_chance * noise_multiplier)
    return base_chance

def get_daily_new_user_chance_weekend(tier_name):
    tier_cfg = _tiers[tier_name]
    base_chance = tier_cfg.get("daily_new_user_chance_weekend", 0.0)
    noise_cfg = tier_cfg.get("daily_new_user_noise", None)
    if noise_cfg:
        noise_multiplier = apply_noise(base_chance, noise_cfg)
        return max(0, base_chance * noise_multiplier)
    return base_chance

def roll_new_user_chance(tier_name, date):
    tier_cfg = _tiers[tier_name]
    month_name = get_month_name(date)
    day_of_week = get_day_of_week(date)

    # --------------------
    # BASE CHANCE
    # --------------------
    if day_of_week in ["saturday", "sunday"]:
        chance = get_daily_new_user_chance_weekend(tier_name)
    else:
        chance = get_daily_new_user_chance(tier_name)

    # --------------------
    # MONTHLY SEASONALITY
    # --------------------
    chance *= tier_cfg.get("monthly_new_user_multiplier", {}).get(month_name, 1.0)

    # --------------------
    # MONTHLY NOISE
    # --------------------
    noise_cfg = tier_cfg.get("monthly_new_user_noise")
    if noise_cfg:
        chance *= apply_noise(chance, noise_cfg)

    # --------------------
    # APPLY GROWTH (BEFORE ROLL)
    # --------------------
    simulation_start = datetime.strptime(
        _date_config["start_date"], "%Y-%m-%d"
    )
    date_obj = datetime.strptime(date, "%Y-%m-%d")

    growth_multiplier = get_growth_multiplier(
        date=date_obj,
        simulation_start=simulation_start,
        growth_cfg=_growth,
        tier_name=tier_name,
        metric="new_user",
    )

    chance *= growth_multiplier

    # --------------------
    # FINAL CLAMP
    # --------------------
    chance = max(0.0, min(chance, 1.0))

    # --------------------
    # BERNOULLI TRIALS
    # --------------------
    retries = tier_cfg.get("daily_retry", 1)
    successes = 0

    for _ in range(retries):
        if random.random() < chance:
            successes += 1

    return successes


def generate_new_users(num_users, tier_name, date, current_user_count):
    if not num_users:
        return []
    
    rows = []
    for i in range(num_users):
        user_id_counter = current_user_count + i + 1
        user_id = generate_user_id(date, user_id_counter)
        row = {
            "tier": tier_name,
            "user_id": user_id,
        }
        rows.append(row)
    return rows

def generate_users(dates):
    import pandas as pd
    base_table = generate_base_user_table()

    base_user_table = pd.DataFrame(base_table)
    base_user_table.to_csv("output/users_base.csv", index=False)

    # Generate new users for the date
    new_user_rows = []
    current_user_count = len(base_user_table)

    for date in dates:
        tier_names = list(_tiers.keys())
        random.shuffle(tier_names)
        date_str = date
        for tier_name in tier_names:
            roll = roll_new_user_chance(tier_name, date_str)
            new_users = generate_new_users(roll, tier_name, date_str, current_user_count)
            if new_users:
                new_user_rows.extend(new_users)
                current_user_count += len(new_users)

        
    if new_user_rows:
        new_user_table = pd.DataFrame(new_user_rows)
        new_user_table.to_csv("output/users_new.csv", index=False)
        final_user_table = pd.concat([base_user_table, new_user_table], ignore_index=True)
        final_user_table.to_csv("output/users_updated.csv", index=False)


if __name__ == "__main__":
    start_date = _date_config["start_date"]
    end_date = _date_config["end_date"]
    dates = date_range(start=start_date, end=end_date)
    generate_users(dates)