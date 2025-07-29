"""
Turbo Air Equipment Viewer - Main Application
Mobile-First Equipment Catalog and Quote Generation System
"""

import streamlit as st
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config, init_session_state
from src.auth import AuthManager
from src.database import DatabaseManager
from src.sync import SyncManager
from src.ui import apply_mobile_css, mobile_header, bottom_navigation
from src.pages import (
    show_home_page,
    show_search_page,
    show_cart_page,
    show_profile_page,
    show_product_detail,
    show_quote_summary
)

# Page configuration
st.set_page_config(
    page_title="Turbo Air",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

def initialize_services():
    """Initialize all services with proper error handling"""
    try:
        # Get configuration
        config = Config()
        
        # Initialize authentication
        auth_manager = AuthManager(
            supabase_url=config.supabase_url,
            supabase_key=config.supabase_key
        )
        
        # Initialize database
        db_manager = DatabaseManager(
            supabase_client=auth_manager.supabase,
            offline_db_path=config.sqlite_path
        )
        
        # Initialize sync manager
        sync_manager = SyncManager(
            database_manager=db_manager,
            supabase_client=auth_manager.supabase
        )
        
        # Store in session state
        st.session_state.auth_manager = auth_manager
        st.session_state.db_manager = db_manager
        st.session_state.sync_manager = sync_manager
        st.session_state.config = config
        
        return auth_manager, db_manager, sync_manager
        
    except Exception as e:
        st.error(f"Failed to initialize services: {str(e)}")
        st.stop()

def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Apply mobile CSS
    apply_mobile_css()
    
    # Initialize services
    auth_manager, db_manager, sync_manager = initialize_services()
    
    # Create database if it doesn't exist
    if not os.path.exists(st.session_state.config.sqlite_path):
        try:
            from src.database.create_db import create_local_database
            create_local_database()
        except Exception as e:
            st.error(f"Error creating database: {e}")
    
    # Main app container
    with st.container():
        st.markdown('<div class="mobile-container">', unsafe_allow_html=True)
        
        # Check authentication
        if not auth_manager.is_authenticated():
            # Show login page
            mobile_header("Turbo Air")
            auth_manager.show_auth_form()
        else:
            # Update sync status
            try:
                sync_manager.update_sync_status()
            except Exception as e:
                print(f"Sync status update error: {e}")
            
            # Get current user
            user = auth_manager.get_current_user()
            user_id = user['id'] if user else 'offline_user'
            
            # Update cart count
            if st.session_state.selected_client:
                try:
                    cart_items = db_manager.get_cart_items(user_id, st.session_state.selected_client)
                    st.session_state.cart_count = len(cart_items)
                except:
                    st.session_state.cart_count = 0
            
            # Main content with padding for bottom nav
            st.markdown('<div class="main-content">', unsafe_allow_html=True)
            
            # Route to appropriate page
            active_page = st.session_state.active_page
            
            if active_page == 'home':
                show_home_page(user, user_id, db_manager, sync_manager, auth_manager)
            
            elif active_page in ['search', 'products']:
                show_search_page(user_id, db_manager)
            
            elif active_page == 'cart':
                show_cart_page(user_id, db_manager)
            
            elif active_page == 'profile':
                show_profile_page(user, auth_manager, sync_manager, db_manager)
            
            elif active_page == 'quote_summary' and st.session_state.last_quote:
                show_quote_summary(st.session_state.last_quote)
            
            # Product detail modal
            if st.session_state.show_product_detail:
                show_product_detail(st.session_state.show_product_detail, user_id, db_manager)
            
            st.markdown('</div>', unsafe_allow_html=True)  # Close main-content
            
            # Bottom navigation
            if not st.session_state.show_product_detail:
                bottom_navigation(st.session_state.active_page)
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close mobile-container

if __name__ == "__main__":
    main()