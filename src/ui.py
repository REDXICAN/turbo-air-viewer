"""
UI Components for Turbo Air Equipment Viewer
Mobile-First iOS-style design
"""

import streamlit as st
import os
from typing import Dict, List, Optional, Callable

# Color palette
COLORS = {
    'primary': '#007AFF',
    'turbo_blue': '#20429c',
    'background': '#FFFFFF',
    'surface': '#F2F2F7',
    'card': '#FFFFFF',
    'text_primary': '#000000',
    'text_secondary': '#6C6C70',
    'text_tertiary': '#8E8E93',
    'border': '#C6C6C8',
    'success': '#34C759',
    'error': '#FF3B30',
    'warning': '#FF9500',
    'divider': '#E5E5EA'
}

# Turbo Air Official Categories
TURBO_AIR_CATEGORIES = {
    "GLASS DOOR MERCHANDISERS": {
        "icon": "🥤",
        "subcategories": [
            "Super Deluxe Series Glass Door Merchandisers",
            "Super Deluxe Jumbo Series Glass Door Merchandisers",
            "Standard Series Glass Door Merchandisers",
            "Ice Merchandisers",
            "E-line - Swing Doors Refrigerators",
            "Top Open Island Freezers",
            "Ice Cream Dipping Cabinets"
        ]
    },
    "DISPLAY CASES": {
        "icon": "🍰",
        "subcategories": [
            "Open Display Merchandisers",
            "Sandwich & Cheese Cases",
            "Vertical Cases",
            "Vertical Air Curtains",
            "Island Display Cases",
            "Bakery & Deli Display Cases",
            "Sushi Cases"
        ]
    },
    "UNDERBAR EQUIPMENT": {
        "icon": "🍺",
        "subcategories": [
            "Bottle Coolers",
            "Glass / Mug Frosters",
            "Beer Dispensers",
            "Club Top Beer Dispensers",
            "Back Bars",
            "Narrow Back Bars"
        ]
    },
    "MILK COOLERS": {
        "icon": "🥛",
        "subcategories": [
            "Milk Coolers"
        ]
    }
}

def apply_mobile_css():
    """Apply mobile-first CSS styling"""
    css = f"""
    <style>
    /* Reset and base styles */
    .stApp {{
        background-color: {COLORS['background']};
        max-width: 100%;
    }}
    
    /* Hide Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* Mobile-first responsive design */
    @media (max-width: 768px) {{
        .stApp > div > div {{
            padding: 0 !important;
        }}
        
        .main > div {{
            padding: 0 !important;
        }}
    }}
    
    /* Typography */
    h1, h2, h3, h4, h5, h6 {{
        font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif;
        font-weight: 600;
        color: {COLORS['text_primary']};
    }}
    
    /* Header styles */
    .mobile-header {{
        background: {COLORS['card']};
        padding: 12px 16px;
        border-bottom: 1px solid {COLORS['divider']};
        position: sticky;
        top: 0;
        z-index: 100;
    }}
    
    /* Search bar */
    .search-container {{
        background: {COLORS['surface']};
        border-radius: 10px;
        padding: 8px 12px;
        margin: 12px 16px;
    }}
    
    /* Category card */
    .category-card {{
        background: {COLORS['turbo_blue']};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        transition: all 0.2s ease;
        cursor: pointer;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    
    .category-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    
    .category-card .icon {{
        font-size: 36px;
        margin-bottom: 8px;
    }}
    
    .category-card h4 {{
        margin: 0;
        font-size: 13px;
        font-weight: 500;
        color: white;
        line-height: 1.2;
    }}
    
    /* Product list item */
    .product-item {{
        background: {COLORS['card']};
        padding: 12px 16px;
        border-bottom: 1px solid {COLORS['divider']};
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .product-info {{
        flex: 1;
    }}
    
    .product-name {{
        font-size: 14px;
        font-weight: 500;
        color: {COLORS['text_primary']};
        margin: 0;
    }}
    
    .product-model {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        margin: 0;
    }}
    
    .product-price {{
        font-size: 16px;
        font-weight: 600;
        color: {COLORS['text_primary']};
    }}
    
    /* Bottom navigation */
    .bottom-nav {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: {COLORS['card']};
        border-top: 1px solid {COLORS['divider']};
        display: flex;
        justify-content: space-around;
        padding: 8px 0;
        z-index: 1000;
    }}
    
    .nav-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        flex: 1;
        padding: 4px;
        color: {COLORS['text_tertiary']};
        cursor: pointer;
        transition: color 0.2s ease;
    }}
    
    .nav-item.active {{
        color: {COLORS['primary']};
    }}
    
    .nav-icon {{
        font-size: 22px;
        margin-bottom: 2px;
    }}
    
    .nav-label {{
        font-size: 10px;
        font-weight: 500;
    }}
    
    /* Metrics card */
    .metric-card {{
        background: {COLORS['surface']};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
    }}
    
    .metric-value {{
        font-size: 32px;
        font-weight: 600;
        color: {COLORS['text_primary']};
        margin: 0;
    }}
    
    .metric-label {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
        margin-top: 4px;
    }}
    
    /* Sync status */
    .sync-status {{
        display: flex;
        align-items: center;
        gap: 8px;
        padding: 8px 16px;
        background: {COLORS['surface']};
        border-radius: 8px;
        font-size: 14px;
    }}
    
    .sync-indicator {{
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: {COLORS['error']};
    }}
    
    .sync-indicator.online {{
        background: {COLORS['success']};
    }}
    
    /* Add padding for bottom nav */
    .main-content {{
        padding-bottom: 80px;
    }}
    
    /* Hide default Streamlit buttons styling */
    .stButton > button {{
        background: none;
        border: none;
        padding: 0;
        width: 100%;
    }}
    
    /* Responsive adjustments */
    @media (min-width: 768px) {{
        .mobile-container {{
            max-width: 768px;
            margin: 0 auto;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            min-height: 100vh;
            background: {COLORS['background']};
        }}
        
        .category-card {{
            height: 160px;
        }}
        
        .search-container {{
            max-width: 500px;
            margin: 12px auto;
        }}
    }}
    
    @media (min-width: 1024px) {{
        .mobile-container {{
            max-width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        .main-content {{
            padding: 20px;
            padding-bottom: 100px;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def mobile_header(title: str, show_back: bool = False):
    """Render mobile header"""
    header_html = f"""
    <div class="mobile-header">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            {'<span style="font-size: 20px; cursor: pointer;">←</span>' if show_back else ''}
            <h2 style="margin: 0; font-size: 20px; font-weight: 600;">{title}</h2>
            <div style="width: 24px;"></div>
        </div>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def mobile_search_bar(placeholder: str = "Search for products"):
    """Render mobile search bar"""
    return st.text_input("", placeholder=placeholder, key="search_input", label_visibility="collapsed")

