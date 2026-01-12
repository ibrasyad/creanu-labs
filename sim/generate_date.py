import yaml, random
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------
# Load configs once
# ------------------------

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

catalog = load_yaml(BASE_DIR / "config/catalog.yaml")["catalog"]
tiers = load_yaml(BASE_DIR / "config/tiers.yaml")["tiers"]
sim = load_yaml(BASE_DIR / "config/simulation.yaml")["simulation"]

# ------------------------
# Helpers
# ------------------------

def weighted_choice(d):
    keys = list(d.keys())
    weights = list(d.values())
    return random.choices(keys, weights)[0]

def date_list(start_date, end_date):
    """Generate a list of dates between start_date and end_date (inclusive)"""
    from datetime import datetime, timedelta

    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    delta = end - start

    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]

def day_of_week(date_str):
    """Return the weekday name for a given date string (YYYY-MM-DD)"""
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    return date_obj.strftime("%A").lower()