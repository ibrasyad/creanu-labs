# Lettuce-Melon

A **Transaction data generator** that simulates customer shopping behavior across different customer tiers with comprehensive user analytics and funnel tracking. Perfect for testing e-commerce analytics, inventory systems, and business intelligence tools.

## What It Does

Lettuce-Melon generates synthetic transaction data with:
- **Customer segmentation** - Budget, Regular, and Premium tiers with distinct shopping patterns
- **Category preferences** - Different customer types prefer different product categories
- **Temporal patterns** - Realistic weekly and monthly transaction variations
- **User lifecycle tracking** - New user acquisition and user base evolution
- **Funnel analytics** - Customer journey and conversion tracking
- **Configurable catalog** - Define your own products, prices, and categories
- **Parquet output** - Efficient columnar storage for large datasets

### Example Output

```python
# Transaction headers
session_id,trx_id,date,tier
sess_001,trx_001,2026-01-01,regular
sess_002,trx_002,2026-01-01,budget

# Transaction items
trx_id,tier,date,product,quantity,unit_price,total_price
trx_001,regular,2026-01-01,spinach,2,3920,7840
trx_001,regular,2026-01-01,strawberries,1,5150,5150
trx_002,budget,2026-01-01,cola_500mL,2,20800,41600

# User analytics
user_id,acquisition_date,tier,total_transactions,total_spent
user_001,2026-01-01,regular,15,125000
user_002,2026-01-02,budget,8,45000
```

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/ibrasyad/lettuce-melon.git
cd lettuce-melon

# Install dependencies
pip install -e .

# Or install with dev dependencies for testing
pip install -e ".[dev]"
```

### Running the Generator

```bash
# Generate a full year of transaction data
python generate.py

# Output will be saved to: output/transaction.parquet, output/transaction_item.parquet, and more
```

## 📋 Configuration Guide

All configuration is managed via YAML files in the `config/` directory:

### 1. **catalog.yaml** - Product Definition
Defines your product hierarchy and base prices:

```yaml
catalog:
  vegetables:
    leafy_greens:
      spinach:
        base_price: 4000
      kale:
        base_price: 5000
```

**Structure:** `category → subcategory → product → base_price`

### 2. **tiers.yaml** - Customer Segments
Defines customer behavior by tier (Budget, Regular, Premium):

```yaml
tiers:
  budget:
    basket:
      min_items: 1
      max_items: 4
    category_weight:
      vegetables: 1.2
      fruits: 1.0
      snacks: 0.4
```

**Key settings:**
- `basket.min/max_items` - Items per transaction
- `category_weight` - Shopping preference (higher = more likely)
- `quantity_model.base_lambda` - Average units per item
- `quantity_bias` - Category-specific quantity multipliers

### 3. **date.yaml** - Temporal Configuration
Controls date range and transaction volume:

```yaml
date:
  start_date: "2026-01-01"
  end_date: "2026-12-31"
  transaction_volume:
    monthly_rate:
      january: 1.0
      december: 1.5  # 50% more transactions in December
```

**Key settings:**
- `start_date / end_date` - Simulation period
- `monthly_rate` - Monthly multiplier (1.0 = baseline)
- `weekday_base` - Expected transactions per day (mon-sun)
- `*_noise` - Random variation applied to rates

### 4. **simulation.yaml** - Global Defaults
System-wide defaults (overridable per tier):

```yaml
simulation:
  basket:
    min_items: 1
    max_items: 8
  price_variation:
    std_pct: 0.08  # 8% std dev for price randomization
