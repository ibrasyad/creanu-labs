"""Campaign and event multipliers."""
from .config import get_event_config, get_tiers

_event = get_event_config()


def is_event_active(event, simulation_year, current_month):
    """Events are configured in simulation years, not calendar years."""
    if simulation_year != event["year"] or current_month < event.get("start_month", 1):
        return False
    end_month = event.get("end_month")
    return end_month is None or current_month <= end_month


def get_metric_multiplier(metric_cfg, funnel_step=None):
    if metric_cfg is None:
        return 1.0
    if isinstance(metric_cfg, (int, float)):
        return float(metric_cfg)
    if isinstance(metric_cfg, dict) and funnel_step:
        return float(metric_cfg.get(funnel_step, 1.0))
    return 1.0


def get_event_multiplier(simulation_year, current_month, metric, tier=None, funnel_step=None):
    """Return cumulative active-event effects with tier > profile > overall precedence."""
    profile = get_tiers().get(tier, {}).get("profile") if tier else None
    multiplier = 1.0
    for event in _event.values():
        if not is_event_active(event, simulation_year, current_month):
            continue
        metric_cfg = event.get("tiers", {}).get(tier, {}).get(metric)
        if metric_cfg is None and profile:
            metric_cfg = event.get("profiles", {}).get(profile, {}).get(metric)
        if metric_cfg is None:
            metric_cfg = event.get("overall", {}).get(metric)
        multiplier *= get_metric_multiplier(metric_cfg, funnel_step)
    return multiplier
