"""
Database operations module for Turbo Air Equipment Viewer
Handles both SQLite (offline) and Supabase (online) operations
Updated with get_user_quotes method and all required functionality
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
        
        # Check and load products if needed
        try:
            if not self.check_products_exist():
                print("No products found in database.")
                excel_path = 'turbo_air_products.xlsx'
                if os.path.exists(excel_path):
                    print(f"Found {excel_path}, loading products...")
                    from .database.create_db import load_products_from_excel
                    conn = self.get_connection()
                    load_products_from_excel(conn)
                    conn.close()
                    print("Products loaded successfully!")
                    # Clear cache to force reload
                    st.cache_data.clear()
                else:
                    print(f"Excel file '{excel_path}' not found in project root")
        except Exception as e:
            print(f"Error during product initialization: {e}")
    
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
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            count = cursor.fetchone()[0]
            conn.close()
            return count > 0
        except Exception as e:
            print(f"Error checking products: {e}")
            return False
    
    @st.cache_data(ttl=300)
    def get_all_products(_self) -> pd.DataFrame:
        """Get all products with caching"""
        if _self.is_online:
            try:
                response = _self.supabase.table('products').select('*').execute()
                if response.data:
                    df = pd.DataFrame(response.data)
                    # Update local cache
                    _self._update_local_products(df)
                    return df
            except Exception as e:
                print(f"Error fetching from Supabase: {e}")
        
        # Fallback to SQLite
        conn = _self.get_connection()
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
    def get_products_by_category(_self, category: str, subcategory: Optional[str] = None) -> pd.DataFrame:
        """Get products by category with caching"""
        # Return empty DataFrame if no products exist
        if not _self.check_products_exist():
            return pd.DataFrame()
        
        if _self.is_online:
            try:
                query = _self.supabase.table('products').select('*').eq('category', category)
                if subcategory:
                    query = query.eq('subcategory', subcategory)
                response = query.execute()
                return pd.DataFrame(response.data)
            except:
                pass
        
        # Use SQLite
        conn = _self.get_connection()
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
    
    def delete_client(self, client_id: int) -> Tuple[bool, str]:
        """Delete a client and all associated data"""
        try:
            if self.is_online and self.supabase:
                # Online mode - delete from Supabase
                # First check if client has quotes
                quotes_response = self.supabase.table('quotes').select('id').eq('client_id', client_id).execute()
                
                if quotes_response.data:
                    return False, "Cannot delete client with existing quotes. Please archive or delete quotes first."
                
                # Delete cart items first (foreign key constraint)
                self.supabase.table('cart_items').delete().eq('client_id', client_id).execute()
                
                # Delete client
                response = self.supabase.table('clients').delete().eq('id', client_id).execute()
                
                if response.data:
                    return True, "Client deleted successfully"
                else:
                    return False, "Failed to delete client"
            
            else:
                # Offline mode - delete from SQLite
                conn = self.get_connection()
                cursor = conn.cursor()
                
                # Check if client has quotes
                cursor.execute("SELECT COUNT(*) FROM quotes WHERE client_id = ?", (client_id,))
                if cursor.fetchone()[0] > 0:
                    conn.close()
                    return False, "Cannot delete client with existing quotes. Please archive or delete quotes first."
                
                # Delete cart items first (foreign key constraint)
                cursor.execute("DELETE FROM cart_items WHERE client_id = ?", (client_id,))
                
                # Delete client
                cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    
                    # Add to sync queue
                    self._add_to_sync_queue(conn, 'clients', 'delete', {'id': client_id})
                    
                    conn.close()
                    return True, "Client deleted successfully"
                else:
                    conn.close()
                    return False, "Client not found"
                    
        except Exception as e:
            return False, f"Error deleting client: {str(e)}"
    
    def get_client_quotes(self, client_id: int) -> pd.DataFrame:
        """Get all quotes for a specific client"""
        try:
            if self.is_online and self.supabase:
                # Online mode
                response = self.supabase.table('quotes').select('*').eq('client_id', client_id).execute()
                return pd.DataFrame(response.data) if response.data else pd.DataFrame()
            
            else:
                # Offline mode
                conn = self.get_connection()
                df = pd.read_sql_query("""
                    SELECT * FROM quotes 
                    WHERE client_id = ?
                    ORDER BY created_at DESC
                """, conn, params=(client_id,))
                conn.close()
                return df
                
        except Exception as e:
            print(f"Error getting client quotes: {e}")
            return pd.DataFrame()
    
    def get_cart_items(self, user_id: str, client_id: Optional[int] = None) -> pd.DataFrame:
        """Get cart items with product details"""
        try:
            if self.is_online and self.supabase:
                # Online mode - get cart items with product details
                query = self.supabase.table('cart_items').select("""
                    id, quantity, user_id, client_id, product_id, created_at,
                    products (
                        id, sku, product_type, description, price, category
                    )
                """).eq('user_id', user_id)
                
                if client_id:
                    query = query.eq('client_id', client_id)
                
                response = query.execute()
                return pd.DataFrame(response.data) if response.data else pd.DataFrame()
            
            else:
                # Offline mode - join with products table
                conn = self.get_connection()
                if client_id:
                    df = pd.read_sql_query("""
                        SELECT 
                            ci.id, ci.quantity, ci.user_id, ci.client_id, ci.product_id, ci.created_at,
                            p.sku, p.product_type, p.description, p.price, p.category
                        FROM cart_items ci
                        JOIN products p ON ci.product_id = p.id
                        WHERE ci.user_id = ? AND ci.client_id = ?
                        ORDER BY ci.created_at DESC
                    """, conn, params=(user_id, client_id))
                else:
                    df = pd.read_sql_query("""
                        SELECT 
                            ci.id, ci.quantity, ci.user_id, ci.client_id, ci.product_id, ci.created_at,
                            p.sku, p.product_type, p.description, p.price, p.category
                        FROM cart_items ci
                        JOIN products p ON ci.product_id = p.id
                        WHERE ci.user_id = ?
                        ORDER BY ci.created_at DESC
                    """, conn, params=(user_id,))
                conn.close()
                return df
                
        except Exception as e:
            print(f"Error getting cart items: {e}")
            return pd.DataFrame()
    
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
    
    def update_cart_quantity(self, cart_item_id: int, new_quantity: int) -> bool:
        """Update quantity of a cart item"""
        try:
            if self.is_online and self.supabase:
                # Online mode
                response = self.supabase.table('cart_items').update({
                    'quantity': new_quantity,
                    'updated_at': datetime.now().isoformat()
                }).eq('id', cart_item_id).execute()
                
                return response.data is not None
            
            else:
                # Offline mode
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE cart_items 
                    SET quantity = ?, updated_at = CURRENT_TIMESTAMP 
                    WHERE id = ?
                """, (new_quantity, cart_item_id))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                # Add to sync queue
                if success:
                    self._add_to_sync_queue(conn, 'cart_items', 'update', {
                        'id': cart_item_id,
                        'quantity': new_quantity
                    })
                
                conn.close()
                return success
                
        except Exception as e:
            print(f"Error updating cart quantity: {e}")
            return False
    
    def remove_from_cart(self, cart_item_id: int) -> bool:
        """Remove item from cart"""
        try:
            if self.is_online and self.supabase:
                # Online mode
                response = self.supabase.table('cart_items').delete().eq('id', cart_item_id).execute()
                return response.data is not None
            
            else:
                # Offline mode
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cart_items WHERE id = ?", (cart_item_id,))
                
                success = cursor.rowcount > 0
                conn.commit()
                
                # Add to sync queue
                if success:
                    self._add_to_sync_queue(conn, 'cart_items', 'delete', {'id': cart_item_id})
                
                conn.close()
                return success
                
        except Exception as e:
            print(f"Error removing from cart: {e}")
            return False
    
    def clear_cart(self, user_id: str, client_id: int) -> bool:
        """Clear all items from cart for a specific client"""
        try:
            if self.is_online and self.supabase:
                # Online mode
                self.supabase.table('cart_items').delete().eq('user_id', user_id).eq('client_id', client_id).execute()
            
            else:
                # Offline mode
                conn = self.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM cart_items WHERE user_id = ? AND client_id = ?", (user_id, client_id))
                conn.commit()
                
                # Add to sync queue
                self._add_to_sync_queue(conn, 'cart_items', 'clear', {
                    'user_id': user_id,
                    'client_id': client_id
                })
                
                conn.close()
                
            return True
            
        except Exception as e:
            print(f"Error clearing cart: {e}")
            return False
    
    def create_quote(self, user_id: str, client_id: int, cart_items_df: pd.DataFrame) -> Tuple[bool, str, str]:
        """Create a quote from cart items"""
        try:
            # Generate quote number
            quote_number = f"TA{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Calculate totals - handle both nested and direct price access
            total_amount = 0
            for _, item in cart_items_df.iterrows():
                # Handle nested product data structure
                product_data = item.get('products', {})
                if isinstance(product_data, dict):
                    price = float(product_data.get('price', 0))
                else:
                    price = float(item.get('price', 0))
                quantity = int(item.get('quantity', 1))
                total_amount += price * quantity
            
            # Add tax (assuming 8% default, but will be overridden by UI)
            tax_rate = 0.08
            subtotal = total_amount
            tax_amount = subtotal * tax_rate
            total_with_tax = subtotal + tax_amount
            
            quote_data = {
                'quote_number': quote_number,
                'user_id': user_id,
                'client_id': client_id,
                'subtotal': subtotal,
                'tax_rate': tax_rate,
                'tax_amount': tax_amount,
                'total_amount': total_with_tax,
                'status': 'draft',
                'created_at': datetime.now().isoformat()
            }
            
            if self.is_online and self.supabase:
                # Online mode
                response = self.supabase.table('quotes').insert(quote_data).execute()
                if response.data:
                    # Create quote items
                    quote_id = response.data[0]['id']
                    for _, item in cart_items_df.iterrows():
                        product_data = item.get('products', {})
                        if isinstance(product_data, dict):
                            price = float(product_data.get('price', 0))
                            product_id = product_data.get('id', item.get('product_id'))
                        else:
                            price = float(item.get('price', 0))
                            product_id = item.get('product_id')
                        
                        quantity = int(item.get('quantity', 1))
                        
                        item_data = {
                            'quote_id': quote_id,
                            'product_id': product_id,
                            'quantity': quantity,
                            'unit_price': price,
                            'total_price': price * quantity
                        }
                        self.supabase.table('quote_items').insert(item_data).execute()
                    
                    return True, f"Quote {quote_number} created successfully!", quote_number
                else:
                    return False, "Failed to create quote", None
            
            else:
                # Offline mode
                conn = self.get_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO quotes (quote_number, user_id, client_id, subtotal, tax_rate, tax_amount, total_amount, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (quote_number, user_id, client_id, subtotal, tax_rate, tax_amount, total_with_tax, 'draft', datetime.now().isoformat()))
                
                quote_id = cursor.lastrowid
                
                # Create quote items
                for _, item in cart_items_df.iterrows():
                    product_data = item.get('products', {})
                    if isinstance(product_data, dict):
                        price = float(product_data.get('price', 0))
                        product_id = product_data.get('id', item.get('product_id'))
                    else:
                        price = float(item.get('price', 0))
                        product_id = item.get('product_id')
                    
                    quantity = int(item.get('quantity', 1))
                    
                    cursor.execute("""
                        INSERT INTO quote_items (quote_id, product_id, quantity, unit_price, total_price)
                        VALUES (?, ?, ?, ?, ?)
                    """, (quote_id, product_id, quantity, price, price * quantity))
                
                conn.commit()
                
                # Add to sync queue
                self._add_to_sync_queue(conn, 'quotes', 'insert', quote_data)
                
                conn.close()
                return True, f"Quote {quote_number} created successfully!", quote_number
                
        except Exception as e:
            return False, f"Error creating quote: {str(e)}", None
    
    def get_user_quotes(self, user_id: str, limit: int = None) -> pd.DataFrame:
        """Get all quotes for a user"""
        if self.is_online:
            try:
                query = self.supabase.table('quotes').select('*').eq('user_id', user_id).order('created_at', desc=True)
                if limit:
                    query = query.limit(limit)
                response = query.execute()
                return pd.DataFrame(response.data)
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        query = """
            SELECT * FROM quotes 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        
        df = pd.read_sql_query(query, conn, params=(user_id,))
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