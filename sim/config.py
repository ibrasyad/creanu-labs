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
    
    valid_profiles = {'conservative', 'aggressive', 'balanced'}
    valid_priorities = {'low', 'medium', 'high'}
    
    for tier_name, tier_config in tiers_dict.items():
        if not isinstance(tier_config, dict):
            raise ConfigError(f"Tier '{tier_name}' configuration must be a dict")
        
        # Validate profile metadata (REQUIRED)
        if 'profile' not in tier_config:
            raise ConfigError(f"Tier '{tier_name}' must specify a profile")
        
        profile = tier_config['profile']
        if profile not in valid_profiles:
            raise ConfigError(f"Tier '{tier_name}' has invalid profile '{profile}'. Must be one of: {valid_profiles}")
        
        # Validate priority metadata (optional)
        if 'priority' in tier_config:
            priority = tier_config['priority']
            if priority not in valid_priorities:
                raise ConfigError(f"Tier '{tier_name}' has invalid priority '{priority}'. Must be one of: {valid_priorities}")
        
        # Validate description (optional)
        if 'description' in tier_config:
            description = tier_config['description']
            if not isinstance(description, str):
                raise ConfigError(f"Tier '{tier_name}' description must be a string")
        
        # Validate basket config
        if "basket" in tier_config:
            basket = tier_config["basket"]
            if not isinstance(basket, dict):
                raise ConfigError(f"Tier '{tier_name}' basket configuration must be a dictionary")
            
            if "min_items" in basket and "max_items" in basket:
                min_items = basket["min_items"]
                max_items = basket["max_items"]
                
                if not isinstance(min_items, int) or not isinstance(max_items, int):
                    raise ConfigError(f"Tier '{tier_name}' basket min_items and max_items must be integers")
                
                if min_items < 0 or max_items < 0:
                    raise ConfigError(f"Tier '{tier_name}' basket item counts cannot be negative")
                
                if min_items > max_items:
                    raise ConfigError(
                        f"Tier '{tier_name}': min_items ({min_items}) "
                        f"cannot exceed max_items ({max_items})"
                    )
        
        # Validate visit chance configuration
        if "visit_chance" in tier_config:
            visit_chance = tier_config["visit_chance"]
            if not isinstance(visit_chance, dict):
                raise ConfigError(f"Tier '{tier_name}' visit_chance must be a dictionary")
            
            valid_days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
            for day in valid_days:
                if day in visit_chance:
                    chance = visit_chance[day]
                    if not isinstance(chance, (int, float)) or not (0 <= chance <= 1):
                        raise ConfigError(f"Tier '{tier_name}' {day} visit chance '{chance}' must be between 0 and 1")


