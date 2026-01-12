import yaml, random
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ------------------------
# Load configs once
# ------------------------

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

catalog = load_yaml(BASE_DIR / "config/catalog.yaml")["catalog"]
tiers = load_yaml(BASE_DIR / "config/tiers.yaml")["tiers"]
sim = load_yaml(BASE_DIR / "config/simulation.yaml")["simulation"]

# ------------------------
# Helpers
# ------------------------

def weighted_choice(d):
    keys = list(d.keys())
    weights = list(d.values())
    return random.choices(keys, weights)[0]


def resolve_basket_config(sim_cfg, tier_cfg):
    sim_basket = sim_cfg["basket"]
    tier_basket = tier_cfg.get("basket", {})

    return {
        "min_items": tier_basket.get("min_items", sim_basket["min_items"]),
        "max_items": tier_basket.get("max_items", sim_basket["max_items"]),
    }

def trx_by_day_of_week(day_of_week):
    return sim['transaction_volume']['weekday_base'][day_of_week]

# ------------------------
# Main API
# ------------------------

def generate_basket(tier_name=None, seed=None):
    """
    Generate a shopping basket.

    Args:
        tier_name (str | None): specific tier, or random if None
        seed (int | None): random seed for reproducibility
    """

    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)

    # Pick tier
    if tier_name is None:
        tier_name = random.choice(list(tiers.keys()))

    tier = tiers[tier_name]

    # Basket size
    basket_cfg = resolve_basket_config(sim, tier)
    basket_size = random.randint(
        basket_cfg["min_items"],
        basket_cfg["max_items"]
    )

    basket = []

    for _ in range(basket_size):

        # Category
        category = weighted_choice(tier["category_weight"])

        # Subcategory
        subcats = catalog[category]
        sub_weights = tier.get("subcategory_weight", {}).get(category)

        if sub_weights:
            subcategory = weighted_choice(sub_weights)
        else:
            subcategory = random.choice(list(subcats))

        # Product
        products = subcats[subcategory]
        product_name = random.choice(list(products))
        product = products[product_name]

        # Quantity
        base_lambda = sim["quantity_model"]["base_lambda"]
        bias = tier.get("quantity_bias", {}).get(category, 1.0)
        quantity = max(1, np.random.poisson(base_lambda * bias))

        # Price
        base_price = product["base_price"]
        std = sim["price_variation"]["std_pct"]
        raw_price = base_price * np.random.normal(1, std)
        unit_price = int(round(max(1, raw_price), -2))

        # cap = tier["price_sensitivity"]["max_multiplier"]
        # unit_price = int(min(raw_price, base_price * cap))

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