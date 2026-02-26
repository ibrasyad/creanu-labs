"""
Shared utilities for simulation modules.
"""
import random
import numpy as np
import os
import pandas as pd
from datetime import datetime, timedelta
from scipy.stats import lognorm, norm
from scipy.optimize import brentq


def weighted_choice(weights_dict):
    """
    Select a random key from a dictionary, weighted by its value.
    
    Args:
        weights_dict: Dict with keys and numeric weights as values
        
    Returns:
        Randomly selected key based on weights
    """
    keys = list(weights_dict.keys())
    weights = list(weights_dict.values())
    return random.choices(keys, weights)[0]


def apply_noise(base_value, noise_config):
    """
    Apply random noise to a base value.
    
    Args:
        base_value: Base numeric value
        noise_config: Dict with 'distribution' and 'multiplier' keys
                     multiplier represents the variance range (e.g., 1.15 = ±15%)
        
    Returns:
        Noise adjustment as a proportion (e.g., 0.85 to 1.15 for multiplier=1.15)
    """
    if not noise_config:
        return 1.0
    
    distribution = noise_config.get("distribution", "poisson")
    multiplier = noise_config.get("multiplier", 1.0)
    
    if distribution == "poisson":
        # Poisson centered around lambda, normalized to variance range
        # E.g., multiplier=1.15 gives roughly ±15% variance
        raw = np.random.poisson(1)
        variance = (raw - 1) * (multiplier - 1)
        return max(0.0, 1 + variance)
    else:
        # Normal distribution for smooth variance
        noise = np.random.normal(0, multiplier - 1)
        return max(0.0, 1 + noise)


def parse_date(date_str):
    """
    Parse date string (YYYY-MM-DD format) into datetime object.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        datetime object
    """
    return datetime.strptime(date_str, "%Y-%m-%d")


def date_range(start_date, end_date):
    """
    Generate a list of date strings between start_date and end_date (inclusive).
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
        
    Returns:
        List of date strings
    """
    start = parse_date(start_date)
    end = parse_date(end_date)
    delta = end - start
    
    return [(start + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(delta.days + 1)]


def get_day_of_week(date_str):
    """
    Get weekday name for a given date string.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Weekday name in lowercase (e.g., 'monday')
    """
    return parse_date(date_str).strftime("%A").lower()


def get_month_name(date_str):
    """
    Get month name for a given date string.
    
    Args:
        date_str: Date string in YYYY-MM-DD format
        
    Returns:
        Month name in lowercase (e.g., 'january')
    """
    return parse_date(date_str).strftime("%B").lower()


def generate_catalog_parquet(output_path="output/catalog.parquet"):
    """
    Generate a catalog.parquet file from catalog.yaml.
    
    Flattens the nested catalog structure (category → subcategory → product → base_price)
    into a Parquet with columns: category, subcategory, product, base_price
    
    Args:
        output_path: Path where the Parquet file will be saved (default: output/catalog.parquet)
        
    Returns:
        List of dicts representing the flattened catalog
    """
    from .config import get_catalog
    
    catalog = get_catalog()
    rows = []
    
    # Flatten the nested structure
    for category, subcategories in catalog.items():
        for subcategory, subcat_data in subcategories.items():
            products = subcat_data.get("product", {})
            for product, attrs in products.items():
                base_price = attrs.get("base_price", 0)
                rows.append({
                    "category": category,
                    "subcategory": subcategory,
                    "product": product,
                    "base_price": base_price
                })
    
    # Write to Parquet
    if rows:
        df = pd.DataFrame(rows)
        df.to_parquet(output_path, index=False)
    
    return rows

def controlled_random(mean, min_val, max_val, p=0.99):
    z = norm.ppf(p)

    for _ in range(5):
        f = lambda s: np.exp(np.log(mean) - 0.5 * s * s + s * z) - max_val

        lo, hi = 0.01, 1.0
        while hi < 50 and f(lo) * f(hi) > 0:
            hi *= 2

        if hi < 50:
            sigma = brentq(f, lo, hi)
            mu = np.log(mean) - 0.5 * sigma * sigma

            dist = lognorm(s=sigma, scale=np.exp(mu))
            a, b = dist.cdf(min_val), dist.cdf(max_val)

            return dist.ppf(np.random.uniform(a, b))

        p = min(p + 0.005, 0.999)
        z = norm.ppf(p)

    sigma = 0.6 * np.log(max_val / mean)
    mu = np.log(mean) - 0.5 * sigma * sigma
    return np.clip(np.random.lognormal(mu, sigma), min_val, max_val)

def append_or_create_parquet(path, df):
    # Nothing to write → do nothing
    if df is None or df.empty:
        return False

    if os.path.exists(path):
        # Read existing, combine, and write back
        existing = pd.read_parquet(path)
        # Filter out empty/NA columns to avoid FutureWarning
        existing_filtered = existing.dropna(axis=1, how='all')
        df_filtered = df.dropna(axis=1, how='all')
        
        combined = pd.concat([existing_filtered, df_filtered], ignore_index=True)
        combined.to_parquet(path, index=False)
    else:
        df.to_parquet(path, index=False)

    return True
