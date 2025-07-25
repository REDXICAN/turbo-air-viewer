"""
Database Creation Script for Turbo Air Equipment Viewer
Creates both SQLite (local) and Supabase (cloud) schemas
"""

import sqlite3
import pandas as pd
import os
from datetime import datetime

# Supabase SQL Schema (run this in Supabase SQL Editor)
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
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
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
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    client_id UUID REFERENCES clients(id),
    product_id UUID REFERENCES products(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Search history table
CREATE TABLE IF NOT EXISTS search_history (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    search_term TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles table (extends Supabase auth.users)
CREATE TABLE IF NOT EXISTS user_profiles (
    id UUID REFERENCES auth.users(id) ON DELETE CASCADE PRIMARY KEY,
    role TEXT DEFAULT 'distributor' CHECK (role IN ('admin', 'sales', 'distributor')),
    company TEXT,
    phone TEXT,
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

-- Products policies (everyone can read, only admins can write)
CREATE POLICY "Products are viewable by everyone" ON products
    FOR SELECT USING (true);

CREATE POLICY "Only admins can insert products" ON products
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.role = 'admin'
        )
    );

CREATE POLICY "Only admins can update products" ON products
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM user_profiles
            WHERE user_profiles.id = auth.uid()
            AND user_profiles.role = 'admin'
        )
    );

-- Clients policies (users can only see/edit their own)
CREATE POLICY "Users can view own clients" ON clients
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own clients" ON clients
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own clients" ON clients
    FOR UPDATE USING (auth.uid() = user_id);

CREATE POLICY "Users can delete own clients" ON clients
    FOR DELETE USING (auth.uid() = user_id);

-- Quotes policies
CREATE POLICY "Users can view own quotes" ON quotes
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own quotes" ON quotes
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Quote items policies
CREATE POLICY "Users can view quote items" ON quote_items
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM quotes
            WHERE quotes.id = quote_items.quote_id
            AND quotes.user_id = auth.uid()
        )
    );

CREATE POLICY "Users can create quote items" ON quote_items
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM quotes
            WHERE quotes.id = quote_items.quote_id
            AND quotes.user_id = auth.uid()
        )
    );

-- Cart items policies
CREATE POLICY "Users can view own cart items" ON cart_items
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can manage own cart items" ON cart_items
    FOR ALL USING (auth.uid() = user_id);

-- Search history policies
CREATE POLICY "Users can view own search history" ON search_history
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create own search history" ON search_history
    FOR INSERT WITH CHECK (auth.uid() = user_id);

-- User profiles policies
CREATE POLICY "Users can view all profiles" ON user_profiles
    FOR SELECT USING (true);

