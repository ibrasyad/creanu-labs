"""
DuckDB database integration for lettuce-melon.
Handles all database operations instead of CSV files.
"""
import duckdb
import pandas as pd
import os
from pathlib import Path
from datetime import datetime

# Database file path
DB_PATH = "output/lettuce_melon.duckdb"

class LettuceMelonDB:
    def __init__(self, db_path=DB_PATH):
        """Initialize database connection."""
        self.db_path = db_path
        self.conn = None
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    def connect(self):
        """Connect to the database."""
        if self.conn is None:
            self.conn = duckdb.connect(self.db_path)
        return self.conn
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_tables(self):
        """Create all necessary tables."""
        conn = self.connect()
        
        # Users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id VARCHAR PRIMARY KEY,
                tier VARCHAR,
                city VARCHAR,
                gender VARCHAR,
                acquisition_channel VARCHAR,
                registered_date DATE,
                last_active_date DATE
            )
        """)
        
        # Transaction table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transaction (
                session_id VARCHAR,
                trx_id VARCHAR,
                date DATE,
                tier VARCHAR
            )
        """)
        
        # Transaction item table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS transaction_item (
                trx_id VARCHAR,
                tier VARCHAR,
                date DATE,
                product VARCHAR,
                quantity INTEGER,
                unit_price INTEGER,
                total_price INTEGER
            )
        """)
        
        # Funnel table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS funnel (
                session_id VARCHAR,
                tier VARCHAR,
                user_id VARCHAR,
                activity VARCHAR,
                activity_datetime TIMESTAMP
            )
        """)
        
        # Catalog table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS catalog (
                category VARCHAR,
                subcategory VARCHAR,
                product VARCHAR,
                base_price INTEGER
            )
        """)
        
        # Create indexes for better performance
        conn.execute("CREATE INDEX IF NOT EXISTS idx_users_last_active ON users(last_active_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trx_date ON transaction(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_trx_item_date ON transaction_item(date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_funnel_date ON funnel(activity_datetime)")
        
        # Check existing users
        existing_users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        print(f"Database initialized at {self.db_path}")
        print(f"Existing users in database: {existing_users}")
        
        if existing_users > 0:
            sample_users = conn.execute("SELECT user_id, tier FROM users LIMIT 5").fetchdf()
            print("Sample existing users:")
            print(sample_users)
    
    def load_catalog_from_csv(self, csv_path="output/catalog.csv"):
        """Load catalog data from CSV file."""
        if not os.path.exists(csv_path):
            print(f"Catalog CSV not found: {csv_path}")
            return
        
        conn = self.connect()
        catalog_df = pd.read_csv(csv_path)
        
        # Clear existing catalog and load new data
        conn.execute("DELETE FROM catalog")
        conn.execute("INSERT INTO catalog SELECT * FROM catalog_df")
        
        print(f"Loaded {len(catalog_df)} catalog items")
    
    def get_users_for_date(self, date):
        """Get users who might be active on given date."""
        conn = self.connect()
        
        # Get all users, but prioritize recently active ones
        users_df = conn.execute("""
            SELECT user_id, tier, city, gender, acquisition_channel, registered_date, last_active_date
            FROM users
            ORDER BY last_active_date DESC
        """).fetchdf()
        
        return users_df
    
    def insert_users(self, users_df):
        """Insert new users."""
        if users_df.empty:
            return
        
        conn = self.connect()
        
        # Debug: print the dataframe structure and first few rows
        print(f"DEBUG: users_df columns: {list(users_df.columns)}")
        print(f"DEBUG: users_df shape: {users_df.shape}")
        print(f"DEBUG: First few rows:")
        print(users_df.head())
        
        # Check for duplicates before inserting
        if 'user_id' in users_df.columns:
            duplicates = users_df['user_id'].duplicated().sum()
            if duplicates > 0:
                print(f"WARNING: Found {duplicates} duplicate user_ids in new data")
                print("Duplicate user_ids:", users_df[users_df['user_id'].duplicated()]['user_id'].tolist())
        
        conn.execute("INSERT INTO users SELECT * FROM users_df")
        print(f"Inserted {len(users_df)} new users")
    
    def update_user_activity(self, user_ids, date):
        """Update last_active_date for users who visited today."""
        if not user_ids:
            return
        
        conn = self.connect()
        # Convert user_ids to strings and quote them for SQL
        user_ids_str = ",".join([f"'{uid}'" for uid in user_ids])
        
        conn.execute(f"""
            UPDATE users 
            SET last_active_date = '{date}'
            WHERE user_id IN ({user_ids_str})
        """)
        
        print(f"Updated activity for {len(user_ids)} users")
    
    def insert_funnel_activities(self, funnel_df):
        """Insert funnel activities."""
        if funnel_df.empty:
            return
        
        conn = self.connect()
        conn.execute("INSERT INTO funnel SELECT * FROM funnel_df")
        print(f"Inserted {len(funnel_df)} funnel activities")
    
    def insert_transactions(self, trx_df, trx_items_df):
        """Insert transactions and transaction items."""
        if trx_df.empty:
            return
        
        conn = self.connect()
        
        # Insert transactions
        conn.execute("INSERT INTO transaction SELECT * FROM trx_df")
        print(f"Inserted {len(trx_df)} transactions")
        
        # Insert transaction items
        if not trx_items_df.empty:
            conn.execute("INSERT INTO transaction_item SELECT * FROM trx_items_df")
            print(f"Inserted {len(trx_items_df)} transaction items")
    
    def get_visited_users(self, date):
        """Get users who visited on specific date (landing_page activity)."""
        conn = self.connect()
        
        result = conn.execute("""
            SELECT DISTINCT user_id
            FROM funnel
            WHERE activity = 'landing_page' 
            AND DATE(activity_datetime) = '{date}'
        """.format(date=date)).fetchdf()
        
        return result
    
    def get_stats(self):
        """Get database statistics."""
        conn = self.connect()
        
        stats = {}
        tables = ['users', 'transaction', 'transaction_item', 'funnel', 'catalog']
        
        for table in tables:
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                stats[table] = count
            except:
                stats[table] = 0
        
        return stats
    
    def export_to_csv(self, output_dir="output"):
        """Export all tables back to CSV format."""
        os.makedirs(output_dir, exist_ok=True)
        conn = self.connect()
        
        tables = {
            'users': 'users_updated.csv',
            'transaction': 'transaction.csv',
            'transaction_item': 'transaction_item.csv',
            'funnel': 'funnel.csv',
            'catalog': 'catalog.csv'
        }
        
        for table, filename in tables.items():
            try:
                df = conn.execute(f"SELECT * FROM {table}").fetchdf()
                df.to_csv(os.path.join(output_dir, filename), index=False)
                print(f"Exported {table} to {filename}")
            except Exception as e:
                print(f"Error exporting {table}: {e}")

# Context manager for database operations
class DatabaseContext:
    def __init__(self, db_path=DB_PATH):
        self.db = LettuceMelonDB(db_path)
    
    def __enter__(self):
        self.db.connect()
        return self.db
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.db.close()
