"""Load generated analytics tables into BigQuery."""
import json
import os
import tempfile
from pathlib import Path

import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq
from google.cloud import bigquery
from google.oauth2 import service_account

COLUMN_TO_DROP = "tier"

SCHEMAS = {
    "catalog": [bigquery.SchemaField("category", "STRING", mode="REQUIRED"), bigquery.SchemaField("subcategory", "STRING", mode="REQUIRED"), bigquery.SchemaField("product", "STRING", mode="REQUIRED"), bigquery.SchemaField("base_price", "INTEGER", mode="REQUIRED")],
    "users_base": [bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("city", "STRING", mode="REQUIRED"), bigquery.SchemaField("gender", "STRING", mode="REQUIRED"), bigquery.SchemaField("acquisition_channel", "STRING", mode="REQUIRED"), bigquery.SchemaField("registered_date", "DATETIME", mode="REQUIRED"), bigquery.SchemaField("last_active_date", "DATETIME")],
    "users_new": [bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("city", "STRING", mode="REQUIRED"), bigquery.SchemaField("gender", "STRING", mode="REQUIRED"), bigquery.SchemaField("acquisition_channel", "STRING", mode="REQUIRED"), bigquery.SchemaField("registered_date", "DATETIME", mode="REQUIRED"), bigquery.SchemaField("last_active_date", "DATETIME")],
    "users_updated": [bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("city", "STRING", mode="REQUIRED"), bigquery.SchemaField("gender", "STRING", mode="REQUIRED"), bigquery.SchemaField("acquisition_channel", "STRING", mode="REQUIRED"), bigquery.SchemaField("registered_date", "DATETIME", mode="REQUIRED"), bigquery.SchemaField("last_active_date", "DATETIME")],
    "funnel": [bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("activity", "STRING", mode="REQUIRED"), bigquery.SchemaField("activity_datetime", "DATETIME", mode="REQUIRED")],
    "transaction": [bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("trx_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("date", "DATETIME", mode="REQUIRED"), bigquery.SchemaField("total_price", "INTEGER", mode="REQUIRED")],
    "transaction_item": [bigquery.SchemaField("trx_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"), bigquery.SchemaField("date", "DATETIME", mode="REQUIRED"), bigquery.SchemaField("product", "STRING", mode="REQUIRED"), bigquery.SchemaField("quantity", "INTEGER", mode="REQUIRED"), bigquery.SchemaField("unit_price", "INTEGER", mode="REQUIRED"), bigquery.SchemaField("total_price", "INTEGER", mode="REQUIRED")],
}
DATETIME_COLUMNS = {"users_base": ["registered_date", "last_active_date"], "users_new": ["registered_date", "last_active_date"], "users_updated": ["registered_date", "last_active_date"], "funnel": ["activity_datetime"], "transaction": ["date"], "transaction_item": ["date"]}


def main():
    project_id, dataset_id = os.environ["BIGQUERY_PROJECT_ID"], os.environ["BIGQUERY_DATASET_ID"]
    credentials = service_account.Credentials.from_service_account_info(json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"]))
    client = bigquery.Client(project=project_id, credentials=credentials)
    for file in Path(os.getenv("OUTPUT_DIR", "output")).glob("*.parquet"):
        if file.name.startswith("_"):
            continue
        table_name = file.stem
        schema = SCHEMAS.get(table_name)
        if schema is None:
            raise ValueError(f"No schema defined for table: {table_name}")
        table = pq.read_table(file)
        for column in DATETIME_COLUMNS.get(table_name, []):
            if column not in table.schema.names:
                continue
            value = table[column]
            if pa.types.is_string(value.type):
                value = pc.strptime(value, format="%Y-%m-%d %H:%M:%S", unit="us")
            if not pa.types.is_timestamp(value.type):
                value = value.cast(pa.timestamp("us"))
            table = table.set_column(table.schema.get_field_index(column), column, value)
        if COLUMN_TO_DROP and COLUMN_TO_DROP in table.schema.names:
            table = table.drop([COLUMN_TO_DROP])
        with tempfile.NamedTemporaryFile(suffix=".parquet") as tmp:
            pq.write_table(table, tmp.name)
            with open(tmp.name, "rb") as source:
                job = client.load_table_from_file(source, f"{project_id}.{dataset_id}.{table_name}", job_config=bigquery.LoadJobConfig(source_format=bigquery.SourceFormat.PARQUET, schema=schema, write_disposition="WRITE_TRUNCATE"))
            job.result()
        print(f"Done: {table_name}")


if __name__ == "__main__":
    main()