CREATE POLICY "Users can update own profile" ON user_profiles
    FOR UPDATE USING (auth.uid() = id);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_clients_user_id ON clients(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_user_id ON quotes(user_id);
CREATE INDEX IF NOT EXISTS idx_quotes_client_id ON quotes(client_id);
CREATE INDEX IF NOT EXISTS idx_cart_items_user_id ON cart_items(user_id);
CREATE INDEX IF NOT EXISTS idx_search_history_user_id ON search_history(user_id);
"""

# Category mappings
CATEGORY_MAPPINGS = {
    "GLASS DOOR MERCHANDISERS": [
        "Super Deluxe Series Glass Door Merchandisers",
        "Swing Door Refrigerators / Freezers",
        "Super Deluxe Jumbo Series Glass Door Merchandisers",
        "Swing Door Refrigerators / Freezers / Ice Merchandisers",
        "Standard Series Glass Door Merchandisers",
        "Swing Doors Refrigerators / Sliding Door Refrigerators / Swing Door Freezers",
        "Ice Merchandisers",
        "E-line - Swing Doors Refrigerators",
        "Top Open Island Freezers",
        "Ice Cream Dipping Cabinets"
    ],
    "DISPLAY CASES": [
        "Open Display Merchandisers",
        "Horizontal Cases - Glass Panel / Solid Panel",
        "Combination Cases - Curved Front Glass / European Straight Front Glass",
        "Horizontal Cases - European Straight",
        "Drop-In Type Horizontal Cases - European Straight",
        "Sandwich & Cheese Cases",
        "Vertical Cases - Glass Panel / Solid Panel / Extra Deep",
        "Vertical Air Curtains",
        "Island Display Cases",
        "Bakery & Deli Display Cases",
        "Deli Cases - Direct Cooling Type",
        "Bakery Cases / Freezer Display Cases",
        "Sushi Cases"
    ],
    "UNDERBAR EQUIPMENT": [
        "Bottle Coolers",
        "Glass / Mug Frosters",
        "Beer Dispensers / Club Top Beer Dispensers",
        "Back Bars / Narrow Back Bars"
    ],
    "MILK COOLERS": [
        "Milk Coolers"
    ]
}

def create_sqlite_database():
    """Create local SQLite database with schema"""
    conn = sqlite3.connect('turbo_air_db_online.sqlite')
    cursor = conn.cursor()
    
    # Drop existing tables to start fresh
    cursor.execute("DROP TABLE IF EXISTS products")
    cursor.execute("DROP TABLE IF EXISTS clients")
    cursor.execute("DROP TABLE IF EXISTS quotes")
    cursor.execute("DROP TABLE IF EXISTS quote_items")
    cursor.execute("DROP TABLE IF EXISTS cart_items")
    cursor.execute("DROP TABLE IF EXISTS search_history")
    cursor.execute("DROP TABLE IF EXISTS user_profiles")
    cursor.execute("DROP TABLE IF EXISTS sync_queue")
    
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # Create sync_queue table for offline changes
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
    
    conn.commit()
    return conn

def categorize_product(product_type):
    """Determine category and subcategory based on product type"""
    if not product_type:
        return "UNCATEGORIZED", "General"
    
    product_type_lower = product_type.lower()
    
    # Check each category
    for main_cat, subcategories in CATEGORY_MAPPINGS.items():
        for sub_cat in subcategories:
            # Simple keyword matching
            if any(keyword in product_type_lower for keyword in sub_cat.lower().split()):
                return main_cat, sub_cat
    
    # Default categorization based on keywords
    if 'glass' in product_type_lower and 'door' in product_type_lower:
        return "GLASS DOOR MERCHANDISERS", "General Glass Door"
    elif 'display' in product_type_lower or 'case' in product_type_lower:
        return "DISPLAY CASES", "General Display"
    elif 'bar' in product_type_lower or 'beer' in product_type_lower:
        return "UNDERBAR EQUIPMENT", "General Underbar"
    elif 'milk' in product_type_lower:
        return "MILK COOLERS", "Milk Coolers"
    
    return "UNCATEGORIZED", "General"

def load_products_to_database(conn):
    """Load products from Excel files into database"""
    try:
        # Load product data
        products_df = pd.read_excel('turbo_air_products.xlsx')
        print(f"Found {len(products_df)} products")
        
        # Load price data
        print("Loading prices...")
        price_df = pd.read_excel('2024 List Price Norbaja Copy.xlsx')
        
        # Build price dictionary
        price_dict = {}
        
        # Look through all rows to find prices
        for idx, row in price_df.iterrows():
            try:
                # Check if first column has a model number and fifth column has a price
                if pd.notna(row.iloc[0]) and pd.notna(row.iloc[4]):
                    model = str(row.iloc[0]).strip()
                    price_val = row.iloc[4]
                    
                    # Convert price to float
                    if isinstance(price_val, (int, float)):
                        price_dict[model] = float(price_val)
                    elif isinstance(price_val, str):
                        # Remove $ and , from string
                        clean_price = price_val.replace('$', '').replace(',', '').strip()
                        if clean_price:
                            try:
                                price_dict[model] = float(clean_price)
                            except:
                                pass
            except:
                continue
        
        print(f"Found {len(price_dict)} prices")
        
        # Insert products into database
        cursor = conn.cursor()
        inserted = 0
        
        for _, row in products_df.iterrows():
            try:
                sku = str(row.get('SKU', '')).strip()
                
                # Find price
                price = price_dict.get(sku, 0.0)
                
                # Categorize product
                category, subcategory = categorize_product(row.get('Product Type', ''))
                
                # Insert product
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
                    category,
                    subcategory
                ))
                inserted += 1
            except Exception as e:
                print(f"Error inserting {sku}: {e}")
        
        conn.commit()
        print(f"Successfully inserted {inserted} products")
        
        # Show sample of products with prices
        cursor.execute("SELECT sku, price FROM products WHERE price > 0 LIMIT 5")
        results = cursor.fetchall()
        if results:
            print("\nSample products with prices:")
            for sku, price in results:
                print(f"  {sku}: ${price:,.2f}")
        
    except Exception as e:
        print(f"Error loading products: {e}")
        conn.rollback()

def main():
    """Main function to create and populate database"""
    print("Creating Turbo Air database...")
    
    # Create SQLite database
    conn = create_sqlite_database()
    print("✓ SQLite database created")
    
    # Load products
    if os.path.exists('turbo_air_products.xlsx'):
        load_products_to_database(conn)
    else:
        print("⚠ Product Excel file not found. Please ensure turbo_air_products.xlsx is in the directory")
    
    # Print Supabase instructions
    print("\n" + "="*50)
    print("SUPABASE SETUP INSTRUCTIONS")
    print("="*50)
    print("1. Copy the SQL schema above (SUPABASE_SCHEMA)")
    print("2. Go to your Supabase project SQL Editor")
    print("3. Paste and run the entire schema")
    print("4. Your cloud database will be ready!")
    print("\n✓ Local database is ready for offline use")
    
    conn.close()

if __name__ == "__main__":
    main()