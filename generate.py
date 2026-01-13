"""
Main transaction data generation script.
"""
import pandas as pd
from sim.config import get_date_config, get_tiers
from sim.generate_basket import generate_basket, generate_total_trx
from sim.utils import date_range, get_day_of_week, weighted_choice


def main():
    """Generate transaction data and save to CSV."""
    date_config = get_date_config()
    tiers = get_tiers()
    
    # Generate dates for the simulation period
    dates = date_range(date_config["start_date"], date_config["end_date"])
    
    rows = []
    
    for date in dates:
        weekday = get_day_of_week(date)
        total_trx = generate_total_trx(date)
        
        # Build tier weights for this weekday
        tier_weights = {
            tier_name: tier["transaction_weight"][weekday]
            for tier_name, tier in tiers.items()
        }
        
        # Generate transactions for this day
        for trx_id in range(int(total_trx)):
            tier_name = weighted_choice(tier_weights)
            basket = generate_basket(tier_name=tier_name)
            
            # Add date and transaction ID to each basket item
            for item in basket:
                item["trx_id"] = trx_id + 1
                item["date"] = date
                rows.append(item)
    
    # Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv("output/baskets.csv", index=False)
    print(f"Generated {len(df)} line items from {df['trx_id'].max()} transactions")


if __name__ == "__main__":
    main()