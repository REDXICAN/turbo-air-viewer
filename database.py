"""
Database operations module for Turbo Air Equipment Viewer
Handles all database queries and operations for both SQLite and Supabase
"""

import sqlite3
import pandas as pd
from datetime import datetime
import json
import streamlit as st
from typing import List, Dict, Optional, Tuple
import uuid

class DatabaseManager:
    def __init__(self, supabase_client=None):
        """Initialize database manager"""
        self.supabase = supabase_client
        self.is_online = supabase_client is not None
        self.sqlite_path = 'turbo_air_db_online.sqlite'
    
    def get_connection(self):
        """Get SQLite connection"""
        return sqlite3.connect(self.sqlite_path)
    
    # Product Operations
    def get_all_products(self) -> pd.DataFrame:
        """Get all products from database"""
        if self.is_online:
            try:
                response = self.supabase.table('products').select('*').execute()
                return pd.DataFrame(response.data)
            except:
                # Fallback to SQLite
                pass
        
        # Use SQLite
        conn = self.get_connection()
        df = pd.read_sql_query("SELECT * FROM products", conn)
        conn.close()
        return df
    
    def search_products(self, search_term: str) -> pd.DataFrame:
        """Search products by SKU, description, or type"""
        search_term = f"%{search_term}%"
        
        if self.is_online:
            try:
                response = self.supabase.table('products').select('*').or_(
                    f"sku.ilike.{search_term},"
                    f"description.ilike.{search_term},"
                    f"product_type.ilike.{search_term}"
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
        df = pd.read_sql_query(query, conn, params=(search_term, search_term, search_term))
        conn.close()
        return df
    
    def get_products_by_category(self, category: str, subcategory: str = None) -> pd.DataFrame:
        """Get products by category and optional subcategory"""
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
    
    # Client Operations
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
                # Try offline mode
                pass
        
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
    
    def update_client(self, client_id: int, **kwargs) -> Tuple[bool, str]:
        """Update client information"""
        if self.is_online:
            try:
                response = self.supabase.table('clients').update(kwargs).eq('id', client_id).execute()
                return True, "Client updated successfully"
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Build update query
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [client_id]
            
            cursor.execute(f"""
                UPDATE clients 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'clients', 'update', {'id': client_id, **kwargs})
            conn.close()
            return True, "Client updated successfully"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    def delete_client(self, client_id: int) -> Tuple[bool, str]:
        """Delete client and associated data"""
        if self.is_online:
            try:
                response = self.supabase.table('clients').delete().eq('id', client_id).execute()
                return True, "Client deleted successfully"
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'clients', 'delete', {'id': client_id})
            conn.close()
            return True, "Client deleted successfully"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    # Cart Operations
    def get_cart_items(self, user_id: str, client_id: int = None) -> pd.DataFrame:
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
    
    def add_to_cart(self, user_id: str, product_id: int, client_id: int = None, 
                   quantity: int = 1) -> Tuple[bool, str]:
        """Add item to cart"""
        # Check if item already exists
        if self.is_online:
            try:
                # Check existing
                query = self.supabase.table('cart_items').select('*').eq('user_id', user_id).eq('product_id', product_id)
                if client_id:
                    query = query.eq('client_id', client_id)
                existing = query.execute()
                
                if existing.data:
                    # Update quantity
                    new_quantity = existing.data[0]['quantity'] + quantity
                    response = self.supabase.table('cart_items').update(
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
                    response = self.supabase.table('cart_items').insert(cart_data).execute()
                
                return True, "Added to cart"
            except:
                pass
        
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
                response = self.supabase.table('cart_items').update(
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
                response = self.supabase.table('cart_items').delete().eq('id', cart_item_id).execute()
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
    
    def clear_cart(self, user_id: str, client_id: int = None) -> Tuple[bool, str]:
        """Clear all cart items for user/client"""
        if self.is_online:
            try:
                query = self.supabase.table('cart_items').delete().eq('user_id', user_id)
                if client_id:
                    query = query.eq('client_id', client_id)
                response = query.execute()
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
    
    # Quote Operations
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
                # Try offline
                pass
        
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
    
    def get_quote_details(self, quote_id: int) -> Tuple[Dict, pd.DataFrame]:
        """Get quote and its items"""
        if self.is_online:
            try:
                # Get quote
                quote_response = self.supabase.table('quotes').select(
                    '*, clients(*)'
                ).eq('id', quote_id).single().execute()
                
                # Get quote items
                items_response = self.supabase.table('quote_items').select(
                    '*, products(*)'
                ).eq('quote_id', quote_id).execute()
                
                return quote_response.data, pd.DataFrame(items_response.data)
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get quote
        cursor.execute("""
            SELECT q.*, c.company, c.contact_name, c.contact_email, c.contact_number
            FROM quotes q
            JOIN clients c ON q.client_id = c.id
            WHERE q.id = ?
        """, (quote_id,))
        
        columns = [description[0] for description in cursor.description]
        quote_row = cursor.fetchone()
        
        if quote_row:
            quote = dict(zip(columns, quote_row))
            
            # Get quote items
            items_df = pd.read_sql_query("""
                SELECT qi.*, p.*
                FROM quote_items qi
                JOIN products p ON qi.product_id = p.id
                WHERE qi.quote_id = ?
            """, conn, params=(quote_id,))
            
            conn.close()
            return quote, items_df
        
        conn.close()
        return None, pd.DataFrame()
    
    # Search History Operations
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
    
    # Admin Operations
    def update_product(self, product_id: int, **kwargs) -> Tuple[bool, str]:
        """Update product information (admin only)"""
        if self.is_online:
            try:
                response = self.supabase.table('products').update(kwargs).eq('id', product_id).execute()
                # Also update SQLite for offline access
                self._update_local_product(product_id, **kwargs)
                return True, "Product updated successfully"
            except Exception as e:
                return False, str(e)
        
        # Offline mode - only update locally
        return self._update_local_product(product_id, **kwargs)
    
    def _update_local_product(self, product_id: int, **kwargs) -> Tuple[bool, str]:
        """Update product in local database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # Build update query
            set_clause = ', '.join([f"{k} = ?" for k in kwargs.keys()])
            values = list(kwargs.values()) + [product_id]
            
            cursor.execute(f"""
                UPDATE products 
                SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, values)
            conn.commit()
            
            # Add to sync queue if offline
            if not self.is_online:
                self._add_to_sync_queue(conn, 'products', 'update', {
                    'id': product_id,
                    **kwargs
                })
            
            conn.close()
            return True, "Product updated successfully"
        except Exception as e:
            conn.close()
            return False, str(e)
    
    # Sync Queue Operations
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
    
    # Statistics and Analytics
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
    
    def get_categories(self) -> List[Dict]:
        """Get all product categories with counts"""
        if self.is_online:
            try:
                response = self.supabase.table('products').select('category, subcategory').execute()
                df = pd.DataFrame(response.data)
                
                # Group by category and subcategory
                categories = []
                for category in df['category'].unique():
                    if category:
                        subcategories = df[df['category'] == category]['subcategory'].unique()
                        categories.append({
                            'name': category,
                            'subcategories': [s for s in subcategories if s],
                            'count': len(df[df['category'] == category])
                        })
                
                return categories
            except:
                pass
        
        # Use SQLite
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT category, subcategory, COUNT(*) as count
            FROM products
            WHERE category IS NOT NULL
            GROUP BY category, subcategory
        """)
        
        results = cursor.fetchall()
        conn.close()
        
        # Organize by category
        categories_dict = {}
        for category, subcategory, count in results:
            if category not in categories_dict:
                categories_dict[category] = {
                    'name': category,
                    'subcategories': [],
                    'count': 0
                }
            
            if subcategory:
                categories_dict[category]['subcategories'].append(subcategory)
            categories_dict[category]['count'] += count
        
        return list(categories_dict.values())