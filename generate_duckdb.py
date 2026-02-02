"""
Main transaction data generation script using DuckDB.
"""
import pandas as pd
import random
from datetime import datetime, timedelta
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket, generate_total_trx
from sim.utils import date_range, get_day_of_week, weighted_choice, generate_catalog_csv
from sim.generate_user import generate_new_users, roll_new_user_chance, generate_base_user_table
from sim.generate_funnel import generate_funnel_table, funnel_wide_to_activity_log
from sim.database import DatabaseContext

def initial_run():
    """Initialize database with base data."""
    print("Starting initial database setup...")
    
    # Generate the catalog first
    generate_catalog_csv()
    
    # Initialize database and load catalog
    with DatabaseContext() as db:
        db.initialize_tables()
        db.load_catalog_from_csv()
        
        # Generate base user table
        base_table = generate_base_user_table()
        base_user_table = pd.DataFrame(base_table)
        
        # Insert base users
        db.insert_users(base_user_table)
        
        print(f"Database initialized with {len(base_user_table)} base users")
        print("Database stats:", db.get_stats())

def generate_for_date(target_date):
    """Generate data for a specific date."""
    print(f"Generating data for date: {target_date}")
    
    _tiers = get_tiers()
    
    with DatabaseContext() as db:
        # Get current users
        users_df = db.get_users_for_date(target_date)
        current_user_count = len(users_df)
        
        # Generate new users for this date
        new_user_rows = []
        tier_names = list(_tiers.keys())
        random.shuffle(tier_names)
        
        for tier_name in tier_names:
            roll = roll_new_user_chance(tier_name, target_date)
            new_users = generate_new_users(roll, tier_name, target_date, current_user_count)
            if new_users:
                new_user_rows.extend(new_users)
                current_user_count += len(new_users)
        
        # Insert new users
        if new_user_rows:
            new_user_table = pd.DataFrame(new_user_rows)
            new_user_table["registered_date"] = target_date
            new_user_table["last_active_date"] = target_date
            db.insert_users(new_user_table)
        
        # Generate funnel activities
        funnel_table = generate_funnel_table(target_date)
        funnel_table = funnel_wide_to_activity_log(funnel_table)
        
        if not funnel_table.empty:
            db.insert_funnel_activities(funnel_table)
        
        # Update user activity for those who visited
        visited_users = funnel_table[funnel_table["activity"] == "landing_page"][["user_id"]].drop_duplicates()
        if not visited_users.empty:
            db.update_user_activity(visited_users["user_id"].tolist(), target_date)
        
        # Generate transactions from paid funnel activities
        filter_column = ["session_id", "activity_datetime", "tier"]
        trx_table = funnel_table[funnel_table["activity"] == "paid"][filter_column].copy().reset_index(drop=True)
        
        if trx_table.empty:
            print(f"No transactions for {target_date}")
            return
        
        # Prepare transaction data
        rename_column = {"activity_datetime": "date"}
        trx_table.rename(columns=rename_column, inplace=True)
        
        # Assign transaction IDs
        trx_table["date"] = pd.to_datetime(trx_table["date"])
        trx_table["trx_seq"] = (
            trx_table
            .groupby(trx_table["date"].dt.date)
            .cumcount()
            .add(1)
        )
        
        trx_table["trx_id"] = (
            trx_table["date"].dt.strftime("%Y%m%d") + "-" +
            trx_table["trx_seq"].astype(str).str.zfill(8)
        )
        trx_table.drop(columns=["trx_seq"], inplace=True)
        
        # Prepare transaction table
        trx_column_list = ["session_id", "trx_id", "date", "tier"]
        
        # Generate basket items
        trx_table["basket"] = trx_table["tier"].apply(
            lambda tier: generate_basket(tier_name=tier)
        )
        
        # Explode basket items
        trx_items = (
            trx_table
            .explode("basket")
            .reset_index(drop=True)
        )
        
        # Normalize basket dict to columns
        basket_cols = pd.json_normalize(trx_items["basket"])
        
        # Final transaction_item table
        trx_items = pd.concat(
            [trx_items.drop(columns=["basket"]), basket_cols],
            axis=1
        )
        
        trx_item_column_list = ["trx_id", "tier", "date", "product", "quantity", "unit_price", "total_price"]
        
        # Insert transactions
        db.insert_transactions(trx_table[trx_column_list], trx_items[trx_item_column_list])
        
        print(f"Generated for {target_date}:")
        print(f"  New users: {len(new_user_rows) if new_user_rows else 0}")
        print(f"  Funnel activities: {len(funnel_table)}")
        print(f"  Transactions: {len(trx_table)}")
        print(f"  Transaction items: {len(trx_items)}")

def main(start_date=None, end_date=None):
    """
    Main generation function.
    
    Args:
        start_date: Start date string (YYYY-MM-DD). If None, uses config.
        end_date: End date string (YYYY-MM-DD). If None, uses config.
    """
    date_config = get_date_config()
    
    # Use provided dates or config dates
    start_date = start_date or date_config["start_date"]
    end_date = end_date or date_config["end_date"]
    
    print(f"Generating data from {start_date} to {end_date}")
    
    # Generate dates for the simulation period
    dates = date_range(start_date, end_date)
    
    for date in dates:
        generate_for_date(date)
    
    # Final stats
    with DatabaseContext() as db:
        print("\nFinal database stats:", db.get_stats())

def daily_run():
    """Generate data for current date in UTC+7."""
    # Get current date in UTC+7
    utc_now = datetime.utcnow()
    utc_plus_7 = utc_now + timedelta(hours=7)
    current_date = utc_plus_7.strftime("%Y-%m-%d")
    
    print(f"Daily run for {current_date} (UTC+7)")
    
    # Check if database exists, if not initialize
    db_path = "output/lettuce_melon.duckdb"
    if not os.path.exists(db_path):
        print("Database not found, running initial setup...")
        initial_run()
    
    # Generate data for current date only
    generate_for_date(current_date)
    
    # Export to CSV for sharing
    with DatabaseContext() as db:
        db.export_to_csv()
        print("Data exported to CSV files")

if __name__ == "__main__":
    import sys
    import os
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "initial":
            initial_run()
        elif command == "daily":
            daily_run()
        elif command == "date":
            if len(sys.argv) >= 3:
                target_date = sys.argv[2]
                generate_for_date(target_date)
            else:
                print("Usage: python generate_duckdb.py date YYYY-MM-DD")
        elif command == "range":
            if len(sys.argv) >= 4:
                start_date = sys.argv[2]
                end_date = sys.argv[3]
                main(start_date, end_date)
            else:
                print("Usage: python generate_duckdb.py range YYYY-MM-DD YYYY-MM-DD")
        else:
            print("Available commands:")
            print("  initial  - Initialize database with base data")
            print("  daily    - Generate data for current date (UTC+7)")
            print("  date     - Generate data for specific date")
            print("  range    - Generate data for date range")
    else:
        # Default: use config dates
        main()
