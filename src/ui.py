"""
UI Components for Turbo Air Equipment Viewer
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
    """Apply responsive CSS styling for all device sizes - Streamlit native compatible"""
    css = f"""
    <style>
    /* Reset and base styles */
    * {{
        box-sizing: border-box;
    }}
    
    html, body {{
        background-color: #ffffff !important;
    }}
    
    .stApp {{
        background-color: #ffffff !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    
    /* Hide Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* Main layout */
    .main {{
        background-color: #ffffff !important;
        padding: 1rem !important;
    }}
    
    .block-container {{
        padding-top: 1rem !important;
        max-width: 100% !important;
    }}
    
    /* Button styling */
    .stButton > button {{
        width: 100%;
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px;
        padding: 12px 16px;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .stButton > button:hover {{
        background-color: #f5f5f5 !important;
        transform: translateY(-1px);
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }}
    
    /* Primary button styling */
    .stButton > button[kind="primary"] {{
        background-color: #007AFF !important;
        color: white !important;
        border: none !important;
    }}
    
    .stButton > button[kind="primary"]:hover {{
        background-color: #0066E0 !important;
    }}
    
    /* Category card styling */
    .category-card {{
        background: {COLORS['card']};
        border: 1px solid {COLORS['divider']};
        border-radius: 12px;
        padding: 16px;
        text-align: center;
        margin-bottom: 12px;
        transition: all 0.2s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }}
    
    .category-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }}
    
    .category-icon {{
        font-size: 32px;
        margin-bottom: 8px;
        display: block;
    }}
    
    .category-name {{
        font-size: 14px;
        font-weight: 500;
        color: {COLORS['text_primary']};
        margin-bottom: 4px;
    }}
    
    .category-count {{
        font-size: 12px;
        color: {COLORS['text_secondary']};
    }}
    
    /* Metric cards */
    .metric-card {{
        background: {COLORS['surface']};
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        margin-bottom: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    }}
    
    .metric-value {{
        font-size: 32px;
        font-weight: 700;
        color: {COLORS['text_primary']};
        margin-bottom: 4px;
    }}
    
    .metric-label {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
    }}
    
    /* Recent items styling */
    .recent-section {{
        background: #f8f9fa;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        border: 1px solid #e9ecef;
    }}
    
    .section-title {{
        font-size: 18px;
        font-weight: 600;
        color: #333;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 2px solid #007AFF;
    }}
    
    /* Product styling */
    .product-row {{
        display: flex;
        align-items: center;
        padding: 12px;
        border-bottom: 1px solid {COLORS['divider']};
        background: {COLORS['card']};
    }}
    
    .product-image-compact {{
        width: 60px;
        height: 60px;
        background: {COLORS['surface']};
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        margin-right: 12px;
        font-size: 12px;
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['divider']};
    }}
    
    .product-info {{
        flex: 1;
    }}
    
    .product-sku {{
        font-weight: 600;
        color: {COLORS['text_primary']};
        font-size: 14px;
    }}
    
    .product-desc {{
        color: {COLORS['text_secondary']};
        font-size: 12px;
    }}
    
    /* Cart styling */
    .cart-summary {{
        background: {COLORS['surface']};
        border-radius: 12px;
        padding: 20px;
        margin: 16px 0;
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
    
    /* Navigation tabs */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: {COLORS['surface']};
        padding: 8px;
        border-radius: 12px;
        margin-bottom: 20px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: {COLORS['text_secondary']};
        font-weight: 500;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {COLORS['primary']} !important;
        color: white !important;
    }}
    
    /* Responsive design */
    @media (min-width: 768px) {{
        .category-row {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
    }}
    
    @media (min-width: 1024px) {{
        .category-row {{
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        
        .metrics-grid {{
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        
        .main {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 2rem !important;
        }}
    }}
    
    /* Hide sidebar */
    section[data-testid="stSidebar"] {{
        display: none;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def search_bar_component(placeholder: str = "Search for products"):
    """Display search bar component"""
    search_term = st.text_input(
        "Search",
        placeholder=placeholder,
        key="main_search"
    )
    return search_term

def category_grid(categories: List[Dict[str, any]]):
    """Display category grid as single clickable buttons"""
    if not categories:
        st.info("No categories available")
        return
    
    # Create responsive grid using columns
    num_cols = 2  # Mobile first
    if st.session_state.get('screen_width', 400) > 768:
        num_cols = 3
    if st.session_state.get('screen_width', 400) > 1024:
        num_cols = 4
    
    # Display categories in grid
    for i in range(0, len(categories), num_cols):
        cols = st.columns(num_cols)
        for j in range(num_cols):
            if i + j < len(categories):
                category = categories[i + j]
                with cols[j]:
                    # Single button with all category info
                    button_text = f"{category.get('icon', '📦')}\n\n{category['name']}\n\n({category.get('count', 0)} items)"
                    
                    if st.button(button_text, key=f"cat_btn_{category['name']}", use_container_width=True, height=120):
                        st.session_state.selected_category = category['name']
                        st.rerun()

def recent_searches_section(searches: List[str]):
    """Display recent searches section with product thumbnails"""
    if not searches:
        return
        
    # Title styling to match "My Clients"
    st.markdown("### Recent Searches")
    
    # Display recent searches with thumbnails
    cols = st.columns(min(len(searches[:5]), 3))  # Max 3 columns
    
    for i, search in enumerate(searches[:5]):
        with cols[i % len(cols)]:
            # Try to find a product image for this search term
            thumbnail_html = f'<div style="width: 80px; height: 80px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; font-size: 24px;">🔍</div>'
            
            # Try to get actual product image if search matches a SKU
            try:
                possible_paths = [
                    f"pdf_screenshots/{search.upper()}/{search.upper()} P.1.png",
                    f"pdf_screenshots/{search.upper()}/{search.upper()}_P.1.png",
                    f"pdf_screenshots/{search.upper()}/{search.upper()}.png",
                    f"pdf_screenshots/{search}/{search} P.1.png",
                    f"pdf_screenshots/{search}/{search}_P.1.png",
                    f"pdf_screenshots/{search}/{search}.png"
                ]
                
                for image_path in possible_paths:
                    image_base64 = get_image_base64(image_path)
                    if image_base64:
                        thumbnail_html = f'''
                        <div style="width: 80px; height: 80px; background: #f0f0f0; border-radius: 8px; display: flex; align-items: center; justify-content: center; margin: 0 auto 8px; overflow: hidden;">
                            <img src="data:image/png;base64,{image_base64}" style="width: 70px; height: 70px; object-fit: contain;">
                        </div>
                        '''
                        break
            except:
                pass
            
            # Display thumbnail and SKU
            st.markdown(thumbnail_html, unsafe_allow_html=True)
            
            # Button with SKU below thumbnail - make key unique with index
            if st.button(search, key=f"recent_search_{i}_{search.replace(' ', '_')}", use_container_width=True):
                # Set the search term in the main search box
                st.session_state["main_search"] = search
                st.rerun()

def recent_quotes_section(quotes: List[Dict]):
    """Display recent quotes section"""
    if not quotes:
        return
        
    st.markdown("""
    <div class="recent-section">
        <div class="section-title">Recent Quotes</div>
    </div>
    """, unsafe_allow_html=True)
    
    for quote in quotes[:5]:
        quote_info = f"#{quote['quote_number']} - ${quote['total_amount']:,.2f}"
        if st.button(quote_info, key=f"quote_{quote['id']}", use_container_width=True):
            st.session_state.selected_quote = quote['id']
            st.rerun()

def metrics_section(metrics: Dict):
    """Display metrics grid"""
    if not metrics:
        return
        
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
            <div class="metric-value">{metrics.get('total_clients', 0)}</div>
            <div class="metric-label" style="color: rgba(255,255,255,0.9);">Total Clients</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white;">
            <div class="metric-value">{metrics.get('total_quotes', 0)}</div>
            <div class="metric-label" style="color: rgba(255,255,255,0.9);">Total Quotes</div>
        </div>
        """, unsafe_allow_html=True)

def product_list_item_compact(product: Dict, cart_items: List[Dict] = None, user_id: str = None, db_manager = None) -> str:
    """Render compact product list item"""
    sku = product.get('sku', 'Unknown')
    description = product.get('description') or product.get('product_type', '')
    price = product.get('price', 0)
    
    # Get current quantity in cart
    current_qty = 0
    if cart_items:
        for item in cart_items:
            if item.get('product_id') == product.get('id'):
                current_qty = item.get('quantity', 0)
                break
    
    # Get image
    image_html = '<div class="product-image-compact">📷</div>'
    possible_paths = [
        f"pdf_screenshots/{sku}/{sku} P.1.png",
        f"pdf_screenshots/{sku}/{sku}_P.1.png",
        f"pdf_screenshots/{sku}/{sku}.png",
        f"pdf_screenshots/{sku}/page_1.png"
    ]
    
    for image_path in possible_paths:
        image_base64 = get_image_base64(image_path)
        if image_base64:
            image_html = f'<div class="product-image-compact"><img src="data:image/png;base64,{image_base64}" alt="{sku}" style="width:50px;height:50px;object-fit:contain;"></div>'
            break
    
    return f"""
    <div class="product-row">
        {image_html}
        <div class="product-info">
            <div class="product-sku">{sku}</div>
            <div class="product-desc">{description}</div>
            <div style="font-weight: 600; color: #007AFF;">${price:,.2f}</div>
        </div>
    </div>
    """

def cart_item_component(item: Dict, db_manager=None):
    """Display cart item with quantity controls"""
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        st.markdown(f"**{item['sku']}**")
        st.caption(truncate_text(item.get('product_type', 'N/A'), 30))
    
    with col2:
        col_minus, col_qty, col_plus = st.columns([1, 2, 1])
        with col_minus:
            if st.button("−", key=f"cart_minus_{item['id']}"):
                if db_manager and item['quantity'] > 1:
                    db_manager.update_cart_quantity(item['id'], item['quantity'] - 1)
                    st.rerun()
        with col_qty:
            st.markdown(f"<div style='text-align: center; font-weight: 500;'>{item['quantity']}</div>", unsafe_allow_html=True)
        with col_plus:
            if st.button("+", key=f"cart_plus_{item['id']}"):
                if db_manager:
                    db_manager.update_cart_quantity(item['id'], item['quantity'] + 1)
                    st.rerun()
    
    with col3:
        st.markdown(f"${item['price']:,.2f}")
    
    with col4:
        st.markdown(f"**${item['price'] * item['quantity']:,.2f}**")
        if st.button("🗑️", key=f"remove_{item['id']}", help="Remove from cart"):
            if db_manager:
                db_manager.remove_from_cart(item['id'])
                st.rerun()

def cart_summary(subtotal: float, tax_rate: float = 0.08):
    """Display cart summary"""
    tax = subtotal * tax_rate
    total = subtotal + tax
    
    st.markdown(f"""
    <div class="cart-summary">
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

def empty_state(icon: str, title: str, description: str):
    """Display empty state"""
    st.markdown(f"""
    <div style="
        text-align: center; 
        padding: 60px 20px;
        background: #f8f9fa;
        border-radius: 16px;
        margin: 20px auto;
        max-width: 400px;
        border: 2px dashed #dee2e6;
    ">
        <div style="font-size: 64px; margin-bottom: 16px;">{icon}</div>
        <h3 style="margin-bottom: 8px; color: #212529; font-size: 24px; font-weight: 600;">{title}</h3>
        <p style="color: #6c757d; font-size: 16px; line-height: 1.5;">{description}</p>
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

def bottom_navigation(active_page: str = 'home'):
    """Display bottom navigation using Streamlit tabs"""
    # This will be handled by the main app navigation
    pass

# Ensure all functions are available for import
__all__ = [
    'get_image_base64',
    'apply_mobile_css',
    'search_bar_component',
    'category_grid',
    'product_list_item_compact',
    'recent_searches_section',
    'recent_quotes_section',
    'metrics_section',
    'cart_item_component',
    'cart_summary',
    'empty_state',
    'format_price',
    'truncate_text',
    'bottom_navigation',
    'COLORS',
    'TURBO_AIR_CATEGORIES'
]