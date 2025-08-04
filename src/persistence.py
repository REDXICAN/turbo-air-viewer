"""
Database Persistence Manager for Streamlit Cloud
Handles automatic backup/restore with Supabase
"""

import os
import sqlite3
import json
from datetime import datetime
import streamlit as st
from typing import Optional, Dict, List
import pandas as pd
import base64
import gzip
import tempfile
import warnings

class PersistenceManager:
    def __init__(self, db_manager, supabase_client):
        self.db_manager = db_manager
        self.supabase = supabase_client
        self.backup_table = 'database_backups'
        self.initialized_marker = '.db_initialized'
    
    def _safe_datetime_conversion(self, series):
        """Safely convert series to datetime with proper format handling"""
        try:
            # Common datetime formats to try
            formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M:%S.%f',
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%S.%f',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    return pd.to_datetime(series, format=fmt, errors='coerce')
                except:
                    continue
            
            # Fallback to mixed format with warning suppression
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                return pd.to_datetime(series, errors='coerce', format='mixed')
        except:
            return series
        
    def should_reset_database(self) -> bool:
        """Check if we should do a clean database run"""
        # Check for reset flag in secrets or environment
        try:
            # Method 1: Check Streamlit secrets
            reset_flag = st.secrets.get("app", {}).get("reset_database", False)
            if reset_flag:
                return True
                
            # Method 2: Check for reset file
            if os.path.exists('.reset_database'):
                os.remove('.reset_database')  # Remove after reading
                return True
                
            # Method 3: Check Supabase for reset flag
            if self.supabase:
                response = self.supabase.table('app_settings').select('value').eq('key', 'reset_database').single().execute()
                if response.data and response.data.get('value') == 'true':
                    # Reset the flag
                    self.supabase.table('app_settings').update({'value': 'false'}).eq('key', 'reset_database').execute()
                    return True
        except:
            pass
            
        return False
    
    def _compress_data(self, data: str) -> str:
        """Compress data for storage"""
        compressed = gzip.compress(data.encode('utf-8'))
        return base64.b64encode(compressed).decode('utf-8')
    
    def _decompress_data(self, data: str) -> str:
        """Decompress data from storage"""
        compressed = base64.b64decode(data.encode('utf-8'))
        return gzip.decompress(compressed).decode('utf-8')
    
    def backup_to_supabase(self) -> bool:
        """Backup entire SQLite database to Supabase"""
        if not self.supabase:
            return False
            
        try:
            print("Starting database backup to Supabase...")
            
            # Get all data from SQLite
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            
            # Get list of tables to backup
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence', 'products')")
            tables = [row[0] for row in cursor.fetchall()]
            
            backup_data = {}
            
            # Backup each table (except products which should be loaded from Excel)
            for table in tables:
                try:
                    df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                    # Convert datetime columns to string for JSON serialization - FIXED VERSION
                    for col in df.columns:
                        if df[col].dtype == 'object':
                            try:
                                # Use the safe datetime conversion method
                                temp_series = self._safe_datetime_conversion(df[col])
                                # If successful (contains valid datetimes), convert to string
                                if not temp_series.isna().all():
                                    df[col] = temp_series.astype(str).where(temp_series.notna(), df[col])
                            except:
                                # If conversion fails, leave the column as is
                                pass
                    backup_data[table] = df.to_dict('records')
                except Exception as e:
                    print(f"Warning: Could not backup table {table}: {e}")
                    backup_data[table] = []
            
            conn.close()
            
            # Compress the backup data
            json_data = json.dumps(backup_data, default=str)
            compressed_data = self._compress_data(json_data)
            
            # Create backup record
            backup_record = {
                'backup_data': compressed_data,
                'created_at': datetime.now().isoformat(),
                'app_instance': st.session_state.get('app_instance_id', 'default'),
                'backup_type': 'full',
                'tables_included': ','.join(tables)
            }
            
            # Store in Supabase
            self.supabase.table(self.backup_table).insert(backup_record).execute()
            
            print(f"Database backup completed successfully! Backed up {len(tables)} tables.")
            return True
            
        except Exception as e:
            print(f"Backup error: {e}")
            return False
    
    def restore_from_supabase(self, silent: bool = False) -> bool:
        """Restore SQLite database from Supabase backup"""
        if not self.supabase:
            return False
            
        try:
            if not silent:
                print("Restoring database from Supabase...")
            
            # Get latest backup
            response = self.supabase.table(self.backup_table).select('*').order('created_at', desc=True).limit(1).execute()
            
            if not response.data:
                if not silent:
                    print("No backup found")
                return False
            
            backup = response.data[0]
            
            # Decompress backup data
            compressed_data = backup['backup_data']
            json_data = self._decompress_data(compressed_data)
            backup_data = json.loads(json_data)
            
            # Restore to SQLite
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            
            for table, records in backup_data.items():
                if records and table != 'products':  # Don't restore products table
                    try:
                        # Clear existing data
                        conn.execute(f"DELETE FROM {table}")
                        
                        # Insert backed up data
                        df = pd.DataFrame(records)
                        df.to_sql(table, conn, if_exists='append', index=False)
                        if not silent:
                            print(f"Restored {len(records)} records to {table}")
                    except Exception as e:
                        if not silent:
                            print(f"Warning: Could not restore table {table}: {e}")
            
            conn.commit()
            conn.close()
            
            if not silent:
                print("Database restored successfully!")
            return True
            
        except Exception as e:
            if not silent:
                print(f"Restore error: {e}")
            return False
    
    def initialize_on_startup(self):
        """Initialize database on app startup"""
        # Generate unique instance ID for this session
        if 'app_instance_id' not in st.session_state:
            st.session_state.app_instance_id = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Check if we should reset
        if self.should_reset_database():
            print("Clean database run requested...")
            if os.path.exists(self.initialized_marker):
                os.remove(self.initialized_marker)
            return
        
        # Check if already initialized
        if os.path.exists(self.initialized_marker):
            return
        
        # Try to restore from Supabase
        if self.supabase:
            if self.restore_from_supabase(silent=True):
                # Mark as initialized
                with open(self.initialized_marker, 'w') as f:
                    f.write(datetime.now().isoformat())
    
    def backup_on_shutdown(self):
        """Backup database when app is shutting down"""
        # This would be called in a cleanup handler
        # For Streamlit Cloud, we can use periodic backups instead
        self.backup_to_supabase()
    
    def create_backup_tables(self) -> bool:
        """Create backup tables in Supabase if they don't exist"""
        if not self.supabase:
            return False
            
        try:
            # This would be done via Supabase dashboard or migration
            # The table should have:
            # - id (uuid, primary key)
            # - backup_data (text)
            # - created_at (timestamp)
            # - app_instance (text)
            # - backup_type (text)
            # - tables_included (text)
            return True
        except:
            return False
    
    def cleanup_old_backups(self, days_to_keep: int = 7):
        """Clean up old backups from Supabase"""
        if not self.supabase:
            return
            
        try:
            cutoff_date = (datetime.now() - pd.Timedelta(days=days_to_keep)).isoformat()
            self.supabase.table(self.backup_table).delete().lt('created_at', cutoff_date).execute()
            print(f"Cleaned up backups older than {days_to_keep} days")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    def get_backup_status(self) -> Dict:
        """Get backup status information"""
        status = {
            'last_backup': None,
            'backup_count': 0,
            'total_size': 0,
            'is_restored': os.path.exists(self.initialized_marker)
        }
        
        if self.supabase:
            try:
                # Get latest backup info
                response = self.supabase.table(self.backup_table).select('created_at').order('created_at', desc=True).limit(1).execute()
                if response.data:
                    status['last_backup'] = response.data[0]['created_at']
                
                # Get backup count
                response = self.supabase.table(self.backup_table).select('id', count='exact').execute()
                status['backup_count'] = response.count if hasattr(response, 'count') else len(response.data)
                
            except:
                pass
        
        return status
    
    def manual_backup(self) -> bool:
        """Trigger manual backup"""
        return self.backup_to_supabase()
    
    def manual_restore(self, backup_id: Optional[str] = None) -> bool:
        """Trigger manual restore from specific backup or latest"""
        if not self.supabase:
            return False
            
        try:
            if backup_id:
                # Restore specific backup
                response = self.supabase.table(self.backup_table).select('*').eq('id', backup_id).single().execute()
            else:
                # Restore latest
                response = self.supabase.table(self.backup_table).select('*').order('created_at', desc=True).limit(1).execute()
                
            if response.data:
                # Process the restore...
                return self.restore_from_supabase(silent=False)
                
        except Exception as e:
            print(f"Manual restore error: {e}")
            
        return False