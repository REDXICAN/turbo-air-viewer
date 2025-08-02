"""
Turbo Air - Main Application
Fixed with proper imports and responsive design
"""

import streamlit as st
import os
import sys
import atexit

# Add src to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.config import Config, init_session_state
from src.auth import AuthManager
from src.database_manager import DatabaseManager
from src.sync import SyncManager
from src.persistence import PersistenceManager

# Import UI components with proper error handling
from src.ui import apply_mobile_css, bottom_navigation, floating_cart_button

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

# Apply responsive CSS
st.markdown("""
<style>
    /* Remove all default Streamlit padding */
    #root > div:nth-child(1) > div > div > div > div > section > div {padding-top: 0rem;}
    .main > div:first-child { padding-top: 0rem !important; }
    div[data-testid="stDecoration"] { display: none; }
    .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        max-width: 100% !important;
    }
    
    /* Ensure content doesn't get hidden behind bottom nav on mobile/tablet */
    @media (max-width: 1024px) {
        .main {
            padding-bottom: 60px !important;
        }
    }
    
    /* Desktop styling */
    @media (min-width: 1024px) {
        .main {
            padding-bottom: 0 !important;
        }
        
        /* Center auth form on desktop */
        .stForm {
            margin-top: 2rem !important;
        }
    }
    
    /* Remove extra spacing from buttons */
    .stButton > button {
        margin: 0 !important;
    }
    
    /* Fix any scrollbar issues */
    .main {
        overflow-x: hidden;
    }
    
    /* Ensure responsive columns work properly */
    @media (min-width: 768px) {
        div[data-testid="column"] > div:first-child > div > div > div {
            padding-top: 0 !important;
        }
    }
    
    /* Logo styling */
    .stImage {
        max-width: 300px;
        margin: 0 auto;
    }
    
    @media (min-width: 768px) {
        .stImage {
            max-width: 400px;
        }
    }
    
    @media (min-width: 1024px) {
        .stImage {
            max-width: 500px;
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
            
            # Ensure database_backups table info is stored
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
        
        # Initialize persistence manager
        persistence_manager = PersistenceManager(
            db_manager=db_manager,
            supabase_client=auth_manager.supabase
        )
        
        # Store in session state
        st.session_state.auth_manager = auth_manager
        st.session_state.db_manager = db_manager
        st.session_state.sync_manager = sync_manager
        st.session_state.config = config
        st.session_state.persistence_manager = persistence_manager
        
        # Initialize persistence on startup
        persistence_manager.initialize_on_startup()
        
        # Set up automatic backup on shutdown (for Streamlit Cloud)
        if 'backup_registered' not in st.session_state:
            atexit.register(lambda: persistence_manager.backup_on_shutdown() if auth_manager.is_online else None)
            st.session_state.backup_registered = True
        
        return auth_manager, db_manager, sync_manager, persistence_manager
        
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

def periodic_backup(persistence_manager, auth_manager):
    """Perform periodic backup if online"""
    # Check if it's been more than 1 hour since last backup
    import time
    current_time = time.time()
    last_backup_time = st.session_state.get('last_backup_time', 0)
    
    if current_time - last_backup_time > 3600:  # 1 hour
        if auth_manager.is_online:
            try:
                persistence_manager.backup_to_supabase()
                st.session_state.last_backup_time = current_time
            except:
                pass

def get_device_type():
    """Determine device type based on viewport (for desktop navigation)"""
    # This is a simple check, in a real app you'd use JavaScript
    # For now, we'll assume desktop if running locally
    return "desktop" if not st.session_state.get('is_mobile', False) else "mobile"

def main():
    """Main application entry point"""
    # Initialize session state
    init_session_state()
    
    # Apply responsive CSS
    apply_mobile_css()
    
    # Check and migrate database if needed
    check_and_migrate_database()
    
    # Create database if it doesn't exist
    if not os.path.exists('turbo_air_db_online.sqlite'):
        try:
            # Check if Excel file exists before creating database
            excel_exists = check_excel_file()
            
            st.info("Creating database for first time setup...")
            
            # Import create_db module properly
            import sys
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
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
    auth_manager, db_manager, sync_manager, persistence_manager = initialize_services()
    
    # Perform periodic backup
    periodic_backup(persistence_manager, auth_manager)
    
    # Check authentication
    if not auth_manager.is_authenticated():
        # Display logo with responsive sizing
        logo_path = "Turboair_Logo_01.png"
        if os.path.exists(logo_path):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo_path, use_column_width=True)
        else:
            st.markdown("<h1 style='text-align: center; margin-bottom: 2rem; margin-top: 1rem;'>Turbo Air</h1>", unsafe_allow_html=True)
        
        # Center the auth form on larger screens
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Show auth form
            auth_manager.show_auth_form()
    else:
        # Display logo for authenticated pages with responsive sizing
        logo_path = "Turboair_Logo_01.png"
        if os.path.exists(logo_path):
            # Create a centered container for the logo
            col1, col2, col3 = st.columns([1, 3, 1])
            with col2:
                st.image(logo_path, use_column_width=True)
                st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
        else:
            st.markdown("""
            <h1 style='
                text-align: center; 
                margin-bottom: 0.5rem; 
                margin-top: 0.5rem;
                font-size: clamp(1.5rem, 4vw, 2.5rem);
            '>
                Turbo Air
            </h1>
            """, unsafe_allow_html=True)
        
        # Update sync status
        try:
            sync_manager.update_sync_status()
        except Exception as e:
            print(f"Sync status update error: {e}")
        
        # Get current user
        user = auth_manager.get_current_user()
        user_id = user['id'] if user else 'offline_user'
        
        # Store user in session state for other pages
        st.session_state.user = user
        
        # Update cart count
        if st.session_state.selected_client:
            try:
                cart_items = db_manager.get_cart_items(user_id, st.session_state.selected_client)
                st.session_state.cart_count = len(cart_items)
            except:
                st.session_state.cart_count = 0
        
        # Handle product detail view
        if st.session_state.get('show_product_detail'):
            show_product_detail(st.session_state.show_product_detail, user_id, db_manager)
            # Don't show bottom navigation on product detail
            return
        
        # Clear product detail when navigating away
        if st.session_state.active_page != 'search':
            st.session_state.show_product_detail = None
        
        # Create content container with responsive padding
        container = st.container()
        with container:
            # Route to appropriate page
            active_page = st.session_state.active_page
            
            if active_page == 'home':
                show_home_page(user, user_id, db_manager, sync_manager, auth_manager)
            
            elif active_page == 'search':
                show_search_page(user_id, db_manager)
            
            elif active_page == 'cart':
                show_cart_page(user_id, db_manager)
            
            elif active_page == 'profile':
                show_profile_page(user, auth_manager, sync_manager, db_manager)
            
            elif active_page == 'quote_summary' and st.session_state.last_quote:
                show_quote_summary(st.session_state.last_quote)
        
        # Bottom navigation (not on product detail or quote summary)
        # Only show on mobile and tablet devices
        if active_page not in ['quote_summary', 'product_detail']:
            bottom_navigation()
        
        # Floating cart button (only on search page when cart has items)
        if active_page == 'search' and st.session_state.cart_count > 0:
            floating_cart_button(st.session_state.cart_count)

if __name__ == "__main__":
    main()