import pandas as pd
import sqlite3
from supabase import create_client

# Your Supabase credentials
SUPABASE_URL = "https://lxaritlhujdevalclhfc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx4YXJpdGxodWpkZXZhbGNsaGZjIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MzM5ODg1MiwiZXhwIjoyMDY4OTc0ODUyfQ.fPIhjfyOr7L2JhwIrvPYdCgnh2jIIDFdNEoA5jZ30-g"

# Connect to SQLite
conn = sqlite3.connect('turbo_air_db_online.sqlite')
products_df = pd.read_sql_query("SELECT * FROM products", conn)
conn.close()

print(f"Found {len(products_df)} products to upload")

# Connect to Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Upload products
for _, product in products_df.iterrows():
    data = product.to_dict()
    data.pop('id', None)  # Remove SQLite ID
    
    try:
        supabase.table('products').insert(data).execute()
        print(f"✓ Uploaded {data['sku']}")
    except Exception as e:
        print(f"✗ Error with {data['sku']}: {e}")

print("Upload complete!")