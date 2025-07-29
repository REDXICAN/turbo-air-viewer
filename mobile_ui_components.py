"""
Mobile-First UI Components for Turbo Air Equipment Viewer
iOS-style design with clean, modern interface
Updated with correct Turbo Air Inc categories and desktop display fix
"""

import streamlit as st
import pandas as pd
from PIL import Image
import os
from typing import Dict, List, Optional
import base64

# Color palette - iOS style with Turbo Air blue
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

# Turbo Air Inc Official Categories
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
    
    /* Quick Access section */
    .quick-access {{
        background: {COLORS['card']};
        border-radius: 12px;
        padding: 16px;
        margin: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }}
    
    .quick-access-title {{
        font-size: 18px;
        font-weight: 600;
        margin-bottom: 16px;
        color: {COLORS['text_primary']};
    }}
    
    .quick-access-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        padding: 12px;
        border-radius: 8px;
        transition: background 0.2s ease;
        cursor: pointer;
        min-height: 80px;
    }}
    
    .quick-access-item:hover {{
        background: {COLORS['surface']};
    }}
    
    .quick-access-icon {{
        font-size: 24px;
        margin-bottom: 4px;
    }}
    
    .quick-access-label {{
        font-size: 11px;
        color: {COLORS['text_secondary']};
        text-align: center;
        line-height: 1.2;
    }}
    
    /* Subcategory button */
    .subcategory-btn {{
        background: {COLORS['surface']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 8px;
        width: 100%;
        text-align: left;
        transition: all 0.2s ease;
    }}
    
    .subcategory-btn:hover {{
        background: {COLORS['primary']};
        color: white;
        border-color: {COLORS['primary']};
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
    
    .product-thumbnail {{
        width: 60px;
        height: 60px;
        border-radius: 8px;
        background: {COLORS['surface']};
        flex-shrink: 0;
        overflow: hidden;
    }}
    
    .product-thumbnail img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
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
    
    /* Filter dropdown */
    .filter-dropdown {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['border']};
        border-radius: 8px;
        padding: 10px 12px;
        font-size: 14px;
        color: {COLORS['text_primary']};
        display: flex;
        justify-content: space-between;
        align-items: center;
        cursor: pointer;
    }}
    
    /* Buttons */
    .primary-button {{
        background: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 14px 24px;
        font-size: 16px;
        font-weight: 500;
        width: 100%;
        cursor: pointer;
        transition: opacity 0.2s ease;
    }}
    
    .primary-button:hover {{
        opacity: 0.9;
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
    
    /* Responsive adjustments - FIXED FOR DESKTOP */
    @media (min-width: 768px) {{
        .mobile-container {{
            max-width: 768px;
            margin: 0 auto;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
            min-height: 100vh;
            background: {COLORS['background']};
        }}
        
        /* Adjust grid layouts for desktop */
        .category-card {{
            height: 160px;
        }}
        
        /* Wider search container on desktop */
        .search-container {{
            max-width: 500px;
            margin: 12px auto;
        }}
    }}
    
    /* Full desktop mode for larger screens */
    @media (min-width: 1024px) {{
        .mobile-container {{
            max-width: 100%;
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
        }}
        
        /* Better spacing for desktop */
        .main-content {{
            padding: 20px;
            padding-bottom: 100px;
        }}
        
        /* Show more columns on desktop */
        .product-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        
        /* Adjust auth form width on desktop */
        .auth-container {{
            max-width: 600px;
            margin: 0 auto;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def mobile_header(title: str, show_back: bool = False, show_search: bool = False):
    """Render mobile header with optional back button and search"""
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
    search_html = f"""
    <div class="search-container">
        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="color: {COLORS['text_secondary']};">🔍</span>
            <input type="text" placeholder="{placeholder}" 
                   style="border: none; background: none; outline: none; flex: 1; font-size: 16px;">
        </div>
    </div>
    """
    st.markdown(search_html, unsafe_allow_html=True)
    return st.text_input("", placeholder=placeholder, key="search_input", label_visibility="collapsed")

def category_grid(categories: List[Dict[str, str]]):
    """Render category grid with Turbo Air categories"""
    cols = st.columns(2)
    for i, category in enumerate(categories):
        with cols[i % 2]:
            # Get icon from TURBO_AIR_CATEGORIES if available
            icon = TURBO_AIR_CATEGORIES.get(category['name'], {}).get('icon', '📦')
            
            if st.button(
                f"{icon}\n{category['name']}",
                key=f"cat_{category['name']}",
                use_container_width=True
            ):
                st.session_state.selected_category = category['name']
                st.session_state.active_page = 'products'
                st.rerun()
            
            # Show category card with icon
            st.markdown(f"""
            <div class="category-card">
                <div class="icon">{icon}</div>
                <h4>{category['name']}</h4>
                <p style="color: white; font-size: 12px; margin: 0;">{category.get('count', 0)} items</p>
            </div>
            """, unsafe_allow_html=True)

def quick_access_section():
    """Render quick access section with Turbo Air categories"""
    st.markdown("""
    <div class="quick-access">
        <div class="quick-access-title">Quick Access</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick access items for main Turbo Air categories
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
    """Render subcategory list as buttons"""
    st.markdown(f"### Select {parent_category} Type")
    
    for subcat in subcategories:
        if st.button(
            subcat,
            key=f"subcat_{subcat}",
            use_container_width=True
        ):
            st.session_state.selected_subcategory = subcat
            st.rerun()
        
        # Add custom styling for subcategory buttons
        st.markdown(f"""
        <style>
        div[data-testid="stButton"] button[kind="secondary"] {{
            background-color: {COLORS['surface']};
            border: 1px solid {COLORS['border']};
            color: {COLORS['text_primary']};
            margin-bottom: 8px;
        }}
        div[data-testid="stButton"] button[kind="secondary"]:hover {{
            background-color: {COLORS['primary']};
            color: white;
            border-color: {COLORS['primary']};
        }}
        </style>
        """, unsafe_allow_html=True)

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
        <div class="nav-item {active_class}" onclick="window.location.hash='#{item["page"]}'">
            <div class="nav-icon">{item["icon"]}</div>
            <div class="nav-label">{item["label"]}</div>
        </div>
        '''
    nav_html += '</div>'
    
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Handle navigation with buttons (hidden)
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
    # Try to load thumbnail
    thumbnail_path = f"pdf_screenshots/{product.get('sku', '')}/{product.get('sku', '')} P.1.png"
    
    if os.path.exists(thumbnail_path):
        # Load and display actual thumbnail
        try:
            from PIL import Image
            img = Image.open(thumbnail_path)
            # Create thumbnail
            img.thumbnail((60, 60))
            # Save to temp location for display
            temp_path = f"temp_thumb_{product.get('sku', '')}.png"
            img.save(temp_path)
            
            item_html = f"""
            <div class="product-item">
                <div class="product-thumbnail">
                    <img src="{temp_path}" alt="{product.get('sku', '')}">
                </div>
                <div class="product-info">
                    <p class="product-name">{product.get('sku', 'Unknown')}</p>
                    <p class="product-model">{product.get('product_type', 'Model')}</p>
                </div>
                <div class="product-price">${product.get('price', 0):,.2f}</div>
            </div>
            """
        except:
            # Fallback if image processing fails
            item_html = f"""
            <div class="product-item">
                <div class="product-info" style="margin-left: 0;">
                    <p class="product-name">{product.get('sku', 'Unknown')}</p>
                    <p class="product-model">{product.get('product_type', 'Model')}</p>
                </div>
                <div class="product-price">${product.get('price', 0):,.2f}</div>
            </div>
            """
    else:
        # No thumbnail available
        item_html = f"""
        <div class="product-item">
            <div class="product-info" style="margin-left: 0;">
                <p class="product-name">{product.get('sku', 'Unknown')}</p>
                <p class="product-model">{product.get('product_type', 'Model')}</p>
            </div>
            <div class="product-price">${product.get('price', 0):,.2f}</div>
        </div>
        """
    
    return item_html

def filter_row():
    """Render filter row with dropdowns"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Main categories
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

def mobile_button(label: str, variant: str = "primary", key: str = None):
    """Render mobile-style button"""
    if variant == "primary":
        if st.button(label, key=key, use_container_width=True):
            return True
    else:
        if st.button(label, key=key, use_container_width=True):
            return True
    return False

def cart_item(product: Dict, quantity: int, item_id: str):
    """Render cart item with quantity controls"""
    col1, col2, col3, col4 = st.columns([1, 3, 2, 1])
    
    with col1:
        # Product thumbnail
        st.markdown(f'<div class="product-thumbnail"></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"**{product.get('sku', 'Unknown')}**")
        st.caption(product.get('product_type', ''))
    
    with col3:
        # Quantity controls
        q_col1, q_col2, q_col3 = st.columns([1, 1, 1])
        with q_col1:
            if st.button("-", key=f"minus_{item_id}"):
                return max(1, quantity - 1)
        with q_col2:
            st.markdown(f"<p style='text-align: center; margin: 0;'>{quantity}</p>", unsafe_allow_html=True)
        with q_col3:
            if st.button("+", key=f"plus_{item_id}"):
                return quantity + 1
    
    with col4:
        st.markdown(f"**${product.get('price', 0) * quantity:,.2f}**")
    
    return quantity

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