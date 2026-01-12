import pandas as pd
from sim.generate_basket import generate_basket

rows = []

#input how many transactions you want to generate
trx_count = input("Enter number of transactions to generate: ")

for i in range(int(trx_count)):
    basket = generate_basket()
    for item in basket:
        item["trx_id"] = i+1
        rows.append(item)

df = pd.DataFrame(rows)

df.to_csv("output/baskets.csv", index=False)