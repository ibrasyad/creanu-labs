"""Shared utilities for simulation modules."""
from __future__ import annotations

import hashlib
import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


def set_random_seed(seed: int) -> None:
    """Seed both random sources once at the boundary of a simulation run."""
    random.seed(seed)
    np.random.seed(seed)


def seed_for_date(seed: int, date_str: str) -> int:
    """Return a stable, independent seed for one simulation date."""
    payload = f"{seed}:{date_str}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") % (2**32)


def weighted_choice(weights_dict):
    """Select a key using non-negative weights, with useful validation."""
    if not weights_dict:
        raise ValueError("weighted_choice requires at least one choice")
    keys = list(weights_dict)
    weights = list(weights_dict.values())
    if any(not isinstance(weight, (int, float)) or weight < 0 for weight in weights):
        raise ValueError("weights must be non-negative numbers")
    if not any(weights):
        raise ValueError("at least one weight must be positive")
    return random.choices(keys, weights=weights, k=1)[0]


def apply_noise(base_value, noise_config):
    """Return a mean-one positive noise multiplier.

    ``multiplier`` is interpreted as 1 + coefficient of variation.  The legacy
    ``poisson`` label is retained for config compatibility but now uses a
    lognormal multiplier: it is continuous, positive, and has no artificial
    zero/long-integer-tail behaviour.
    """
    if not noise_config:
        return 1.0
    cv = max(0.0, float(noise_config.get("multiplier", 1.0)) - 1.0)
    if cv == 0:
        return 1.0
    distribution = noise_config.get("distribution", "lognormal")
    if distribution == "uniform":
        return float(np.random.uniform(max(0.0, 1 - cv), 1 + cv))
    if distribution not in {"poisson", "normal", "lognormal"}:
        raise ValueError(f"Unsupported noise distribution: {distribution}")
    sigma = np.sqrt(np.log1p(cv * cv))
    return float(np.random.lognormal(mean=-0.5 * sigma * sigma, sigma=sigma))


def parse_date(date_str):
    return datetime.strptime(str(date_str), "%Y-%m-%d")


def date_range(start_date, end_date):
    start, end = parse_date(start_date), parse_date(end_date)
    if end < start:
        raise ValueError("end_date must be on or after start_date")
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end - start).days + 1)]


def get_day_of_week(date_str):
    return parse_date(date_str).strftime("%A").lower()


def get_month_name(date_str):
    return parse_date(date_str).strftime("%B").lower()


def generate_catalog_parquet(output_path="output/catalog.parquet"):
    from .config import get_catalog

    rows = []
    for category, subcategories in get_catalog().items():
        for subcategory, subcat_data in subcategories.items():
            for product, attrs in subcat_data.get("product", {}).items():
                rows.append({"category": category, "subcategory": subcategory,
                             "product": product, "base_price": attrs["base_price"]})
    if rows:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        pd.DataFrame(rows).to_parquet(output_path, index=False)
    return rows


def controlled_random(mean, min_val, max_val, p=0.99):
    """Sample a bounded beta distribution whose expected value is ``mean``."""
    if min_val > max_val:
        raise ValueError("min_val cannot exceed max_val")
    if min_val == max_val:
        return float(min_val)
    if not min_val <= mean <= max_val:
        raise ValueError("mean must lie between min_val and max_val")
    position = (mean - min_val) / (max_val - min_val)
    if position == 0:
        return float(min_val)
    if position == 1:
        return float(max_val)
    concentration = 6.0
    return float(min_val + (max_val - min_val) * np.random.beta(position * concentration, (1 - position) * concentration))


def append_or_create_parquet(path, df):
    """Append while preserving the union of columns and an empty-file schema."""
    if df is None or df.empty:
        return False
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    if os.path.exists(path):
        existing = pd.read_parquet(path)
        combined = df.copy() if existing.empty else pd.concat([existing, df], ignore_index=True, sort=False)
    else:
        combined = df.copy()
    combined.to_parquet(path, index=False)
    return True
