"""
Shared utilities for simulation modules.
"""
import random
import numpy as np
from datetime import datetime, timedelta


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


def generate_catalog_csv(output_path="output/catalog.csv"):
    """
    Generate a catalog.csv file from catalog.yaml.
    
    Flattens the nested catalog structure (category → subcategory → product → base_price)
    into a CSV with columns: category, subcategory, product, base_price
    
    Args:
        output_path: Path where the CSV file will be saved (default: output/catalog.csv)
        
    Returns:
        List of dicts representing the flattened catalog
    """
    from .config import get_catalog
    import csv
    
    catalog = get_catalog()
    rows = []
    
    # Flatten the nested structure
    for category, subcategories in catalog.items():
        for subcategory, products in subcategories.items():
            for product, attrs in products.items():
                base_price = attrs.get("base_price", 0)
                rows.append({
                    "category": category,
                    "subcategory": subcategory,
                    "product": product,
                    "base_price": base_price
                })
    
    # Write to CSV
    if rows:
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["category", "subcategory", "product", "base_price"])
            writer.writeheader()
            writer.writerows(rows)
    
    return rows