```

## Enhanced Data Models

### Transaction System
- **Sessions** - Groups related transactions by customer visit
- **Transaction Headers** - High-level transaction metadata (session_id, trx_id, date, tier)
- **Transaction Items** - Detailed line items with products, quantities, and pricing

### User Analytics
- **Base User Table** - Initial user population with acquisition dates and tiers
- **User Updates** - Evolving user base with transaction history and spending patterns
- **New Users** - Daily user acquisition tracking with tier distribution

### Funnel Analytics
- **Customer Journey** - Track users from acquisition through repeat purchases
- **Conversion Events** - Model user behavior at different funnel stages
- **Activity Logs** - Detailed event-based user interaction data

## How It Works

1. **Initialization:**
   - Generate base user population with tier distribution
   - Create product catalog in Parquet format
   - Initialize empty transaction and funnel tables

2. **For each day in the simulation period:**
   - Calculate expected transactions based on weekday + month
   - Generate new users based on growth models
   - Add realistic noise to transaction volume

3. **For each transaction:**
   - Determine basket size based on tier preferences
   - For each item in basket:
     - Pick category based on tier preferences
     - Pick product from category
     - Randomize quantity and price around base values

4. **User & Funnel Processing:**
   - Update user transaction history and spending patterns
   - Generate funnel events and conversion tracking
   - Create activity logs for customer journey analysis

5. **Output:**
   - Write all data to Parquet files in `output/` directory
   - Print summary statistics and user metrics

## Project Structure

```
lettuce-melon/
├── generate.py                 # Main entry point
├── setup.py                    # Package metadata
├── README.md                   # This file
├── config/
│   ├── catalog.yaml           # Product definitions
│   ├── tiers.yaml             # Customer segments
│   ├── date.yaml              # Date range & volume
│   └── simulation.yaml         # Global defaults
├── sim/
│   ├── __init__.py
│   ├── config.py              # Config loader
│   ├── generate_basket.py      # Basket generation logic
│   ├── generate_date.py        # Date utilities
│   ├── generate_funnel.py      # Funnel analytics generation
│   ├── generate_user.py        # User lifecycle management
│   ├── growth.py              # User growth modeling
│   ├── event.py               # Event processing
│   └── utils.py               # Shared utilities
├── output/
│   ├── transaction.parquet         # Generated transaction headers
│   ├── transaction_item.parquet      # Generated transaction line items
│   ├── users_base.parquet            # Initial user base
│   ├── users_updated.parquet         # Updated user table (Main user table)
│   ├── users_new.parquet             # New users table for each day
│   ├── funnel.parquet                # Funnel activity data
│   └── catalog.parquet               # Flattened product catalog
└── tests/                      # Unit & integration tests (coming soon)
```

## Usage Examples

### Default Behavior
```bash
python generate.py
```
Generates 1 year of transactions using all config files, outputs to Parquet files in `output/` directory

### Programmatic Usage
```python
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket

# Get a random basket for Budget tier
basket = generate_basket(tier_name="budget")

# Generate basket with reproducibility
basket = generate_basket(tier_name="regular", seed=42)
```

### Data Access & Analysis

```python
import pandas as pd

# Load transaction data
transactions = pd.read_parquet("output/transaction.parquet")
transaction_items = pd.read_parquet("output/transaction_item.parquet")

# Load user analytics
users = pd.read_parquet("output/users_updated.parquet")
new_users = pd.read_parquet("output/users_new.parquet")

# Load funnel data
funnel = pd.read_parquet("output/funnel.parquet")

# Example: Daily revenue analysis
daily_revenue = transaction_items.groupby('date')['total_price'].sum()

# Example: User tier distribution
tier_dist = users['tier'].value_counts(normalize=True)
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=sim --cov-report=html
```

## Automation & CI/CD

### GitHub Actions Workflows

**Daily Data Generation**
- Runs automatically every day at 23:00 UTC (06:00 UTC+7)
- Generates data for the previous day
- Updates Parquet files and creates GitHub releases
- Can be triggered manually with custom dates

**Initial Data Generation**
- One-time setup for historical data
- Configurable date ranges (default: 2023-01-01 to 2025-12-31)
- Generates complete user base and transaction history

### Manual Workflow Triggers

```bash
# Trigger daily run for specific date
github workflow run daily-run.yml -f date=2026-01-15

# Trigger initial run with custom range
github workflow run initial-run.yml -f start_date=2023-01-01 -f end_date=2025-12-31
```

## Dependencies

### Required
- **pyyaml** - YAML configuration parsing
- **pandas** - Data manipulation and Parquet export
- **numpy** - Numerical operations for noise generation
- **scipy** - Statistical distributions for realistic modeling
- **pyarrow** - Parquet file format support

### Development
- **pytest** - Unit testing framework
- **pytest-cov** - Code coverage tracking
- **black** - Code formatting

**Current Version:** 1.0.0  
**Release Date:** February 10, 2026

## License

MIT License - See [LICENSE](LICENSE) for details

## Contributing

This is an active development project. For issues or suggestions, please open a GitHub issue.

---

**Made for testing e-commerce data pipelines and to help fellow data enthusiasts to learn about data engineering and analytics**
