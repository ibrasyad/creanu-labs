"""State-aware basket generation for transaction simulation."""
from __future__ import annotations

import random

import numpy as np
import pandas as pd

from .config import get_catalog, get_date_config, get_simulation, get_tiers
from .utils import apply_noise, get_day_of_week, get_month_name, weighted_choice

_catalog = get_catalog()
_tiers = get_tiers()
_sim = get_simulation()
_date_config = get_date_config()


def product_lookup():
    return {
        product: (category, subcategory, attrs)
        for category, subcategories in _catalog.items()
        for subcategory, data in subcategories.items()
        for product, attrs in data["product"].items()
    }


_PRODUCT_LOOKUP = product_lookup()


def market_activity_multiplier(date_str):
    """Relative market demand from the reference weekday/month volume pattern."""
    volume = _date_config.get("transaction_volume", {})
    weekday = volume.get("weekday_base", {})
    monthly = volume.get("monthly_rate", {})
    if not weekday or not monthly:
        return 1.0
    weekday_mean = sum(weekday.values()) / len(weekday)
    return (weekday.get(get_day_of_week(date_str), weekday_mean) / weekday_mean) * monthly.get(get_month_name(date_str), 1.0)


def generate_total_trx(date_str):
    """Return the reference daily market volume; it is not a hard order target."""
    volume = _date_config["transaction_volume"]
    baseline = volume["weekday_base"][get_day_of_week(date_str)]
    return int(round(baseline * volume["monthly_rate"][get_month_name(date_str)] * apply_noise(baseline, volume.get("weekday_rate_noise"))))


def _history_key(user_id, category, subcategory):
    return user_id, category, subcategory


def build_purchase_history(transaction_items):
    """Build latest subcategory purchases from persisted transaction lines."""
    history = {}
    if transaction_items is None or transaction_items.empty:
        return history
    for row in transaction_items[["user_id", "product", "date"]].itertuples(index=False):
        details = _PRODUCT_LOOKUP.get(row.product)
        if details is None:
            continue
        category, subcategory, _ = details
        date = pd.Timestamp(row.date).normalize()
        key = _history_key(row.user_id, category, subcategory)
        history[key] = max(history.get(key, date), date)
    return history


def update_purchase_history(history, user_id, purchase_date, basket):
    purchase_date = pd.Timestamp(purchase_date).normalize()
    for item in basket:
        category, subcategory, _ = _PRODUCT_LOOKUP[item["product"]]
        history[_history_key(user_id, category, subcategory)] = purchase_date


def _effective_cooldown(category, subcategory, product):
    product_cfg = _catalog[category][subcategory]["product"][product]
    return int(product_cfg.get("cooldown", _catalog[category][subcategory].get("cooldown", 1)))


def _available(category, subcategory, product, user_id, current_date, history):
    last_purchase = history.get(_history_key(user_id, category, subcategory))
    if last_purchase is None:
        return True
    return (pd.Timestamp(current_date).normalize() - last_purchase).days >= _effective_cooldown(category, subcategory, product)


def _basket_config(tier):
    basket = dict(_sim.get("basket", {}))
    basket.update(tier.get("basket", {}))
    return basket


def _candidate(tier, user_id, current_date, history, picked_subcategories, duplicate_rules):
    categories = tier["category_weight"]
    for _ in range(100):
        category = weighted_choice(categories)
        subcategories = _catalog[category]
        weights = tier.get("subcategory_weight", {}).get(category)
        subcategory = weighted_choice(weights) if weights else weighted_choice({name: 1 for name in subcategories})
        if not duplicate_rules.get(subcategory, True) and subcategory in picked_subcategories:
            continue
        products = subcategories[subcategory]["product"]
        product = weighted_choice({name: attrs.get("weight", 1.0) for name, attrs in products.items()})
        if _available(category, subcategory, product, user_id, current_date, history):
            return category, subcategory, product, products[product]
    return None


def generate_basket(tier_name=None, user_id=None, current_date=None, purchase_history=None, seed=None):
    """Generate a basket that honours duplicate and historical cooldown rules."""
    if seed is not None:
        # Local seed support without changing the surrounding simulation stream.
        numpy_state, random_state = np.random.get_state(), random.getstate()
        np.random.seed(seed)
        random.seed(seed)
    try:
        if tier_name is None:
            tier_name = random.choice(list(_tiers))
        tier = _tiers[tier_name]
        user_id = user_id or "anonymous"
        current_date = current_date or _date_config["start_date"]
        history = purchase_history if purchase_history is not None else {}
        basket_cfg = _basket_config(tier)
        min_items, max_items = basket_cfg["min_items"], basket_cfg["max_items"]
        # A triangular distribution avoids overproducing extreme basket sizes.
        basket_size = int(round(random.triangular(min_items, max_items, (min_items + max_items) / 2)))
        duplicate_rules = dict(_sim.get("subcategory_allow_duplicates", {}))
        duplicate_rules.update(tier.get("subcategory_allow_duplicates", {}))
        basket, picked = [], set()
        for _ in range(basket_size):
            candidate = _candidate(tier, user_id, current_date, history, picked, duplicate_rules)
            if candidate is None:
                break
            category, subcategory, product_name, product = candidate
            base_lambda = tier.get("quantity_model", {}).get("base_lambda", _sim["quantity_model"]["base_lambda"])
            quantity = max(1, int(np.random.poisson(base_lambda * tier.get("quantity_bias", {}).get(category, 1.0))))
            cv = float(_sim["price_variation"].get("std_pct", 0.0))
            sigma = np.sqrt(np.log1p(cv * cv))
            unit_price = max(1, int(round(product["base_price"] * np.random.lognormal(-0.5 * sigma * sigma, sigma), -2)))
            basket.append({"product": product_name, "quantity": quantity, "unit_price": unit_price,
                           "total_price": unit_price * quantity})
            picked.add(subcategory)
        return basket
    finally:
        if seed is not None:
            np.random.set_state(numpy_state)
            random.setstate(random_state)
