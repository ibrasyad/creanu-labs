import random
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Handle both module import and direct script execution
try:
    from .config import get_catalog, get_tiers, get_simulation, get_date_config, get_growth_config, get_event_config
    from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, date_range
except ImportError:
    # Allow running as a script
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_catalog, get_tiers, get_simulation, get_date_config, get_growth_config, get_event_config
    from utils import weighted_choice, apply_noise, get_day_of_week, get_month_name, date_range

# Cache configs
_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()
_growth = get_growth_config()
_event = get_event_config()


def is_event_active(event, current_year, current_month):
    """Check if event is active at a given time"""
    start = (event["year"], event["start_month"])
    end_month = event.get("end_month")

    current = (current_year, current_month)

    if current < start:
        return False

    if end_month is None:
        return True

    end = (event["year"], end_month)
    return current <= end


def get_metric_multiplier(metric_cfg, funnel_step=None):
    """
    Metric config can be:
    - float -> global
    - dict -> per funnel step
    """
    if metric_cfg is None:
        return 1.0

    if isinstance(metric_cfg, (int, float)):
        return metric_cfg

    if isinstance(metric_cfg, dict) and funnel_step:
        return metric_cfg.get(funnel_step, 1.0)

    return 1.0


def get_event_multiplier(
    current_year,
    current_month,
    metric,
    tier=None,
    funnel_step=None
):
    """
    Returns the cumulative multiplier from all active events
    """

    multiplier = 1.0

    for event in _event.values():
        if not is_event_active(event, current_year, current_month):
            continue

        # 1️⃣ tier-level overrides
        tier_cfg = event.get("tiers", {}).get(tier, {})
        metric_cfg = tier_cfg.get(metric)

        if metric_cfg is not None:
            multiplier *= get_metric_multiplier(metric_cfg, funnel_step)
            continue  # tier overrides overall

        # 2️⃣ overall fallback
        overall_cfg = event.get("overall", {})
        metric_cfg = overall_cfg.get(metric)

        if metric_cfg is not None:
            multiplier *= get_metric_multiplier(metric_cfg, funnel_step)

    return multiplier