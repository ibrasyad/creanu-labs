# Dynamic Tier System

This document explains how to add new customer tiers to the simulation system without manually updating growth and event configurations.

## Overview

The system now uses **profile-based tier management** instead of hardcoded tier names. Each tier is assigned a profile that determines its growth patterns and event targeting.

## Available Profiles

### 1. **conservative**
- **Description**: Budget-conscious tiers with careful spending patterns
- **Growth Pattern**: Lower user acquisition, higher conversion focus
- **Use Case**: Students, health-conscious shoppers

### 2. **aggressive** 
- **Description**: Growth-focused tiers with high spending potential
- **Growth Pattern**: High user acquisition and engagement
- **Use Case**: Young professionals, business owners

### 3. **balanced**
- **Description**: Steady, predictable tiers with moderate patterns
- **Growth Pattern**: Balanced across all metrics
- **Use Case**: Family shoppers, regular customers

## Adding a New Tier

### Step 1: Create Tier File
Create a new YAML file in `config/tiers/` (e.g., `new_tier.yaml`):

```yaml
new_tier: # Brief description
  profile: conservative  # Choose from: conservative, aggressive, balanced
  priority: medium      # Choose from: low, medium, high
  description: "Detailed description of this tier"
  
  # ... rest of tier configuration (visit_chance, basket, etc.)
```

### Step 2: Configure Tier Behavior
Add the standard tier configuration sections:
- `visit_chance`: Daily visit probabilities (0.0-1.0)
- `monthly_visit_chance_multiplier`: Seasonal adjustments
- `landing_page`, `product_view`, `add_to_cart`, `checkout`, `paid`: Funnel configuration
- `basket`: Shopping basket parameters (min_items, max_items)
- `category_weight`: Product category preferences
- etc.

### Step 3: Test the Configuration
Run the configuration test:

```bash
cd d:\Windsurf\lettuce-melon
python -c "from sim.config import get_tiers, get_tiers_by_profile; print('Tiers:', list(get_tiers().keys())); print('Conservative tiers:', list(get_tiers_by_profile('conservative').keys()))"
```

## How It Works

### Growth Application
- Each year has `profile_multipliers` for each profile type
- Tiers automatically inherit multipliers based on their `profile` field
- No need to update `growth.yaml` when adding new tiers

### Event Targeting  
- Events target profiles instead of specific tiers
- All tiers with the targeted profile automatically receive event effects
- Supports both direct metrics (new_user, visit, conversion) and nested effects (funnel-specific)
- No need to update `event.yaml` when adding new tiers

### Validation
- System validates that all tiers have valid profiles and priorities
- Ensures consistency across the configuration
- Validates numeric values are non-negative
- Checks date ranges and month boundaries

## Example: Adding a "senior_citizens" Tier

```yaml
# config/tiers/senior_citizens.yaml
senior_citizens: # Retired individuals with fixed incomes
  profile: conservative
  priority: medium
  description: "Retired individuals with careful spending habits"
  
  visit_chance:
    monday: 0.05
    tuesday: 0.05
    # ... etc.
```

This tier will automatically:
- Get conservative growth multipliers from `growth.yaml`
- Be targeted by conservative-focused events in `event.yaml`
- Work with all existing simulation modules

## Advanced Features

### Nested Event Effects
The system supports nested event effects for funnel-specific modifications:

```yaml
event_name:
  profiles:
    aggressive:
      conversion:
        landing_page: 1.25  # Only affects landing page conversion
        checkout: 1.10       # Only affects checkout conversion
```

### Input Validation
All functions include comprehensive validation:
- Years must be positive integers
- Months must be 1-12
- Multipliers must be non-negative numbers
- Profile names must be valid

### Error Handling
- Graceful degradation with sensible defaults
- Clear error messages for configuration issues
- Validation at startup prevents runtime errors

## Benefits

1. **Zero Manual Updates**: Add tiers without touching growth/event configs
2. **Consistent Behavior**: Profile-based ensures predictable patterns
3. **Easy Maintenance**: Centralized profile management
4. **Automatic Validation**: System validates tier metadata
5. **Flexible Events**: Supports both simple and nested event effects
6. **Robust Error Handling**: Comprehensive validation and error messages

## Migration Notes

Old tier files have been updated with the new metadata:
- `health_conscious`: conservative profile
- `young_professionals`: aggressive profile  
- `students`: conservative profile
- `small_business_owners`: aggressive profile
- `family_shoppers`: balanced profile
- `random`: balanced profile

## API Reference

### Core Functions

```python
# Get all tiers
tiers = get_tiers()

# Get tiers by profile
conservative_tiers = get_tiers_by_profile('conservative')

# Apply growth multipliers
growth_effects = apply_growth_multipliers(tiers, growth_config, year)

# Apply event effects (returns both direct and nested effects)
event_effects, nested_effects = apply_event_effects(tiers, event_config, year, month)
```

### Validation Functions

```python
# Validate individual configurations
validate_tiers(tiers_dict)
validate_growth_config(growth_dict)
validate_event_config(event_dict)
