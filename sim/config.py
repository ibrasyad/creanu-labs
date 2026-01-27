"""
Centralized configuration loader for all simulation modules.
Includes validation and error handling for configuration files.
"""
import yaml
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class ConfigError(Exception):
    """Raised when configuration is invalid or missing."""
    pass


def load_yaml(path):
    """
    Load and parse a YAML file.
    
    Args:
        path: Path object or string to YAML file
        
    Returns:
        Parsed YAML content (dict or list)
        
    Raises:
        ConfigError: If file doesn't exist or YAML is invalid
    """
    path = Path(path)
    
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    
    try:
        with open(path) as f:
            data = yaml.safe_load(f)
        if data is None:
            raise ConfigError(f"Configuration file is empty: {path}")
        return data
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in {path}: {e}")
    except Exception as e:
        raise ConfigError(f"Error reading {path}: {e}")

def validate_catalog(catalog_dict):
    """
    Validate catalog structure.

    Expected structure:
    category -> subcategory -> { cooldown, product }
    product -> product_name -> { base_price }
    """
    if not isinstance(catalog_dict, dict):
        raise ConfigError("Catalog must be a dictionary of categories")

    for category, subcats in catalog_dict.items():
        if not isinstance(subcats, dict):
            raise ConfigError(f"Category '{category}' must contain subcategories")

        for subcat_name, subcat_cfg in subcats.items():
            if not isinstance(subcat_cfg, dict):
                raise ConfigError(
                    f"Subcategory '{subcat_name}' in '{category}' must be a dict"
                )

            # ---- cooldown (optional but must be valid if present)
            cooldown = subcat_cfg.get("cooldown")
            if cooldown is not None and (
                not isinstance(cooldown, int) or cooldown < 0
            ):
                raise ConfigError(
                    f"Subcategory '{subcat_name}' cooldown must be a non-negative int"
                )

            # ---- product block (required)
            products = subcat_cfg.get("product")
            if not isinstance(products, dict) or not products:
                raise ConfigError(
                    f"Subcategory '{subcat_name}' must contain a 'product' dict"
                )

            for product_name, attrs in products.items():
                if not isinstance(attrs, dict):
                    raise ConfigError(
                        f"Product '{product_name}' in '{subcat_name}' must be a dict"
                    )

                if "base_price" not in attrs:
                    raise ConfigError(
                        f"Product '{product_name}' missing 'base_price'"
                    )

                if (
                    not isinstance(attrs["base_price"], (int, float))
                    or attrs["base_price"] <= 0
                ):
                    raise ConfigError(
                        f"Product '{product_name}' base_price must be a positive number"
                    )


# def validate_catalog(catalog_dict):
#     """
#     Validate catalog structure.
    
#     Args:
#         catalog_dict: Catalog configuration dict
        
#     Raises:
#         ConfigError: If catalog is invalid
#     """
#     if not isinstance(catalog_dict, dict):
#         raise ConfigError("Catalog must be a dictionary of categories")
    
#     for category, subcats in catalog_dict.items():
#         if not isinstance(subcats, dict):
#             raise ConfigError(f"Category '{category}' must contain subcategories")
        
#         for subcat, products in subcats.get("product", {}).items():
#             if not isinstance(products, dict):
#                 raise ConfigError(f"Subcategory '{subcat}' must contain products")
            
#             for product, attrs in products.items():
#                 if not isinstance(attrs, dict) or "base_price" not in attrs:
#                     raise ConfigError(f"Product '{product}' must have 'base_price'")
                
#                 if not isinstance(attrs["base_price"], (int, float)) or attrs["base_price"] <= 0:
#                     raise ConfigError(f"Product '{product}' base_price must be positive number")


def validate_tiers(tiers_dict):
    """
    Validate tiers configuration structure.
    
    Args:
        tiers_dict: Tiers configuration dict
        
    Raises:
        ConfigError: If tiers are invalid
    """
    if not isinstance(tiers_dict, dict) or not tiers_dict:
        raise ConfigError("Tiers must be a non-empty dictionary")
    
    for tier_name, tier_config in tiers_dict.items():
        if not isinstance(tier_config, dict):
            raise ConfigError(f"Tier '{tier_name}' configuration must be a dict")
        
        # Validate basket config
        if "basket" in tier_config:
            basket = tier_config["basket"]
            if "min_items" in basket and "max_items" in basket:
                if basket["min_items"] > basket["max_items"]:
                    raise ConfigError(
                        f"Tier '{tier_name}': min_items ({basket['min_items']}) "
                        f"cannot exceed max_items ({basket['max_items']})"
                    )


