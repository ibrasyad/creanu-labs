import os
import json
import tempfile
from pathlib import Path

import pyarrow.parquet as pq
from google.cloud import bigquery
from google.oauth2 import service_account

PROJECT_ID = os.environ["BIGQUERY_PROJECT_ID"]
DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

COLUMN_TO_DROP = "tier"  # set None to keep all columns

credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
)

client = bigquery.Client(
    project=PROJECT_ID,
    credentials=credentials,
)

# ----------------------------
# Explicit schemas per table
# ----------------------------

SCHEMAS = {
    "users_base": [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("registered_date", "DATETIME"),
        bigquery.SchemaField("last_active_date", "DATETIME"),
    ],
    "users_new": [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("registered_date", "DATETIME"),
        bigquery.SchemaField("last_active_date", "DATETIME"),
    ],
    "users_updated": [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("registered_date", "DATETIME"),
        bigquery.SchemaField("last_active_date", "DATETIME"),
    ],
    "funnel": [
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),

        bigquery.SchemaField("landing_page", "STRING"),
        bigquery.SchemaField("landing_page_datetime", "DATETIME"),

        bigquery.SchemaField("product_view", "STRING"),
        bigquery.SchemaField("product_view_datetime", "DATETIME"),

        bigquery.SchemaField("add_to_cart", "STRING"),
        bigquery.SchemaField("add_to_cart_datetime", "DATETIME"),

        bigquery.SchemaField("checkout", "STRING"),
        bigquery.SchemaField("checkout_datetime", "DATETIME"),

        bigquery.SchemaField("paid", "STRING"),
        bigquery.SchemaField("paid_datetime", "DATETIME"),
    ],
    "transaction": [
        bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("session_id", "STRING"),

        bigquery.SchemaField("transaction_datetime", "DATETIME", mode="REQUIRED"),
        bigquery.SchemaField("total_amount", "FLOAT"),
        bigquery.SchemaField("payment_method", "STRING"),
        bigquery.SchemaField("status", "STRING"),
    ],
    "transaction_item": [
        bigquery.SchemaField("transaction_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("quantity", "INTEGER"),
        bigquery.SchemaField("price", "FLOAT"),
    ],
}

# ----------------------------
# Upload loop
# ----------------------------

for file in Path(OUTPUT_DIR).glob("*.parquet"):
    table_name = file.stem
    print(f"Uploading {file.name}...")

    table = pq.read_table(file)

    if COLUMN_TO_DROP and COLUMN_TO_DROP in table.schema.names:
        table = table.drop([COLUMN_TO_DROP])

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{table_name}"

    schema = SCHEMAS.get(table_name)
    if not schema:
        raise ValueError(f"No schema defined for table: {table_name}")

    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.PARQUET,
        schema=schema,                     # 👈 force schema
        write_disposition="WRITE_TRUNCATE",
    )

    with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
        pq.write_table(table, tmp.name)

        with open(tmp.name, "rb") as f:
            job = client.load_table_from_file(
                f,
                table_id,
                job_config=job_config,
            )

        job.result()

    print(f"✅ Done: {table_id}")
