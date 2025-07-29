"""
Configuration management for Turbo Air Equipment Viewer
"""

import streamlit as st
import os
from typing import Optional

class Config:
    """Application configuration management"""
    
    def __init__(self):
        # Environment
        self.environment = os.getenv("ENVIRONMENT", "production")
        self.debug = self.environment == "development"
        
        # Database
        self.sqlite_path = 'turbo_air_db_online.sqlite'
        
        # Supabase configuration
        try:
            self.supabase_url = st.secrets["supabase"]["url"]
            self.supabase_key = st.secrets["supabase"]["anon_key"]
            self.has_supabase = bool(self.supabase_url and self.supabase_key)
        except:
            self.supabase_url = None
            self.supabase_key = None
            self.has_supabase = False
        
        # Email configuration
        try:
            self.email_config = {
                'smtp_server': st.secrets["email"]["smtp_server"],
                'smtp_port': st.secrets["email"]["smtp_port"],
                'sender_email': st.secrets["email"]["sender_email"],
                'sender_password': st.secrets["email"]["sender_password"]
            }
            self.has_email = all(self.email_config.values())
        except:
            self.email_config = {}
            self.has_email = False
        
        # Cache configuration
        self.cache_ttl = 300 if self.environment == "production" else 60
        self.max_upload_size = 200
        
        # UI configuration
        self.items_per_page = 20
        self.max_search_history = 10

def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'user': None,
        'user_role': 'distributor',
        'active_page': 'home',
        'selected_category': None,
        'selected_subcategory': None,
        'selected_client': None,
        'view_mode': 'grid',
        'cart_count': 0,
        'show_product_detail': None,
        'auth_manager': None,
        'db_manager': None,
        'sync_manager': None,
        'config': None,
        'sync_status': {
            'is_online': False,
            'last_sync': None,
            'pending_changes': 0,
            'sync_errors': []
        },
        'search_term': '',
        'last_quote': None,
        'cache': {}
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

class AppError(Exception):
    """Base exception for application errors"""
    pass

class DatabaseError(AppError):
    """Database connection or query errors"""
    pass

class AuthError(AppError):
    """Authentication errors"""
    pass

class SyncError(AppError):
    """Synchronization errors"""
    pass