import random
import numpy as np
import sys
from pathlib import Path

from pandas import date_range

# Handle both module import and direct script execution
try:
    from .config import get_catalog, get_tiers, get_simulation, get_date_config
    from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name
except ImportError:
    # Allow running as a script
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_catalog, get_tiers, get_simulation, get_date_config
    from utils import weighted_choice, apply_noise, get_day_of_week, get_month_name

# Cache configs
_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()

def get_base_user(tier_name):
    base_user = _tiers[tier_name]["base_user"]
    return base_user

def generate_user_id(date, user_counter):
    # Generate user_id as yyyymmddUUUUUU format
    date_str = date.replace("-", "")
    user_id = f"{date_str}{user_counter:06d}"
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
        })

    return rows

def get_daily_new_user_chance(tier_name):
    tier_cfg = _tiers[tier_name]
    base_chance = tier_cfg.get("daily_new_user_chance", 0)
    noise_cfg = tier_cfg.get("daily_new_user_noise", None)
    if noise_cfg:
        noise = apply_noise(base_chance, noise_cfg)
        return max(0, noise)
    return base_chance

def get_daily_new_user_chance_weekend(tier_name):
    tier_cfg = _tiers[tier_name]
    base_chance = tier_cfg.get("daily_new_user_chance_weekend", 0.0)
    noise_cfg = tier_cfg.get("daily_new_user_noise", None)
    if noise_cfg:
        noise = apply_noise(base_chance, noise_cfg)
        return max(0, noise)
    return base_chance

def roll_new_user_chance(tier_name, date):
    tier_cfg = _tiers[tier_name]
    month_name = get_month_name(date)
    day_of_week = get_day_of_week(date)

    # Determine the chance based on day type and add month multiplier
    if day_of_week in ["saturday", "sunday"]:
        chance = get_daily_new_user_chance_weekend(tier_name) * tier_cfg.get("monthly_new_user_multiplier", {}).get(month_name, 1.0)
    else:
        chance = get_daily_new_user_chance(tier_name) * tier_cfg.get("monthly_new_user_multiplier", {}).get(month_name, 1.0)
    
    # Apply monthly noise
    noise_cfg = tier_cfg.get("monthly_new_user_noise", None)
    if noise_cfg:
        noise = apply_noise(chance, noise_cfg)
        chance = max(0, noise)
        chance = min(max(chance, 0), 1)

    retries = tier_cfg.get("daily_retry", 1)
    for retry in range(retries):
        roll = random.random()
        roll_result = roll < chance
        if roll_result:
            return True
    return False

def generate_new_users(roll_result, tier_name, date, base_user_table):
    if not roll_result:
        return []
    
    user_id_counter = base_user_table + 1
    rows = []
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
        date_str = date.strftime("%Y-%m-%d")
        for tier_name in _tiers.keys():
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