def validate_growth_config(growth_dict):
    """
    Validate growth configuration structure.
    
    Args:
        growth_dict: Growth configuration dict
        
    Raises:
        ConfigError: If growth config is invalid
    """
    if not isinstance(growth_dict, dict):
        raise ConfigError("Growth configuration must be a dictionary")
    
    # Validate base configuration
    if 'base' not in growth_dict:
        raise ConfigError("Growth configuration must contain 'base' section")
    
    base = growth_dict['base']
    if not isinstance(base, dict):
        raise ConfigError("Growth base configuration must be a dictionary")
    
    if 'tier_profiles' not in base:
        raise ConfigError("Growth base configuration must contain 'tier_profiles'")
    
    # Validate tier profiles
    tier_profiles = base['tier_profiles']
    valid_profiles = {'conservative', 'aggressive', 'balanced'}
    valid_metrics = {'new_user', 'visit', 'conversion'}
    
    if not isinstance(tier_profiles, dict):
        raise ConfigError("Growth tier_profiles must be a dictionary")
    
    for profile_name, profile_config in tier_profiles.items():
        if profile_name not in valid_profiles:
            raise ConfigError(f"Invalid growth profile '{profile_name}'. Must be one of: {valid_profiles}")
        
        if not isinstance(profile_config, dict):
            raise ConfigError(f"Growth profile '{profile_name}' must be a dictionary")
        
        for metric in valid_metrics:
            if metric not in profile_config:
                raise ConfigError(f"Growth profile '{profile_name}' must contain '{metric}' metric")
            
            value = profile_config[metric]
            if not isinstance(value, (int, float)) or value < 0:
                raise ConfigError(f"Growth profile '{profile_name}' {metric} value '{value}' must be non-negative number.")
    
    # Validate yearly configuration
    if 'yearly' in growth_dict:
        yearly = growth_dict['yearly']
        if not isinstance(yearly, dict):
            raise ConfigError("Growth yearly configuration must be a dictionary")
        
        valid_year_keys = [f"year_{i}" for i in range(1, 9)] + ["year_8_plus"]
        
        for year_key, year_config in yearly.items():
            if year_key not in valid_year_keys:
                raise ConfigError(f"Invalid year key '{year_key}'. Must be one of: {valid_year_keys}")
            
            if not isinstance(year_config, dict):
                raise ConfigError(f"Year '{year_key}' configuration must be a dictionary")
            
            if 'profile_multipliers' not in year_config:
                raise ConfigError(f"Year '{year_key}' must contain 'profile_multipliers'")
            
            profile_multipliers = year_config['profile_multipliers']
            if not isinstance(profile_multipliers, dict):
                raise ConfigError(f"Year '{year_key}' profile_multipliers must be a dictionary")
            
            for profile_name, multiplier_config in profile_multipliers.items():
                if profile_name not in valid_profiles:
                    raise ConfigError(f"Invalid profile multiplier '{profile_name}' in year '{year_key}'. Must be one of: {valid_profiles}")
                
                if not isinstance(multiplier_config, dict):
                    raise ConfigError(f"Profile multiplier '{profile_name}' in year '{year_key}' must be a dictionary")
                
                for metric in valid_metrics:
                    if metric not in multiplier_config:
                        raise ConfigError(f"Profile multiplier '{profile_name}' in year '{year_key}' must contain '{metric}' metric")
                    
                    value = multiplier_config[metric]
                    if not isinstance(value, (int, float)) or value < 0:
                        raise ConfigError(f"Profile multiplier '{profile_name}' {metric} value '{value}' in year '{year_key}' must be non-negative number.")


def validate_event_config(event_dict):
    """
    Validate event configuration structure.
    
    Args:
        event_dict: Event configuration dict
        
    Raises:
        ConfigError: If event config is invalid
    """
    if not isinstance(event_dict, dict):
        raise ConfigError("Event configuration must be a dictionary")
    
    valid_profiles = {'conservative', 'aggressive', 'balanced'}
    valid_metrics = {'new_user', 'visit', 'conversion'}
    
    for event_name, event_config in event_dict.items():
        if not isinstance(event_config, dict):
            raise ConfigError(f"Event '{event_name}' configuration must be a dictionary")
        
        # Validate required fields
        if 'year' not in event_config:
            raise ConfigError(f"Event '{event_name}' missing required 'year' field")
        
        year = event_config['year']
        if not isinstance(year, int) or year < 1:
            raise ConfigError(f"Event '{event_name}' has invalid year '{year}'. Must be positive integer.")
        
        # Validate month fields
        start_month = event_config.get('start_month', 1)
        end_month = event_config.get('end_month')
        
        if not isinstance(start_month, int) or not (1 <= start_month <= 12):
            raise ConfigError(f"Event '{event_name}' has invalid start_month '{start_month}'. Must be 1-12.")
        
        if end_month is not None:
            if not isinstance(end_month, int) or not (1 <= end_month <= 12):
                raise ConfigError(f"Event '{event_name}' has invalid end_month '{end_month}'. Must be 1-12.")
            if start_month > end_month:
                raise ConfigError(f"Event '{event_name}' start_month ({start_month}) cannot be greater than end_month ({end_month}).")
        
        # Validate overall effects
        overall = event_config.get('overall', {})
        if not isinstance(overall, dict):
            raise ConfigError(f"Event '{event_name}' overall effects must be a dictionary")
        
        for metric in overall:
            if metric not in valid_metrics:
                raise ConfigError(f"Event '{event_name}' has invalid overall metric '{metric}'. Must be one of: {valid_metrics}")
            
            value = overall[metric]
            if not isinstance(value, (int, float)) or value < 0:
                raise ConfigError(f"Event '{event_name}' overall {metric} value '{value}' must be non-negative number.")
        
        # Validate profile-based targeting
        if 'profiles' in event_config:
            profiles = event_config['profiles']
            if not isinstance(profiles, dict):
                raise ConfigError(f"Event '{event_name}' profiles must be a dictionary")
            
            for profile_name, profile_config in profiles.items():
                if profile_name not in valid_profiles:
                    raise ConfigError(f"Event '{event_name}' has invalid profile '{profile_name}'. Must be one of: {valid_profiles}")
                
                if not isinstance(profile_config, dict):
                    raise ConfigError(f"Event '{event_name}' profile '{profile_name}' configuration must be a dictionary")
                
                # Validate profile effects
                for key, value in profile_config.items():
                    if isinstance(value, dict):
                        # Nested effects validation (like funnel-specific conversions)
                        # This is valid - skip numeric validation for nested dicts
                        pass
                    elif key in valid_metrics:
                        # Direct metric validation
                        if not isinstance(value, (int, float)) or value < 0:
                            raise ConfigError(f"Event '{event_name}' profile '{profile_name}' {key} value '{value}' must be non-negative number.")


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
            raise ConfigError("'event' key missing from event.yaml")
        
        # Validate content
        validate_catalog(catalog)
        validate_tiers(tiers)
        validate_date_config(date_config)
        validate_growth_config(growth)
        validate_event_config(event)
        
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


