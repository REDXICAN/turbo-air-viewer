import sqlite3
import hashlib
import uuid
from datetime import datetime

def fix_local_database():
    """Ensure local SQLite database has all necessary tables"""
    
    # Work with BOTH database files
    databases = ['turbo_air_local.db', 'turbo_air_db_online.sqlite']
    
    for db_file in databases:
        print(f"\nFixing database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Create products table (matching create_database.py schema)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
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
        print("✓ products table created/verified")
        
        # Create user_profiles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_profiles (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE,
                role TEXT DEFAULT 'distributor' CHECK (role IN ('admin', 'sales', 'distributor')),
                company TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ user_profiles table created/verified")
        
        # Create clients table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
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
        print("✓ clients table created/verified")
        
        # Create quotes table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quotes (
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
        print("✓ quotes table created/verified")
        
        # Create quote_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS quote_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER REFERENCES quotes(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price REAL,
                total_price REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ quote_items table created/verified")
        
        # Create cart_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cart_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                client_id INTEGER REFERENCES clients(id),
                product_id INTEGER REFERENCES products(id),
                quantity INTEGER NOT NULL DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ cart_items table created/verified")
        
        # Create search_history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                search_term TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ search_history table created/verified")
        
        # Create sync_queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT NOT NULL,
                operation TEXT NOT NULL,
                data TEXT NOT NULL,
                synced BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✓ sync_queue table created/verified")
        
        # Check if admin user exists
        cursor.execute("SELECT * FROM user_profiles WHERE email = ?", ('andres.xbgo@outlook.com',))
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            # Create admin user
            admin_id = '227d00ff-082a-4530-8793-e590385605ab'
            
            cursor.execute("""
                INSERT INTO user_profiles (id, email, role, company)
                VALUES (?, ?, ?, ?)
            """, (
                admin_id,
                'andres.xbgo@outlook.com',
                'admin',
                'Turbo Air Mexico'
            ))
            print("✓ Admin user created")
            print("  Email: andres.xbgo@outlook.com")
            print("  Note: Use Supabase auth or local auth module for password")
        else:
            print("✓ Admin user already exists")
        
        # Check products table
        try:
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"✓ Products in {db_file}: {product_count}")
            
            if product_count == 0:
                print(f"  ⚠️  No products in {db_file}")
                print("     Run: python create_database.py")
        except Exception as e:
            print(f"  ⚠️  Error checking products: {e}")
        
        conn.commit()
        conn.close()
    
    print("\n✅ Local databases fixed successfully!")
    print("\nNext steps:")
    print("1. If products are missing, run: python create_database.py")
    print("2. Run the app: streamlit run app.py")
    print("3. Login with: andres.xbgo@outlook.com")

if __name__ == "__main__":
    fix_local_database()