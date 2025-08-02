"""
UI Components for Turbo Air Equipment Viewer
Fixed with compact list view and proper navigation
"""

import streamlit as st
import os
from typing import Dict, List, Optional, Callable
import base64

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

# New Turbo Air Categories Structure
TURBO_AIR_CATEGORIES = {
    "REACH-IN REFRIGERATION": {
        "icon": "❄️",
        "series": ["PRO", "TSF", "M3R", "M3F", "M3H"],
        "types": ["Refrigerators", "Freezers", "Dual Temperature"]
    },
    "FOOD PREP TABLES": {
        "icon": "🥗",
        "series": ["PST", "TST", "MST", "TPR"],
        "types": ["Sandwich/Salad Prep", "Pizza Prep"]
    },
    "UNDERCOUNTER REFRIGERATION": {
        "icon": "📦",
        "series": ["MUR", "PUR", "EUR"],
        "types": ["Refrigerators", "Freezers"]
    },
    "WORKTOP REFRIGERATION": {
        "icon": "🔧",
        "series": ["TWR", "PWR"],
        "types": ["Refrigerators", "Freezers"]
    },
    "GLASS DOOR MERCHANDISERS": {
        "icon": "🥤",
        "series": ["TGM", "TGF"],
        "types": ["Refrigerators", "Freezers"]
    },
    "DISPLAY CASES": {
        "icon": "🍰",
        "series": ["Various"],
        "types": ["Open Display", "Deli Cases", "Bakery Cases"]
    },
    "UNDERBAR EQUIPMENT": {
        "icon": "🍺",
        "series": ["Various"],
        "types": ["Bottle Coolers", "Beer Dispensers", "Back Bars"]
    },
    "MILK COOLERS": {
        "icon": "🥛",
        "series": ["TMC", "TMW"],
        "types": ["Milk Coolers"]
    }
}

