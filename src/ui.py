"""
UI Components for Turbo Air Equipment Viewer
Fixed with responsive design for desktop, tablet, and mobile
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
    """Apply responsive CSS styling for all device sizes"""
    css = f"""
    <style>
    /* Reset and base styles */
    * {{
        margin: 0;
        box-sizing: border-box;
    }}
    
    html, body {{
        background-color: #ffffff !important;
    }}
    
    .stApp {{
        background-color: #ffffff !important;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    }}
    
    /* Ensure main content has white background */
    .main {{
        background-color: #ffffff !important;
    }}
    
    [data-testid="stAppViewContainer"] {{
        background-color: #ffffff !important;
    }}
    
    [data-testid="stMain"] {{
        background-color: #ffffff !important;
    }}
    
    /* Hide Streamlit elements */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    .stDeployButton {{display: none;}}
    
    /* Remove default Streamlit padding */
    .main {{
        padding: 0 !important;
        margin-bottom: 90px; /* Space for bottom nav + console */
    }}
    
    .block-container {{
        padding: 0 !important;
        max-width: 100% !important;
    }}
    
    /* Search container */
    .search-container {{
        padding: 12px 16px;
        background: {COLORS['background']};
        border-bottom: 1px solid {COLORS['divider']};
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
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
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
    
    /* Product list styling */
    .product-list-header {{
        display: grid;
        grid-template-columns: 80px 1fr 100px 120px 80px;
        gap: 8px;
        align-items: center;
        padding: 8px 12px;
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
        grid-template-columns: 80px 1fr 100px 120px 80px;
        gap: 8px;
        align-items: center;
        padding: 12px;
        border-bottom: 1px solid {COLORS['divider']};
        background: {COLORS['card']};
        min-height: 80px;
        transition: background 0.2s ease;
    }}
    
    .product-row:hover {{
        background: {COLORS['surface']};
    }}
    
    .product-image-compact {{
        width: 70px;
        height: 70px;
        background: {COLORS['surface']};
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        font-size: 12px;
        color: {COLORS['text_secondary']};
        border: 1px solid {COLORS['divider']};
    }}
    
    .product-image-compact img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        padding: 4px;
    }}
    
    .product-info {{
        display: flex;
        flex-direction: column;
        gap: 4px;
    }}
    
    .product-sku {{
        font-weight: 600;
        color: {COLORS['text_primary']};
        font-size: 14px;
    }}
    
    .product-desc {{
        color: {COLORS['text_secondary']};
        font-size: 12px;
        line-height: 1.4;
    }}
    
    .product-price-compact {{
        font-weight: 600;
        color: {COLORS['text_primary']};
        text-align: right;
        font-size: 15px;
    }}
    
    .view-details-link {{
        color: {COLORS['primary']};
        font-size: 13px;
        text-decoration: underline;
        cursor: pointer;
        text-align: center;
    }}
    
    .view-details-link:hover {{
        color: #0066E0;
    }}
    
    /* Quantity controls */
    .quantity-controls {{
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 8px;
    }}
    
    .qty-btn {{
        width: 24px;
        height: 24px;
        border-radius: 4px;
        background: {COLORS['primary']};
        color: white;
        border: none;
        font-size: 16px;
        font-weight: bold;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
    }}
    
    .qty-btn:hover {{
        background: #0066E0;
        transform: scale(1.1);
    }}
    
    .qty-btn:disabled {{
        background: {COLORS['border']};
        cursor: not-allowed;
        transform: none;
    }}
    
    .qty-value {{
        font-size: 14px;
        font-weight: 500;
        min-width: 20px;
        text-align: center;
        color: {COLORS['text_primary']};
    }}
    
    /* Product details expansion */
    .product-details {{
        grid-column: 1 / -1;
        padding: 20px;
        background: {COLORS['surface']};
        border-top: 1px solid {COLORS['divider']};
        margin: 0 -12px;
    }}
    
    .details-grid {{
        display: grid;
        grid-template-columns: 200px 1fr;
        gap: 20px;
        align-items: start;
    }}
    
    .details-image {{
        width: 100%;
        height: 200px;
        background: white;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        border: 1px solid {COLORS['divider']};
    }}
    
    .details-image img {{
        width: 100%;
        height: 100%;
        object-fit: contain;
        padding: 8px;
    }}
    
    .details-info h3 {{
        font-size: 18px;
        margin-bottom: 8px;
        color: {COLORS['text_primary']};
    }}
    
    .details-info p {{
        font-size: 14px;
        color: {COLORS['text_secondary']};
        margin-bottom: 16px;
    }}
    
    .specs-grid {{
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 12px;
    }}
    
    .spec-item {{
        font-size: 13px;
    }}
    
    .spec-label {{
        font-weight: 600;
        color: {COLORS['text_primary']};
    }}
    
    .spec-value {{
        color: {COLORS['text_secondary']};
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
        transition: all 0.2s ease;
    }}
    
    .recent-item:hover {{
        background: {COLORS['card']};
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
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
        transition: all 0.2s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
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
        transition: all 0.2s ease;
    }}
    
    .primary-button:hover {{
        background: #0066E0;
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,122,255,0.3);
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
        transition: all 0.2s ease;
    }}
    
    .export-button:hover {{
        background: {COLORS['card']};
        transform: translateY(-1px);
    }}
    
    .export-button.primary {{
        background: {COLORS['primary']};
        color: white;
        border: none;
    }}
    
    .export-button.primary:hover {{
        background: #0066E0;
    }}
    
    /* Floating cart button */
    .floating-cart {{
        position: fixed;
        bottom: 100px; /* Adjusted for bottom nav + console */
        right: 20px;
        background: {COLORS['primary']};
        color: white;
        width: 56px;
        height: 56px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        cursor: pointer;
        z-index: 999;
        transition: all 0.2s ease;
    }}
    
    .floating-cart:hover {{
        transform: scale(1.1);
        box-shadow: 0 6px 16px rgba(0,0,0,0.2);
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
    
    /* Updated responsive styles for search container */
    @media (min-width: 768px) and (max-width: 1024px) {{
        .category-row {{
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
        }}
        
        .content-area {{
            max-width: 100%;
            padding: 24px;
        }}
        
        .metrics-grid {{
            grid-template-columns: repeat(2, 1fr);
            gap: 16px;
        }}
        
        .product-row, .product-list-header {{
            grid-template-columns: 100px 1fr 120px 140px 100px;
            padding: 16px;
        }}
        
        .product-image-compact {{
            width: 90px;
            height: 90px;
        }}
        
        .search-container {{
            padding: 10px 24px;
        }}
        
        .floating-cart {{
            bottom: 100px; /* Adjusted for bottom nav + console */
        }}
    }}
    
    /* Desktop Responsive (1024px+) */
    @media (min-width: 1024px) {{
        .category-row {{
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        
        .content-area {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 32px;
        }}
        
        .metrics-grid {{
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
        }}
        
        .product-row, .product-list-header {{
            grid-template-columns: 120px 1fr 140px 160px 120px;
            padding: 20px 24px;
        }}
        
        .product-image-compact {{
            width: 100px;
            height: 100px;
        }}
        
        .product-sku {{
            font-size: 16px;
        }}
        
        .product-desc {{
            font-size: 14px;
        }}
        
        .product-price-compact {{
            font-size: 16px;
        }}
        
        /* Show desktop navigation */
        .main {{
            margin-bottom: 30px; /* Only console on desktop */
        }}
        
        .search-container {{
            padding: 12px 32px;
            background: {COLORS['surface']};
            margin-bottom: 20px;
        }}
        
        .category-card {{
            padding: 24px;
        }}
        
        .category-icon {{
            font-size: 40px;
            margin-bottom: 12px;
        }}
        
        .category-name {{
            font-size: 16px;
        }}
        
        .category-count {{
            font-size: 14px;
        }}
        
        .floating-cart {{
            bottom: 50px; /* Only console on desktop */
            right: 30px;
            width: 64px;
            height: 64px;
        }}
        
        .details-grid {{
            grid-template-columns: 300px 1fr;
            gap: 30px;
        }}
        
        .details-image {{
            height: 300px;
        }}
    }}
    
    /* Fix for Streamlit container width */
    section.main > div {{
        max-width: 100% !important;
    }}
    
    /* Ensure forms work properly */
    [data-testid="stForm"] {{
        background: transparent !important;
        border: none !important;
        padding: 0 !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def app_header():
    """Display app header with title - removed from individual pages"""
    pass

def search_bar_component(placeholder: str = "Search for products"):
    """Display search bar component"""
    # Create search container
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    search_key = f"search_{st.session_state.get('active_page', 'home')}"
    search_term = st.text_input(
        "Search",
        placeholder=placeholder,
        key=search_key,
        label_visibility="collapsed"
    )
    st.markdown('</div>', unsafe_allow_html=True)
    return search_term

def category_grid(categories: List[Dict[str, any]]):
    """Display category grid for search page"""
    # Responsive columns based on screen size
    cols = st.columns(2)  # Default mobile layout
    
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

def product_list_item_compact(product: Dict, cart_items: List[Dict] = None, user_id: str = None, db_manager = None) -> str:
    """Render compact product list item with quantity controls"""
    sku = product.get('sku', 'Unknown')
    description = product.get('description') or product.get('product_type', '')
    price = product.get('price', 0)
    product_id = product.get('id')
    
    # Get current quantity in cart
    current_qty = 0
    if cart_items and product_id:
        for item in cart_items:
            if item.get('product_id') == product_id:
                current_qty = item.get('quantity', 0)
                break
    
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
    
    # Build the HTML
    html = f"""
    <div class="product-row">
        {image_html}
        <div class="product-info">
            <div class="product-sku">{sku}</div>
            <div class="product-desc">{description}</div>
        </div>
        <div class="view-details-link">View Details</div>
        <div class="product-price-compact">${price:,.2f}</div>
        <div class="quantity-controls">
            <button class="qty-btn" id="minus_{product_id}" {'disabled' if current_qty == 0 else ''}>−</button>
            <span class="qty-value">{current_qty}</span>
            <button class="qty-btn" id="plus_{product_id}">+</button>
        </div>
    </div>
    """
    
    return html

def product_details_expanded(product: Dict) -> str:
    """Render expanded product details section"""
    sku = product.get('sku', 'Unknown')
    description = product.get('description') or product.get('product_type', '')
    price = product.get('price', 0)
    
    # Get image
    image_html = '<div class="details-image">📷</div>'
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
            <div class="details-image">
                <img src="data:image/png;base64,{image_base64}" alt="{sku}">
            </div>
            '''
            break
    
    # Build specifications
    specs_html = ""
    specs = {
        "Category": product.get('category', '-'),
        "Subcategory": product.get('subcategory', '-'),
        "Capacity": product.get('capacity', '-'),
        "Dimensions": product.get('dimensions', '-'),
        "Weight": product.get('weight', '-'),
        "Voltage": product.get('voltage', '-'),
        "Temperature Range": product.get('temperature_range', '-'),
        "Refrigerant": product.get('refrigerant', '-')
    }
    
    specs_items = []
    for key, value in specs.items():
        if value and value != '-':
            specs_items.append(f'''
            <div class="spec-item">
                <span class="spec-label">{key}:</span> <span class="spec-value">{value}</span>
            </div>
            ''')
    
    if specs_items:
        specs_html = f'<div class="specs-grid">{"".join(specs_items)}</div>'
    
    html = f"""
    <div class="product-details">
        <div class="details-grid">
            {image_html}
            <div class="details-info">
                <h3>{sku}</h3>
                <p>{description}</p>
                <div style="font-size: 24px; font-weight: bold; color: {COLORS['primary']}; margin-bottom: 16px;">
                    ${price:,.2f}
                </div>
                {specs_html}
            </div>
        </div>
    </div>
    """
    
    return html

def product_list_item(product: Dict) -> str:
    """Render product list item with image"""
    # Redirect to compact version
    return product_list_item_compact(product)

def recent_searches_section(searches: List[str]):
    """Display recent searches section"""
    if searches:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        ">
            <h3 style="
                font-size: 18px;
                font-weight: 600;
                color: #333;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 2px solid #007AFF;
            ">Recent Searches</h3>
        </div>
        """, unsafe_allow_html=True)
        
        for search in searches[:5]:
            col1, col2 = st.columns([10, 1])
            with col1:
                if st.button(f"🔍 {search}", key=f"recent_{search}", use_container_width=True):
                    st.session_state.search_term = search
                    st.session_state.active_page = 'search'
                    st.rerun()

def recent_quotes_section(quotes: List[Dict]):
    """Display recent quotes section"""
    if quotes:
        st.markdown("""
        <div style="
            background: #f8f9fa;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #e9ecef;
        ">
            <h3 style="
                font-size: 18px;
                font-weight: 600;
                color: #333;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 2px solid #007AFF;
            ">Recent Quotes</h3>
        </div>
        """, unsafe_allow_html=True)
        
        for quote in quotes[:5]:
            quote_info = f"#{quote['quote_number']} - ${quote['total_amount']:,.2f}"
            if st.button(quote_info, key=f"quote_{quote['id']}", use_container_width=True):
                st.session_state.selected_quote = quote['id']
                st.session_state.active_page = 'profile'
                st.rerun()

def metrics_section(metrics: Dict):
    """Display metrics grid"""
    st.markdown("""
    <div style="
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 16px;
        margin-bottom: 24px;
    ">
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        ">
            <div style="font-size: 36px; font-weight: 700; margin-bottom: 8px;">
                """ + str(metrics.get('total_clients', 0)) + """
            </div>
            <div style="font-size: 14px; opacity: 0.9;">Total Clients</div>
        </div>
        <div style="
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            color: white;
            box-shadow: 0 4px 12px rgba(245, 87, 108, 0.3);
        ">
            <div style="font-size: 36px; font-weight: 700; margin-bottom: 8px;">
                """ + str(metrics.get('total_quotes', 0)) + """
            </div>
            <div style="font-size: 14px; opacity: 0.9;">Total Quotes</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def cart_item_component(item: Dict, db_manager=None):
    """Display cart item with quantity controls"""
    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
    
    with col1:
        st.markdown(f"""
        <div class="cart-item-info">
            <div class="cart-item-name">{item['sku']}</div>
            <div class="cart-item-model">{truncate_text(item.get('product_type', 'N/A'), 30)}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        col_minus, col_qty, col_plus = st.columns([1, 2, 1])
        with col_minus:
            if st.button("−", key=f"cart_minus_{item['id']}"):
                if db_manager and item['quantity'] > 1:
                    db_manager.update_cart_quantity(item['id'], item['quantity'] - 1)
                    st.rerun()
        with col_qty:
            st.markdown(f"<div style='text-align: center; font-size: 16px; font-weight: 500;'>{item['quantity']}</div>", unsafe_allow_html=True)
        with col_plus:
            if st.button("+", key=f"cart_plus_{item['id']}"):
                if db_manager:
                    db_manager.update_cart_quantity(item['id'], item['quantity'] + 1)
                    st.rerun()
    
    with col3:
        st.markdown(f"<div style='text-align: right; font-size: 14px; color: #666;'>${item['price']:,.2f}</div>", unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"<div style='text-align: right; font-weight: 600; font-size: 15px;'>${item['price'] * item['quantity']:,.2f}</div>", unsafe_allow_html=True)
        if st.button("🗑️", key=f"remove_{item['id']}", help="Remove from cart"):
            if db_manager:
                db_manager.remove_from_cart(item['id'])
                st.rerun()

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
        <h3 style="
            margin-bottom: 8px; 
            color: #212529;
            font-size: 24px;
            font-weight: 600;
        ">{title}</h3>
        <p style="
            color: #6c757d;
            font-size: 16px;
            line-height: 1.5;
        ">{description}</p>
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