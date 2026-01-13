"""
Main transaction data generation script.
"""
import pandas as pd
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket, generate_total_trx
from sim.utils import date_range, get_day_of_week, weighted_choice, generate_catalog_csv


def main():
    # Generate the catalog for csv first
    generate_catalog_csv()

    """Generate transaction data and save to CSV."""
    date_config = get_date_config()
    tiers = get_tiers()
    
    # Generate dates for the simulation period
    dates = date_range(date_config["start_date"], date_config["end_date"])
    
    rows = []
        
    for date in dates:
        weekday = get_day_of_week(date)
        total_trx = generate_total_trx(date)
        
        # Convert date to yyyymmdd format
        date_str = date.replace("-", "")
        trx_counter = 1
        
        # Build tier weights for this weekday
        tier_weights = {
            tier_name: tier["transaction_weight"][weekday]
            for tier_name, tier in tiers.items()
        }
        
        # Generate transactions for this day
        for trx_counter in range(int(total_trx)):
            tier_name = weighted_choice(tier_weights)
            basket = generate_basket(tier_name=tier_name)
            
            # Generate trx_id as yyyymmdd000000 format
            trx_id = f"{date_str}{trx_counter + 1:06d}"
            
            # Add date and transaction ID to each basket item
            for item in basket:
                item["trx_id"] = trx_id
                item["date"] = date
                rows.append(item)
    
    # Prepare the data
    df_item = pd.DataFrame(rows)
    
    df_trx = df_item.groupby(["trx_id", "date", "tier"]).agg({
        "product": "nunique",
        "total_price": "sum"
    }).reset_index()

    # Save to CSV
    df_item.to_csv("output/transaction_item.csv", index=False)
    df_trx.to_csv("output/transaction.csv", index=False)
    
    # Print summary
    total_trx = df_item["trx_id"].nunique()
    print(f"Generated {len(df_item)} line items from {total_trx} transactions")
    
    for tier_name in df_item['tier'].unique():
        tier_transaction_count = df_item[df_item['tier'] == tier_name]['trx_id'].nunique()
        print(f" - Tier '{tier_name}': {tier_transaction_count} transactions")
        tier_basket_count = df_item[df_item['tier'] == tier_name]['trx_id'].count()
        print(f"   - Tier '{tier_name}': {tier_basket_count} total item")


if __name__ == "__main__":
    main()