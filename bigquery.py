import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Set, Union, Dict

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bigquery_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class BigQueryUploader:
    """A class to handle BigQuery data uploads with proper error handling and configuration."""
    
    def __init__(self, project_id: str, dataset_id: str, table_id: str):
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.table_id = table_id
        self.table_ref = f"{project_id}.{dataset_id}.{table_id}"
        self.client = self._initialize_client()
    
    def _initialize_client(self) -> bigquery.Client:
        """Initialize BigQuery client with service account credentials."""
        json_str = os.getenv("GOOGLE_SERVICE_ACCOUNT")
        if not json_str:
            logger.error("GOOGLE_SERVICE_ACCOUNT environment variable is not set")
            raise ValueError("GOOGLE_SERVICE_ACCOUNT environment variable is not set")
        
        try:
            credentials_dict = json.loads(json_str)
            credentials = service_account.Credentials.from_service_account_info(credentials_dict)
            logger.info(f"Successfully initialized BigQuery client for project: {self.project_id}")
            return bigquery.Client(credentials=credentials, project=self.project_id)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT: {e}")
            raise ValueError(f"Invalid JSON in GOOGLE_SERVICE_ACCOUNT: {e}")
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery client: {e}")
            raise RuntimeError(f"Failed to initialize BigQuery client: {e}")
    
    def delete_table_if_exists(self) -> None:
        """Delete the target table if it exists."""
        try:
            self.client.delete_table(self.table_ref, not_found_ok=True)
            print(f"Table {self.table_ref} deleted or did not exist")
        except Exception as e:
            raise RuntimeError(f"Failed to delete table {self.table_ref}: {e}")
    
    def upload_dataframe(self, df: pd.DataFrame, write_disposition: str = "WRITE_APPEND", 
                        columns_to_keep: Optional[List[str]] = None) -> None:
        """Upload a pandas DataFrame to BigQuery table with optional column filtering."""
        if not isinstance(df, pd.DataFrame):
            raise TypeError("df must be a pandas DataFrame")
        
        if df.empty:
            raise ValueError("DataFrame is empty")
        
        # Filter columns if specified
        if columns_to_keep:
            missing_columns = set(columns_to_keep) - set(df.columns)
            if missing_columns:
                raise ValueError(f"Columns not found in DataFrame: {missing_columns}")
            df = df[columns_to_keep]
            print(f"Filtered to columns: {columns_to_keep}")
        
        try:
            job_config = bigquery.LoadJobConfig(
                write_disposition=write_disposition,
                autodetect=True
            )
            
            job = self.client.load_table_from_dataframe(
                df, self.table_ref, job_config=job_config
            )
            
            print(f"Starting upload job {job.job_id}...")
            job.result()  # Wait for the job to complete
            
            print(f"Successfully uploaded {len(df)} rows to {self.table_ref}")
            
        except Exception as e:
            raise RuntimeError(f"Failed to upload DataFrame to BigQuery: {e}")
    
    def create_empty_table(self) -> None:
        """Create an empty table with the specified reference."""
        try:
            table = bigquery.Table(self.table_ref)
            self.client.create_table(table)
            print(f"Created empty table {self.table_ref}")
        except Exception as e:
            raise RuntimeError(f"Failed to create table {self.table_ref}: {e}")


    def upload_parquet_files(self, directory_path: str, target_table_name: Optional[str] = None,
                          columns_to_keep: Optional[Union[List[str], Dict[str, List[str]]]] = None,
                          write_disposition: str = "WRITE_TRUNCATE") -> None:
        """Upload all parquet files from a directory to BigQuery tables.
        
        If target_table_name is provided, all files are combined into one table.
        If not provided, each file creates its own table named after the filename.
        """
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        parquet_files = list(directory.glob("*.parquet"))
        if not parquet_files:
            raise ValueError(f"No parquet files found in {directory_path}")
        
        print(f"Found {len(parquet_files)} parquet files:")
        for file in parquet_files:
            print(f"  - {file.name}")
        
        original_table_ref = self.table_ref
        
        if target_table_name:
            # Combine all files into a single table
            print(f"\nUploading all files to single table: {target_table_name}")
            self.table_ref = f"{self.project_id}.{self.dataset_id}.{target_table_name}"
            
            # Delete and recreate the table to reset expiration
            print(f"Deleting existing table {self.table_ref}...")
            self.delete_table_if_exists()
            print(f"Creating new table {self.table_ref}...")
            self.create_empty_table()
            
            # Combine all parquet files into a single DataFrame
            all_data = []
            for parquet_file in parquet_files:
                try:
                    print(f"\nProcessing {parquet_file.name}...")
                    df = pd.read_parquet(parquet_file)
                    
                    # Add source file column for tracking
                    df['source_file'] = parquet_file.stem
                    
                    # Apply file-specific column filtering if available
                    file_specific_columns = None
                    if isinstance(columns_to_keep, dict) and parquet_file.stem in columns_to_keep:
                        file_specific_columns = columns_to_keep[parquet_file.stem]
                    elif columns_to_keep is not None:
                        file_specific_columns = columns_to_keep
                    
                    if file_specific_columns:
                        # Ensure source_file is included if filtering
                        if 'source_file' not in file_specific_columns:
                            file_specific_columns = file_specific_columns + ['source_file']
                        missing_columns = set(file_specific_columns) - set(df.columns)
                        if missing_columns:
                            print(f"Warning: Missing columns {missing_columns} in {parquet_file.name}")
                            available_columns = [col for col in file_specific_columns if col in df.columns]
                            df = df[available_columns]
                        else:
                            df = df[file_specific_columns]
                        print(f"Filtered to columns: {list(df.columns)}")
                    
                    all_data.append(df)
                    print(f"Added {len(df)} rows from {parquet_file.name}")
                    
                except Exception as e:
                    print(f"Failed to process {parquet_file.name}: {e}")
                    continue
            
            if not all_data:
                raise ValueError("No data was successfully loaded from any parquet files")
            
            # Combine all data
            combined_df = pd.concat(all_data, ignore_index=True)
            print(f"\nCombined total: {len(combined_df)} rows from {len(all_data)} files")
            
            # Upload the combined data
            self.upload_dataframe(combined_df, write_disposition=write_disposition)
            print(f"\nSuccessfully uploaded all data to table {target_table_name}")
            
        else:
            # Create separate tables for each file
            print(f"\nUploading each file to its own table:")
            for parquet_file in parquet_files:
                try:
                    print(f"\nProcessing {parquet_file.name}...")
                    df = pd.read_parquet(parquet_file)
                    
                    # Create table name from filename (without extension)
                    table_name = parquet_file.stem
                    self.table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
                    
                    # Delete and recreate the table to reset expiration
                    print(f"Deleting existing table {self.table_ref}...")
                    self.delete_table_if_exists()
                    print(f"Creating new table {self.table_ref}...")
                    self.create_empty_table()
                    
                    # Apply file-specific column filtering if available
                    file_specific_columns = None
                    if isinstance(columns_to_keep, dict) and table_name in columns_to_keep:
                        file_specific_columns = columns_to_keep[table_name]
                    elif columns_to_keep is not None:
                        file_specific_columns = columns_to_keep
                    
                    # Upload the data
                    self.upload_dataframe(df, write_disposition=write_disposition, columns_to_keep=file_specific_columns)
                    print(f"Successfully uploaded {len(df)} rows to table {table_name}")
                    
                except Exception as e:
                    print(f"Failed to process {parquet_file.name}: {e}")
                    continue
            
            print(f"\nCompleted processing all parquet files")
        
        # Restore original table reference
        self.table_ref = original_table_ref