def get_tiers_by_profile(profile_name):
    """
    Get all tiers that match a specific profile.
    
    Args:
        profile_name: Profile name (conservative, aggressive, balanced)
        
    Returns:
        Dict of tier_name -> tier_config for matching tiers
    """
    matching_tiers = {}
    for tier_name, tier_config in _tiers.items():
        if tier_config.get('profile') == profile_name:
            matching_tiers[tier_name] = tier_config
    return matching_tiers


def get_tiers_by_priority(priority_name):
    """
    Get all tiers that match a specific priority.
    
    Args:
        priority_name: Priority name (low, medium, high)
        
    Returns:
        Dict of tier_name -> tier_config for matching tiers
    """
    matching_tiers = {}
    for tier_name, tier_config in _tiers.items():
        if tier_config.get('priority') == priority_name:
            matching_tiers[tier_name] = tier_config
    return matching_tiers


def apply_growth_multipliers(tiers, growth_config, year):
    """
    Apply growth multipliers to tiers based on their profiles.
    
    Args:
        tiers: Dict of tier configurations
        growth_config: Growth configuration dict
        year: Year number (positive integer)
        
    Returns:
        Dict with tier_name -> {new_user, visit, conversion} multipliers
        
    Raises:
        ValueError: If year is invalid
        ConfigError: If growth configuration is invalid
    """
    # Input validation
    if not isinstance(year, int) or year < 1:
        raise ValueError(f"Invalid year: {year}. Must be positive integer.")
    
    # Centralized default profile values
    DEFAULT_PROFILE_MULTIPLIERS = {
        'new_user': 1.0,
        'visit': 1.0,
        'conversion': 1.0
    }
    
    # Determine year key with proper validation
    if year <= 7:
        year_key = f"year_{year}"
    else:
        year_key = "year_8_plus"
    
    # Validate growth config structure
    if not isinstance(growth_config, dict):
        raise ConfigError("Growth config must be a dictionary")
    
    # Get base profile multipliers
    base_profiles = growth_config.get('base', {}).get('tier_profiles', {})
    if not isinstance(base_profiles, dict):
        raise ConfigError("Base tier_profiles must be a dictionary")
    
    # Get yearly multipliers if available
    yearly_config = growth_config.get('yearly', {}).get(year_key, {})
    yearly_multipliers = yearly_config.get('profile_multipliers', {}) if isinstance(yearly_config, dict) else {}
    
    tier_multipliers = {}
    
    for tier_name, tier_config in tiers.items():
        if not isinstance(tier_config, dict):
            continue  # Skip invalid tier configs
            
        profile = tier_config.get('profile')
        if not profile:
            raise ConfigError(f"Tier '{tier_name}' missing required 'profile' field")
        
        # Start with base profile values
        base_multipliers = base_profiles.get(profile, DEFAULT_PROFILE_MULTIPLIERS)
        if not isinstance(base_multipliers, dict):
            base_multipliers = DEFAULT_PROFILE_MULTIPLIERS
        
        # Apply yearly multipliers if available
        year_multiplier = yearly_multipliers.get(profile, DEFAULT_PROFILE_MULTIPLIERS)
        if not isinstance(year_multiplier, dict):
            year_multiplier = DEFAULT_PROFILE_MULTIPLIERS
        
        # Validate multiplier values
        for multiplier_dict in [base_multipliers, year_multiplier]:
            for metric in ['new_user', 'visit', 'conversion']:
                if metric in multiplier_dict:
                    value = multiplier_dict[metric]
                    if not isinstance(value, (int, float)) or value < 0:
                        raise ConfigError(f"Invalid multiplier value for {metric}: {value}. Must be non-negative number.")
        
        # Combine base and yearly multipliers
        tier_multipliers[tier_name] = {
            'new_user': base_multipliers.get('new_user', 1.0) * year_multiplier.get('new_user', 1.0),
            'visit': base_multipliers.get('visit', 1.0) * year_multiplier.get('visit', 1.0),
            'conversion': base_multipliers.get('conversion', 1.0) * year_multiplier.get('conversion', 1.0)
        }
    
    return tier_multipliers


