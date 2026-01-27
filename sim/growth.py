import random
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Handle both module import and direct script execution
try:
    from .config import get_catalog, get_tiers, get_simulation, get_date_config, get_growth_config
    from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, date_range
except ImportError:
    # Allow running as a script
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_catalog, get_tiers, get_simulation, get_date_config, get_growth_config
    from utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, date_range

# Cache configs
_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()
_growth = get_growth_config()


def get_simulation_year(date, simulation_start):
    """
    Year 1 = simulation_start.year
    Year 2 = simulation_start.year + 1
    etc.
    """
    return date.year - simulation_start.year + 1


def resolve_year_key(year, yearly_cfg):
    key = f"year_{year}"
    if key in yearly_cfg:
        return key
    if "year_8_plus" in yearly_cfg and year >= 8:
        return "year_8_plus"
    return None

def get_nested(cfg, *keys):
    val = cfg
    for k in keys:
        if val is None:
            return None
        val = val.get(k)
    return val


def get_growth_multiplier(
    *,
    date,
    simulation_start,
    growth_cfg,
    tier_name,
    metric,
):
    sim_year = date.year - simulation_start.year + 1

    year_key = f"year_{sim_year}"
    if year_key not in growth_cfg["yearly"]:
        year_key = "year_8_plus"

    yearly = growth_cfg["yearly"].get(year_key, {})
    base = growth_cfg.get("base", {})

    return (
        # 1️⃣ yearly tier
        get_nested(yearly, "tiers", tier_name, metric)
        # 2️⃣ yearly overall
        or get_nested(yearly, "overall", metric)
        # 3️⃣ base tier
        or get_nested(base, "tiers", tier_name, metric)
        # 4️⃣ base overall
        or get_nested(base, "overall", metric)
        # 5️⃣ default
        or 1.0
    )