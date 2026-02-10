#!/usr/bin/env python3
"""
Test script to verify datetime schema and timezone in parquet files.
"""
import pandas as pd
from pathlib import Path

def check_parquet_schema():
    """Check schema and timezone info for all parquet files."""
    output_dir = Path("output")
    
    parquet_files = [
        "funnel.parquet",
        "transaction.parquet", 
        "transaction_item.parquet",
        "users_updated.parquet"
    ]
    
    print("=== PARQUET SCHEMA VERIFICATION ===\n")
    
    for file_name in parquet_files:
        file_path = output_dir / file_name
        if not file_path.exists():
            print(f"[MISSING] {file_name}: File not found")
            continue
            
        try:
            df = pd.read_parquet(file_path)
            print(f"[FILE] {file_name}:")
            print(f"   Shape: {df.shape}")
            
            # Check datetime columns
            datetime_cols = [col for col in df.columns if 'datetime64' in str(df[col].dtype)]
            if len(datetime_cols) > 0:
                print(f"   Datetime columns: {list(datetime_cols)}")
                for col in datetime_cols:
                    dtype = str(df[col].dtype)
                    has_tz = df[col].dt.tz is not None
                    tz_info = str(df[col].dt.tz) if has_tz else "None"
                    print(f"     - {col}: {dtype}, timezone: {tz_info}")
                    
                    # Show sample values
                    sample_values = df[col].dropna().head(2).tolist()
                    print(f"       Sample: {sample_values}")
            else:
                print("   No datetime columns found")
            
            print()
            
        except Exception as e:
            print(f"[ERROR] {file_name}: Error reading file - {e}")
            print()

if __name__ == "__main__":
    check_parquet_schema()
