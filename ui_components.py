"""
UI Components for Turbo Air Equipment Viewer
Reusable UI components with Apple-like design
"""

import streamlit as st
import pandas as pd
from PIL import Image
import os
from typing import Dict, List, Optional
import base64

# Color palette
COLORS = {
    'turbo_blue': '#20429c',
    'turbo_red': '#d3242b',
    'success_green': '#34C759',
    'warning_yellow': '#FFF3CD',
    'background_light': '#F2F2F7',
    'background_dark': '#1C1C1E',
    'text_primary': '#000000',
    'text_secondary': '#6C6C70',
    'card_bg': '#FFFFFF',
    'border': '#E5E5EA'
}

def apply_custom_css():
    """Apply custom CSS for Apple-like design"""
    css = f"""
    <style>
    /* Global Styles */
    .stApp {{
        background-color: {COLORS['background_light']};
    }}
    
    /* Typography */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {{
        font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }}
    
    /* Card Styles */
    .product-card {{
        background: {COLORS['card_bg']};
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
        cursor: pointer;
    }}
    
    .product-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(0,0,0,0.12);
    }}
    
    /* Button Styles */
    .stButton > button {{
        background: {COLORS['turbo_blue']};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .stButton > button:hover {{
        background: #1a3580;
        transform: translateY(-1px);
    }}
    
    /* Search Bar */
    .search-container {{
        background: #F0F0F5;
        border-radius: 12px;
        padding: 12px 16px;
        margin-bottom: 20px;
    }}
    
    .search-container input {{
        border: none;
        background: transparent;
        font-size: 16px;
        width: 100%;
        outline: none;
    }}
    
    /* Category Cards */
    .category-card {{
        background: white;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        border: 1px solid {COLORS['border']};
    }}
    
    .category-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        border-color: {COLORS['turbo_blue']};
    }}
    
    /* Success Animation */
    @keyframes success-pulse {{
        0% {{ transform: scale(1); opacity: 1; }}
        50% {{ transform: scale(1.2); opacity: 0.8; }}
        100% {{ transform: scale(1); opacity: 1; }}
    }}
    
    .success-icon {{
        animation: success-pulse 0.5s ease-in-out;
    }}
    
    /* Quantity Controls */
    .quantity-controls {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    
    .quantity-btn {{
        width: 32px;
        height: 32px;
        border-radius: 50%;
        border: 1px solid {COLORS['border']};
        background: white;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        transition: all 0.2s ease;
    }}
    
    .quantity-btn:hover {{
        background: {COLORS['background_light']};
    }}
    
    /* Hide Streamlit Branding */
    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
    header {{visibility: hidden;}}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def mobile_navigation(active_page: str):
    """Simple mobile navigation using columns and buttons"""
    # Create navigation using columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("Home", key="mob_nav_home", use_container_width=True,
                    type="primary" if active_page == "home" else "secondary"):
            st.session_state.active_page = "home"
            st.rerun()
    
    with col2:
        if st.button("Search", key="mob_nav_search", use_container_width=True,
                    type="primary" if active_page in ["search", "products"] else "secondary"):
            st.session_state.active_page = "search"
            st.rerun()
    
    with col3:
        cart_label = f"Cart ({st.session_state.cart_count})" if st.session_state.cart_count > 0 else "Cart"
        if st.button(cart_label, key="mob_nav_cart", use_container_width=True,
                    type="primary" if active_page == "cart" else "secondary"):
            st.session_state.active_page = "cart"
            st.rerun()
    
    with col4:
        if st.button("Profile", key="mob_nav_profile", use_container_width=True,
                    type="primary" if active_page == "profile" else "secondary"):
            st.session_state.active_page = "profile"
            st.rerun()
    
    # Add divider after navigation
    st.divider()

def desktop_navigation(active_page: str):
    """Render desktop sidebar navigation"""
    with st.sidebar:
        st.markdown("### Navigation")
        
        # Home button
        if st.button("Home", key="desk_nav_home", use_container_width=True,
                    type="primary" if active_page == "home" else "secondary"):
            st.session_state.active_page = "home"
            st.rerun()
        
        # Products button
        if st.button("Products", key="desk_nav_products", use_container_width=True,
                    type="primary" if active_page in ["search", "products"] else "secondary"):
            st.session_state.active_page = "search"
            st.rerun()
        
        # Cart button with count
        cart_label = f"Cart ({st.session_state.cart_count})" if st.session_state.cart_count > 0 else "Cart"
        if st.button(cart_label, key="desk_nav_cart", use_container_width=True,
                    type="primary" if active_page == "cart" else "secondary"):
            st.session_state.active_page = "cart"
            st.rerun()
        
        # Profile button
        if st.button("Profile", key="desk_nav_profile", use_container_width=True,
                    type="primary" if active_page == "profile" else "secondary"):
            st.session_state.active_page = "profile"
            st.rerun()

def product_card(product: Dict, show_add_button: bool = True):
    """Render a product card"""
    # Try to load product image
    image_path = f"pdf_screenshots/{product['sku']}/page_1.png"
    
    card_html = f'''
    <div class="product-card">
        <div style="aspect-ratio: 1; overflow: hidden; border-radius: 8px; margin-bottom: 12px;">
    '''
    
    if os.path.exists(image_path):
        # Load and encode image
        with open(image_path, "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        card_html += f'<img src="data:image/png;base64,{img_data}" style="width: 100%; height: 100%; object-fit: cover;">'
    else:
        # Placeholder
        card_html += f'''
        <div style="width: 100%; height: 100%; background: {COLORS['background_light']}; 
                    display: flex; align-items: center; justify-content: center;">
            <span style="color: {COLORS['text_secondary']};">No Image</span>
        </div>
        '''
    
    card_html += f'''
        </div>
        <h4 style="margin: 0 0 4px 0; font-size: 14px;">{product['sku']}</h4>
        <p style="margin: 0 0 8px 0; color: {COLORS['text_secondary']}; font-size: 12px;">
            {product.get('product_type', 'N/A')}
        </p>
        <p style="margin: 0; font-weight: 600; color: {COLORS['turbo_blue']};">
            ${product.get('price', 0):,.2f}
        </p>
    </div>
    '''
    
    return card_html

def search_bar(placeholder: str = "Search products...") -> str:
    """Render search bar with results dropdown"""
    search_term = st.text_input("", placeholder=placeholder, key="search_input")
    
    # Show search results dropdown if there's a search term
    if search_term and len(search_term) >= 2:
        with st.container():
            # This would be populated with actual search results
            st.markdown("""
            <div style="background: white; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); 
                        padding: 8px; margin-top: 4px;">
                <!-- Search results would go here -->
            </div>
            """, unsafe_allow_html=True)
    
    return search_term

def category_grid(categories: List[Dict]):
    """Render category grid"""
    # Determine columns based on screen size
    cols = st.columns(3)  # Desktop: 3 columns
    
    for i, category in enumerate(categories):
        with cols[i % 3]:
            if st.button(
                f"{category['name']}\n({category['count']} items)",
                key=f"cat_{category['name']}",
                use_container_width=True,
                help=f"View {category['name']} products"
            ):
                st.session_state.selected_category = category['name']
                st.session_state.active_page = 'products'
                st.rerun()

def quantity_selector(current_quantity: int, item_id: int) -> int:
    """Render quantity selector with +/- buttons"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col1:
        if st.button("-", key=f"minus_{item_id}"):
            return max(1, current_quantity - 1)
    
    with col2:
        st.markdown(f"<h3 style='text-align: center; margin: 0;'>{current_quantity}</h3>", 
                   unsafe_allow_html=True)
    
    with col3:
        if st.button("+", key=f"plus_{item_id}"):
            return current_quantity + 1
    
    return current_quantity

