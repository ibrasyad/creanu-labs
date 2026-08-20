"""Growth multipliers applied to behavioral rates."""
from .config import get_tiers


def get_simulation_year(date, simulation_start):
    year = date.year - simulation_start.year + 1
    if (date.month, date.day) < (simulation_start.month, simulation_start.day):
        year -= 1
    return max(1, year)


def _value(mapping, *keys):
    current = mapping
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return 1.0
        current = current[key]
    return float(current) if current is not None else 1.0


def get_growth_multiplier(*, date, simulation_start, growth_cfg, tier_name, metric):
    """Compose global, profile, yearly-global and yearly-profile multipliers."""
    simulation_year = get_simulation_year(date, simulation_start)
    yearly_cfg = growth_cfg.get("yearly", {})
    year_key = f"year_{simulation_year}"
    yearly = yearly_cfg.get(year_key, yearly_cfg.get("year_8_plus", {}))
    profile = get_tiers().get(tier_name, {}).get("profile", "balanced")
    base = growth_cfg.get("base", {})
    return (
        _value(base, "overall", metric)
        * _value(base, "tier_profiles", profile, metric)
        * _value(yearly, "overall", metric)
        * _value(yearly, "profile_multipliers", profile, metric)
    )
