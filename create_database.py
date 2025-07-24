"""
Simple Database Creation Script for Turbo Air Equipment Viewer
This version focuses on getting the database created with prices
"""

import sqlite3
import pandas as pd
import os

def create_database():
    """Create SQLite database"""
    conn = sqlite3.connect('turbo_air_db_online.sqlite')
    cursor = conn.cursor()
    
    # Drop existing tables to start fresh
    cursor.execute("DROP TABLE IF EXISTS products")
    
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
            subcategory TEXT
        )
    """)
    
    # Create other tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            company TEXT NOT NULL,
            contact_name TEXT,
            contact_email TEXT,
            contact_number TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            client_id INTEGER,
            product_id INTEGER,
            quantity INTEGER DEFAULT 1
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            search_term TEXT NOT NULL
        )
    """)
    
    conn.commit()
    return conn

def load_products(conn):
    """Load products and prices"""
    print("Loading products...")
    
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
            
            # Simple category assignment
            product_type = str(row.get('Product Type', '')).lower()
            if 'glass' in product_type:
                category = 'GLASS DOOR MERCHANDISERS'
            elif 'display' in product_type:
                category = 'DISPLAY CASES'
            elif 'bar' in product_type:
                category = 'UNDERBAR EQUIPMENT'
            elif 'milk' in product_type:
                category = 'MILK COOLERS'
            else:
                category = 'UNCATEGORIZED'
            
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
                'General'
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

def main():
    """Main function"""
    print("Creating Turbo Air database...")
    
    # Check if files exist
    if not os.path.exists('turbo_air_products.xlsx'):
        print("ERROR: turbo_air_products.xlsx not found!")
        return
    
    if not os.path.exists('2024 List Price Norbaja Copy.xlsx'):
        print("ERROR: 2024 List Price Norbaja Copy.xlsx not found!")
        return
    
    # Create database
    conn = create_database()
    print("Database created successfully")
    
    # Load products
    load_products(conn)
    
    # Close connection
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    main()