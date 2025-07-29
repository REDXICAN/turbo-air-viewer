"""
Turbo Air Equipment Viewer - Core Modules
"""

from .config import Config, init_session_state, AppError, DatabaseError, AuthError, SyncError
from .auth import AuthManager
from .database import DatabaseManager
from .sync import SyncManager
from .ui import (
    apply_mobile_css, mobile_header, mobile_search_bar, category_grid,
    quick_access_section, bottom_navigation, product_list_item, filter_row,
    metric_card, sync_status_bar, summary_section, subcategory_list,
    quantity_selector, empty_state, format_price, truncate_text,
    COLORS, TURBO_AIR_CATEGORIES
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
    'AuthManager', 'DatabaseManager', 'SyncManager',
    
    # UI Components
    'apply_mobile_css', 'mobile_header', 'mobile_search_bar', 'category_grid',
    'quick_access_section', 'bottom_navigation', 'product_list_item', 'filter_row',
    'metric_card', 'sync_status_bar', 'summary_section', 'subcategory_list',
    'quantity_selector', 'empty_state', 'format_price', 'truncate_text',
    'COLORS', 'TURBO_AIR_CATEGORIES',
    
    # Pages
    'show_home_page', 'show_search_page', 'show_cart_page', 'show_profile_page',
    'show_product_detail', 'show_quote_summary',
    
    # Export
    'export_quote_to_excel', 'export_quote_to_pdf', 'prepare_email_attachments',
    
    # Email
    'EmailService', 'get_email_service', 'show_email_quote_dialog', 'is_email_configured'
]