def success_message(message: str):
    """Show success message with animation"""
    st.markdown(f"""
    <div class="success-icon" style="text-align: center; color: {COLORS['success_green']}; 
                font-size: 48px; margin: 20px 0;">
        ✓
    </div>
    <p style="text-align: center; font-weight: 500;">{message}</p>
    """, unsafe_allow_html=True)

def loading_spinner(message: str = "Loading..."):
    """Show loading spinner"""
    st.markdown(f"""
    <div style="text-align: center; padding: 40px;">
        <div class="spinner" style="border: 3px solid {COLORS['border']}; 
                border-top: 3px solid {COLORS['turbo_blue']}; 
                border-radius: 50%; width: 40px; height: 40px; 
                animation: spin 1s linear infinite; margin: 0 auto;">
        </div>
        <p style="margin-top: 16px; color: {COLORS['text_secondary']};">{message}</p>
    </div>
    <style>
    @keyframes spin {{
        0% {{ transform: rotate(0deg); }}
        100% {{ transform: rotate(360deg); }}
    }}
    </style>
    """, unsafe_allow_html=True)

def empty_state(icon: str, title: str, description: str, action_label: str = None, action_callback = None):
    """Show empty state message"""
    st.markdown(f"""
    <div style="text-align: center; padding: 60px 20px;">
        <div style="font-size: 64px; margin-bottom: 16px;">{icon}</div>
        <h3 style="margin: 0 0 8px 0;">{title}</h3>
        <p style="color: {COLORS['text_secondary']}; margin: 0 0 24px 0;">{description}</p>
    </div>
    """, unsafe_allow_html=True)
    
    if action_label and action_callback:
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button(action_label, use_container_width=True):
                action_callback()

def confirm_dialog(title: str, message: str, confirm_label: str = "Confirm", 
                  cancel_label: str = "Cancel") -> bool:
    """Show confirmation dialog"""
    with st.container():
        st.markdown(f"### {title}")
        st.markdown(message)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button(cancel_label, use_container_width=True):
                return False
        with col2:
            if st.button(confirm_label, use_container_width=True, type="primary"):
                return True
    
    return False

def format_price(price: float) -> str:
    """Format price for display"""
    return f"${price:,.2f}"

def truncate_text(text: str, max_length: int = 50) -> str:
    """Truncate text with ellipsis"""
    if len(text) > max_length:
        return text[:max_length-3] + "..."
    return text

def get_placeholder_image():
    """Get base64 encoded placeholder image"""
    # Create a simple placeholder image
    from PIL import Image, ImageDraw
    
    img = Image.new('RGB', (200, 200), color=COLORS['background_light'])
    draw = ImageDraw.Draw(img)
    
    # Draw text
    text = "No Image"
    bbox = draw.textbbox((0, 0), text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((200 - text_width) // 2, (200 - text_height) // 2)
    draw.text(position, text, fill=COLORS['text_secondary'])
    
    # Convert to base64
    from io import BytesIO
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"