"""
Turbo Air Equipment Viewer - Core Modules
Updated with new navigation structure
"""

from .config import Config, init_session_state, AppError, DatabaseError, AuthError, SyncError
from .auth import AuthManager
from .database_manager import DatabaseManager
from .sync import SyncManager
from .persistence import PersistenceManager
from .ui_components import (
    apply_mobile_css, app_header, search_bar_component, bottom_navigation,
    category_grid, product_list_item, recent_searches_section, recent_quotes_section,
    metrics_section, cart_item_component, cart_summary, quote_export_buttons,
    empty_state, format_price, truncate_text, COLORS, TURBO_AIR_CATEGORIES
)
from .pages import (
    show_home_page, show_search_page, show_cart_page, show_profile_page,
    show_product_detail, show_quote_summary
)
from .export import (
    export_quote_to_excel, export_quote_to_pdf, prepare_email_attachments
)
from .email import (
    EmailService, get_email_service, show_email_quote_dialog, is_email_configured
)

__all__ = [
    # Config
    'Config', 'init_session_state', 'AppError', 'DatabaseError', 'AuthError', 'SyncError',
    
    # Core Services
    'AuthManager', 'DatabaseManager', 'SyncManager', 'PersistenceManager',
    
    # UI Components
    'apply_mobile_css', 'app_header', 'search_bar_component', 'bottom_navigation',
    'category_grid', 'product_list_item', 'recent_searches_section', 'recent_quotes_section',
    'metrics_section', 'cart_item_component', 'cart_summary', 'quote_export_buttons',
    'empty_state', 'format_price', 'truncate_text', 'COLORS', 'TURBO_AIR_CATEGORIES',
    
    # Pages
    'show_home_page', 'show_search_page', 'show_cart_page', 'show_profile_page',
    'show_product_detail', 'show_quote_summary',
    
    # Export
    'export_quote_to_excel', 'export_quote_to_pdf', 'prepare_email_attachments',
    
    # Email
    'EmailService', 'get_email_service', 'show_email_quote_dialog', 'is_email_configured'
]