def get_image_base64(image_path):
    """Convert image to base64 for inline display"""
    try:
        if os.path.exists(image_path):
            with open(image_path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except:
        pass
    return None

def apply_mobile_css():
    """Apply mobile-first CSS styling with compact list view"""
    css = f"""
    <style>
    /* Reset and base styles */
    * {{
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }}
    
    .stApp {{
        background-color: {COLORS['background']};
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    
    /* Hide Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* Remove default Streamlit padding */
    .main {{
        padding: 0 !important;
        margin-bottom: 40px; /* Further reduced space for bottom nav */
    }}
    
    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}
    
    /* Search section with padding */
    .search-section {{
        padding: 12px 16px; /* Added horizontal padding */
        background: {COLORS['background']};
        border-bottom: 1px solid {COLORS['divider']};
    }}
    
    .search-title {{
        font-size: 18px;
        font-weight: 600;
        color: {COLORS['text_primary']};
        margin-bottom: 10px;
    }}
    
    /* Content area */
    .content-area {{
        padding: 16px;
        min-height: calc(100vh - 120px);
    }}
    
    /* Category cards for search */
    .category-row {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-bottom: 20px;
    }}
    
    .category-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['divider']};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .category-card:hover {{
        background: {COLORS['surface']};
        transform: translateY(-2px);
    }}
    
    .category-icon {{
        font-size: 32px;
        margin-bottom: 8px;
    }}
    
    .category-name {{
        font-size: 14px;
        font-weight: 500;
        color: {COLORS['text_primary']};
    }}
    
    .category-count {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
        margin-top: 4px;
    }}
    
    /* Ultra-compact product list styling - True Excel-like with images */
    .product-list-header {{
        display: grid;
        grid-template-columns: 45px 110px 1fr 90px;
        gap: 8px;
        align-items: center;
        padding: 6px 8px;
        background: #f0f0f0;
        border-bottom: 2px solid {COLORS['divider']};
        font-weight: bold;
        font-size: 13px;
        position: sticky;
        top: 0;
        z-index: 10;
    }}
    
    .product-row {{
        display: grid;
        grid-template-columns: 45px 110px 1fr 90px;
        gap: 8px;
        align-items: center;
        padding: 4px 8px;
        border-bottom: 1px solid {COLORS['divider']};
        background: {COLORS['card']};
        min-height: 36px;
    }}
    
    .product-row:hover {{
        background: {COLORS['surface']};
    }}
    
    .product-image-compact {{
        width: 40px;
        height: 32px;
        background: {COLORS['surface']};
        border-radius: 3px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        font-size: 9px;
        color: {COLORS['text_secondary']};
    }}
    
    .product-image-compact img {{
        width: 100%;
        height: 100%;
        object-fit: cover;
    }}
    
    .product-sku {{
        font-weight: 600;
        color: {COLORS['text_primary']};
        font-size: 12px;
    }}
    
    .product-desc {{
        color: {COLORS['text_secondary']};
        font-size: 12px;
        overflow: hidden;
        text-overflow: ellipsis;
        white-space: nowrap;
    }}
    
    .product-price-compact {{
        font-weight: 600;
        color: {COLORS['text_primary']};
        text-align: right;
        font-size: 12px;
    }}
    
    /* Bottom navigation - ultra compact */
    .bottom-nav {{
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: {COLORS['background']};
        border-top: 1px solid {COLORS['divider']};
        display: flex;
        justify-content: space-around;
        padding: 2px 0;
        z-index: 1000;
        height: 40px; /* Further reduced height */
    }}
    
    .nav-item {{
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        flex: 1;
        padding: 1px;
        color: {COLORS['text_tertiary']};
        cursor: pointer;
        text-decoration: none;
        transition: color 0.2s ease;
    }}
    
    .nav-item.active {{
        color: {COLORS['primary']};
    }}
    
    .nav-icon {{
        font-size: 18px; /* Further reduced */
        margin-bottom: 1px;
    }}
    
    .nav-label {{
        font-size: 9px; /* Further reduced */
        font-weight: 500;
    }}
    
    /* Recent items styling */
    .recent-section {{
        margin-bottom: 24px;
    }}
    
    .section-title {{
        font-size: 18px;
        font-weight: 600;
        color: {COLORS['text_primary']};
        margin-bottom: 12px;
    }}
    
    .recent-item {{
        padding: 12px;
        background: {COLORS['surface']};
        border-radius: 10px;
        margin-bottom: 8px;
        cursor: pointer;
    }}
    
    .recent-item:hover {{
        background: {COLORS['card']};
    }}
    
    /* Metric cards */
    .metrics-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
        margin-bottom: 24px;
    }}
    
    .metric-card {{
        background: {COLORS['surface']};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }}
    
    .metric-value {{
        font-size: 32px;
        font-weight: 700;
        color: {COLORS['text_primary']};
    }}
    
    .metric-label {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
        margin-top: 4px;
    }}
    
    /* Cart styling */
    .cart-item {{
        display: flex;
        align-items: center;
        padding: 16px;
        background: {COLORS['card']};
        border-bottom: 1px solid {COLORS['divider']};
    }}
    
    .cart-item-image {{
        width: 60px;
        height: 60px;
        background: {COLORS['surface']};
        border-radius: 8px;
        margin-right: 12px;
    }}
    
    .cart-item-info {{
        flex: 1;
    }}
    
    .cart-item-name {{
        font-size: 16px;
        font-weight: 500;
        color: {COLORS['text_primary']};
    }}
    
    .cart-item-model {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
    }}
    
    .quantity-controls {{
        display: flex;
        align-items: center;
        gap: 16px;
    }}
    
    .quantity-btn {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        background: {COLORS['surface']};
        border: none;
        font-size: 18px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
    }}
    
    .quantity-value {{
        font-size: 18px;
        font-weight: 500;
        min-width: 30px;
        text-align: center;
    }}
    
    /* Summary section */
    .summary-section {{
        padding: 20px;
        background: {COLORS['surface']};
        border-radius: 12px;
        margin: 16px;
    }}
    
    .summary-row {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 12px;
        font-size: 16px;
    }}
    
    .summary-row.total {{
        font-weight: 600;
        font-size: 18px;
        padding-top: 12px;
        border-top: 1px solid {COLORS['divider']};
    }}
    
    /* Buttons */
    .primary-button {{
        width: 100%;
        padding: 16px;
        background: {COLORS['primary']};
        color: white;
        border: none;
        border-radius: 12px;
        font-size: 16px;
        font-weight: 600;
        cursor: pointer;
        margin: 16px;
    }}
    
    .export-buttons {{
        display: flex;
        gap: 12px;
        padding: 16px;
    }}
    
    .export-button {{
        flex: 1;
        padding: 12px;
        background: {COLORS['surface']};
        border: 1px solid {COLORS['divider']};
        border-radius: 10px;
        font-size: 14px;
        font-weight: 500;
        cursor: pointer;
        text-align: center;
    }}
    
    .export-button.primary {{
        background: {COLORS['primary']};
        color: white;
        border: none;
    }}
    
    /* Floating cart button */
    .floating-cart {{
        position: fixed;
        bottom: 50px; /* Adjusted for smaller nav */
        right: 20px;
        background: {COLORS['primary']};
        color: white;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        cursor: pointer;
        z-index: 999;
    }}
    
    .cart-badge {{
        position: absolute;
        top: -5px;
        right: -5px;
        background: {COLORS['error']};
        color: white;
        min-width: 20px;
        height: 20px;
        border-radius: 10px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 12px;
        font-weight: bold;
    }}
    
    /* Action buttons row */
    .action-buttons-row {{
        display: flex;
        gap: 8px;
        padding: 4px 8px;
        background: {COLORS['card']};
    }}
    
    .action-button {{
        flex: 1;
        font-size: 11px;
        padding: 4px 8px;
        border-radius: 4px;
    }}
    
    /* Hide Streamlit specific elements */
    .stButton > button {{
        width: 100%;
        background: none;
        border: none;
        padding: 0;
    }}
    
    div[data-testid="stSidebar"] {{
        display: none;
    }}
    
    /* Responsive design */
    @media (min-width: 768px) {{
        .category-row {{
            grid-template-columns: repeat(4, 1fr);
        }}
        
        .content-area {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .metrics-grid {{
            grid-template-columns: repeat(4, 1fr);
        }}
        
        .product-row, .product-list-header {{
            grid-template-columns: 50px 140px 1fr 100px;
        }}
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def app_header():
    """Display app header with title - removed from individual pages"""
    pass

def search_bar_component(placeholder: str = "Search for products"):
    """Display search bar component with title and padding"""
    st.markdown('<div class="search-section">', unsafe_allow_html=True)
    st.markdown('<div class="search-title">Search</div>', unsafe_allow_html=True)
    search_key = f"search_{st.session_state.get('active_page', 'home')}"
    search_term = st.text_input(
        "Search",
        placeholder=placeholder,
        key=search_key,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    return search_term

def bottom_navigation():
    """Display bottom navigation bar with ultra-compact height"""
    active_page = st.session_state.get('active_page', 'home')
    
    nav_items = [
        {"icon": "🏠", "label": "Home", "page": "home"},
        {"icon": "🔍", "label": "Search", "page": "search"},
        {"icon": "🛒", "label": "Cart", "page": "cart"},
        {"icon": "👤", "label": "Profile", "page": "profile"}
    ]
    
    # Create the navigation HTML
    nav_html = '<div class="bottom-nav">'
    for item in nav_items:
        active_class = "active" if item["page"] == active_page else ""
        nav_html += f'''
        <div class="nav-item {active_class}" id="nav_{item['page']}">
            <div class="nav-icon">{item["icon"]}</div>
            <div class="nav-label">{item["label"]}</div>
        </div>
        '''
    nav_html += '</div>'
    
    st.markdown(nav_html, unsafe_allow_html=True)
    
    # Handle navigation clicks
    col1, col2, col3, col4 = st.columns(4)
    cols = [col1, col2, col3, col4]
    
    for i, item in enumerate(nav_items):
        with cols[i]:
            if st.button(
                "",
                key=f"nav_btn_{item['page']}",
                use_container_width=True,
                disabled=(item["page"] == active_page)
            ):
                st.session_state.active_page = item["page"]
                # Clear category selection when navigating away from search
                if item["page"] != "search":
                    st.session_state.selected_category = None
                st.rerun()

def category_grid(categories: List[Dict[str, any]]):
    """Display category grid for search page"""
    cols = st.columns(2)
    for i, (cat_name, cat_info) in enumerate(TURBO_AIR_CATEGORIES.items()):
        with cols[i % 2]:
            # Get product count
            count = next((c['count'] for c in categories if c['name'] == cat_name), 0)
            
            if st.button(
                f"{cat_info['icon']}\n{cat_name}\n({count} items)",
                key=f"cat_{cat_name}",
                use_container_width=True
            ):
                st.session_state.selected_category = cat_name
                st.rerun()

def product_list_item_compact(product: Dict) -> str:
    """Render ultra-compact product list item with working images"""
    sku = product.get('sku', 'Unknown')
    description = product.get('description') or product.get('product_type', '')
    price = product.get('price', 0)
    
    # Get image path - check multiple possible locations
    image_html = '<div class="product-image-compact">📷</div>'
    
    # Try different image paths
    possible_paths = [
        f"pdf_screenshots/{sku}/{sku} P.1.png",
        f"pdf_screenshots/{sku}/{sku}_P.1.png",
        f"pdf_screenshots/{sku}/{sku}.png",
        f"pdf_screenshots/{sku}/page_1.png"
    ]
    
    for image_path in possible_paths:
        image_base64 = get_image_base64(image_path)
        if image_base64:
            image_html = f'''
            <div class="product-image-compact">
                <img src="data:image/png;base64,{image_base64}" alt="{sku}">
            </div>
            '''
            break
    
    return f"""
    <div class="product-row">
        {image_html}
        <div class="product-sku">{sku}</div>
        <div class="product-desc">{truncate_text(description, 50)}</div>
        <div class="product-price-compact">${price:,.2f}</div>
    </div>
    """

def product_list_item(product: Dict) -> str:
    """Render product list item with image"""
    # Redirect to compact version
    return product_list_item_compact(product)

def recent_searches_section(searches: List[str]):
    """Display recent searches section"""
    if searches:
        st.markdown('<div class="recent-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Recent Searches</h3>', unsafe_allow_html=True)
        
        for search in searches[:5]:
            if st.button(f"🔍 {search}", key=f"recent_{search}", use_container_width=True):
                st.session_state.search_term = search
                st.session_state.active_page = 'search'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def recent_quotes_section(quotes: List[Dict]):
    """Display recent quotes section"""
    if quotes:
        st.markdown('<div class="recent-section">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Recent Quotes</h3>', unsafe_allow_html=True)
        
        for quote in quotes[:5]:
            quote_info = f"#{quote['quote_number']} - ${quote['total_amount']:,.2f}"
            if st.button(quote_info, key=f"quote_{quote['id']}", use_container_width=True):
                st.session_state.selected_quote = quote['id']
                st.session_state.active_page = 'profile'
                st.rerun()
        
        st.markdown('</div>', unsafe_allow_html=True)

def metrics_section(metrics: Dict):
    """Display metrics grid"""
    st.markdown('<div class="metrics-grid">', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics.get('total_clients', 0)}</div>
            <div class="metric-label">Total Clients</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics.get('total_quotes', 0)}</div>
            <div class="metric-label">Total Quotes</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

def cart_item_component(item: Dict, db_manager=None):
    """Display cart item with quantity controls"""
    col1, col2, col3 = st.columns([3, 2, 1])
    
    with col1:
        st.markdown(f"""
        <div class="cart-item-info">
            <div class="cart-item-name">{item['sku']}</div>
            <div class="cart-item-model">{truncate_text(item.get('product_type', 'N/A'), 30)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        col_minus, col_qty, col_plus = st.columns([1, 1, 1])
        with col_minus:
            if st.button("−", key=f"minus_{item['id']}"):
                if db_manager and item['quantity'] > 1:
                    db_manager.update_cart_quantity(item['id'], item['quantity'] - 1)
                    st.rerun()
        with col_qty:
            st.markdown(f"<div class='quantity-value'>{item['quantity']}</div>", unsafe_allow_html=True)
        with col_plus:
            if st.button("+", key=f"plus_{item['id']}"):
                if db_manager:
                    db_manager.update_cart_quantity(item['id'], item['quantity'] + 1)
                    st.rerun()
    
    with col3:
        st.markdown(f"<div class='product-price-compact'>${item['price'] * item['quantity']:,.2f}</div>", unsafe_allow_html=True)

def cart_summary(subtotal: float, tax_rate: float = 0.08):
    """Display cart summary"""
    tax = subtotal * tax_rate
    total = subtotal + tax
    
    st.markdown(f"""
    <div class="summary-section">
        <div class="summary-row">
            <span>Subtotal</span>
            <span>${subtotal:,.2f}</span>
        </div>
        <div class="summary-row">
            <span>Tax ({tax_rate*100:.0f}%)</span>
            <span>${tax:,.2f}</span>
        </div>
        <div class="summary-row total">
            <span>Total</span>
            <span>${total:,.2f}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    return total

def floating_cart_button(cart_count: int):
    """Display floating cart button with count"""
    cart_html = f"""
    <div class="floating-cart" onclick="document.getElementById('floating_cart_btn').click()">
        🛒
        <div class="cart-badge">{cart_count}</div>
    </div>
    """
    st.markdown(cart_html, unsafe_allow_html=True)
    
    # Hidden button for click handling
    if st.button("", key="floating_cart_btn", help="Go to cart", disabled=False, 
                 type="secondary", use_container_width=False):
        st.session_state.active_page = 'cart'
        st.rerun()

def quote_export_buttons():
    """Display quote export buttons"""
    st.markdown("""
    <div class="export-buttons">
        <div class="export-button">Export as Excel</div>
        <div class="export-button primary">Export as PDF</div>
    </div>
    """, unsafe_allow_html=True)

def empty_state(icon: str, title: str, description: str):
    """Display empty state"""
    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 16px;">{icon}</div>
        <h3 style="margin-bottom: 8px; color: {COLORS['text_primary']};">{title}</h3>
        <p style="color: {COLORS['text_secondary']};">{description}</p>
    </div>
    """, unsafe_allow_html=True)

def format_price(price: float) -> str:
    """Format price for display"""
    return f"${price:,.2f}"

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text to specified length"""
    if not text:
        return ""
    return text[:max_length] + "..." if len(text) > max_length else text