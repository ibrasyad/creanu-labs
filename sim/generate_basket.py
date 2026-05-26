"""
Basket generation module for transaction simulation.
"""
import random
import numpy as np
import sys
from pathlib import Path
from datetime import datetime

# Handle both module import and direct script execution
try:
    from .config import get_catalog, get_tiers, get_simulation, get_date_config
    from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name
except ImportError:
    # Allow running as a script
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_catalog, get_tiers, get_simulation, get_date_config
    from utils import weighted_choice, apply_noise, get_day_of_week, get_month_name

# Cache configs
_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()


def resolve_basket_config(sim_cfg, tier_cfg):
    """
    Resolve basket configuration with tier overrides.
    
    Args:
        sim_cfg: Simulation config dict
        tier_cfg: Tier config dict
        
    Returns:
        Dict with min_items and max_items
    """
    sim_basket = sim_cfg["basket"]
    tier_basket = tier_cfg.get("basket", {})

    return {
        "min_items": tier_basket.get("min_items", sim_basket["min_items"]),
        "max_items": tier_basket.get("max_items", sim_basket["max_items"]),
    }


def resolve_subcategory_duplicates(sim_cfg, tier_cfg):
    """
    Resolve subcategory duplicate rules with tier overrides.
    
    Args:
        sim_cfg: Simulation config dict
        tier_cfg: Tier config dict
        
    Returns:
        Dict mapping subcategories to boolean (True = allow duplicates)
    """
    # Start with simulation defaults
    defaults = sim_cfg.get("subcategory_allow_duplicates", {})
    
    # Apply tier-specific overrides
    tier_overrides = tier_cfg.get("subcategory_allow_duplicates", {})
    
    result = defaults.copy()
    result.update(tier_overrides)
    
    return result


def generate_total_trx(date_str):
    """
    Calculate total transactions for a given date.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Number of transactions (int)
    """
    weekday = get_day_of_week(date_str)
    base_trx = _date_config["transaction_volume"]["weekday_base"][weekday]
    
    # Apply weekday noise
    weekday_noise_config = _date_config.get("transaction_volume", {}).get("weekday_rate_noise")
    base_trx *= apply_noise(base_trx, weekday_noise_config)
    
    # Apply monthly rate
    month = get_month_name(date_str)
    monthly_rate = _date_config["transaction_volume"]["monthly_rate"][month]
    
    # Apply monthly noise
    monthly_noise_config = _date_config.get("transaction_volume", {}).get("monthly_rate_noise")
    monthly_rate *= apply_noise(monthly_rate, monthly_noise_config)
    
    return int(base_trx * monthly_rate)

def get_effective_cooldown(catalog, category, subcategory, product_name):
    """
    Get cooldown for a specific product, checking product-level override first.
    
    Args:
        catalog: Catalog dict
        category: Category name
        subcategory: Subcategory name
        product_name: Product name
        
    Returns:
        Cooldown days (int)
    """
    # Check product-level cooldown first
    product_cooldown = catalog[category][subcategory]["product"][product_name].get("cooldown")
    if product_cooldown is not None:
        return product_cooldown
    # Fall back to subcategory cooldown
    return catalog[category][subcategory].get("cooldown", 1)


def is_subcategory_under_cooldown(
    customer_id,
    category,
    subcategory,
    current_date,
    purchase_history_df,
    catalog
):
    # Get the most recent purchase in this subcategory
    history = purchase_history_df[
        (purchase_history_df["customer_id"] == customer_id) &
        (purchase_history_df["subcategory"] == subcategory)
    ]

    if history.empty:
        return False

    # Find the most recent purchase and its specific cooldown
    most_recent = history.loc[history["last_purchase_date"].idxmax()]
    last_product = most_recent["product"]
    last_purchase_date = most_recent["last_purchase_date"]
    
    # Get the cooldown for the specific product that was purchased
    cooldown_days = get_effective_cooldown(catalog, category, subcategory, last_product)
    
    if cooldown_days <= 0:
        return False

    days_since = (current_date - last_purchase_date).days
    return days_since < cooldown_days


def pick_available_subcategory(
    customer_id,
    category,
    tier,
    current_date,
    purchase_history_df,
    max_retries=10
):
    subcats = _catalog[category]
    sub_weights = tier.get("subcategory_weight", {}).get(category)

    for _ in range(max_retries):
        if sub_weights:
            subcategory = weighted_choice(sub_weights)
        else:
            subcategory = random.choice(list(subcats))

        if not is_subcategory_under_cooldown(
            customer_id,
            category,
            subcategory,
            current_date,
            purchase_history_df,
            _catalog
        ):
            return subcategory

    return None

def generate_basket(tier_name=None, seed=None):
    """
    Generate a shopping basket for a customer.

    Args:
        tier_name (str | None): Customer tier, or random if None
        seed (int | None): Random seed for reproducibility

    Returns:
        List of dicts representing items in the basket
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Pick tier
    if tier_name is None:
        tier_name = random.choice(list(_tiers.keys()))

    tier = _tiers[tier_name]

    # Determine basket size
    basket_cfg = resolve_basket_config(_sim, tier)
    basket_size = random.randint(basket_cfg["min_items"], basket_cfg["max_items"])

    # Get subcategory duplicate rules for this tier
    dup_rules = resolve_subcategory_duplicates(_sim, tier)

    basket = []
    picked_subcategories = set()

    for _ in range(basket_size):
        # Select category based on tier preferences
        category = weighted_choice(tier["category_weight"])

        # Select subcategory
        subcats = _catalog[category]
        sub_weights = tier.get("subcategory_weight", {}).get(category)
        
        if sub_weights:
            subcategory = weighted_choice(sub_weights)
        else:
            subcategory = random.choice(list(subcats))

        # Select product
        products = subcats[subcategory].get("product", {})
        product_name = random.choice(list(products))
        product = products[product_name]
        
        cooldown = get_effective_cooldown(_catalog, category, subcategory, product_name)
        allows_dup = dup_rules.get(subcategory, True)
        
        # cooldown > 1 means "do not repeat in same basket"
        if cooldown > 1 and subcategory in picked_subcategories:
            max_retries = 10
            for _ in range(max_retries):
                category = weighted_choice(tier["category_weight"])
                subcats = _catalog[category]
                sub_weights = tier.get("subcategory_weight", {}).get(category)

                if sub_weights:
                    subcategory = weighted_choice(sub_weights)
                else:
                    subcategory = random.choice(list(subcats))

                # Select product
                products = subcats[subcategory].get("product", {})
                product_name = random.choice(list(products))
                product = products[product_name]
                
                cooldown = get_effective_cooldown(_catalog, category, subcategory, product_name)
                allows_dup = dup_rules.get(subcategory, True)

                if (cooldown <= 1) or (subcategory not in picked_subcategories):
                    break

        # Calculate quantity
        base_lambda = tier.get("quantity_model", {}).get("base_lambda") or \
                      _sim.get("quantity_model", {}).get("base_lambda", 1.0)
        bias = tier.get("quantity_bias", {}).get(category, 1.0)
        quantity = max(1, np.random.poisson(base_lambda * bias))

        # Calculate price with variation
        base_price = product["base_price"]
        price_std = _sim["price_variation"]["std_pct"]
        raw_price = base_price * np.random.normal(1, price_std)
        unit_price = int(round(max(1, raw_price), -2))

        basket.append({
            # "tier": tier_name,
            "product": product_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": unit_price * quantity
        })

        # Track this subcategory as picked
        picked_subcategories.add(subcategory)
    
    return basket


if __name__ == "__main__":
    basket = generate_basket()
    from pprint import pprint
    pprint(basket)
