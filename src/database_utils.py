"""
Database utilities for better SQLite connection management
"""

import sqlite3
import time
from contextlib import contextmanager
from typing import Optional

class DatabaseConnection:
    """Manages SQLite connections with retry logic and proper settings"""
    
    def __init__(self, db_path: str = 'turbo_air_db_online.sqlite'):
        self.db_path = db_path
        self.max_retries = 5
        self.base_delay = 0.1
    
    @contextmanager
    def get_connection(self):
        """Get a database connection with retry logic"""
        conn = None
        retry_delay = self.base_delay
        
        for attempt in range(self.max_retries):
            try:
                # Connect with extended timeout
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                
                # Enable WAL mode for better concurrency
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA busy_timeout=30000")  # 30 second timeout
                
                # Return connection
                yield conn
                
                # Commit and close
                conn.commit()
                return
                
            except sqlite3.OperationalError as e:
                if conn:
                    conn.close()
                
                if "locked" in str(e) and attempt < self.max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                else:
                    raise
            except Exception:
                if conn:
                    conn.close()
                raise
        
        raise sqlite3.OperationalError("Database locked after all retries")

# Global instance
db_connection = DatabaseConnection()

def execute_with_retry(query: str, params: Optional[tuple] = None):
    """Execute a query with retry logic"""
    with db_connection.get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor

def fetchone_with_retry(query: str, params: Optional[tuple] = None):
    """Fetch one result with retry logic"""
    with db_connection.get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchone()

def fetchall_with_retry(query: str, params: Optional[tuple] = None):
    """Fetch all results with retry logic"""
    with db_connection.get_connection() as conn:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        return cursor.fetchall()