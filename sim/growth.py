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

DAYS_IN_YEAR = 365


def get_simulation_year(current_date, simulation_start):
    delta_days = (current_date - simulation_start).days
    return delta_days // DAYS_IN_YEAR + 1


def resolve_year_key(year, yearly_cfg):
    key = f"year_{year}"
    if key in yearly_cfg:
        return key
    if "year_8_plus" in yearly_cfg and year >= 8:
        return "year_8_plus"
    return None


def get_daily_growth_multiplier(
    *,
    date,
    simulation_start,
    growth_cfg,
    tier_name,
    metric="new_user",
):
    """
    Returns DAILY multiplier derived from YEARLY intent
    """

    year = get_simulation_year(date, simulation_start)
    yearly_cfg = growth_cfg.get("yearly", {})

    year_key = resolve_year_key(year, yearly_cfg)
    if not year_key:
        return 1.0

    year_block = yearly_cfg[year_key]

    # ---- overall yearly intent
    overall_yearly = (
        year_block
        .get("overall", {})
        .get(metric, 1.0)
    )

    # ---- tier yearly intent
    tier_yearly = (
        year_block
        .get("tiers", {})
        .get(tier_name, 1.0)
    )

    yearly_multiplier = overall_yearly * tier_yearly

    # Convert annual intent → daily-safe multiplier
    daily_multiplier = yearly_multiplier ** (1 / DAYS_IN_YEAR)

    return daily_multiplier