def category_grid(categories: List[Dict[str, str]]):
    """Render category grid"""
    cols = st.columns(2)
    for i, category in enumerate(categories):
        with cols[i % 2]:
            icon = TURBO_AIR_CATEGORIES.get(category['name'], {}).get('icon', '📦')
            
            if st.button(
                f"{icon}\n{category['name']}",
                key=f"cat_{category['name']}",
                use_container_width=True
            ):
                st.session_state.selected_category = category['name']
                st.session_state.active_page = 'products'
                st.rerun()
            
            st.markdown(f"""
            <div class="category-card">
                <div class="icon">{icon}</div>
                <h4>{category['name']}</h4>
                <p style="color: white; font-size: 12px; margin: 0;">{category.get('count', 0)} items</p>
            </div>
            """, unsafe_allow_html=True)

def quick_access_section():
    """Render quick access section"""
    st.markdown("### Quick Access")
    
    items = [
        {"icon": "🥤", "label": "Glass Door\nMerchandisers", "category": "GLASS DOOR MERCHANDISERS"},
        {"icon": "🍰", "label": "Display\nCases", "category": "DISPLAY CASES"},
        {"icon": "🍺", "label": "Underbar\nEquipment", "category": "UNDERBAR EQUIPMENT"},
        {"icon": "🥛", "label": "Milk\nCoolers", "category": "MILK COOLERS"}
    ]
    
    cols = st.columns(4)
    for i, item in enumerate(items):
        with cols[i]:
            if st.button(
                f"{item['icon']}\n{item['label']}",
                key=f"quick_{item['category']}",
                use_container_width=True
            ):
                st.session_state.selected_category = item['category']
                st.session_state.active_page = 'products'
                st.rerun()

def subcategory_list(subcategories: List[str], parent_category: str):
    """Render subcategory list"""
    st.markdown(f"### Select {parent_category} Type")
    
    for subcat in subcategories:
        if st.button(
            subcat,
            key=f"subcat_{subcat}",
            use_container_width=True
        ):
            st.session_state.selected_subcategory = subcat
            st.rerun()