def apply_event_effects(tiers, event_config, current_year, current_month):
    """
    Apply event effects to tiers based on their profiles.
    
    Args:
        tiers: Dict of tier configurations
        event_config: Event configuration dict
        current_year: Current year number
        current_month: Current month number (1-12)
        
    Returns:
        Dict with tier_name -> {new_user, visit, conversion} event multipliers
        Dict with tier_name -> {funnel_stage: multiplier} for nested effects
    """
    # Input validation
    if not isinstance(current_year, int) or current_year < 1:
        raise ValueError(f"Invalid year: {current_year}. Must be positive integer.")
    if not isinstance(current_month, int) or not (1 <= current_month <= 12):
        raise ValueError(f"Invalid month: {current_month}. Must be 1-12.")
    
    event_effects = {}
    nested_effects = {}
    
    # Initialize with no effects
    for tier_name in tiers:
        event_effects[tier_name] = {
            'new_user': 1.0,
            'visit': 1.0,
            'conversion': 1.0
        }
        nested_effects[tier_name] = {}
    
    # Find active events
    for event_name, event_data in event_config.items():
        if not isinstance(event_data, dict):
            continue  # Skip invalid event data
            
        event_year = event_data.get('year')
        start_month = event_data.get('start_month', 1)
        end_month = event_data.get('end_month', 12)
        
        # Validate event date ranges
        if (event_year is None or 
            not isinstance(start_month, int) or not (1 <= start_month <= 12) or
            (end_month is not None and not isinstance(end_month, int)) or
            (end_month is not None and not (1 <= end_month <= 12))):
            continue  # Skip events with invalid dates
            
        # Check if event is active
        if (event_year == current_year and 
            start_month <= current_month <= (end_month or 12)):
            
            # Apply overall effects
            overall = event_data.get('overall', {})
            for tier_name in event_effects:
                for metric in ['new_user', 'visit', 'conversion']:
                    if metric in overall and isinstance(overall[metric], (int, float)):
                        event_effects[tier_name][metric] *= overall[metric]
            
            # Apply profile-based effects
            profiles = event_data.get('profiles', {})
            for tier_name, tier_config in tiers.items():
                profile = tier_config.get('profile', 'balanced')
                if profile in profiles:
                    profile_effects = profiles[profile]
                    
                    # Handle direct metrics (new_user, visit, conversion)
                    for metric in ['new_user', 'visit', 'conversion']:
                        if metric in profile_effects and isinstance(profile_effects[metric], (int, float)):
                            event_effects[tier_name][metric] *= profile_effects[metric]
                    
                    # Handle nested effects (like funnel-specific conversions)
                    for key, value in profile_effects.items():
                        if isinstance(value, dict):
                            # Store nested effects for application by specific modules
                            for nested_key, nested_value in value.items():
                                if isinstance(nested_value, (int, float)):
                                    if nested_key not in nested_effects[tier_name]:
                                        nested_effects[tier_name][nested_key] = 1.0
                                    nested_effects[tier_name][nested_key] *= nested_value
    
    return event_effects, nested_effects