def validate_date_config(date_dict):
    """
    Validate date configuration.
    
    Args:
        date_dict: Date configuration dict
        
    Raises:
        ConfigError: If date config is invalid
    """
    if "start_date" not in date_dict or "end_date" not in date_dict:
        raise ConfigError("Date config must contain 'start_date' and 'end_date'")
    
    # Validate date format (basic check)
    for date_field in ["start_date", "end_date"]:
        date_str = date_dict[date_field]
        try:
            from datetime import datetime
            datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            raise ConfigError(f"Invalid date format in '{date_field}': {date_str}. Expected YYYY-MM-DD")


def _load_tiers_from_directory():
    """
    Load all tier configurations from individual YAML files in config/tiers/ directory.
    
    Returns:
        Dict with merged tier configurations
        
    Raises:
        ConfigError: If tier loading fails
    """
    tiers_dir = BASE_DIR / "config/tiers"
    
    if not tiers_dir.exists():
        raise ConfigError(f"Tiers directory not found: {tiers_dir}")
    
    merged_tiers = {}
    yaml_files = sorted(tiers_dir.glob("*.yaml"))
    
    if not yaml_files:
        raise ConfigError(f"No YAML files found in {tiers_dir}")
    
    for yaml_file in yaml_files:
        # Skip template file
        if yaml_file.name.startswith("_"):
            continue
        
        try:
            tier_data = load_yaml(yaml_file)
            if isinstance(tier_data, dict):
                merged_tiers.update(tier_data)
            else:
                raise ConfigError(f"Tier file {yaml_file.name} must contain a dictionary")
        except ConfigError:
            raise
        except Exception as e:
            raise ConfigError(f"Error loading tier file {yaml_file.name}: {e}")
    
    if not merged_tiers:
        raise ConfigError(f"No tier configurations found in {tiers_dir}")
    
    return merged_tiers


def _load_and_validate_configs():
    """
    Load and validate all configuration files.
    
    Returns:
        Tuple of (catalog, tiers, simulation, date_config)
        
    Raises:
        ConfigError: If any configuration is invalid
    """
    try:
        # Load all configs
        catalog_data = load_yaml(BASE_DIR / "config/catalog.yaml")
        tiers = _load_tiers_from_directory()
        sim_data = load_yaml(BASE_DIR / "config/simulation.yaml")
        date_data = load_yaml(BASE_DIR / "config/date.yaml")
        funnel_data = load_yaml(BASE_DIR / "config/funnel.yaml")
        growth_data = load_yaml(BASE_DIR / "config/growth.yaml")
        event_data = load_yaml(BASE_DIR / "config/event.yaml")
        
        # Extract root keys
        catalog = catalog_data.get("catalog")
        simulation = sim_data.get("simulation")
        date_config = date_data.get("date")
        funnel = funnel_data.get("funnel")
        growth = growth_data.get("growth")
        event = event_data.get("event")
        
        # Validate structure
        if not catalog:
            raise ConfigError("'catalog' key missing from catalog.yaml")
        if not tiers:
            raise ConfigError("No tiers found in config/tiers/ directory")
        if not simulation:
            raise ConfigError("'simulation' key missing from simulation.yaml")
        if not date_config:
            raise ConfigError("'date' key missing from date.yaml")
        if not funnel:
            raise ConfigError("'funnel' key missing from funnel.yaml")
        if not growth:
            raise ConfigError("'growth' key missing from growth.yaml")
        if not event:
            raise ConfigError("'event' key missing from growth.yaml")
        
        # Validate content
        validate_catalog(catalog)
        validate_tiers(tiers)
        validate_date_config(date_config)
        
        return catalog, tiers, simulation, date_config, funnel, growth, event
        
    except ConfigError:
        raise
    except Exception as e:
        raise ConfigError(f"Unexpected error loading configuration: {e}")


# Load all configs at module level with validation
try:
    _catalog, _tiers, _sim, _date_config, _funnel, _growth, _event = _load_and_validate_configs()
except ConfigError as e:
    raise SystemExit(f"Configuration Error: {e}")


# Public accessors
def get_catalog():
    """
    Get the product catalog.
    
    Returns:
        Dict with structure: category → subcategory → product → base_price
    """
    return _catalog


def get_tiers():
    """
    Get customer tier configurations.
    
    Returns:
        Dict with tier names as keys, tier configs as values
    """
    return _tiers


def get_simulation():
    """
    Get global simulation defaults.
    
    Returns:
        Dict with simulation settings
    """
    return _sim


def get_date_config():
    """
    Get date range and transaction volume configuration.
    
    Returns:
        Dict with date settings
    """
    return _date_config

def get_funnel_config():
    return _funnel

def get_growth_config():
    return _growth

def get_event_config():
    return _event