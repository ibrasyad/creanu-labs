import os
import json
import tempfile
from pathlib import Path

import pyarrow.parquet as pq
import pyarrow as pa
import pyarrow.compute as pc
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
    "catalog": [
        bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("subcategory", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("product", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("base_price", "INTEGER", mode="REQUIRED"),
    ],
    "users_base": [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gender", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("acquisition_channel", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("registered_date", "DATETIME", mode="REQUIRED"),
        bigquery.SchemaField("last_active_date", "DATETIME"),
    ],
    "users_new": [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gender", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("acquisition_channel", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("registered_date", "DATETIME", mode="REQUIRED"),
        bigquery.SchemaField("last_active_date", "DATETIME"),
    ],
    "users_updated": [
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("city", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("gender", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("acquisition_channel", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("registered_date", "DATETIME", mode="REQUIRED"),
        bigquery.SchemaField("last_active_date", "DATETIME"),
    ],
    "funnel": [
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
        # bigquery.SchemaField("tier", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("activity", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("activity_datetime", "DATETIME", mode="REQUIRED"),
    ],
    "transaction": [
        bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("trx_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("date", "DATETIME", mode="REQUIRED"),
    ],
    "transaction_item": [
        bigquery.SchemaField("trx_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("date", "DATETIME", mode="REQUIRED"),
        bigquery.SchemaField("product", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("unit_price", "INTEGER", mode="REQUIRED"),
        bigquery.SchemaField("total_price", "INTEGER", mode="REQUIRED"),
    ],
}

DATETIME_COLUMNS = {
    "users_base": ["registered_date", "last_active_date"],
    "users_new": ["registered_date", "last_active_date"],
    "users_updated": ["registered_date", "last_active_date"],
    "funnel": ["activity_datetime"],
    "transaction": ["date"],
    "transaction_item": ["date"],
}

# ----------------------------
# Upload loop
# ----------------------------


for file in Path(OUTPUT_DIR).glob("*.parquet"):
    table_name = file.stem
    print(f"Uploading {file.name}...")

    table = pq.read_table(file)

    if table_name in DATETIME_COLUMNS:
        for col in DATETIME_COLUMNS[table_name]:
            if col in table.schema.names:
                arr = table[col]

                # If stored as string, cast to timestamp
                if pa.types.is_string(arr.type):
                    arr = pc.strptime(
                        arr,
                        format="%Y-%m-%d %H:%M:%S",
                        unit="us"
                    )

                # Ensure final type is timestamp (no timezone)
                # If already timestamp, keep as-is (do NOT downcast precision)
                if not pa.types.is_timestamp(arr.type):
                    arr = arr.cast(pa.timestamp("us"))

                table = table.set_column(
                    table.schema.get_field_index(col),
                    col,
                    arr
                )

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
