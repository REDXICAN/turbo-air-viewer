"""
Turbo Air Equipment Viewer - Main Application
Mobile-First Equipment Catalog and Quote Generation System
Fixed: UI rendering and database initialization
"""

import streamlit as st
import os
import sys

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config, init_session_state
from src.auth import AuthManager
from src.database_manager import DatabaseManager
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

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Turbo Air",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Remove top padding immediately after page config
st.markdown("""
<style>
    /* Remove all default Streamlit padding */
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    .main > div:first-child { padding-top: 0rem !important; }
    div[data-testid="stDecoration"] { display: none; }
    .block-container { padding-top: 0rem !important; }
    
    /* Fix desktop form centering without extra padding */
    @media (min-width: 768px) {
        div[data-testid="column"] > div:first-child > div > div > div {
            padding-top: 0 !important;
        }
        .stForm {
            margin-top: 2rem !important;
        }
    }
</style>
""", unsafe_allow_html=True)

def check_and_migrate_database():
    """Check database and run migrations if needed"""
    db_path = 'turbo_air_db_online.sqlite'
    
    if os.path.exists(db_path):
        # Check if migration is needed
        import sqlite3
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check for password_hash column
            cursor.execute("PRAGMA table_info(user_profiles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'password_hash' not in columns:
                st.warning("Database schema needs updating. Running migration...")
                cursor.execute("""
                    ALTER TABLE user_profiles 
                    ADD COLUMN password_hash TEXT
                """)
                conn.commit()
                st.success("Database migration completed!")
            
            # Ensure auth_tokens table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Ensure sync_queue table exists
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
            
            conn.commit()
        except Exception as e:
            st.error(f"Migration error: {e}")
        finally:
            conn.close()

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

def check_excel_file():
    """Check if Excel file exists and provide instructions if not"""
    excel_path = 'turbo_air_products.xlsx'
    if not os.path.exists(excel_path):
        st.error("⚠️ Product data file not found!")
        st.info("""
        **To load products, you need to:**
        1. Place `turbo_air_products.xlsx` in the project root directory (same folder as `app.py`)
        2. Restart the application
        """)
        return False
    return True

def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Apply mobile CSS
    apply_mobile_css()
    
    # Check and migrate database if needed
    check_and_migrate_database()
    
    # Create database if it doesn't exist
    if not os.path.exists('turbo_air_db_online.sqlite'):
        try:
            # Check if Excel file exists before creating database
            excel_exists = check_excel_file()
            
            st.info("Creating database for first time setup...")
            from src.database.create_db import create_local_database
            if create_local_database():
                if excel_exists:
                    st.success("Database created and products loaded successfully!")
                else:
                    st.warning("Database created but no products loaded. Please add turbo_air_products.xlsx")
                st.rerun()
        except Exception as e:
            st.error(f"Error creating database: {e}")
            # Don't stop - allow app to continue with empty database
    
    # Initialize services
    auth_manager, db_manager, sync_manager = initialize_services()
    
    # Main app container with proper styling
    st.markdown('<div class="mobile-container">', unsafe_allow_html=True)
    
    # Check authentication
    if not auth_manager.is_authenticated():
        # Show login page with proper header and centered content
        st.markdown("""
        <div class="mobile-header" style="margin-bottom: 0;">
            <div style="display: flex; align-items: center; justify-content: center;">
                <h2 style="margin: 0; font-size: 20px; font-weight: 600;">Turbo Air</h2>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Center the auth form on larger screens without extra padding
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Show auth form
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