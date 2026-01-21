"""
Main transaction data generation script.
"""
import pandas as pd
import random
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket, generate_total_trx
from sim.utils import date_range, get_day_of_week, weighted_choice, generate_catalog_csv, append_or_create_csv
from sim.generate_user import generate_new_users, roll_new_user_chance, generate_base_user_table
from sim.generate_funnel import generate_funnel_table

trx_column_list = [
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
        "tier",
        "user_id",
        "landing_page",
        "landing_page_datetime",
        "product_view",
        "product_view_datetime",
        "add_to_cart",
        "add_to_cart_datetime",
        "checkout",
        "checkout_datetime",
        "paid",
        "paid_datetime"
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
        rows = []
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
            new_user_table.to_csv("output/users_new.csv", index=False)
            final_user_table = pd.concat([base_user_table, new_user_table], ignore_index=True)
            final_user_table.to_csv("output/users_updated.csv", index=False)
        
        # Generate funnel here
        output_funnel = "output/funnel.csv"
        funnel_table = generate_funnel_table(date)
        append_or_create_csv(
            output_funnel,
            funnel_table
            )
        
        # -------------------
        # Generate the basket
        filter_column = ["paid_datetime", "tier"]
        trx_table = funnel_table[funnel_table["paid"] == "paid"][filter_column].copy().reset_index(drop=True)
        
        if trx_table.empty:
            continue

        rename_column = {
            "paid_datetime": "date", 
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
            trx_table["date"].dt.strftime("%Y%m%d") +
            trx_table["trx_seq"].astype(str).str.zfill(8)
        )
        trx_table.drop(columns=["trx_seq"], inplace=True)
        output_trx = "output/transaction.csv"

        append_or_create_csv(output_trx, trx_table)

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
        append_or_create_csv(output_trx_item, trx_items)

        
        # # Convert date to yyyymmdd format
        # date_yyyymmdd = date.replace("-", "")
        
        # output_item = "output/transaction_item.csv"
        # output_trx = "output/transaction.csv"
        # trx_counter = len(pd.read_csv(output_trx))


        
        # basket = generate_basket(tier_name=tier_name)
        
        # # Generate trx_id as yyyymmdd000000 format
        # trx_id = f"{date_yyyymmdd}{trx_counter + 1:06d}"
        
        # # Add date and transaction ID to each basket item
        # for item in basket:
        #     item["trx_id"] = trx_id
        #     item["date"] = date
        #     rows.append(item)

        # df_item = append_or_create_csv(
        #     output_item, 
        #     pd.DataFrame(rows)
        #     )
        
        # append_or_create_csv(
        #     output_trx, 
        #     df_item.groupby(["trx_id", "date", "tier"]).agg({
        #         "product": "nunique",
        #         "total_price": "sum"
        #     }).reset_index()
        #     )

    # # Prepare the data
    # output_item = "output/transaction_item.csv"
    # output_trx = "output/transaction.csv"

    
    # df_item = append_or_create_csv(
    #     output_item, 
    #     pd.DataFrame(rows)
    #     )
    
    # df_trx = append_or_create_csv(
    #     output_trx, 
    #     df_item.groupby(["trx_id", "date", "tier"]).agg({
    #         "product": "nunique",
    #         "total_price": "sum"
    #     }).reset_index()
    #     )
        








# def main():
#     # Generate the catalog for csv first
#     generate_catalog_csv()

#     """Generate transaction data and save to CSV."""
#     date_config = get_date_config()
#     tiers = get_tiers()
    
#     # Generate dates for the simulation period
#     dates = date_range(date_config["start_date"], date_config["end_date"])
    
#     rows = []
        
#     for date in dates:
#         weekday = get_day_of_week(date)
#         total_trx = generate_total_trx(date)
        
#         # Convert date to yyyymmdd format
#         date_str = date.replace("-", "")
#         trx_counter = 1
        
#         # Build tier weights for this weekday
#         tier_weights = {
#             tier_name: tier["transaction_weight"][weekday]
#             for tier_name, tier in tiers.items()
#         }
        
#         # Generate transactions for this day
#         for trx_counter in range(int(total_trx)):
#             tier_name = weighted_choice(tier_weights)
#             basket = generate_basket(tier_name=tier_name)
            
#             # Generate trx_id as yyyymmdd000000 format
#             trx_id = f"{date_str}{trx_counter + 1:06d}"
            
#             # Add date and transaction ID to each basket item
#             for item in basket:
#                 item["trx_id"] = trx_id
#                 item["date"] = date
#                 rows.append(item)
    
#     # Prepare the data
#     df_item = pd.DataFrame(rows)
    
#     df_trx = df_item.groupby(["trx_id", "date", "tier"]).agg({
#         "product": "nunique",
#         "total_price": "sum"
#     }).reset_index()

#     # Save to CSV
#     df_item.to_csv("output/transaction_item.csv", index=False)
#     df_trx.to_csv("output/transaction.csv", index=False)
    
#     # Print summary
#     total_trx = df_item["trx_id"].nunique()
#     print(f"Generated {len(df_item)} line items from {total_trx} transactions")
    
#     for tier_name in df_item['tier'].unique():
#         tier_transaction_count = df_item[df_item['tier'] == tier_name]['trx_id'].nunique()
#         print(f" - Tier '{tier_name}': {tier_transaction_count} transactions")
#         tier_basket_count = df_item[df_item['tier'] == tier_name]['trx_id'].count()
#         print(f"   - Tier '{tier_name}': {tier_basket_count} total item")



if __name__ == "__main__":
    initial_run()
    main()