def main():
    """Main function to upload parquet files from output directory."""
    logger.info("Starting BigQuery upload process")
    
    # Configuration
    PROJECT_ID = os.getenv("BIGQUERY_PROJECT_ID")
    DATASET_ID = os.getenv("BIGQUERY_DATASET_ID")
    TABLE_ID = os.getenv("BIGQUERY_TABLE_ID")  # Default table for single uploads
    OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
    
    logger.info(f"Configuration - Project: {PROJECT_ID}, Dataset: {DATASET_ID}, Output Dir: {OUTPUT_DIR}")
    
    # Column filtering configuration - modify as needed
    # Set to None to keep all columns, or specify list of columns to keep
    COLUMNS_TO_KEEP = {
        'funnel': ['session_id', 'user_id', 'activity', 'activity_datetime'],  # Excluding 'tier'
        'transaction': ['session_id', 'trx_id', 'date'],  # Excluding 'tier'
        'transaction_item': ['trx_id', 'date', 'product', 'quantity', 'unit_price', 'total_price'],  # Excluding 'tier'
        'users_base': ['user_id', 'city', 'gender', 'acquisition_channel', 'registered_date', 'last_active_date'],  # Excluding 'tier'
        'users_new': ['user_id', 'city', 'gender', 'acquisition_channel', 'registered_date', 'last_active_date'],  # Excluding 'tier'
        'users_updated': ['user_id', 'city', 'gender', 'acquisition_channel', 'registered_date', 'last_active_date']  # Excluding 'tier'
    }
    
    if not all([PROJECT_ID, DATASET_ID]):
        logger.error("BIGQUERY_PROJECT_ID and BIGQUERY_DATASET_ID environment variables are required")
        return 1
    
    try:
        # Initialize uploader
        uploader = BigQueryUploader(PROJECT_ID, DATASET_ID, TABLE_ID or "default_table")
        
        # Upload all parquet files with column filtering
        # Use filename as table name by default, or set TARGET_TABLE_NAME to combine all files
        TARGET_TABLE_NAME = os.getenv("TARGET_TABLE_NAME")  # None = use filename as table name
        
        logger.info(f"Target table mode: {'Single table: ' + TARGET_TABLE_NAME if TARGET_TABLE_NAME else 'Separate tables per file'}")
        
        uploader.upload_parquet_files(
            directory_path=OUTPUT_DIR,
            target_table_name=TARGET_TABLE_NAME,  # None = create separate tables per file
            columns_to_keep=COLUMNS_TO_KEEP,  # Use file-specific column filtering
            write_disposition="WRITE_TRUNCATE"
        )
        
        logger.info("BigQuery upload completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"BigQuery upload failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())