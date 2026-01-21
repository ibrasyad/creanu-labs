"""
Main transaction data generation script.
"""
import pandas as pd
import random
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket, generate_total_trx
from sim.utils import date_range, get_day_of_week, weighted_choice, generate_catalog_csv, append_or_create_csv
from sim.generate_user import generate_new_users, roll_new_user_chance, generate_base_user_table
from sim.generate_funnel import generate_funnel_table, funnel_wide_to_activity_log

trx_column_list = [
        "session_id",
        "trx_id",
        "date",
        "tier"
    ]

trx_item_column_list = [
        "trx_id",
        "tier",
        "date",
        "product",
        "quantity",
        "unit_price",
        "total_price"
    ]

def initial_run():
    # Generate the catalog for csv first
    generate_catalog_csv()
    
    # Generate base user table
    base_table = generate_base_user_table()

    base_user_table = pd.DataFrame(base_table)
    base_user_table.to_csv("output/users_base.csv", index=False)
    base_user_table.to_csv("output/users_updated.csv", index=False)

    # -------------------
    # Create EMPTY transaction_item.csv
    df_transaction_item = pd.DataFrame(columns=trx_item_column_list)
    df_transaction_item.to_csv("output/transaction_item.csv", index=False)

    # -------------------
    # Create EMPTY transaction.csv
    df_transaction = pd.DataFrame(columns=trx_column_list)
    df_transaction.to_csv("output/transaction.csv", index=False)

    # -------------------
    # Create EMPTY funnel.csv
    df_funnel = pd.DataFrame(columns=[
        "session_id",
        "tier",
        "user_id",
        "activity",
        "activity_datetime"
    ])
    df_funnel.to_csv("output/funnel.csv", index=False)

def main():
    date_config = get_date_config()
    _tiers = get_tiers()

    base_user_table = pd.read_csv("output/users_updated.csv")
    current_user_count = len(base_user_table)
    # print(current_user_count)

    # Generate dates for the simulation period
    dates = date_range(date_config["start_date"], date_config["end_date"])

    for date in dates:
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
            new_user_table["registered_date"] = date
            new_user_table["last_active_date"] = date
            new_user_table.to_csv("output/users_new.csv", index=False)
            base_user_table = pd.concat([base_user_table, new_user_table], ignore_index=True)
            base_user_table.to_csv("output/users_updated.csv", index=False)
        
        # Generate funnel here
        output_funnel = "output/funnel.csv"
        funnel_table = generate_funnel_table(date)

        funnel_table = funnel_wide_to_activity_log(funnel_table)

        append_or_create_csv(
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
            visited_users["last_active_date"] = date
        
        # Update users table for their activity:
        if not visited_users.empty:
            base_user_table["last_active_date"] = (
                pd.to_datetime(base_user_table["last_active_date"], format="mixed")
                .dt.normalize()
            )

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
            base_user_table.to_csv("output/users_updated.csv", index=False)
        
        # -------------------
        # Generate the basket
        filter_column = ["session_id", "activity_datetime", "tier"]
        trx_table = funnel_table[funnel_table["activity"] == "paid"][filter_column].copy().reset_index(drop=True)
        
        if trx_table.empty:
            continue

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
        output_trx = "output/transaction.csv"

        append_or_create_csv(output_trx, trx_table[trx_column_list])

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

        output_trx_item = "output/transaction_item.csv"
        append_or_create_csv(output_trx_item, trx_items[trx_item_column_list])


if __name__ == "__main__":
    initial_run()
    main()