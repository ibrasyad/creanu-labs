import os
import json
from pathlib import Path

import pyarrow.parquet as pq
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = os.environ["BIGQUERY_PROJECT_ID"]
DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

COLUMN_TO_DROP = "tier"

credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
)

client = bigquery.Client(
    project=PROJECT_ID,
    credentials=credentials,
)

for file in Path(OUTPUT_DIR).glob("*.parquet"):
    print(f"Uploading {file.name}...")

    table = pq.read_table(file)

    if COLUMN_TO_DROP and COLUMN_TO_DROP in table.schema.names:
        table = table.drop([COLUMN_TO_DROP])

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{file.stem}"

    job = client.load_table_from_dataframe(
        table,
        table_id,
        job_config=bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
            autodetect=True,
        ),
    )

    job.result()
    print(f"✅ Done: {table_id}")
