"""
Database operations module for Turbo Air Equipment Viewer
Handles both SQLite (offline) and Supabase (online) operations
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json
import streamlit as st
from typing import List, Dict, Optional, Tuple
import uuid
import os

class DatabaseManager:
    def __init__(self, supabase_client=None, offline_db_path='turbo_air_db_online.sqlite'):
        """Initialize database manager"""
        self.supabase = supabase_client
        self.is_online = supabase_client is not None
        self.sqlite_path = offline_db_path
        self._init_cache()
    
    def _init_cache(self):
        """Initialize in-memory cache"""
        if 'db_cache' not in st.session_state:
            st.session_state.db_cache = {
                'products': None,
                'categories': None,
                'last_update': {}
            }
    
    def get_connection(self):
        """Get SQLite connection"""
        return sqlite3.connect(self.sqlite_path)
    
    def check_products_exist(self) -> bool:
        """Check if any products exist in the database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    
    @st.cache_data(ttl=300)
    def get_all_products(self) -> pd.DataFrame:
        """Get all products with caching"""
        if self.is_online:
            try:
                response = self.supabase.table('products').select('*').execute()
                if response.data:
                    df = pd.DataFrame(response.data)
                    # Update local cache
                    self._update_local_products(df)
                    return df
            except Exception as e:
                print(f"Error fetching from Supabase: {e}")
        
        # Fallback to SQLite
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()
        
        # If no products found, return empty DataFrame with proper columns
        if df.empty:
            df = pd.DataFrame(columns=[
                'id', 'sku', 'category', 'subcategory', 'product_type', 'description',
                'voltage', 'amperage', 'phase', 'frequency', 'plug_type',
                'dimensions', 'dimensions_metric', 'weight', 'weight_metric',
                'temperature_range', 'temperature_range_metric', 'refrigerant',
                'compressor', 'capacity', 'doors', 'shelves', 'features',
                'certifications', 'price', 'created_at', 'updated_at'
            ])
        
        return df
    
    def search_products(self, search_term: str) -> pd.DataFrame:
        """Search products by SKU, description, or type"""
        # Return empty DataFrame if no products exist
        if not self.check_products_exist():
            return pd.DataFrame()
        
        search_pattern = f"%{search_term}%"
        
        if self.is_online:
            try:
                response = self.supabase.table('products').select('*').or_(
                    f"sku.ilike.{search_pattern},"
                    f"description.ilike.{search_pattern},"
                    f"product_type.ilike.{search_pattern}"
                ).execute()
                return pd.DataFrame(response.data)
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        query = """
            SELECT * FROM products 
            WHERE sku LIKE ? OR description LIKE ? OR product_type LIKE ?
        """
        df = pd.read_sql_query(query, conn, params=(search_pattern, search_pattern, search_pattern))
        conn.close()
        return df
    
    @st.cache_data(ttl=300)
    def get_products_by_category(self, category: str, subcategory: Optional[str] = None) -> pd.DataFrame:
        """Get products by category with caching"""
        # Return empty DataFrame if no products exist
        if not self.check_products_exist():
            return pd.DataFrame()
        
        if self.is_online:
            try:
                query = self.supabase.table('products').select('*').eq('category', category)
                if subcategory:
                    query = query.eq('subcategory', subcategory)
                response = query.execute()
                return pd.DataFrame(response.data)
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        if subcategory:
            query = "SELECT * FROM products WHERE category = ? AND subcategory = ?"
            df = pd.read_sql_query(query, conn, params=(category, subcategory))
        else:
            query = "SELECT * FROM products WHERE category = ?"
            df = pd.read_sql_query(query, conn, params=(category,))
        conn.close()
        return df
    
    def get_categories_with_counts(self) -> List[Dict[str, any]]:
        """Get all categories with product counts"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get unique categories with counts
        cursor.execute("""
            SELECT category, COUNT(*) as count 
            FROM products 
            WHERE category IS NOT NULL 
            GROUP BY category 
            ORDER BY category
        """)
        
        categories = []
        for row in cursor.fetchall():
            categories.append({
                'name': row[0],
                'count': row[1]
            })
        
        conn.close()
        return categories
    
    def get_product_by_sku(self, sku: str) -> Optional[Dict]:
        """Get single product by SKU"""
        if self.is_online:
            try:
                response = self.supabase.table('products').select('*').eq('sku', sku).single().execute()
                return response.data
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE sku = ?", (sku,))
        columns = [description[0] for description in cursor.description]
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(zip(columns, row))
        return None
    
    def get_user_clients(self, user_id: str) -> pd.DataFrame:
        """Get all clients for a user"""
        if self.is_online:
            try:
                response = self.supabase.table('clients').select('*').eq('user_id', user_id).execute()
                return pd.DataFrame(response.data)
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM clients WHERE user_id = ?", conn, params=(user_id,))
        conn.close()
        return df
    
    def create_client(self, user_id: str, company: str, contact_name: str = '', 
                     contact_email: str = '', contact_number: str = '') -> Tuple[bool, str]:
        """Create new client"""
        client_data = {
            'user_id': user_id,
            'company': company,
            'contact_name': contact_name,
            'contact_email': contact_email,
            'contact_number': contact_number
        }
        
        if self.is_online:
            try:
                response = self.supabase.table('clients').insert(client_data).execute()
                return True, "Client created successfully"
            except Exception as e:
                if "duplicate" in str(e).lower():
                    return False, "Client already exists"
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO clients (user_id, company, contact_name, contact_email, contact_number)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, company, contact_name, contact_email, contact_number))
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'clients', 'insert', client_data)
            conn.close()
            return True, "Client created successfully"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def get_cart_items(self, user_id: str, client_id: Optional[int] = None) -> pd.DataFrame:
        """Get cart items for user and optional client"""
        if self.is_online:
            try:
                query = self.supabase.table('cart_items').select(
                    '*, products(*)'
                ).eq('user_id', user_id)
                
                if client_id:
                    query = query.eq('client_id', client_id)
                
                response = query.execute()
                return pd.DataFrame(response.data)
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        if client_id:
            query = """
                SELECT c.*, p.* 
                FROM cart_items c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ? AND c.client_id = ?
            """
            df = pd.read_sql_query(query, conn, params=(user_id, client_id))
        else:
            query = """
                SELECT c.*, p.* 
                FROM cart_items c
                JOIN products p ON c.product_id = p.id
                WHERE c.user_id = ?
            """
            df = pd.read_sql_query(query, conn, params=(user_id,))
        conn.close()
        return df
    
    def add_to_cart(self, user_id: str, product_id: int, client_id: Optional[int] = None, 
                   quantity: int = 1) -> Tuple[bool, str]:
        """Add item to cart"""
        if self.is_online:
            try:
                # Check if item exists
                query = self.supabase.table('cart_items').select('*').eq('user_id', user_id).eq('product_id', product_id)
                if client_id:
                    query = query.eq('client_id', client_id)
                existing = query.execute()
                
                if existing.data:
                    # Update quantity
                    new_quantity = existing.data[0]['quantity'] + quantity
                    self.supabase.table('cart_items').update(
                        {'quantity': new_quantity}
                    ).eq('id', existing.data[0]['id']).execute()
                else:
                    # Insert new
                    cart_data = {
                        'user_id': user_id,
                        'product_id': product_id,
                        'client_id': client_id,
                        'quantity': quantity
                    }
                    self.supabase.table('cart_items').insert(cart_data).execute()
                
                return True, "Added to cart"
            except Exception as e:
                print(f"Online cart error: {e}")
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Check if exists
            if client_id:
                cursor.execute("""
                    SELECT id, quantity FROM cart_items 
                    WHERE user_id = ? AND product_id = ? AND client_id = ?
                """, (user_id, product_id, client_id))
            else:
                cursor.execute("""
                    SELECT id, quantity FROM cart_items 
                    WHERE user_id = ? AND product_id = ? AND client_id IS NULL
                """, (user_id, product_id))
            
            existing = cursor.fetchone()
            
            if existing:
                # Update quantity
                new_quantity = existing[1] + quantity
                cursor.execute("""
                    UPDATE cart_items SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (new_quantity, existing[0]))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO cart_items (user_id, product_id, client_id, quantity)
                    VALUES (?, ?, ?, ?)
                """, (user_id, product_id, client_id, quantity))
            
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'cart_items', 'upsert', {
                'user_id': user_id,
                'product_id': product_id,
                'client_id': client_id,
                'quantity': quantity
            })
            
            conn.close()
            return True, "Added to cart"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def update_cart_quantity(self, cart_item_id: int, quantity: int) -> Tuple[bool, str]:
        """Update cart item quantity"""
        if quantity <= 0:
            return self.remove_from_cart(cart_item_id)
        
        if self.is_online:
            try:
                self.supabase.table('cart_items').update(
                    {'quantity': quantity}
                ).eq('id', cart_item_id).execute()
                return True, "Quantity updated"
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE cart_items 
                SET quantity = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (quantity, cart_item_id))
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'cart_items', 'update', {
                'id': cart_item_id,
                'quantity': quantity
            })
            
            conn.close()
            return True, "Quantity updated"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def remove_from_cart(self, cart_item_id: int) -> Tuple[bool, str]:
        """Remove item from cart"""
        if self.is_online:
            try:
                self.supabase.table('cart_items').delete().eq('id', cart_item_id).execute()
                return True, "Removed from cart"
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM cart_items WHERE id = ?", (cart_item_id,))
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'cart_items', 'delete', {'id': cart_item_id})
            
            conn.close()
            return True, "Removed from cart"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def clear_cart(self, user_id: str, client_id: Optional[int] = None) -> Tuple[bool, str]:
        """Clear all cart items for user/client"""
        if self.is_online:
            try:
                query = self.supabase.table('cart_items').delete().eq('user_id', user_id)
                if client_id:
                    query = query.eq('client_id', client_id)
                query.execute()
                return True, "Cart cleared"
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            if client_id:
                cursor.execute("DELETE FROM cart_items WHERE user_id = ? AND client_id = ?", 
                             (user_id, client_id))
            else:
                cursor.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
            
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'cart_items', 'clear', {
                'user_id': user_id,
                'client_id': client_id
            })
            
            conn.close()
            return True, "Cart cleared"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def create_quote(self, user_id: str, client_id: int, cart_items: pd.DataFrame) -> Tuple[bool, str, str]:
        """Create quote from cart items"""
        # Generate quote number
        quote_number = f"Q-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # Calculate total
        total_amount = (cart_items['quantity'] * cart_items['price']).sum()
        
        if self.is_online:
            try:
                # Create quote
                quote_data = {
                    'user_id': user_id,
                    'client_id': client_id,
                    'quote_number': quote_number,
                    'total_amount': float(total_amount),
                    'status': 'draft'
                }
                quote_response = self.supabase.table('quotes').insert(quote_data).execute()
                quote_id = quote_response.data[0]['id']
                
                # Create quote items
                for _, item in cart_items.iterrows():
                    item_data = {
                        'quote_id': quote_id,
                        'product_id': item['product_id'],
                        'quantity': item['quantity'],
                        'unit_price': float(item['price']),
                        'total_price': float(item['quantity'] * item['price'])
                    }
                    self.supabase.table('quote_items').insert(item_data).execute()
                
                return True, "Quote created successfully", quote_number
            except Exception as e:
                print(f"Online quote error: {e}")
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Create quote
            cursor.execute("""
                INSERT INTO quotes (user_id, client_id, quote_number, total_amount, status)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, client_id, quote_number, float(total_amount), 'draft'))
            
            quote_id = cursor.lastrowid
            
            # Create quote items
            for _, item in cart_items.iterrows():
                cursor.execute("""
                    INSERT INTO quote_items (quote_id, product_id, quantity, unit_price, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (quote_id, item['product_id'], item['quantity'], 
                      float(item['price']), float(item['quantity'] * item['price'])))
            
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'quotes', 'insert', {
                'user_id': user_id,
                'client_id': client_id,
                'quote_number': quote_number,
                'total_amount': float(total_amount)
            })
            
            conn.close()
            return True, "Quote created successfully", quote_number
        except Exception as e:
            conn.close()
            return False, str(e), ""
    
    def get_client_quotes(self, client_id: int) -> pd.DataFrame:
        """Get all quotes for a client"""
        if self.is_online:
            try:
                response = self.supabase.table('quotes').select('*').eq('client_id', client_id).execute()
                return pd.DataFrame(response.data)
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM quotes WHERE client_id = ? ORDER BY created_at DESC", 
                              conn, params=(client_id,))
        conn.close()
        return df
    
    def add_search_history(self, user_id: str, search_term: str):
        """Add search term to history"""
        if self.is_online:
            try:
                self.supabase.table('search_history').insert({
                    'user_id': user_id,
                    'search_term': search_term
                }).execute()
            except:
                pass
        
        # Always add to SQLite for offline access
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO search_history (user_id, search_term)
            VALUES (?, ?)
        """, (user_id, search_term))
        conn.commit()
        
        # Add to sync queue if offline
        if not self.is_online:
            self._add_to_sync_queue(conn, 'search_history', 'insert', {
                'user_id': user_id,
                'search_term': search_term
            })
        
        conn.close()
    
    def get_search_history(self, user_id: str, limit: int = 10) -> List[str]:
        """Get recent search history"""
        if self.is_online:
            try:
                response = self.supabase.table('search_history').select(
                    'search_term'
                ).eq('user_id', user_id).order(
                    'created_at', desc=True
                ).limit(limit).execute()
                return [item['search_term'] for item in response.data]
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT search_term 
            FROM search_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (user_id, limit))
        
        results = [row[0] for row in cursor.fetchall()]
        conn.close()
        return results
    
    def clear_search_history(self, user_id: str) -> Tuple[bool, str]:
        """Clear user's search history"""
        if self.is_online:
            try:
                self.supabase.table('search_history').delete().eq('user_id', user_id).execute()
            except:
                pass
        
        # Clear from SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM search_history WHERE user_id = ?", (user_id,))
            conn.commit()
            
            # Add to sync queue if offline
            if not self.is_online:
                self._add_to_sync_queue(conn, 'search_history', 'clear', {
                    'user_id': user_id
                })
            
            conn.close()
            return True, "Search history cleared"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def get_dashboard_stats(self, user_id: str) -> Dict:
        """Get dashboard statistics for user"""
        stats = {
            'total_clients': 0,
            'total_quotes': 0,
            'recent_quotes': 0,
            'cart_items': 0
        }
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total clients
        cursor.execute("SELECT COUNT(*) FROM clients WHERE user_id = ?", (user_id,))
        stats['total_clients'] = cursor.fetchone()[0]
        
        # Total quotes
        cursor.execute("SELECT COUNT(*) FROM quotes WHERE user_id = ?", (user_id,))
        stats['total_quotes'] = cursor.fetchone()[0]
        
        # Recent quotes (last 30 days)
        cursor.execute("""
            SELECT COUNT(*) FROM quotes 
            WHERE user_id = ? 
            AND datetime(created_at) > datetime('now', '-30 days')
        """, (user_id,))
        stats['recent_quotes'] = cursor.fetchone()[0]
        
        # Cart items
        cursor.execute("SELECT COUNT(*) FROM cart_items WHERE user_id = ?", (user_id,))
        stats['cart_items'] = cursor.fetchone()[0]
        
        conn.close()
        return stats
    
    def _update_local_products(self, products_df: pd.DataFrame):
        """Update local product cache"""
        try:
            conn = self.get_connection()
            products_df.to_sql('products', conn, if_exists='replace', index=False)
            conn.close()
        except:
            pass
    
    def _add_to_sync_queue(self, conn, table_name: str, operation: str, data: Dict):
        """Add operation to sync queue"""
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sync_queue (table_name, operation, data)
            VALUES (?, ?, ?)
        """, (table_name, operation, json.dumps(data)))
        conn.commit()
    
    def get_pending_sync_items(self) -> pd.DataFrame:
        """Get items pending synchronization"""
        conn = self.get_connection()
        df = pd.read_sql_query("""
            SELECT * FROM sync_queue 
            WHERE synced = 0 
            ORDER BY created_at
        """, conn)
        conn.close()
        return df
    
    def mark_synced(self, sync_ids: List[int]):
        """Mark items as synced"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE sync_queue 
            SET synced = 1 
            WHERE id IN ({','.join(['?' for _ in sync_ids])})
        """, sync_ids)
        conn.commit()
        conn.close()
    
    def sync_products_to_supabase(self) -> Tuple[bool, str]:
        """Sync all products from SQLite to Supabase"""
        if not self.is_online:
            return False, "No internet connection"
        
        try:
            # Get all products from SQLite
            conn = self.get_connection()
            products_df = pd.read_sql_query("SELECT * FROM products", conn)
            conn.close()
            
            if products_df.empty:
                return True, "No products to sync"
            
            # Convert DataFrame to list of dicts
            products = products_df.to_dict('records')
            
            # Remove SQLite-specific fields
            for product in products:
                if 'id' in product:
                    del product['id']
                if 'created_at' in product:
                    del product['created_at']
                if 'updated_at' in product:
                    del product['updated_at']
            
            # Clear existing products in Supabase
            self.supabase.table('products').delete().neq('sku', '').execute()
            
            # Batch insert to Supabase (in chunks of 100)
            chunk_size = 100
            total_synced = 0
            
            for i in range(0, len(products), chunk_size):
                chunk = products[i:i + chunk_size]
                self.supabase.table('products').insert(chunk).execute()
                total_synced += len(chunk)
            
            return True, f"Successfully synced {total_synced} products"
            
        except Exception as e:
            return False, f"Sync error: {str(e)}"
    
    def load_products_from_excel(self, file_path: str = 'turbo_air_products.xlsx') -> Tuple[bool, str]:
        """Load products from Excel file"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                return False, f"Excel file '{file_path}' not found. Please add it to the project directory."
            
            # Import the loading function
            from .database.create_db import load_products_from_excel
            
            conn = self.get_connection()
            load_products_from_excel(conn)
            conn.close()
            
            # Clear the products cache
            if 'get_all_products' in st.session_state:
                del st.session_state['get_all_products']
            
            # If online, sync immediately
            if self.is_online:
                sync_success, sync_message = self.sync_products_to_supabase()
                if sync_success:
                    return True, "Products loaded and synced successfully"
                else:
                    return True, f"Products loaded locally. Sync failed: {sync_message}"
            else:
                return True, "Products loaded locally (will sync when online)"
                
        except Exception as e:
            return False, f"Error loading products: {str(e)}"
    
    def get_null_display_value(self) -> str:
        """Get display value for NULL/empty fields"""
        return "-"