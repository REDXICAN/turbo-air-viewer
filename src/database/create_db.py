"""
Database Creation Script for Turbo Air Equipment Viewer
Creates local SQLite database with schema
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

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
            load_products_from_excel(conn)
        except Exception as e:
            print(f"Could not load products from Excel: {e}")
    
    conn.close()
    return True

def load_products_from_excel(conn):
    """Load products from Excel file into database"""
    try:
        # Load product data
        products_df = pd.read_excel('turbo_air_products.xlsx')
        
        # Load price data if available
        prices = {}
        if os.path.exists('2024 List Price Norbaja Copy.xlsx'):
            try:
                price_df = pd.read_excel('2024 List Price Norbaja Copy.xlsx')
                # Build price dictionary from price file
                for idx, row in price_df.iterrows():
                    try:
                        if pd.notna(row.iloc[0]) and pd.notna(row.iloc[4]):
                            model = str(row.iloc[0]).strip()
                            price_val = row.iloc[4]
                            
                            if isinstance(price_val, (int, float)):
                                prices[model] = float(price_val)
                            elif isinstance(price_val, str):
                                clean_price = price_val.replace('$', '').replace(',', '').strip()
                                if clean_price:
                                    try:
                                        prices[model] = float(clean_price)
                                    except:
                                        pass
                    except:
                        continue
            except:
                pass
        
        # Insert products
        cursor = conn.cursor()
        
        for _, row in products_df.iterrows():
            try:
                sku = str(row.get('SKU', '')).strip()
                price = prices.get(sku, row.get('Price', 0))
                
                cursor.execute("""
                    INSERT INTO products (
                        sku, product_type, description, capacity, doors, amperage,
                        dimensions, dimensions_metric, weight, weight_metric,
                        temperature_range, temperature_range_metric, voltage, phase,
                        frequency, plug_type, refrigerant, compressor, shelves,
                        features, certifications, price, category, subcategory
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sku,
                    row.get('Product Type', ''),
                    row.get('Description', ''),
                    row.get('Capacity', ''),
                    row.get('Doors', ''),
                    row.get('Amperage', ''),
                    row.get('Dimensions', ''),
                    row.get('Dimensions (Metric)', ''),
                    row.get('Weight', ''),
                    row.get('Weight (Metric)', ''),
                    row.get('Temperature Range', ''),
                    row.get('Temperature Range (Metric)', ''),
                    row.get('Voltage', ''),
                    row.get('Phase', ''),
                    row.get('Frequency', ''),
                    row.get('Plug Type', ''),
                    row.get('Refrigerant', ''),
                    row.get('Compressor', ''),
                    row.get('Shelves', ''),
                    row.get('Features', ''),
                    row.get('Certifications', ''),
                    price,
                    row.get('Category', 'UNCATEGORIZED'),
                    row.get('Subcategory', 'General')
                ))
            except Exception as e:
                print(f"Error inserting product {sku}: {e}")
        
        conn.commit()
        print(f"Successfully loaded {len(products_df)} products")
        
    except Exception as e:
        print(f"Error loading products: {e}")
        conn.rollback()

# Supabase SQL Schema for reference
SUPABASE_SCHEMA = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
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
    price DECIMAL(10, 2),
    category TEXT,
    subcategory TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Clients table
CREATE TABLE IF NOT EXISTS clients (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    company TEXT NOT NULL,
    contact_name TEXT,
    contact_email TEXT,
    contact_number TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quotes table
CREATE TABLE IF NOT EXISTS quotes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    quote_number TEXT UNIQUE NOT NULL,
    total_amount DECIMAL(10, 2),
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Quote items table
CREATE TABLE IF NOT EXISTS quote_items (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    quote_id UUID REFERENCES quotes(id) ON DELETE CASCADE,
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Cart items table
CREATE TABLE IF NOT EXISTS cart_items (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    client_id UUID REFERENCES clients(id),
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID NOT NULL,
    search_term TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID PRIMARY KEY,
    email TEXT UNIQUE,
    role TEXT DEFAULT 'distributor' CHECK (role IN ('admin', 'sales', 'distributor')),
    company TEXT,
    phone TEXT,
    password_hash TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Row Level Security Policies
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
ALTER TABLE clients ENABLE ROW LEVEL SECURITY;
ALTER TABLE quotes ENABLE ROW LEVEL SECURITY;
ALTER TABLE quote_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE cart_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- Products policies (everyone can read)
CREATE POLICY "Products are viewable by everyone" ON products
    FOR SELECT USING (true);

-- Clients policies (users can only see their own)
CREATE POLICY "Users can view own clients" ON clients
    FOR SELECT USING (user_id = current_user_id());

CREATE POLICY "Users can create own clients" ON clients
    FOR INSERT WITH CHECK (user_id = current_user_id());

CREATE POLICY "Users can update own clients" ON clients
    FOR UPDATE USING (user_id = current_user_id());

-- Similar policies for other tables...

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id);
"""

if __name__ == "__main__":
    create_local_database()
    print("Database created successfully!")
    print("\nTo set up Supabase:")
    print("1. Copy the SUPABASE_SCHEMA above")
    print("2. Go to your Supabase SQL Editor")
    print("3. Run the schema to create tables")
    print("4. Your cloud database will be ready!")