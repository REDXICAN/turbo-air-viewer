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
from src.ui import apply_mobile_css, floating_cart_button

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

# Apply responsive CSS with sticky navigation
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
    
    /* Ensure content doesn't get hidden behind console and nav */
    .main {
        padding-bottom: 100px !important;
    }
    
    /* Fix Streamlit button styling */
    .stButton > button {
        margin: 0 !important;
        width: 100%;
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px;
        padding: 12px 16px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    
    .stButton > button:hover {
        background-color: #f5f5f5 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Primary button styling */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #007AFF !important;
        color: white !important;
        border: none !important;
    }
    
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background-color: #0066E0 !important;
    }
    
    /* Fix any scrollbar issues */
    .main {
        overflow-x: hidden;
    }
    
    /* Section styling for better distinction */
    section[data-testid="stSidebar"] + div {
        background-color: #ffffff;
    }
    
    /* Content sections */
    .element-container {
        background-color: #ffffff;
    }
    
    /* Fix hidden navigation buttons */
    .stButton button[key^="nav_"] {
        position: absolute;
        opacity: 0;
        pointer-events: none;
        width: 1px;
        height: 1px;
    }
    
    /* Base app styling */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Main content area */
    .main > div {
        background-color: #ffffff;
        padding: 0 16px;
    }
    
    /* Sticky header for search page */
    .sticky-header {
        position: sticky;
        position: -webkit-sticky;
        top: 0;
        background: #ffffff;
        z-index: 100;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        padding-bottom: 10px;
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    /* Hide search title when scrolling */
    .sticky-header.scrolled .search-title {
        opacity: 0;
        height: 0;
        margin: 0;
        transition: all 0.3s ease;
    }
    
    /* Logo styling */
    .stImage {
        max-width: 200px;
        margin: 0 auto;
    }
    
    /* Search container styling */
    .search-container {
        background: #ffffff;
        padding: 8px 16px;
        margin: 0;
    }
    
    /* Categories section */
    .categories-section {
        background: #f8f9fa;
        border-radius: 12px;
        padding: 16px;
        margin: 16px 0;
    }
    
    .categories-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
        padding: 8px 0;
        user-select: none;
    }
    
    .categories-header:hover {
        color: #007AFF;
    }
    
    .categories-toggle {
        font-size: 20px;
        transition: transform 0.3s ease;
    }
    
    .categories-toggle.open {
        transform: rotate(180deg);
    }
    
    .categories-content {
        max-height: 0;
        overflow: hidden;
        transition: max-height 0.3s ease;
    }
    
    .categories-content.open {
        max-height: 1000px;
    }
    
    /* Material design shadow for category buttons */
    .category-button {
        background: #ffffff;
        border: none;
        border-radius: 8px;
        padding: 16px;
        margin: 8px;
        cursor: pointer;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06);
    }
    
    .category-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15), 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .category-button:active {
        transform: translateY(0);
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    
    @media (min-width: 768px) {
        .stImage {
            max-width: 250px;
        }
        .search-container {
            padding: 10px 24px;
        }
    }
    
    @media (min-width: 1024px) {
        .stImage {
            max-width: 300px;
        }
        .search-container {
            padding: 12px 32px;
        }
    }
    
    /* Console display */
    .console-display {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        height: 30px;
        background: #1a1a1a;
        color: #00ff00;
        font-family: monospace;
        font-size: 12px;
        padding: 5px 10px;
        display: flex;
        align-items: center;
        z-index: 10000;
        border-top: 1px solid #333;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }
    
    /* Navigation menu */
    .nav-menu {
        position: fixed;
        bottom: 30px;
        left: 0;
        right: 0;
        background: #ffffff;
        border-top: 2px solid #007AFF;
        display: flex;
        justify-content: space-around;
        align-items: center;
        height: 60px;
        z-index: 9999;
        box-shadow: 0 -4px 16px rgba(0,0,0,0.15);
    }
    
    .nav-item {
        flex: 1;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        cursor: pointer;
        transition: all 0.2s ease;
        text-decoration: none;
        color: #666;
        position: relative;
    }
    
    .nav-item:hover {
        background: #f0f7ff;
        color: #007AFF;
    }
    
    .nav-item.active {
        color: #007AFF;
        background: #f0f7ff;
    }
    
    .nav-item.active::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: #007AFF;
    }
    
    .nav-icon {
        font-size: 24px;
        margin-bottom: 4px;
    }
    
    .nav-label {
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Hide navigation on desktop */
    @media (min-width: 1024px) {
        .nav-menu {
            display: none;
        }
        .main {
            padding-bottom: 40px !important;
        }
    }
    
    @media (min-width: 768px) {
        .console-display {
            font-size: 13px;
            padding: 5px 15px;
        }
    }
    
    @media (min-width: 1024px) {
        .console-display {
            font-size: 14px;
            padding: 5px 20px;
        }
    }
</style>

<script>
    // Add scroll detection for sticky header
    window.addEventListener('scroll', function() {
        const stickyHeader = document.querySelector('.sticky-header');
        if (stickyHeader) {
            if (window.scrollY > 50) {
                stickyHeader.classList.add('scrolled');
            } else {
                stickyHeader.classList.remove('scrolled');
            }
        }
    });
    
    // Categories toggle functionality
    function toggleCategories() {
        const content = document.querySelector('.categories-content');
        const toggle = document.querySelector('.categories-toggle');
        if (content && toggle) {
            content.classList.toggle('open');
            toggle.classList.toggle('open');
        }
    }
</script>
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

def show_console():
    """Display console at the bottom of the page with user role"""
    from datetime import datetime
    current_time = datetime.now().strftime("%H:%M:%S")
    
    message = f"[{current_time}] "
    
    if hasattr(st.session_state, 'auth_manager') and st.session_state.auth_manager.is_authenticated():
        user = st.session_state.auth_manager.get_current_user()
        if user:
            message += f"User: {user.get('email', 'Unknown')} | "
            # Add user role
            role = st.session_state.auth_manager.get_user_role()
            message += f"Role: {role.title()} | "
        message += f"Page: {st.session_state.active_page} | "
        if st.session_state.auth_manager.is_online:
            message += "Status: Online"
        else:
            message += "Status: Offline"
    else:
        message += "Awaiting authentication..."
    
    st.markdown(f'<div class="console-display">{message}</div>', unsafe_allow_html=True)

def show_navigation():
    """Display navigation menu"""
    active_page = st.session_state.get('active_page', 'home')
    
    # Create navigation with better visibility
    nav_html = f'''
    <div class="nav-menu">
        <div class="nav-item {'active' if active_page == 'home' else ''}" onclick="document.getElementById('nav_home').click()">
            <div class="nav-icon">🏠</div>
            <div class="nav-label">Home</div>
        </div>
        <div class="nav-item {'active' if active_page == 'search' else ''}" onclick="document.getElementById('nav_search').click()">
            <div class="nav-icon">🔍</div>
            <div class="nav-label">Search</div>
        </div>
        <div class="nav-item {'active' if active_page == 'cart' else ''}" onclick="document.getElementById('nav_cart').click()">
            <div class="nav-icon">🛒</div>
            <div class="nav-label">Cart</div>
        </div>
        <div class="nav-item {'active' if active_page == 'profile' else ''}" onclick="document.getElementById('nav_profile').click()">
            <div class="nav-icon">👤</div>
            <div class="nav-label">Profile</div>
        </div>
    </div>
    '''
    
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Hidden buttons for navigation - place them in a hidden container
    st.markdown('<div style="position: absolute; left: -9999px;">', unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("Home", key="nav_home"):
            st.session_state.active_page = 'home'
            st.rerun()
    with col2:
        if st.button("Search", key="nav_search"):
            st.session_state.active_page = 'search'
            st.rerun()
    with col3:
        if st.button("Cart", key="nav_cart"):
            st.session_state.active_page = 'cart'
            st.rerun()
    with col4:
        if st.button("Profile", key="nav_profile"):
            st.session_state.active_page = 'profile'
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

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
                st.image(logo_path, use_container_width=True)
        else:
            st.markdown("<h1 style='text-align: center; margin-bottom: 2rem; margin-top: 1rem;'>Turbo Air</h1>", unsafe_allow_html=True)
        
        # Show auth form centered
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            # Show auth form
            auth_manager.show_auth_form()
    else:
        # Main app content
        # Display logo for all pages except search (search page handles its own)
        if st.session_state.active_page != 'search':
            logo_path = "Turboair_Logo_01.png"
            if os.path.exists(logo_path):
                col1, col2, col3 = st.columns([1, 3, 1])
                with col2:
                    st.image(logo_path, use_container_width=True)
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
            # Show navigation on product detail
            show_navigation()
            show_console()
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
        
        # Show navigation (not on quote summary)
        if active_page != 'quote_summary':
            show_navigation()
        
        # Floating cart button (only on search page when cart has items)
        if active_page == 'search' and st.session_state.cart_count > 0:
            floating_cart_button(st.session_state.cart_count)
    
    # Always show console at the bottom
    show_console()

if __name__ == "__main__":
    main()