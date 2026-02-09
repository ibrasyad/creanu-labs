import pandas as pd
import os
from pathlib import Path

def convert_csv_files():
    """Convert CSV files in output directory to Parquet and XLSX formats"""
    
    # Set up paths
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Find all CSV files
    csv_files = list(output_dir.glob("*.csv"))
    
    if not csv_files:
        print("No CSV files found in output directory")
        return
    
    print(f"Found {len(csv_files)} CSV files to convert:")
    
    for csv_file in csv_files:
        print(f"\nProcessing: {csv_file.name}")
        
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            print(f"  - Shape: {df.shape}")
            
            # Convert to Parquet
            parquet_file = output_dir / f"{csv_file.stem}.parquet"
            df.to_parquet(parquet_file, index=False)
            parquet_size = parquet_file.stat().st_size
            print(f"  - Parquet: {parquet_file.name} ({parquet_size:,} bytes)")
            
            # Convert to XLSX
            xlsx_file = output_dir / f"{csv_file.stem}.xlsx"
            df.to_excel(xlsx_file, index=False)
            xlsx_size = xlsx_file.stat().st_size
            print(f"  - XLSX: {xlsx_file.name} ({xlsx_size:,} bytes)")
            
            # Show original CSV size
            csv_size = csv_file.stat().st_size
            print(f"  - CSV: {csv_file.name} ({csv_size:,} bytes)")
            
        except Exception as e:
            print(f"  - Error processing {csv_file.name}: {e}")
    
    print("\nConversion complete!")

if __name__ == "__main__":
    convert_csv_files()
