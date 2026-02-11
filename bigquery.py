import os
from pathlib import Path

import pyarrow.parquet as pq
from google.cloud import bigquery
from google.oauth2 import service_account

# ---- Config from env (GitHub Secrets) ----
PROJECT_ID = os.environ["BIGQUERY_PROJECT_ID"]
DATASET_ID = os.environ["BIGQUERY_DATASET_ID"]
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

COLUMN_TO_DROP = "tier"  # set to None if you don't want to drop anything

# ---- Auth (service account JSON string) ----
credentials = service_account.Credentials.from_service_account_info(
    json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT"])
)

client = bigquery.Client(
    project=PROJECT_ID,
    credentials=credentials,
)

# ---- Upload loop ----
for file in Path(OUTPUT_DIR).glob("*.parquet"):
    print(f"Uploading {file.name}...")

    table = pq.read_table(file)

    if COLUMN_TO_DROP and COLUMN_TO_DROP in table.schema.names:
        table = table.drop([COLUMN_TO_DROP])

    table_id = f"{PROJECT_ID}.{DATASET_ID}.{file.stem}"

    job = client.load_table_from_file(
        file_obj=table,  # PyArrow table is supported
        destination=table_id,
        job_config=bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.PARQUET,
            write_disposition="WRITE_TRUNCATE",
            autodetect=True,
        ),
    )

    job.result()
    print(f"✅ Done: {table_id}")