import pandas as pd
import yaml, random
from pathlib import Path
from sim.generate_basket import generate_basket, trx_by_day_of_week, weighted_choice
from sim.generate_date import date_list, day_of_week

BASE_DIR = Path(__file__).resolve().parent

# ------------------------
# Load configs once
# ------------------------

def load_yaml(path):
    with open(path) as f:
        return yaml.safe_load(f)

catalog = load_yaml(BASE_DIR / "config/catalog.yaml")["catalog"]
tiers = load_yaml(BASE_DIR / "config/tiers.yaml")["tiers"]
sim = load_yaml(BASE_DIR / "config/simulation.yaml")["simulation"]

# ------------------------
# Main API
# ------------------------

date_list = date_list("2026-01-12", "2026-01-13")

rows = []

for i in date_list:
    day_of_week_name = day_of_week(i)
    total_trx = trx_by_day_of_week(day_of_week_name)

    # Build tier weights for this weekday
    tier_weights = {
        tier_name: tier["transaction_weight"][day_of_week_name]
        for tier_name, tier in tiers.items()
    }

    for j in range(int(total_trx)):
        tier_name = weighted_choice(tier_weights)
        basket = generate_basket(tier_name=tier_name)

        for item in basket:
            item["trx_id"] = j + 1
            item["date"] = i
            rows.append(item)


df = pd.DataFrame(rows)

df.to_csv("output/baskets.csv", index=False)

# import pandas as pd
# from sim.generate_basket import generate_basket

# rows = []

# #input how many transactions you want to generate
# trx_count = input("Enter number of transactions to generate: ")

# for i in range(int(trx_count)):
#     basket = generate_basket()
#     for item in basket:
#         item["trx_id"] = i+1
#         rows.append(item)

# df = pd.DataFrame(rows)

# df.to_csv("output/baskets.csv", index=False)