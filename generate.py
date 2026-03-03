"""
Main transaction data generation script.
"""
import pandas as pd
import random
import argparse
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket, generate_total_trx
from sim.utils import date_range, get_day_of_week, weighted_choice, generate_catalog_parquet, append_or_create_parquet
from sim.generate_user import generate_new_users, roll_new_user_chance, generate_base_user_table
from sim.generate_funnel import generate_funnel_table, funnel_wide_to_activity_log

trx_column_list = [
        "session_id",
        "user_id",
        "trx_id",
        "date",
        "tier",
        "total_price"
    ]

trx_item_column_list = [
        "trx_id",
        "user_id",
        "tier",
        "date",
        "product",
        "quantity",
        "unit_price",
        "total_price"
    ]

def initial_run():
    # Generate the catalog for parquet first
    generate_catalog_parquet()
    
    # Generate base user table
    base_table = generate_base_user_table()

    base_user_table = pd.DataFrame(base_table)
    base_user_table.to_parquet("output/users_base.parquet", index=False)
    base_user_table.to_parquet("output/users_updated.parquet", index=False)

    # -------------------
    # Create EMPTY transaction_item.parquet
    df_transaction_item = pd.DataFrame(columns=trx_item_column_list)
    df_transaction_item.to_parquet("output/transaction_item.parquet", index=False)

    # -------------------
    # Create EMPTY transaction.parquet
    df_transaction = pd.DataFrame(columns=trx_column_list)
    df_transaction.to_parquet("output/transaction.parquet", index=False)

    # -------------------
    # Create EMPTY funnel.parquet
    df_funnel = pd.DataFrame(columns=[
        "session_id",
        "tier",
        "user_id",
        "activity",
        "activity_datetime"
    ])
    df_funnel.to_parquet("output/funnel.parquet", index=False)

def main(start_date=None, end_date=None):
    date_config = get_date_config()
    _tiers = get_tiers()

    # Use command line arguments if provided, otherwise use config
    start_date = start_date or date_config["start_date"]
    end_date = end_date or date_config["end_date"]

    base_user_table = pd.read_parquet("output/users_updated.parquet")
    current_user_count = len(base_user_table)

    # Generate dates for the simulation period
    dates = date_range(start_date, end_date)
    
    for date in dates:
        print(date)

        # rows = []
        new_user_rows = []
        
        tier_names = list(_tiers.keys())
        random.shuffle(tier_names)
        for tier_name in tier_names:
            roll = roll_new_user_chance(tier_name, date)
            new_users = generate_new_users(roll, tier_name, date, current_user_count)
            if new_users:
                new_user_rows.extend(new_users)
                current_user_count += len(new_users)
    
        if new_user_rows:
            new_user_table = pd.DataFrame(new_user_rows)
            new_user_table["registered_date"] = pd.to_datetime(date)
            new_user_table["last_active_date"] = pd.to_datetime(date)
            new_user_table.to_parquet("output/users_new.parquet", index=False)
            
            # Ensure consistent datetime types before concat
            last_active_dt = pd.to_datetime(base_user_table["last_active_date"], errors='coerce')
            registered_dt = pd.to_datetime(base_user_table["registered_date"], errors='coerce')
                
            base_user_table["last_active_date"] = last_active_dt
            base_user_table["registered_date"] = registered_dt
            
            base_user_table = pd.concat([base_user_table, new_user_table], ignore_index=True)
            base_user_table.to_parquet("output/users_updated.parquet", index=False)
        
        # Generate funnel here
        output_funnel = "output/funnel.parquet"
        funnel_table = generate_funnel_table(date)

        funnel_table = funnel_wide_to_activity_log(funnel_table)
        # Defensive: ensure no timezone sneaks in
        for col in funnel_table.select_dtypes(include=["datetimetz"]).columns:
            funnel_table[col] = funnel_table[col].dt.tz_localize(None)


        append_or_create_parquet(
            output_funnel,
            funnel_table
            )

        # Users who visited today (landing_page)
        visited_users = (
            funnel_table[funnel_table["activity"] == "landing_page"]
            [["user_id"]]
            .drop_duplicates()
        )

        if not visited_users.empty:
            visited_users["last_active_date"] = pd.to_datetime(date)
        
        # Update users table for their activity:
        if not visited_users.empty:
            # Convert to datetime first to avoid mixed types
            last_active_dt = pd.to_datetime(base_user_table["last_active_date"], errors='coerce')
                
            base_user_table["last_active_date"] = last_active_dt
            visited_users["last_active_date"] = pd.to_datetime(date)
            
            base_user_table = base_user_table.merge(
                visited_users,
                on="user_id",
                how="left",
                suffixes=("", "_new")
            )

            base_user_table["last_active_date"] = (
                base_user_table["last_active_date_new"]
                .combine_first(base_user_table["last_active_date"])
            )

            base_user_table.drop(columns=["last_active_date_new"], inplace=True)

            # Persist update
            base_user_table.to_parquet("output/users_updated.parquet", index=False)
        
        # -------------------
        # Generate the basket
        filter_column = ["session_id", "user_id", "activity_datetime", "tier"]
        trx_table = funnel_table[funnel_table["activity"] == "paid"][filter_column].copy().reset_index(drop=True)
        
        if not trx_table.empty:
            rename_column = {
                "activity_datetime": "date", 
            }
            trx_table.rename(columns=rename_column, inplace=True)

            # Assignt trx_id
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
            output_trx = "output/transaction.parquet"

            # Generate basket per paid transaction
            trx_table["basket"] = trx_table["tier"].apply(
                lambda tier: generate_basket(tier_name=tier)
            )

            # Explode basket items
            trx_items = (
                trx_table
                .explode("basket")
                .reset_index(drop=True)
            )

            # Normalize dict → columns
            basket_cols = pd.json_normalize(trx_items["basket"])

            # Final transaction_item table
            trx_items = pd.concat(
                [trx_items.drop(columns=["basket"]), basket_cols],
                axis=1
            )

            # Calculate total price per transaction
            trx_totals = trx_items.groupby("trx_id")["total_price"].sum().reset_index()
            
            # Merge total price back into trx_table
            trx_table = trx_table.merge(trx_totals, on="trx_id", how="left")
            
            append_or_create_parquet(output_trx, trx_table[trx_column_list])

            output_trx_item = "output/transaction_item.parquet"
            append_or_create_parquet(output_trx_item, trx_items[trx_item_column_list])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate simulation data')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    args = parser.parse_args()
    
    initial_run()
    main(start_date=args.start_date, end_date=args.end_date)