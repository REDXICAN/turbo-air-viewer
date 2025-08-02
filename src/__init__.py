"""
Turbo Air Equipment Viewer - Core Modules
Updated imports for compact list view
"""

from .config import Config, init_session_state, AppError, DatabaseError, AuthError, SyncError
from .auth import AuthManager
from .database_manager import DatabaseManager
from .sync import SyncManager
from .persistence import PersistenceManager
from .ui import (
    apply_mobile_css, app_header, search_bar_component, bottom_navigation,
    category_grid, product_list_item, product_list_item_compact, product_details_expanded,
    recent_searches_section, recent_quotes_section, metrics_section, 
    cart_item_component, cart_summary, quote_export_buttons, 
    empty_state, format_price, truncate_text, floating_cart_button, 
    get_image_base64, COLORS, TURBO_AIR_CATEGORIES
)
from .pages import (
    show_home_page, show_search_page, show_cart_page, show_profile_page,
    show_product_detail, show_quote_summary
)
from .export import (
    generate_excel_quote, generate_pdf_quote, export_quote_to_excel, 
    export_quote_to_pdf, prepare_email_attachments
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
    'category_grid', 'product_list_item', 'product_list_item_compact', 
    'product_details_expanded', 'recent_searches_section', 'recent_quotes_section',
    'metrics_section', 'cart_item_component', 'cart_summary', 'quote_export_buttons',
    'empty_state', 'format_price', 'truncate_text', 'floating_cart_button',
    'get_image_base64', 'COLORS', 'TURBO_AIR_CATEGORIES',
    
    # Pages
    'show_home_page', 'show_search_page', 'show_cart_page', 'show_profile_page',
    'show_product_detail', 'show_quote_summary',
    
    # Export
    'generate_excel_quote', 'generate_pdf_quote', 'export_quote_to_excel',
    'export_quote_to_pdf', 'prepare_email_attachments',
    
    # Email
    'EmailService', 'get_email_service', 'show_email_quote_dialog', 'is_email_configured'
]