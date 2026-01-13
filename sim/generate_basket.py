"""
Basket generation module for transaction simulation.
"""
import random
import numpy as np
from .config import get_catalog, get_tiers, get_simulation, get_date_config
from .utils import weighted_choice, apply_noise, get_day_of_week, get_month_name

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

    basket = []

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
        products = subcats[subcategory]
        product_name = random.choice(list(products))
        product = products[product_name]

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
            "tier": tier_name,
            "category": category,
            "subcategory": subcategory,
            "product": product_name,
            "quantity": quantity,
            "unit_price": unit_price,
            "total_price": unit_price * quantity
        })
    
    return basket


if __name__ == "__main__":
    basket = generate_basket()
    from pprint import pprint
    pprint(basket)