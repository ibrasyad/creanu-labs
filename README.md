# 🍅🍈 Lettuce-Melon

A **realistic transaction data generator** that simulates customer shopping behavior across different customer tiers. Perfect for testing e-commerce analytics, inventory systems, and business intelligence tools.

## 🎯 What It Does

Lettuce-Melon generates synthetic transaction data with:
- **Customer segmentation** - Budget, Regular, and Premium tiers with distinct shopping patterns
- **Category preferences** - Different customer types prefer different product categories
- **Temporal patterns** - Realistic weekly and monthly transaction variations
- **Configurable catalog** - Define your own products, prices, and categories
- **CSV output** - Easy integration with data pipelines and analytics tools

### Example Output

```
trx_id,date,category,subcategory,product,base_price,quantity,price,amount
1,2026-01-01,vegetables,leafy_greens,spinach,4000,2,3920,7840
2,2026-01-01,fruits,berries,strawberries,5000,1,5150,5150
3,2026-01-01,beverages,soda,cola_500mL,20000,2,20800,41600
```

## 🚀 Quick Start

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

# Output will be saved to: output/transaction.csv and output/transaction_item.csv
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

## 📊 How It Works

1. **For each day in the simulation period:**
   - Calculate expected transactions based on weekday + month
   - Add realistic noise to transaction volume

2. **For each transaction:**
   - Randomly select a customer tier (weighted by tier distribution)
   - Determine basket size based on tier preferences
   - For each item in basket:
     - Pick category based on tier preferences
     - Pick product from category
     - Randomize quantity and price around base values

3. **Output:**
   - Write all items to `output/transaction.csv` and `output/transaction_item.csv`
   - Print summary statistics

## 🔧 Project Structure

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
│   └── utils.py               # Shared utilities
├── output/
│   ├── transaction.csv         # Generated transaction headers
│   ├── transaction_item.csv    # Generated transaction line items
│   ├── users_base.csv          # Initial user base
│   ├── users_updated.csv       # Updated user table
│   ├── users_new.csv           # New users
│   ├── funnel.csv              # Funnel activity data
│   └── catalog.csv             # Flattened product catalog
└── tests/                      # Unit & integration tests (coming soon)
```

## 💻 Usage Examples

### Default Behavior
```bash
python generate.py
```
Generates 1 year of transactions using all config files, outputs to `output/transaction.csv` and `output/transaction_item.csv`

### Programmatic Usage
```python
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket

# Get a random basket for Budget tier
basket = generate_basket(tier_name="budget")

# Generate basket with reproducibility
basket = generate_basket(tier_name="regular", seed=42)
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=sim --cov-report=html
```

## 📚 Dependencies

### Required
- **pyyaml** - YAML configuration parsing
- **pandas** - Data manipulation and CSV export
- **numpy** - Numerical operations for noise generation

### Development
- **pytest** - Unit testing framework
- **pytest-cov** - Code coverage tracking
- **black** - Code formatting

## 🛣️ Roadmap

See [ROADMAP.md](ROADMAP.md) for the full v1.0.0 release plan.

**Current Version:** 0.1.0 (Pre-release)  
**Target Release:** January 28, 2026

## 📝 License

MIT License - See [LICENSE](LICENSE) for details

## 🤝 Contributing

This is an active development project. For issues or suggestions, please open a GitHub issue.

---

**Made with ❤️ for testing e-commerce data pipelines**