def bottom_navigation(active_page: str):
    """Render bottom navigation bar"""
    nav_items = [
        {"icon": "🏠", "label": "Home", "page": "home"},
        {"icon": "🔍", "label": "Search", "page": "search"},
        {"icon": "🛒", "label": "Cart", "page": "cart"},
        {"icon": "👤", "label": "Profile", "page": "profile"}
    ]
    
    nav_html = '<div class="bottom-nav">'
    for item in nav_items:
        active_class = "active" if item["page"] == active_page else ""
        nav_html += f'''
        <div class="nav-item {active_class}">
            <div class="nav-icon">{item["icon"]}</div>
            <div class="nav-label">{item["label"]}</div>
        </div>
        '''
    nav_html += '</div>'
    
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Handle navigation with hidden buttons
    cols = st.columns(4)
    for i, item in enumerate(nav_items):
        with cols[i]:
            if st.button(
                "",
                key=f"nav_{item['page']}",
                use_container_width=True,
                disabled=(item["page"] == active_page)
            ):
                st.session_state.active_page = item["page"]
                st.rerun()

def product_list_item(product: Dict):
    """Render product list item"""
    # Get values with "-" for None/empty
    sku = product.get('sku', 'Unknown')
    product_type = product.get('product_type') or '-'
    price = product.get('price', 0)
    
    item_html = f"""
    <div class="product-item">
        <div class="product-info" style="margin-left: 0;">
            <p class="product-name">{sku}</p>
            <p class="product-model">{product_type}</p>
        </div>
        <div class="product-price">${price:,.2f}</div>
    </div>
    """
    return item_html

def filter_row():
    """Render filter row"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        categories = ["All"] + list(TURBO_AIR_CATEGORIES.keys())
        st.selectbox("Category", categories, key="filter_category")
    
    with col2:
        st.selectbox("Price", ["All", "Under $3,000", "$3,000-$5,000", "$5,000-$10,000", "Over $10,000"], key="filter_price")
    
    with col3:
        st.selectbox("Type", ["All", "Refrigerator", "Freezer", "Display", "Underbar"], key="filter_type")

def metric_card(label: str, value: int):
    """Render metric card"""
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-value">{value}</div>
        <div class="metric-label">{label}</div>
    </div>
    """, unsafe_allow_html=True)

def sync_status_bar(is_online: bool, is_synced: bool):
    """Render sync status bar"""
    status_text = "All synced" if is_synced else "Sync needed"
    indicator_class = "online" if is_online else ""
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown(f"""
        <div class="sync-status">
            <div class="sync-indicator {indicator_class}"></div>
            <span>{"Online" if is_online else "Offline"}</span>
            <span style="margin-left: auto; color: {COLORS['text_secondary']};">{status_text}</span>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if st.button("Sync Now", key="sync_now", use_container_width=True):
            return True
    
    return False

def summary_section(subtotal: float, tax_rate: float = 0.075):
    """Render cart/quote summary section"""
    tax = subtotal * tax_rate
    total = subtotal + tax
    
    st.markdown("### Summary")
    
    st.markdown(f"""
    <div style="padding: 16px; background: {COLORS['surface']}; border-radius: 12px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span>Subtotal</span>
            <span>${subtotal:,.2f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
            <span>Estimated Taxes</span>
            <span>${tax:,.2f}</span>
        </div>
        <div style="display: flex; justify-content: space-between; font-weight: 600; font-size: 18px; 
                    padding-top: 8px; border-top: 1px solid {COLORS['divider']};">
            <span>Total</span>
            <span>${total:,.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return total

def quantity_selector(current_quantity: int, unique_key: str) -> int:
    """Create a quantity selector"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("−", key=f"decrease_{unique_key}"):
            return max(1, current_quantity - 1)
    
    with col2:
        st.markdown(f"<h4 style='text-align: center; margin: 0;'>{current_quantity}</h4>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("+", key=f"increase_{unique_key}"):
            return current_quantity + 1
    
    return current_quantity

def empty_state(icon: str, title: str, description: str, 
                button_text: Optional[str] = None, 
                button_action: Optional[Callable] = None):
    """Display an empty state"""
    st.markdown(
        f"""
        <div style='text-align: center; padding: 3rem 1rem;'>
            <div style='font-size: 4rem; margin-bottom: 1rem;'>{icon}</div>
            <h3 style='margin-bottom: 0.5rem;'>{title}</h3>
            <p style='color: #666; margin-bottom: 2rem;'>{description}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if button_text and button_action:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(button_text, use_container_width=True):
                button_action()
                st.rerun()

def format_price(price: float, currency_symbol: str = "$") -> str:
    """Format a price value"""
    return f"{currency_symbol}{price:,.2f}"

def truncate_text(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """Truncate text to a maximum length"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix