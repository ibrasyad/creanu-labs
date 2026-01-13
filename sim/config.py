"""
Centralized configuration loader for all simulation modules.
"""
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def load_yaml(path):
    """Load and parse a YAML file."""
    with open(path) as f:
        return yaml.safe_load(f)


# Load all configs once at module level
_catalog = load_yaml(BASE_DIR / "config/catalog.yaml")["catalog"]
_tiers = load_yaml(BASE_DIR / "config/tiers.yaml")["tiers"]
_sim = load_yaml(BASE_DIR / "config/simulation.yaml")["simulation"]
_date_config = load_yaml(BASE_DIR / "config/date.yaml")["date"]


# Public accessors
def get_catalog():
    return _catalog


def get_tiers():
    return _tiers


def get_simulation():
    return _sim


def get_date_config():
    return _date_config
