# DuckDB Integration for Lettuce-Melon

This document explains the DuckDB integration and how to use it.

## Overview

The DuckDB integration replaces CSV file operations with a single database file (`lettuce_melon.duckdb`) that contains all your data. This provides:

- **Better performance**: No more reading/writing entire CSV files
- **Single file**: All data in one `.duckdb` file for easy sharing
- **SQL access**: Direct SQL queries on your data
- **Efficient updates**: Only insert/update new data, not entire tables

## Files

### Core Files
- `sim/database.py` - DuckDB integration module
- `generate_duckdb.py` - Main script using DuckDB instead of CSV
- `.github/workflows/initial-run.yml` - GitHub Action for initial data generation
- `.github/workflows/daily-run.yml` - GitHub Action for daily updates

### Database Schema
```sql
-- Users table
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY,
    tier VARCHAR,
    registered_date DATE,
    last_active_date DATE
);

-- Transaction headers
CREATE TABLE transaction (
    session_id VARCHAR,
    trx_id VARCHAR,
    date DATE,
    tier VARCHAR
);

-- Transaction line items
CREATE TABLE transaction_item (
    trx_id VARCHAR,
    tier VARCHAR,
    date DATE,
    product VARCHAR,
    quantity INTEGER,
    unit_price INTEGER,
    total_price INTEGER
);

-- Funnel activities
CREATE TABLE funnel (
    session_id VARCHAR,
    tier VARCHAR,
    user_id INTEGER,
    activity VARCHAR,
    activity_datetime TIMESTAMP
);

-- Product catalog
CREATE TABLE catalog (
    category VARCHAR,
    subcategory VARCHAR,
    product VARCHAR,
    base_price INTEGER
);
```

## Usage

### Local Development

#### Initial Setup
```bash
# Install dependencies (includes DuckDB)
pip install -e .

# Initialize database with base data
python generate_duckdb.py initial

# Generate historical data
python generate_duckdb.py range 2022-01-01 2022-12-31
```

#### Daily Operations
```bash
# Generate data for current date (UTC+7)
python generate_duckdb.py daily

# Generate data for specific date
python generate_duckdb.py date 2022-01-15
```

#### Direct Database Access
```python
from sim.database import DatabaseContext

# Connect and query
with DatabaseContext() as db:
    # Get recent transactions
    recent = db.conn.execute("""
        SELECT * FROM transaction 
        WHERE date >= '2022-01-01' 
        LIMIT 10
    """).fetchdf()
    
    # Get database stats
    stats = db.get_stats()
    print(stats)
```

### GitHub Actions

#### Initial Run (Manual)
1. Go to Actions → Initial Data Generation
2. Click "Run workflow"
3. Optionally specify custom start/end dates
4. Workflow will:
   - Initialize database
   - Generate historical data
   - Upload `.duckdb` file as artifact
   - Commit files to repository

#### Daily Run (Automated)
- Runs automatically every day at 07:30 UTC+7
- Downloads existing database
- Generates data for current date
- Uploads updated database
- Commits changes to repository

#### Manual Daily Run
1. Go to Actions → Daily Data Generation
2. Click "Run workflow"
3. Optionally specify target date
4. Same process as automated run

## Data Access for Consumers

### Option 1: Download DuckDB File
```bash
# Download from GitHub Releases or Artifacts
wget https://github.com/ibrasyad/lettuce-melon/releases/latest/download/lettuce_melon.duckdb

# Query directly
python -c "
import duckdb
conn = duckdb.connect('lettuce_melon.duckdb')
result = conn.execute('SELECT COUNT(*) FROM transaction').fetchone()
print(f'Total transactions: {result[0]}')
"
```

### Option 2: CSV Files (Still Generated)
```python
import pandas as pd

# Traditional CSV access still works
transactions = pd.read_csv('transaction.csv')
users = pd.read_csv('users_updated.csv')
```

### Option 3: Direct GitHub Access
```python
import duckdb
import requests

# Load directly from GitHub
db_url = "https://github.com/ibrasyad/lettuce-melon/raw/main/output/lettuce_melon.duckdb"
response = requests.get(db_url)

with open('temp.duckdb', 'wb') as f:
    f.write(response.content)

conn = duckdb.connect('temp.duckdb')
data = conn.execute("SELECT * FROM transaction LIMIT 10").fetchdf()
```

## Migration from CSV

The DuckDB integration maintains full compatibility with your existing CSV workflow:

1. **CSV files are still generated** - for backward compatibility
2. **Same configuration files** - no changes needed
3. **Same data generation logic** - just storage method changed
4. **Easy rollback** - you can switch back to `generate.py` anytime

## Performance Benefits

### Before (CSV)
```python
# Each day:
base_user_table = pd.read_csv("output/users_updated.csv")  # Read entire file
# ... process ...
base_user_table.to_csv("output/users_updated.csv", index=False)  # Write entire file
```

### After (DuckDB)
```python
# Each day:
with DatabaseContext() as db:
    users = db.get_users_for_date(date)  # Only what you need
    db.update_user_activity(user_ids, date)  # Only updates
```

## File Size Comparison

Typical file sizes for one year of data:
- **CSV files**: ~5MB total (multiple files)
- **DuckDB file**: ~2MB (single file, compressed)

## Troubleshooting

### Database Not Found
```bash
# Run initial setup first
python generate_duckdb.py initial
```

### Permission Issues
```bash
# Ensure output directory exists and is writable
mkdir -p output
chmod 755 output
```

### GitHub Actions Failures
- Check that DuckDB dependency is installed
- Verify workflow permissions in repository settings
- Check artifact storage limits

## Future Enhancements

1. **BigQuery Export**: Easy migration from DuckDB to BigQuery
2. **Real-time API**: Serve queries via web API
3. **Data Validation**: Automated data quality checks
4. **Backup Strategy**: Automated database backups
