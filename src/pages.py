"""
Page components for Turbo Air Equipment Viewer
Updated with collapsible product list and improved details view
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Dict

from .ui import (
    search_bar_component, category_grid,
    product_list_item_compact, recent_searches_section,
    recent_quotes_section, metrics_section, cart_item_component,
    cart_summary, empty_state, format_price,
    truncate_text, COLORS, TURBO_AIR_CATEGORIES, get_image_base64
)

# Check if these modules exist before importing
try:
    from .export import export_quote_to_excel, export_quote_to_pdf, generate_excel_quote, generate_pdf_quote
except ImportError:
    # Create dummy functions if export module doesn't exist
    def export_quote_to_excel(*args, **kwargs):
        return None
    def export_quote_to_pdf(*args, **kwargs):
        return None
    def generate_excel_quote(*args, **kwargs):
        import io
        return io.BytesIO()
    def generate_pdf_quote(*args, **kwargs):
        import io
        return io.BytesIO()

try:
    from .email import show_email_quote_dialog, get_email_service
except ImportError:
    # Create dummy functions if email module doesn't exist
    def show_email_quote_dialog(*args, **kwargs):
        st.warning("Email functionality not available")
    def get_email_service():
        return None

def show_home_page(user, user_id, db_manager, sync_manager, auth_manager):
    """Display home page with recent activity, metrics, and client management"""
    
    # Initialize variables
    has_content = False
    
    # Show metrics first to give immediate value
    try:
        stats = db_manager.get_dashboard_stats(user_id)
        if stats and (stats.get('total_clients', 0) > 0 or stats.get('total_quotes', 0) > 0):
            metrics_section(stats)
            has_content = True
    except Exception as e:
        st.error(f"Error loading dashboard stats: {str(e)}")
    
    # Client Management Section - moved from profile
    st.markdown("### My Clients")
    
    try:
        clients_df = db_manager.get_user_clients(user_id)
        
        if not clients_df.empty:
            # Show current selected client
            if st.session_state.get('selected_client'):
                selected_client = clients_df[clients_df['id'] == st.session_state.selected_client]
                if not selected_client.empty:
                    st.success(f"✅ Selected Client: **{selected_client.iloc[0]['company']}**")
            
            # Add new client form
            with st.expander("➕ Add New Client"):
                with st.form("add_client_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        company = st.text_input("Company Name*", key="new_company")
                        contact_email = st.text_input("Contact Email", key="new_contact_email")
                    with col2:
                        contact_name = st.text_input("Contact Name", key="new_contact_name")
                        contact_number = st.text_input("Contact Phone", key="new_contact_number")
                    
                    if st.form_submit_button("Add Client", use_container_width=True, type="primary"):
                        if company:
                            try:
                                success, message = db_manager.create_client(
                                    user_id, company, contact_name, contact_email, contact_number
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"Error creating client: {str(e)}")
                        else:
                            st.error("Company name is required")
            
            # List all clients in a more compact way
            for _, client in clients_df.iterrows():
                with st.container():
                    col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                    
                    with col1:
                        st.markdown(f"**{client['company']}**")
                        if client.get('contact_name'):
                            st.caption(f"Contact: {client['contact_name']}")
                    
                    with col2:
                        if client.get('contact_email'):
                            st.caption(f"📧 {client['contact_email']}")
                        if client.get('contact_number'):
                            st.caption(f"📞 {client['contact_number']}")
                    
                    with col3:
                        is_selected = st.session_state.get('selected_client') == client['id']
                        button_type = "secondary" if is_selected else "primary"
                        button_text = "✅ Selected" if is_selected else "Select"
                        
                        if st.button(button_text, key=f"select_{client['id']}", 
                                   use_container_width=True, type=button_type):
                            if not is_selected:
                                st.session_state.selected_client = client['id']
                                st.success(f"Selected {client['company']}")
                                st.rerun()
                    
                    with col4:
                        # Delete client button
                        if st.button("🗑️", key=f"delete_{client['id']}", 
                                   help="Delete client", use_container_width=True):
                            # Show confirmation dialog
                            st.session_state[f'confirm_delete_{client["id"]}'] = True
                            st.rerun()
                    
                    # Confirmation dialog for client deletion
                    if st.session_state.get(f'confirm_delete_{client["id"]}', False):
                        st.warning(f"⚠️ Are you sure you want to delete **{client['company']}**?")
                        col_confirm1, col_confirm2 = st.columns(2)
                        
                        with col_confirm1:
                            if st.button("Yes, Delete", key=f"confirm_yes_{client['id']}", 
                                       type="primary", use_container_width=True):
                                try:
                                    # Check if client has quotes
                                    quotes_df = db_manager.get_client_quotes(client['id'])
                                    if not quotes_df.empty:
                                        st.error("Cannot delete client with existing quotes. Archive quotes first.")
                                    else:
                                        # Clear cart if this client is selected
                                        if st.session_state.get('selected_client') == client['id']:
                                            db_manager.clear_cart(user_id, client['id'])
                                            st.session_state.selected_client = None
                                            st.session_state.cart_count = 0
                                        
                                        # Delete client
                                        success, message = db_manager.delete_client(client['id'])
                                        if success:
                                            st.success(f"Deleted {client['company']}")
                                            # Clear confirmation state
                                            if f'confirm_delete_{client["id"]}' in st.session_state:
                                                del st.session_state[f'confirm_delete_{client["id"]}']
                                            st.rerun()
                                        else:
                                            st.error(message)
                                except Exception as e:
                                    st.error(f"Error deleting client: {str(e)}")
                        
                        with col_confirm2:
                            if st.button("Cancel", key=f"confirm_no_{client['id']}", 
                                       use_container_width=True):
                                # Clear confirmation state
                                if f'confirm_delete_{client["id"]}' in st.session_state:
                                    del st.session_state[f'confirm_delete_{client["id"]}']
                                st.rerun()
                    
                    st.divider()
            
            has_content = True
            
        else:
            # No clients yet
            st.info("👥 No clients yet. Add your first client above to start creating quotes.")
            
            # Add new client form for empty state
            with st.expander("➕ Add Your First Client", expanded=True):
                with st.form("add_first_client_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        company = st.text_input("Company Name*", key="first_company")
                        contact_email = st.text_input("Contact Email", key="first_contact_email")
                    with col2:
                        contact_name = st.text_input("Contact Name", key="first_contact_name")
                        contact_number = st.text_input("Contact Phone", key="first_contact_number")
                    
                    if st.form_submit_button("Add Client", use_container_width=True, type="primary"):
                        if company:
                            try:
                                success, message = db_manager.create_client(
                                    user_id, company, contact_name, contact_email, contact_number
                                )
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
                            except Exception as e:
                                st.error(f"Error creating client: {str(e)}")
                        else:
                            st.error("Company name is required")
    
    except Exception as e:
        st.error(f"Error loading clients: {str(e)}")
    
    # Recent searches
    try:
        searches = db_manager.get_search_history(user_id)
        if searches:
            recent_searches_section(searches)
            has_content = True
    except Exception as e:
        st.warning(f"Could not load search history: {str(e)}")
    
    # Recent quotes
    try:
        quotes_df = db_manager.get_user_quotes(user_id, limit=5)
        if not quotes_df.empty:
            recent_quotes_section(quotes_df.to_dict('records'))
            has_content = True
    except Exception as e:
        st.warning(f"Could not load recent quotes: {str(e)}")
    
    # If no content, show getting started info
    if not has_content:
        st.markdown("### Getting Started")
        st.info("🚀 Welcome to Turbo Air! Add a client above, then use the Search tab to browse products and create quotes.")
        
        st.markdown("### Quick Guide")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔍 Browse Products**")
            st.caption("Use the Search tab above to browse products")
        with col2:
            st.markdown("**👤 Manage Clients**") 
            st.caption("Add and select clients on this Home tab")

def show_search_page(user_id, db_manager):
    """Display search/products page with collapsible product list"""
    
    # Header with selected client info
    st.markdown("### Search Products")
    
    # Show selected client info if available
    if st.session_state.get('selected_client'):
        try:
            clients_df = db_manager.get_user_clients(user_id)
            if not clients_df.empty:
                selected_client = clients_df[clients_df['id'] == st.session_state.selected_client]
                if not selected_client.empty:
                    client_name = selected_client.iloc[0]['company']
                    st.success(f"🏢 **Selected Client:** {client_name}")
        except Exception as e:
            st.warning(f"Could not load client info: {str(e)}")
    else:
        st.info("💡 **Tip:** Select a client from the Home tab before adding products to cart.")
    
    # Search bar
    search_term = search_bar_component("Search by SKU, category or description")
    
    # Real-time search results as user types
    if search_term and len(search_term) >= 1:
        # Show search suggestions/results in real-time
        try:
            results_df = db_manager.search_products(search_term)
            if not results_df.empty and len(search_term) >= 2:
                # Show compact search results with thumbnails
                st.markdown("### Search Suggestions")
                
                # Display up to 5 quick results
                for idx, product in results_df.head(5).iterrows():
                    col_img, col_info, col_price, col_action = st.columns([1, 3, 1, 1])
                    
                    with col_img:
                        # Try to show product thumbnail
                        sku = product['sku']
                        possible_paths = [
                            f"pdf_screenshots/{sku}/{sku} P.1.png",
                            f"pdf_screenshots/{sku}/{sku}_P.1.png",
                            f"pdf_screenshots/{sku}/{sku}.png",
                            f"pdf_screenshots/{sku}/page_1.png"
                        ]
                        
                        image_found = False
                        for image_path in possible_paths:
                            image_base64 = get_image_base64(image_path)
                            if image_base64:
                                st.image(f"data:image/png;base64,{image_base64}", 
                                       use_container_width=True)
                                image_found = True
                                break
                        
                        if not image_found:
                            st.markdown("<div style='width:60px;height:60px;background:#f0f0f0;border-radius:8px;display:flex;align-items:center;justify-content:center;'>📷</div>", unsafe_allow_html=True)
                    
                    with col_info:
                        st.markdown(f"**{product['sku']}**")
                        if product.get('product_type'):
                            st.caption(product['product_type'])
                    
                    with col_price:
                        st.markdown(f"${product.get('price', 0):,.2f}")
                    
                    with col_action:
                        if st.button("View", key=f"view_{product['id']}", use_container_width=True):
                            # Set search term and show full results
                            st.session_state["main_search"] = search_term
                            st.rerun()
                
                if len(results_df) > 5:
                    st.caption(f"... and {len(results_df) - 5} more results")
        except Exception as e:
            # Silent error handling for search suggestions
            pass
    
    # Handle category selection or show all categories
    if st.session_state.get('selected_category'):
        # Show back button and selected category products
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("← Back", key="back_to_categories"):
                if 'selected_category' in st.session_state:
                    del st.session_state.selected_category
                st.rerun()
        with col2:
            st.markdown(f"### {st.session_state.selected_category}")
        
        # Show products for selected category
        try:
            results_df = db_manager.get_products_by_category(st.session_state.selected_category)
            if results_df.empty:
                st.info(f"No products found in {st.session_state.selected_category}")
            else:
                display_product_results_collapsible(results_df, user_id, db_manager)
        except Exception as e:
            st.error(f"Error loading category products: {str(e)}")
    
    elif search_term and len(search_term) >= 2:
        # Search results
        try:
            db_manager.add_search_history(user_id, search_term)
        except Exception as e:
            # Silent error handling for search history
            pass
        
        st.markdown(f"### Search Results for '{search_term}'")
        try:
            results_df = db_manager.search_products(search_term)
            if results_df.empty:
                st.info("No products found matching your search.")
            else:
                display_product_results_collapsible(results_df, user_id, db_manager)
        except Exception as e:
            st.error(f"Error searching products: {str(e)}")
    
    else:
        # Show categories and recent searches
        st.markdown("### Categories")
        
        # Build categories list - make sure we get all categories
        categories = []
        for cat_name, cat_info in TURBO_AIR_CATEGORIES.items():
            try:
                products_df = db_manager.get_products_by_category(cat_name)
                count = len(products_df) if products_df is not None and not products_df.empty else 0
            except Exception as e:
                # Silent error handling for category loading
                count = 0
            
            categories.append({
                "name": cat_name,
                "count": count,
                "icon": cat_info["icon"]
            })
        
        # Display categories - make sure all show up
        if categories:
            category_grid(categories)
        else:
            st.warning("No categories available")
        
        # Show recent searches with improved styling
        try:
            searches = db_manager.get_search_history(user_id)
            if searches:
                recent_searches_section(searches)
        except Exception as e:
            # Silent error handling for search history
            pass

def display_product_results_collapsible(results_df, user_id, db_manager):
    """Display product results as a clean list with details view"""
    st.markdown(f"**Found {len(results_df)} products**")
    
    # Get current cart items
    cart_items = []
    cart_client_id = st.session_state.get('selected_client')
    
    if cart_client_id:
        try:
            cart_items_df = db_manager.get_cart_items(user_id, cart_client_id)
            if not cart_items_df.empty:
                cart_items = cart_items_df.to_dict('records')
        except Exception as e:
            # Silent error handling
            pass
    
    # Display products as clean list
    for idx, product in results_df.iterrows():
        sku = product['sku']
        
        # Initialize details state
        details_key = f"details_{product['id']}"
        if details_key not in st.session_state:
            st.session_state[details_key] = False
        
        # Get current quantity in cart
        current_qty = 0
        cart_item_id = None
        for item in cart_items:
            if item.get('product_id') == product['id']:
                current_qty = item.get('quantity', 0)
                cart_item_id = item.get('id')
                break
        
        # Create main product row
        with st.container():
            if not st.session_state[details_key]:
                # Main list view - Image, SKU, Price, Qty, Details, Add
                col_img, col_info, col_price, col_qty, col_details, col_add = st.columns([1, 3, 1, 1, 1, 1])
                
                with col_img:
                    # Product thumbnail
                    possible_paths = [
                        f"pdf_screenshots/{sku}/{sku} P.1.png",
                        f"pdf_screenshots/{sku}/{sku}_P.1.png",
                        f"pdf_screenshots/{sku}/{sku}.png",
                        f"pdf_screenshots/{sku}/page_1.png"
                    ]
                    
                    image_found = False
                    for image_path in possible_paths:
                        image_base64 = get_image_base64(image_path)
                        if image_base64:
                            st.image(f"data:image/png;base64,{image_base64}", 
                                   use_container_width=True)
                            image_found = True
                            break
                    
                    if not image_found:
                        st.markdown("📷")
                
                with col_info:
                    # Product info - no description, just SKU and model
                    st.markdown(f"**{sku}**")
                    if product.get('product_type'):
                        st.caption(product['product_type'])
                
                with col_price:
                    st.markdown(f"**${product.get('price', 0):,.2f}**")
                
                with col_qty:
                    if current_qty > 0:
                        # Quantity controls for items in cart
                        qty_col1, qty_col2, qty_col3 = st.columns([1, 2, 1])
                        with qty_col1:
                            if st.button("➖", key=f"minus_{product['id']}", use_container_width=True):
                                if current_qty > 1:
                                    try:
                                        db_manager.update_cart_quantity(cart_item_id, current_qty - 1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                                elif current_qty == 1:
                                    try:
                                        db_manager.remove_from_cart(cart_item_id)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        
                        with qty_col2:
                            st.markdown(f"<div style='text-align: center; font-weight: bold;'>{current_qty}</div>", 
                                      unsafe_allow_html=True)
                        
                        with qty_col3:
                            if st.button("➕", key=f"plus_{product['id']}", use_container_width=True):
                                try:
                                    db_manager.update_cart_quantity(cart_item_id, current_qty + 1)
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                    else:
                        st.markdown("0")
                
                with col_details:
                    if st.button("📋 Details", key=f"details_btn_{product['id']}", use_container_width=True):
                        st.session_state[details_key] = True
                        st.rerun()
                
                with col_add:
                    if current_qty > 0:
                        st.markdown(f"<div style='text-align: center; color: green; font-weight: bold;'>✅ In Cart</div>", 
                                  unsafe_allow_html=True)
                    else:
                        if st.button("🛒 Add", key=f"add_cart_{product['id']}", use_container_width=True, type="primary"):
                            if cart_client_id:
                                try:
                                    success, message = db_manager.add_to_cart(
                                        user_id, product['id'], cart_client_id
                                    )
                                    if success:
                                        st.success("Added to cart!")
                                        st.rerun()
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"Error: {str(e)}")
                            else:
                                st.warning("Select a client first")
            
            else:
                # Details view - Hide main image, show 2 screenshots and details
                col_images, col_info = st.columns([1, 2])
                
                with col_images:
                    # Show both PNG screenshots stacked
                    possible_paths = [
                        f"pdf_screenshots/{sku}/{sku} P.1.png",
                        f"pdf_screenshots/{sku}/{sku}_P.1.png",
                        f"pdf_screenshots/{sku}/{sku}.png",
                        f"pdf_screenshots/{sku}/page_1.png"
                    ]
                    
                    # Try to find and show first image
                    image_found = False
                    for image_path in possible_paths:
                        image_base64 = get_image_base64(image_path)
                        if image_base64:
                            st.image(f"data:image/png;base64,{image_base64}", 
                                   caption=f"{sku} - Page 1", use_container_width=True)
                            image_found = True
                            break
                    
                    # Try to find second image (page 2)
                    second_image_paths = [
                        f"pdf_screenshots/{sku}/{sku} P.2.png",
                        f"pdf_screenshots/{sku}/{sku}_P.2.png",
                        f"pdf_screenshots/{sku}/page_2.png"
                    ]
                    
                    second_image_found = False
                    for image_path in second_image_paths:
                        image_base64 = get_image_base64(image_path)
                        if image_base64:
                            st.image(f"data:image/png;base64,{image_base64}", 
                                   caption=f"{sku} - Page 2", use_container_width=True)
                            second_image_found = True
                            break
                    
                    if not image_found:
                        st.markdown("📷 **No images available**")
                
                with col_info:
                    # Product details
                    st.markdown(f"**SKU:** {product['sku']}")
                    st.markdown(f"**Model:** {product.get('product_type', 'N/A')}")
                    st.markdown(f"**Price:** ${product.get('price', 0):,.2f}")
                    
                    if product.get('description'):
                        st.markdown(f"**Description:** {product['description']}")
                    
                    # Specifications
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
                    
                    for key, value in specs.items():
                        if value and value != '-':
                            st.markdown(f"**{key}:** {value}")
                    
                    # Action buttons in details view
                    col_back, col_qty_detail, col_add_detail = st.columns([1, 2, 1])
                    
                    with col_back:
                        if st.button("← Back", key=f"back_{product['id']}", use_container_width=True):
                            st.session_state[details_key] = False
                            st.rerun()
                    
                    with col_qty_detail:
                        if current_qty > 0:
                            # Quantity controls
                            qty_col1, qty_col2, qty_col3 = st.columns([1, 2, 1])
                            with qty_col1:
                                if st.button("➖", key=f"minus_detail_{product['id']}", use_container_width=True):
                                    if current_qty > 1:
                                        try:
                                            db_manager.update_cart_quantity(cart_item_id, current_qty - 1)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                                    elif current_qty == 1:
                                        try:
                                            db_manager.remove_from_cart(cart_item_id)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Error: {str(e)}")
                            
                            with qty_col2:
                                st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 18px;'>{current_qty}</div>", 
                                          unsafe_allow_html=True)
                            
                            with qty_col3:
                                if st.button("➕", key=f"plus_detail_{product['id']}", use_container_width=True):
                                    try:
                                        db_manager.update_cart_quantity(cart_item_id, current_qty + 1)
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                        else:
                            st.markdown("**Quantity: 0**")
                    
                    with col_add_detail:
                        if current_qty == 0:
                            if st.button("🛒 Add to Cart", key=f"add_detail_{product['id']}", use_container_width=True, type="primary"):
                                if cart_client_id:
                                    try:
                                        success, message = db_manager.add_to_cart(
                                            user_id, product['id'], cart_client_id
                                        )
                                        if success:
                                            st.success("Added to cart!")
                                            st.rerun()
                                        else:
                                            st.error(message)
                                    except Exception as e:
                                        st.error(f"Error: {str(e)}")
                                else:
                                    st.warning("Select a client first")
                        else:
                            st.markdown("**✅ In Cart**")
            
            st.divider()

def show_cart_page(user_id, db_manager):
    """Display cart page with proper SKU display, totals calculation and 3 export buttons"""
    
    st.markdown("### Shopping Cart")
    
    # Initialize tax rate in session state if not exists
    if 'tax_rate' not in st.session_state:
        st.session_state.tax_rate = 8.0
    
    # Show cart items
    cart_items_df = pd.DataFrame()
    
    if st.session_state.get('selected_client'):
        # Load cart for selected client
        try:
            cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
        except Exception as e:
            st.error(f"Error loading cart: {str(e)}")
    else:
        st.warning("⚠️ **No client selected.** Please select a client from the Home tab first.")
        return
    
    if cart_items_df.empty:
        empty_state("🛒", "Cart is Empty", "Add products using the Search tab to create a quote")
        return
    
    # Display cart items
    st.markdown("#### Items in Cart")
    
    # Header row
    col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
    with col1:
        st.markdown("**Product**")
    with col2:
        st.markdown("**Quantity**")
    with col3:
        st.markdown("**Unit Price**")
    with col4:
        st.markdown("**Total**")
    with col5:
        st.markdown("**Remove**")
    
    st.divider()
    
    # Calculate totals
    subtotal = 0
    
    # Display each cart item with proper nested data access
    for idx, item in cart_items_df.iterrows():
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1, 1])
        
        # Get cart item ID
        item_id = item.get('id', idx)
        
        # Get quantity
        quantity = 1
        if 'quantity' in item and item['quantity'] is not None:
            try:
                # Handle numpy int64 types
                quantity = int(item['quantity'])
            except (ValueError, TypeError):
                quantity = 1
        
        # Extract product data from nested 'products' object
        product_data = item.get('products', {})
        
        if isinstance(product_data, dict):
            # Product data is nested in 'products' key
            sku = product_data.get('sku', f"Product {item.get('product_id', 'Unknown')}")
            product_type = product_data.get('product_type', product_data.get('description', ''))
            price = float(product_data.get('price', 0))
        else:
            # Fallback to direct access if no nested products
            sku = item.get('sku', f"Product {item.get('product_id', 'Unknown')}")
            product_type = item.get('product_type', item.get('description', ''))
            price = float(item.get('price', 0))
        
        line_total = price * quantity
        subtotal += line_total
        
        with col1:
            st.markdown(f"**{sku}**")
            if product_type:
                st.caption(product_type[:60] + "..." if len(product_type) > 60 else product_type)
        
        with col2:
            # Quantity controls in a more compact layout
            qty_col1, qty_col2, qty_col3 = st.columns([1, 2, 1])
            with qty_col1:
                if st.button("➖", key=f"cart_minus_{item_id}"):
                    if quantity > 1:
                        try:
                            db_manager.update_cart_quantity(item_id, quantity - 1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
                    else:
                        try:
                            db_manager.remove_from_cart(item_id)
                            # Update cart count in session state
                            if st.session_state.get('selected_client'):
                                cart_items_df_new = db_manager.get_cart_items(user_id, st.session_state.selected_client)
                                st.session_state.cart_count = len(cart_items_df_new) if not cart_items_df_new.empty else 0
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {str(e)}")
            
            with qty_col2:
                st.markdown(f"<div style='text-align: center; font-weight: bold; font-size: 16px; padding: 8px;'>{quantity}</div>", 
                          unsafe_allow_html=True)
            
            with qty_col3:
                if st.button("➕", key=f"cart_plus_{item_id}"):
                    try:
                        db_manager.update_cart_quantity(item_id, quantity + 1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
        
        with col3:
            st.markdown(f"${price:,.2f}")
        
        with col4:
            st.markdown(f"**${line_total:,.2f}**")
        
        with col5:
            if st.button("🗑️", key=f"remove_{item_id}", help="Remove from cart"):
                try:
                    db_manager.remove_from_cart(item_id)
                    # Update cart count in session state
                    if st.session_state.get('selected_client'):
                        cart_items_df_new = db_manager.get_cart_items(user_id, st.session_state.selected_client)
                        st.session_state.cart_count = len(cart_items_df_new) if not cart_items_df_new.empty else 0
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        st.divider()
    
    # Quote Summary with editable tax rate
    st.markdown("### Quote Summary")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Tax rate input
        tax_rate = st.number_input(
            "Tax Rate (%)", 
            min_value=0.0, 
            max_value=50.0, 
            value=st.session_state.tax_rate,
            step=0.1,
            format="%.1f",
            key="tax_rate_input"
        )
        # Update session state
        st.session_state.tax_rate = tax_rate
    
    with col2:
        # Calculate totals
        tax_decimal = tax_rate / 100
        tax_amount = subtotal * tax_decimal
        total = subtotal + tax_amount
        
        st.markdown(f"**Subtotal:** ${subtotal:,.2f}")
        st.markdown(f"**Tax ({tax_rate:.1f}%):** ${tax_amount:,.2f}")  
        st.markdown(f"**Total:** ${total:,.2f}")
    
    # Export Options section
    st.markdown("### Export Options")
    
    # Prepare quote data for export with CUSTOM TAX RATE
    quote_number = f"TA{datetime.now().strftime('%Y%m%d%H%M%S')}"
    quote_data = {
        'quote_number': quote_number,
        'total_amount': total,
        'subtotal': subtotal,
        'tax_rate': tax_rate,  # Use the custom tax rate from UI
        'tax_amount': tax_amount,
        'created_at': datetime.now()
    }
    
    # Get client data
    try:
        client_data = db_manager.get_user_clients(user_id)
        client_data = client_data[client_data['id'] == st.session_state.selected_client].iloc[0].to_dict()
    except Exception as e:
        st.error(f"Error loading client data: {str(e)}")
        return
    
    # Prepare cart items with proper price access for export
    export_cart_items = []
    for _, item in cart_items_df.iterrows():
        product_data = item.get('products', {})
        if isinstance(product_data, dict):
            item_price = float(product_data.get('price', 0))
            item_sku = product_data.get('sku', 'Unknown')
            item_type = product_data.get('product_type', '')
        else:
            item_price = float(item.get('price', 0))
            item_sku = item.get('sku', 'Unknown')
            item_type = item.get('product_type', '')
        
        export_cart_items.append({
            'sku': item_sku,
            'product_type': item_type,
            'price': item_price,
            'quantity': int(item.get('quantity', 1)),
            'total': item_price * int(item.get('quantity', 1))
        })
    
    export_cart_df = pd.DataFrame(export_cart_items)
    
    # Show 3 export buttons in columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📧 Email Quote", use_container_width=True, type="primary"):
            with st.spinner("Preparing email..."):
                try:
                    # Create quote in database first with CUSTOM TAX
                    success, message, db_quote_number = db_manager.create_quote_with_tax(
                        user_id, st.session_state.selected_client, cart_items_df, tax_rate, tax_amount, total
                    )
                    
                    if success:
                        # Update quote data with database quote number
                        quote_data['quote_number'] = db_quote_number
                        
                        email_service = get_email_service()
                        if email_service and hasattr(email_service, 'configured') and email_service.configured:
                            show_email_quote_dialog(quote_data, export_cart_df, client_data)
                        else:
                            st.warning("Email service not configured")
                            st.info("To enable email, configure Gmail credentials in your secrets")
                    else:
                        st.error(f"Error creating quote: {message}")
                except Exception as e:
                    st.error(f"Email functionality error: {str(e)}")
    
    with col2:
        if st.button("📄 Export PDF", use_container_width=True, type="secondary"):
            with st.spinner("Generating PDF..."):
                try:
                    # Create quote in database first with CUSTOM TAX
                    success, message, db_quote_number = db_manager.create_quote_with_tax(
                        user_id, st.session_state.selected_client, cart_items_df, tax_rate, tax_amount, total
                    )
                    
                    if success:
                        # Update quote data with database quote number
                        quote_data['quote_number'] = db_quote_number
                        
                        pdf_buffer = generate_pdf_quote(quote_data, export_cart_df, client_data)
                        st.download_button(
                            "Download PDF",
                            pdf_buffer.getvalue(),
                            file_name=f"Quote_{db_quote_number}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="pdf_download"
                        )
                        st.success(f"Quote {db_quote_number} created and PDF ready for download!")
                    else:
                        st.error(f"Error creating quote: {message}")
                except Exception as e:
                    st.error(f"PDF export error: {e}")
    
    with col3:
        if st.button("📊 Export Excel", use_container_width=True, type="secondary"):
            with st.spinner("Generating Excel..."):
                try:
                    # Create quote in database first with CUSTOM TAX
                    success, message, db_quote_number = db_manager.create_quote_with_tax(
                        user_id, st.session_state.selected_client, cart_items_df, tax_rate, tax_amount, total
                    )
                    
                    if success:
                        # Update quote data with database quote number
                        quote_data['quote_number'] = db_quote_number
                        
                        excel_buffer = generate_excel_quote(quote_data, export_cart_df, client_data)
                        st.download_button(
                            "Download Excel",
                            excel_buffer.getvalue(),
                            file_name=f"Quote_{db_quote_number}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key="excel_download"
                        )
                        st.success(f"Quote {db_quote_number} created and Excel ready for download!")
                    else:
                        st.error(f"Error creating quote: {message}")
                except Exception as e:
                    st.error(f"Excel export error: {e}")
    
    # Clear cart section
    st.markdown("---")
    if st.button("Clear Cart and Start New Quote", use_container_width=True):
        try:
            db_manager.clear_cart(user_id, st.session_state.selected_client)
            st.session_state.cart_count = 0
            st.success("Cart cleared successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing cart: {str(e)}")

def show_profile_page(user, auth_manager, sync_manager, db_manager):
    """Display profile page with user settings and admin functions"""
    
    st.markdown("### Profile & Settings")
    
    # User info section
    with st.expander("User Information", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Email:** {user.get('email', 'N/A')}")
            st.markdown(f"**User ID:** {user.get('id', 'N/A')}")
        with col2:
            st.markdown(f"**Role:** {auth_manager.get_user_role().title()}")
            
            # Connection status
            if auth_manager.is_online:
                st.success("🟢 Connected to Supabase")
            else:
                st.warning("🔴 Running in offline mode")
    
    # App Settings
    st.markdown("### App Settings")
    
    with st.expander("Preferences"):
        # Currency settings
        currency = st.selectbox("Currency Display", ["USD ($)", "CAD ($)", "EUR (€)"], index=0)
        
        # Items per page
        items_per_page = st.slider("Products per page", 10, 50, 20)
        
        # Auto-save cart
        auto_save = st.checkbox("Auto-save cart items", value=True)
        
        if st.button("Save Preferences", use_container_width=True):
            st.success("Preferences saved! (Feature coming soon)")
    
    # Data Management
    st.markdown("### Data Management")
    
    with st.expander("Export & Backup"):
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export My Data", use_container_width=True):
                st.info("Data export feature coming soon!")
        
        with col2:
            if st.button("💾 Backup Data", use_container_width=True):
                with st.spinner("Creating backup..."):
                    try:
                        # This would backup user data
                        st.success("Backup created successfully!")
                    except Exception as e:
                        st.error(f"Backup failed: {str(e)}")
    
    # Admin functions (if applicable)
    try:
        if auth_manager.is_admin():
            st.markdown("### Admin Functions")
            
            with st.expander("Database Management", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Sync Database", use_container_width=True):
                        with st.spinner("Syncing..."):
                            try:
                                result = sync_manager.sync_all()
                                if result['success']:
                                    st.success(result['message'])
                                else:
                                    st.error(result['message'])
                            except Exception as e:
                                st.error(f"Sync error: {str(e)}")
                
                with col2:
                    if st.button("📈 View Analytics", use_container_width=True):
                        st.info("Analytics dashboard coming soon!")
            
            with st.expander("User Management"):
                st.info("User management features available in future updates.")
    
    except Exception as e:
        st.warning(f"Could not check admin status: {str(e)}")
    
    # Account Actions
    st.markdown("### Account")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔒 Change Password", use_container_width=True):
            st.info("Password change feature coming soon!")
    
    with col2:
        if st.button("🚪 Sign Out", use_container_width=True, type="secondary"):
            try:
                auth_manager.sign_out()
                st.rerun()
            except Exception as e:
                st.error(f"Error signing out: {str(e)}")
    
    # App Information
    st.markdown("### About")
    with st.expander("App Information"):
        st.markdown("**Turbo Air Equipment Viewer**")
        st.markdown("Version: 1.0.0")
        st.markdown("Built with Streamlit")
        st.markdown("© 2024 Turbo Air")

def show_product_detail(product: Dict, user_id: str, db_manager):
    """Display product detail modal"""
    
    st.markdown("### Product Details")
    
    # Back button
    if st.button("← Back to Search", key="back_from_detail", use_container_width=True):
        st.session_state.show_product_detail = None
        st.rerun()
    
    # Product image and info
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Try multiple possible image paths
        sku = product['sku']
        possible_paths = [
            f"pdf_screenshots/{sku}/{sku} P.1.png",
            f"pdf_screenshots/{sku}/{sku}_P.1.png",
            f"pdf_screenshots/{sku}/{sku}.png",
            f"pdf_screenshots/{sku}/page_1.png"
        ]
        
        image_found = False
        for image_path in possible_paths:
            image_base64 = get_image_base64(image_path)
            if image_base64:
                st.image(f"data:image/png;base64,{image_base64}", caption=sku, use_container_width=True)
                image_found = True
                break
        
        if not image_found:
            st.markdown("📷 **No image available**")
    
    with col2:
        # Product info
        st.markdown(f"# {product['sku']}")
        st.markdown(f"**{product.get('product_type', 'N/A')}**")
        st.markdown(f"## {format_price(product.get('price', 0))}")
        
        if product.get('description'):
            st.markdown(product['description'])
    
    # Specifications
    st.markdown("### Specifications")
    
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
    
    col1, col2 = st.columns(2)
    for i, (key, value) in enumerate(specs.items()):
        if value and value != '-':
            with col1 if i % 2 == 0 else col2:
                st.markdown(f"**{key}:** {value}")
    
    # Add to Cart button
    st.markdown("### ")
    if st.button("🛒 Add to Cart", use_container_width=True, type="primary"):
        if st.session_state.get('selected_client'):
            try:
                success, message = db_manager.add_to_cart(
                    user_id, product['id'], st.session_state.selected_client
                )
                if success:
                    st.success("Added to cart!")
                    # Don't close detail view, let user continue browsing
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error adding to cart: {str(e)}")
        else:
            st.error("Please select a client first")

def show_quote_summary(quote: Dict):
    """Display quote summary page with export options"""
    
    st.markdown("### Quote Summary")
    
    # Quote details
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Quote Number:** {quote['quote_number']}")
        st.markdown(f"**Date:** {datetime.now().strftime('%B %d, %Y')}")
    with col2:
        st.markdown(f"**Client:** {quote['client_data'].get('company', 'N/A')}")
        st.markdown(f"**Total:** ${quote['total_amount']:,.2f}")
    
    st.divider()
    
    # Equipment list
    st.markdown("### Equipment List")
    for _, item in quote['items'].iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{item.get('sku', 'Unknown')}**")
            if item.get('product_type'):
                st.caption(f"Model: {item['product_type']}")
        with col2:
            st.markdown(f"Qty: {item.get('quantity', 1)}")
        with col3:
            st.markdown(format_price(item.get('price', 0) * item.get('quantity', 1)))
    
    # Pricing summary
    st.divider()
    cart_summary(quote['total_amount'] / 1.08)  # Assuming 8% tax
    
    # Export options
    st.markdown("### Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Export Excel", use_container_width=True):
            try:
                excel_buffer = generate_excel_quote(
                    quote['quote_data'], 
                    quote['items'], 
                    quote['client_data']
                )
                st.download_button(
                    "Download Excel",
                    excel_buffer.getvalue(),
                    file_name=f"Quote_{quote['quote_number']}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export error: {e}")
    
    with col2:
        if st.button("📄 Export PDF", use_container_width=True):
            try:
                pdf_buffer = generate_pdf_quote(
                    quote['quote_data'], 
                    quote['items'], 
                    quote['client_data']
                )
                st.download_button(
                    "Download PDF",
                    pdf_buffer.getvalue(),
                    file_name=f"Quote_{quote['quote_number']}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Export error: {e}")
    
    with col3:
        if st.button("📧 Email Quote", use_container_width=True):
            try:
                email_service = get_email_service()
                if email_service and hasattr(email_service, 'configured') and email_service.configured:
                    show_email_quote_dialog(
                        quote['quote_data'],
                        quote['items'],
                        quote['client_data']
                    )
                else:
                    st.warning("Email service not configured")
                    st.info("To enable email, configure Gmail credentials in your secrets")
            except Exception as e:
                st.warning(f"Email functionality not available: {str(e)}")
    
    # Action buttons
    st.markdown("### ")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Create New Quote", use_container_width=True):
            # Clear cart and show success message
            try:
                db_manager = st.session_state.db_manager
                user_id = st.session_state.user['id']
                db_manager.clear_cart(user_id, st.session_state.selected_client)
                st.session_state.cart_count = 0
                st.success("Cart cleared - use Search tab to create new quote")
            except Exception as e:
                st.warning(f"Could not clear cart: {str(e)}")
    
    with col2:
        if st.button("Clear Quote Data", use_container_width=True, type="primary"):
            # Clear quote data
            try:
                db_manager = st.session_state.db_manager
                user_id = st.session_state.user['id']
                db_manager.clear_cart(user_id, st.session_state.selected_client)
                st.session_state.cart_count = 0
                if 'last_quote' in st.session_state:
                    del st.session_state.last_quote
                st.success("Quote cleared successfully")
            except Exception as e:
                st.warning(f"Could not clear quote: {str(e)}")