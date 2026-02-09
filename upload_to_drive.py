#!/usr/bin/env python3
"""
Upload parquet files to Google Drive after data generation.
Requires Google Drive API credentials and service account setup.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
import argparse

try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2 import service_account
    from google.auth.transport.requests import Request
except ImportError:
    print("Required packages not found. Install with:")
    print("pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "output"

# Google Drive folder ID where files will be uploaded
# This should be set as an environment variable or hardcoded
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID", "")

def authenticate_google_drive():
    """Authenticate with Google Drive using service account."""
    creds_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_PATH")
    
    if not creds_path:
        print("Error: GOOGLE_SERVICE_ACCOUNT_PATH environment variable not set")
        return None
    
    if not os.path.exists(creds_path):
        print(f"Error: Service account file not found at {creds_path}")
        return None
    
    try:
        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Error authenticating with Google Drive: {e}")
        return None

def upload_to_drive(service, file_path, folder_id):
    """Upload a file to Google Drive."""
    try:
        file_metadata = {
            'name': file_path.name,
            'parents': [folder_id] if folder_id else []
        }
        
        media = MediaFileUpload(str(file_path), resumable=True)
        
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id,name,size'
        ).execute()
        
        print(f"✓ Uploaded {file_path.name} (ID: {file['id']}, Size: {file['size']} bytes)")
        return file['id']
        
    except Exception as e:
        print(f"✗ Failed to upload {file_path.name}: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Upload parquet files to Google Drive')
    parser.add_argument('--folder-id', help='Google Drive folder ID (overrides env var)')
    parser.add_argument('--dry-run', action='store_true', help='Show files that would be uploaded without actually uploading')
    args = parser.parse_args()
    
    folder_id = args.folder_id or DRIVE_FOLDER_ID
    
    if not folder_id and not args.dry_run:
        print("Error: Google Drive folder ID not provided. Set DRIVE_FOLDER_ID env var or use --folder-id")
        sys.exit(1)
    
    # Check if output directory exists
    if not OUTPUT_DIR.exists():
        print(f"Error: Output directory {OUTPUT_DIR} not found")
        sys.exit(1)
    
    # Find all parquet files
    parquet_files = list(OUTPUT_DIR.glob("*.parquet"))
    
    if not parquet_files:
        print("No parquet files found in output directory")
        return
    
    print(f"Found {len(parquet_files)} parquet files:")
    for file in sorted(parquet_files):
        print(f"  - {file.name} ({file.stat().st_size:,} bytes)")
    
    if args.dry_run:
        print("\nDry run mode - no files will be uploaded")
        return
    
    # Authenticate with Google Drive
    print("\nAuthenticating with Google Drive...")
    service = authenticate_google_drive()
    
    if not service:
        print("Failed to authenticate with Google Drive")
        sys.exit(1)
    
    # Upload files
    print(f"\nUploading files to Google Drive folder {folder_id}...")
    success_count = 0
    
    for file_path in sorted(parquet_files):
        if upload_to_drive(service, file_path, folder_id):
            success_count += 1
    
    print(f"\nUpload complete: {success_count}/{len(parquet_files)} files uploaded successfully")
    
    # Create upload log
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "files_uploaded": success_count,
        "total_files": len(parquet_files),
        "folder_id": folder_id
    }
    
    log_file = OUTPUT_DIR / "upload_log.txt"
    with open(log_file, "a") as f:
        f.write(f"{log_entry}\n")
    
    print(f"Upload log saved to {log_file}")

if __name__ == "__main__":
    main()
