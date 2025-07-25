"""
Sync Manager for Turbo Air Equipment Viewer
Handles synchronization between SQLite (offline) and Supabase (online)
"""

import streamlit as st
import sqlite3
import json
from datetime import datetime
import pandas as pd
from typing import Dict, List
import time
import threading

class SyncManager:
    def __init__(self, database_manager=None, supabase_client=None):
        """Initialize sync manager"""
        self.db_manager = database_manager
        self.supabase = supabase_client
        self.is_syncing = False
        self.last_sync = None
        
        # Initialize sync status in session state
        self._init_sync_status()
    
    def _init_sync_status(self):
        """Initialize sync status in session state"""
        if 'sync_status' not in st.session_state:
            st.session_state.sync_status = {
                'is_online': False,
                'last_sync': None,
                'pending_changes': 0,
                'sync_errors': []
            }
    
    def check_connectivity(self) -> bool:
        """Check if we have internet connectivity"""
        if self.supabase:
            try:
                # Try a simple query to check connection
                self.supabase.table('products').select('id').limit(1).execute()
                return True
            except:
                return False
        return False
    
    def update_sync_status(self):
        """Update sync status in session state"""
        # Ensure sync status is initialized
        self._init_sync_status()
        
        is_online = self.check_connectivity()
        st.session_state.sync_status['is_online'] = is_online
        
        # Count pending changes
        if self.db_manager:
            try:
                pending_df = self.db_manager.get_pending_sync_items()
                st.session_state.sync_status['pending_changes'] = len(pending_df)
            except:
                st.session_state.sync_status['pending_changes'] = 0
        
        return is_online
    
    def sync_all(self) -> Dict:
        """Perform full synchronization"""
        if self.is_syncing:
            return {'success': False, 'message': 'Sync already in progress'}
        
        self.is_syncing = True
        results = {
            'success': True,
            'synced_items': 0,
            'errors': [],
            'message': ''
        }
        
        try:
            # Check connectivity
            if not self.check_connectivity():
                results['success'] = False
                results['message'] = 'No internet connection'
                return results
            
            # Get pending sync items
            pending_df = self.db_manager.get_pending_sync_items()
            
            if pending_df.empty:
                results['message'] = 'No items to sync'
                return results
            
            # Process each sync item
            synced_ids = []
            
            for _, item in pending_df.iterrows():
                try:
                    success = self._sync_item(item)
                    if success:
                        synced_ids.append(item['id'])
                        results['synced_items'] += 1
                    else:
                        results['errors'].append(f"Failed to sync {item['table_name']} {item['operation']}")
                except Exception as e:
                    results['errors'].append(str(e))
            
            # Mark items as synced
            if synced_ids:
                self.db_manager.mark_synced(synced_ids)
            
            # Update last sync time
            self.last_sync = datetime.now()
            st.session_state.sync_status['last_sync'] = self.last_sync
            
            # Set success message
            results['message'] = f"Successfully synced {results['synced_items']} items"
            
            # Store errors in session state
            st.session_state.sync_status['sync_errors'] = results['errors']
            
        except Exception as e:
            results['success'] = False
            results['message'] = f"Sync error: {str(e)}"
            results['errors'].append(str(e))
        
        finally:
            self.is_syncing = False
        
        return results
    
    def _sync_item(self, sync_item) -> bool:
        """Sync individual item to Supabase"""
        table_name = sync_item['table_name']
        operation = sync_item['operation']
        data = json.loads(sync_item['data'])
        
        try:
            if operation == 'insert':
                self.supabase.table(table_name).insert(data).execute()
            
            elif operation == 'update':
                item_id = data.pop('id')
                self.supabase.table(table_name).update(data).eq('id', item_id).execute()
            
            elif operation == 'delete':
                self.supabase.table(table_name).delete().eq('id', data['id']).execute()
            
            elif operation == 'upsert':
                # For cart items, handle upsert logic
                if table_name == 'cart_items':
                    # Check if exists
                    existing = self.supabase.table(table_name).select('*').eq(
                        'user_id', data['user_id']
                    ).eq('product_id', data['product_id'])
                    
                    if data.get('client_id'):
                        existing = existing.eq('client_id', data['client_id'])
                    else:
                        existing = existing.is_('client_id', None)
                    
                    existing_data = existing.execute()
                    
                    if existing_data.data:
                        # Update
                        self.supabase.table(table_name).update({
                            'quantity': data['quantity']
                        }).eq('id', existing_data.data[0]['id']).execute()
                    else:
                        # Insert
                        self.supabase.table(table_name).insert(data).execute()
                else:
                    # Default upsert
                    self.supabase.table(table_name).upsert(data).execute()
            
            elif operation == 'clear':
                # Handle clear operations
                if table_name == 'cart_items':
                    query = self.supabase.table(table_name).delete().eq('user_id', data['user_id'])
                    if data.get('client_id'):
                        query = query.eq('client_id', data['client_id'])
                    query.execute()
                elif table_name == 'search_history':
                    self.supabase.table(table_name).delete().eq('user_id', data['user_id']).execute()
            
            return True
            
        except Exception as e:
            print(f"Sync error for {table_name} {operation}: {str(e)}")
            return False
    
    def sync_down_products(self) -> bool:
        """Sync products from Supabase to local SQLite"""
        try:
            if not self.check_connectivity():
                return False
            
            # Get all products from Supabase
            response = self.supabase.table('products').select('*').execute()
            products = response.data
            
            if not products:
                return True
            
            # Update local database
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            # Clear existing products
            cursor.execute("DELETE FROM products")
            
            # Insert new products
            for product in products:
                cursor.execute("""
                    INSERT INTO products (
                        sku, product_type, description, capacity, doors, amperage,
                        dimensions, dimensions_metric, weight, weight_metric,
                        temperature_range, temperature_range_metric, voltage, phase,
                        frequency, plug_type, refrigerant, compressor, shelves,
                        features, certifications, price, category, subcategory
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product.get('sku'),
                    product.get('product_type'),
                    product.get('description'),
                    product.get('capacity'),
                    product.get('doors'),
                    product.get('amperage'),
                    product.get('dimensions'),
                    product.get('dimensions_metric'),
                    product.get('weight'),
                    product.get('weight_metric'),
                    product.get('temperature_range'),
                    product.get('temperature_range_metric'),
                    product.get('voltage'),
                    product.get('phase'),
                    product.get('frequency'),
                    product.get('plug_type'),
                    product.get('refrigerant'),
                    product.get('compressor'),
                    product.get('shelves'),
                    product.get('features'),
                    product.get('certifications'),
                    product.get('price'),
                    product.get('category'),
                    product.get('subcategory')
                ))
            
            conn.commit()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error syncing products: {str(e)}")
            return False
    
    def auto_sync(self, interval_seconds=300):
        """Auto sync at specified interval (default 5 minutes)"""
        def sync_loop():
            while True:
                time.sleep(interval_seconds)
                if self.check_connectivity():
                    self.sync_all()
        
        # Start sync thread
        sync_thread = threading.Thread(target=sync_loop, daemon=True)
        sync_thread.start()
    
    def get_sync_status_display(self) -> str:
        """Get formatted sync status for display"""
        self._init_sync_status()  # Ensure initialized
        status = st.session_state.sync_status
        
        if status['is_online']:
            online_status = "🟢 Online"
        else:
            online_status = "🔴 Offline"
        
        if status['pending_changes'] > 0:
            pending = f"📤 {status['pending_changes']} pending"
        else:
            pending = "✅ All synced"
        
        if status['last_sync']:
            last_sync = f"🕐 {status['last_sync'].strftime('%H:%M')}"
        else:
            last_sync = "🕐 Never synced"
        
        return f"{online_status} | {pending} | {last_sync}"

def show_sync_status():
    """Display sync status in the UI"""
    sync_status = st.session_state.get('sync_status', {})
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if sync_status.get('is_online'):
            st.success("🟢 Online")
        else:
            st.warning("🔴 Offline")
    
    with col2:
        pending = sync_status.get('pending_changes', 0)
        if pending > 0:
            st.info(f"📤 {pending} changes pending")
        else:
            st.success("✅ All synced")
    
    with col3:
        last_sync = sync_status.get('last_sync')
        if last_sync:
            st.caption(f"Last sync: {last_sync.strftime('%H:%M')}")
        else:
            st.caption("Never synced")
    
    # Show sync errors if any
    if sync_status.get('sync_errors'):
        with st.expander("Sync Errors", expanded=False):
            for error in sync_status['sync_errors']:
                st.error(error)

def manual_sync_button(sync_manager):
    """Display manual sync button"""
    if st.button("🔄 Sync Now", help="Manually sync data with cloud"):
        with st.spinner("Syncing..."):
            results = sync_manager.sync_all()
            
            if results['success']:
                st.success(results['message'])
            else:
                st.error(results['message'])
            
            if results['errors']:
                with st.expander("Sync Errors"):
                    for error in results['errors']:
                        st.error(error)
            
            # Update sync status
            sync_manager.update_sync_status()
            st.rerun()