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
    df_transaction_item = pd.DataFrame(columns=[
        "tier",
        "product",
        "quantity",
        "unit_price",
        "total_price",
        "trx_id",
        "date"
    ])
    df_transaction_item.to_csv("output/transaction_item.csv", index=False)

    # -------------------
    # Create EMPTY transaction.csv
    df_transaction = pd.DataFrame(columns=[
        "trx_id",
        "date",
        "tier",
        "product",
        "total_price"
    ])
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

    rows = []
    new_user_rows = []

    for date in dates:
        
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

    # print(len(final_user_table))
        
    #     # -------------------
    #     # Generate the basket
    #     weekday = get_day_of_week(date)
    #     total_trx = generate_total_trx(date)
        
    #     # Convert date to yyyymmdd format
    #     date_yyyymmdd = date_iso.replace("-", "")
    #     trx_counter = 1
        
    #     # Build tier weights for this weekday NOT USED ANYMORE
    #     tier_weights = { NOT USED ANYMORE
    #         tier_name: tier["transaction_weight"][weekday] NOT USED ANYMORE
    #         for tier_name, tier in _tiers.items() NOT USED ANYMORE
    #     } NOT USED ANYMORE
        
    #     # Generate transactions for this day
    #     for trx_counter in range(int(total_trx)):
    #         tier_name = weighted_choice(tier_weights) NOT USED ANYMORE
    #         basket = generate_basket(tier_name=tier_name)
            
    #         # Generate trx_id as yyyymmdd000000 format
    #         trx_id = f"{date_yyyymmdd}{trx_counter + 1:06d}"
            
    #         # Add date and transaction ID to each basket item
    #         for item in basket:
    #             item["trx_id"] = trx_id
    #             item["date"] = date
    #             rows.append(item)

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