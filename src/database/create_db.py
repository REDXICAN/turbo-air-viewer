"""
Database Creation Script for Turbo Air Equipment Viewer
Creates local SQLite database and syncs with Supabase
Updated to handle new Excel structure with Category/Subcategory
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime
from supabase import create_client, Client
from typing import Optional
import re

# Supabase schema for table creation
SUPABASE_SCHEMA = """
-- Products table
CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    sku TEXT UNIQUE NOT NULL,
    product_type TEXT,
    description TEXT,
    capacity TEXT,
    doors TEXT,
    amperage TEXT,
    dimensions TEXT,
    dimensions_metric TEXT,
    weight TEXT,
    weight_metric TEXT,
    temperature_range TEXT,
    temperature_range_metric TEXT,
    voltage TEXT,
    phase TEXT,
    frequency TEXT,
    plug_type TEXT,
    refrigerant TEXT,
    compressor TEXT,
    shelves TEXT,
    features TEXT,
    certifications TEXT,
    price DECIMAL(10,2),
    category TEXT,
    subcategory TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Other required tables
CREATE TABLE IF NOT EXISTS clients (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    company TEXT NOT NULL,
    contact_name TEXT,
    contact_email TEXT,
    contact_number TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quotes (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    client_id INTEGER REFERENCES clients(id),
    quote_number TEXT UNIQUE NOT NULL,
    total_amount DECIMAL(10,2),
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS quote_items (
    id SERIAL PRIMARY KEY,
    quote_id INTEGER REFERENCES quotes(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10,2),
    total_price DECIMAL(10,2),
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS cart_items (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    client_id INTEGER REFERENCES clients(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS search_history (
    id SERIAL PRIMARY KEY,
    user_id TEXT NOT NULL,
    search_term TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_profiles (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE,
    role TEXT DEFAULT 'distributor' CHECK (role IN ('admin', 'sales', 'distributor')),
    company TEXT,
    phone TEXT,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id);
"""

def get_supabase_client() -> Optional[Client]:
    """Get Supabase client if credentials are available"""
    try:
        import streamlit as st
        supabase_url = st.secrets.get("supabase", {}).get("url")
        supabase_key = st.secrets.get("supabase", {}).get("anon_key")
        
        if supabase_url and supabase_key:
            return create_client(supabase_url, supabase_key)
    except:
        # Try environment variables as fallback
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_ANON_KEY")
        
        if supabase_url and supabase_key:
            return create_client(supabase_url, supabase_key)
    
    return None

def create_local_database():
    """Create local SQLite database with schema"""
    conn = sqlite3.connect('turbo_air_db_online.sqlite')
    cursor = conn.cursor()
    
    # Drop existing tables to ensure clean state
    tables = [
        'products', 'clients', 'quotes', 'quote_items', 
        'cart_items', 'search_history', 'user_profiles', 
        'sync_queue', 'auth_tokens'
    ]
    
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    
    # Create products table
    cursor.execute("""
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            product_type TEXT,
            description TEXT,
            capacity TEXT,
            doors TEXT,
            amperage TEXT,
            dimensions TEXT,
            dimensions_metric TEXT,
            weight TEXT,
            weight_metric TEXT,
            temperature_range TEXT,
            temperature_range_metric TEXT,
            voltage TEXT,
            phase TEXT,
            frequency TEXT,
            plug_type TEXT,
            refrigerant TEXT,
            compressor TEXT,
            shelves TEXT,
            features TEXT,
            certifications TEXT,
            price REAL,
            category TEXT,
            subcategory TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create clients table
    cursor.execute("""
        CREATE TABLE clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            company TEXT NOT NULL,
            contact_name TEXT,
            contact_email TEXT,
            contact_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create quotes table
    cursor.execute("""
        CREATE TABLE quotes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            client_id INTEGER REFERENCES clients(id),
            quote_number TEXT UNIQUE NOT NULL,
            total_amount REAL,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create quote_items table
    cursor.execute("""
        CREATE TABLE quote_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            quote_id INTEGER REFERENCES quotes(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL,
            unit_price REAL,
            total_price REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create cart_items table
    cursor.execute("""
        CREATE TABLE cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            client_id INTEGER REFERENCES clients(id),
            product_id INTEGER REFERENCES products(id),
            quantity INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create search_history table
    cursor.execute("""
        CREATE TABLE search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            search_term TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create user_profiles table
    cursor.execute("""
        CREATE TABLE user_profiles (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            role TEXT DEFAULT 'distributor' CHECK (role IN ('admin', 'sales', 'distributor')),
            company TEXT,
            phone TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create sync_queue table
    cursor.execute("""
        CREATE TABLE sync_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_name TEXT NOT NULL,
            operation TEXT NOT NULL,
            data TEXT NOT NULL,
            synced BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create auth_tokens table
    cursor.execute("""
        CREATE TABLE auth_tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            token TEXT UNIQUE NOT NULL,
            expires_at TIMESTAMP NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create indexes for better performance
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
        "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category)",
        "CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_quotes_client_id ON quotes(client_id)",
        "CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id)",
        "CREATE INDEX IF NOT EXISTS idx_auth_tokens_token ON auth_tokens(token)",
        "CREATE INDEX IF NOT EXISTS idx_sync_queue_synced ON sync_queue(synced)"
    ]
    
    for index in indexes:
        cursor.execute(index)
    
    conn.commit()
    
    # Load initial product data if available
    if os.path.exists('turbo_air_products.xlsx'):
        try:
            print("Found turbo_air_products.xlsx - loading products...")
            load_products_from_excel(conn)
        except Exception as e:
            print(f"Warning: Could not load products from Excel: {e}")
            print("Database created without products. Please ensure Excel file is properly formatted.")
    else:
        print("Warning: turbo_air_products.xlsx not found.")
        print("Database created without products. To load products:")
        print("1. Add turbo_air_products.xlsx to the project directory")
        print("2. Restart the application or use the 'Load Products' feature")
    
    conn.close()
    return True

def clean_price(price_value) -> Optional[float]:
    """Clean and convert price value to float"""
    if pd.isna(price_value):
        return None
    
    if isinstance(price_value, (int, float)):
        return float(price_value)
    
    if isinstance(price_value, str):
        # Remove currency symbols and commas
        clean_value = re.sub(r'[$,]', '', price_value.strip())
        if clean_value:
            try:
                return float(clean_value)
            except ValueError:
                return None
    
    return None

def load_products_from_excel(conn):
    """Load products from Excel file into database and Supabase"""
    try:
        excel_path = 'turbo_air_products.xlsx'
        
        # Check if file exists
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Excel file '{excel_path}' not found in project directory")
        
        # Load product data with new column structure
        print(f"Loading Excel file: {excel_path}")
        products_df = pd.read_excel(excel_path, sheet_name=0)
        
        print(f"Found {len(products_df)} rows in Excel file")
        print(f"Columns found: {list(products_df.columns)}")
        
        # Expected columns in order
        expected_columns = [
            'SKU', 'Category', 'Subcategory', 'Product Type', 'Description',
            'Voltage', 'Amperage', 'Phase', 'Frequency', 'Plug Type',
            'Dimensions', 'Dimensions (Metric)', 'Weight', 'Weight (Metric)',
            'Temperature Range', 'Temperature Range (Metric)', 'Refrigerant',
            'Compressor', 'Capacity', 'Doors', 'Shelves', 'Features',
            'Certifications', 'Price'
        ]
        
        # Verify columns exist
        missing_columns = set(expected_columns) - set(products_df.columns)
        if missing_columns:
            print(f"Warning: Missing columns in Excel file: {missing_columns}")
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Insert products
        cursor = conn.cursor()
        products_inserted = 0
        products_skipped = 0
        products_for_supabase = []
        
        for idx, row in products_df.iterrows():
            try:
                # Get values with None for empty cells
                sku = str(row.get('SKU', '')).strip() if pd.notna(row.get('SKU')) else None
                
                if not sku:
                    products_skipped += 1
                    continue
                
                # Prepare product data
                product_data = {
                    'sku': sku,
                    'category': str(row.get('Category', '')).strip() if pd.notna(row.get('Category')) else None,
                    'subcategory': str(row.get('Subcategory', '')).strip() if pd.notna(row.get('Subcategory')) else None,
                    'product_type': str(row.get('Product Type', '')).strip() if pd.notna(row.get('Product Type')) else None,
                    'description': str(row.get('Description', '')).strip() if pd.notna(row.get('Description')) else None,
                    'voltage': str(row.get('Voltage', '')).strip() if pd.notna(row.get('Voltage')) else None,
                    'amperage': str(row.get('Amperage', '')).strip() if pd.notna(row.get('Amperage')) else None,
                    'phase': str(row.get('Phase', '')).strip() if pd.notna(row.get('Phase')) else None,
                    'frequency': str(row.get('Frequency', '')).strip() if pd.notna(row.get('Frequency')) else None,
                    'plug_type': str(row.get('Plug Type', '')).strip() if pd.notna(row.get('Plug Type')) else None,
                    'dimensions': str(row.get('Dimensions', '')).strip() if pd.notna(row.get('Dimensions')) else None,
                    'dimensions_metric': str(row.get('Dimensions (Metric)', '')).strip() if pd.notna(row.get('Dimensions (Metric)')) else None,
                    'weight': str(row.get('Weight', '')).strip() if pd.notna(row.get('Weight')) else None,
                    'weight_metric': str(row.get('Weight (Metric)', '')).strip() if pd.notna(row.get('Weight (Metric)')) else None,
                    'temperature_range': str(row.get('Temperature Range', '')).strip() if pd.notna(row.get('Temperature Range')) else None,
                    'temperature_range_metric': str(row.get('Temperature Range (Metric)', '')).strip() if pd.notna(row.get('Temperature Range (Metric)')) else None,
                    'refrigerant': str(row.get('Refrigerant', '')).strip() if pd.notna(row.get('Refrigerant')) else None,
                    'compressor': str(row.get('Compressor', '')).strip() if pd.notna(row.get('Compressor')) else None,
                    'capacity': str(row.get('Capacity', '')).strip() if pd.notna(row.get('Capacity')) else None,
                    'doors': str(row.get('Doors', '')).strip() if pd.notna(row.get('Doors')) else None,
                    'shelves': str(row.get('Shelves', '')).strip() if pd.notna(row.get('Shelves')) else None,
                    'features': str(row.get('Features', '')).strip() if pd.notna(row.get('Features')) else None,
                    'certifications': str(row.get('Certifications', '')).strip() if pd.notna(row.get('Certifications')) else None,
                    'price': clean_price(row.get('Price'))
                }
                
                # Insert into SQLite
                cursor.execute("""
                    INSERT INTO products (
                        sku, category, subcategory, product_type, description,
                        voltage, amperage, phase, frequency, plug_type,
                        dimensions, dimensions_metric, weight, weight_metric,
                        temperature_range, temperature_range_metric, refrigerant,
                        compressor, capacity, doors, shelves, features,
                        certifications, price
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_data['sku'], product_data['category'], product_data['subcategory'],
                    product_data['product_type'], product_data['description'],
                    product_data['voltage'], product_data['amperage'], product_data['phase'],
                    product_data['frequency'], product_data['plug_type'],
                    product_data['dimensions'], product_data['dimensions_metric'],
                    product_data['weight'], product_data['weight_metric'],
                    product_data['temperature_range'], product_data['temperature_range_metric'],
                    product_data['refrigerant'], product_data['compressor'], product_data['capacity'],
                    product_data['doors'], product_data['shelves'], product_data['features'],
                    product_data['certifications'], product_data['price']
                ))
                
                products_inserted += 1
                
                # Prepare for Supabase (collect for batch insert)
                if supabase:
                    products_for_supabase.append(product_data)
                
            except sqlite3.IntegrityError as e:
                if "UNIQUE constraint failed" in str(e):
                    print(f"Skipping duplicate SKU: {sku}")
                    products_skipped += 1
                else:
                    print(f"Error inserting product {sku}: {e}")
                    products_skipped += 1
            except Exception as e:
                print(f"Error inserting product at row {idx + 1}: {e}")
                products_skipped += 1
        
        conn.commit()
        print(f"Successfully loaded {products_inserted} products into SQLite")
        if products_skipped > 0:
            print(f"Skipped {products_skipped} rows (empty SKUs or duplicates)")
        
        # Sync to Supabase if online
        if supabase and products_for_supabase:
            try:
                print("Syncing products to Supabase...")
                # Clear existing products in Supabase
                supabase.table('products').delete().neq('sku', '').execute()
                
                # Batch insert to Supabase (in chunks of 100)
                chunk_size = 100
                for i in range(0, len(products_for_supabase), chunk_size):
                    chunk = products_for_supabase[i:i + chunk_size]
                    supabase.table('products').insert(chunk).execute()
                
                print(f"Successfully synced {len(products_for_supabase)} products to Supabase")
            except Exception as e:
                print(f"Warning: Could not sync to Supabase (will sync later): {e}")
                # Add to sync queue for later
                cursor = conn.cursor()
                import json
                for product in products_for_supabase:
                    cursor.execute("""
                        INSERT INTO sync_queue (table_name, operation, data)
                        VALUES (?, ?, ?)
                    """, ('products', 'insert', json.dumps(product)))
                conn.commit()
                print("Products queued for sync when online")
        
    except Exception as e:
        print(f"Error loading products: {e}")
        conn.rollback()
        raise

if __name__ == "__main__":
    create_local_database()
    print("Database created successfully!")