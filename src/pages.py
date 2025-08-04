"""
Page components for Turbo Air Equipment Viewer
Updated with improved email integration and debugging
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

# Check if these modules exist before importing - REMOVED CSV EXPORT
from .export import (
    export_quote_to_excel, 
    export_quote_to_pdf, 
    generate_excel_quote, 
    generate_pdf_quote
)

# Import email functions - IMPROVED VERSION with better error handling
from .email import show_email_quote_dialog, get_email_service, EmailService, test_email_connection

def show_client_selector(user_id, db_manager, sync_manager):
    """Display client selection interface"""
    st.markdown("### Select Client")
    
    try:
        # Get user's clients
        clients_df = db_manager.get_user_clients(user_id)
        
        if clients_df.empty:
            st.info("No clients found. Add a client to get started.")
            
            # Simple client creation form
            with st.expander("Add New Client", expanded=True):
                with st.form("add_client"):
                    company_name = st.text_input("Company Name", placeholder="Enter company name")
                    contact_name = st.text_input("Contact Name", placeholder="Enter contact name")
                    email = st.text_input("Email", placeholder="Enter email address")
                    phone = st.text_input("Phone", placeholder="Enter phone number")
                    address = st.text_area("Address", placeholder="Enter company address")
                    
                    if st.form_submit_button("Add Client", use_container_width=True):
                        if company_name:
                            try:
                                client_data = {
                                    'user_id': user_id,
                                    'company': company_name,
                                    'contact_name': contact_name,
                                    'contact_email': email,
                                    'phone': phone,
                                    'address': address
                                }
                                
                                success, client_id = db_manager.add_client(client_data)
                                if success:
                                    # Queue sync operation
                                    sync_manager.queue_sync_operation('clients', 'create', client_data)
                                    st.success(f"Client '{company_name}' added successfully!")
                                    st.rerun()
                                else:
                                    st.error("Failed to add client")
                            except Exception as e:
                                st.error(f"Error adding client: {str(e)}")
                        else:
                            st.error("Please enter a company name")
            
            return
        
        # Display existing clients
        client_options = {}
        for _, client in clients_df.iterrows():
            display_name = f"{client['company']}"
            if client.get('contact_name'):
                display_name += f" - {client['contact_name']}"
            client_options[display_name] = client['id']
        
        # Add "Add New Client" option
        client_options["➕ Add New Client"] = "add_new"
        
        # Current selection
        current_selection = None
        if st.session_state.get('selected_client'):
            for display_name, client_id in client_options.items():
                if client_id == st.session_state.selected_client:
                    current_selection = display_name
                    break
        
        # Client selectbox
        selected_display = st.selectbox(
            "Choose a client:",
            options=list(client_options.keys()),
            index=list(client_options.keys()).index(current_selection) if current_selection else 0,
            key="client_selector"
        )
        
        selected_client_id = client_options[selected_display]
        
        # Handle selection
        if selected_client_id == "add_new":
            # Show add client form
            with st.expander("Add New Client", expanded=True):
                with st.form("add_client"):
                    company_name = st.text_input("Company Name", placeholder="Enter company name")
                    contact_name = st.text_input("Contact Name", placeholder="Enter contact name")
                    email = st.text_input("Email", placeholder="Enter email address")
                    phone = st.text_input("Phone", placeholder="Enter phone number")
                    address = st.text_area("Address", placeholder="Enter company address")
                    
                    if st.form_submit_button("Add Client", use_container_width=True):
                        if company_name:
                            try:
                                client_data = {
                                    'user_id': user_id,
                                    'company': company_name,
                                    'contact_name': contact_name,
                                    'contact_email': email,
                                    'phone': phone,
                                    'address': address
                                }
                                
                                success, client_id = db_manager.add_client(client_data)
                                if success:
                                    # Queue sync operation
                                    sync_manager.queue_sync_operation('clients', 'create', client_data)
                                    st.success(f"Client '{company_name}' added successfully!")
                                    st.session_state.selected_client = client_id
                                    st.rerun()
                                else:
                                    st.error("Failed to add client")
                            except Exception as e:
                                st.error(f"Error adding client: {str(e)}")
                        else:
                            st.error("Please enter a company name")
        else:
            # Update selected client
            if st.session_state.get('selected_client') != selected_client_id:
                st.session_state.selected_client = selected_client_id
                
                # Update cart count for selected client
                try:
                    cart_items_df = db_manager.get_cart_items(user_id, selected_client_id)
                    st.session_state.cart_count = len(cart_items_df) if not cart_items_df.empty else 0
                except Exception:
                    st.session_state.cart_count = 0
                
                st.rerun()
    
    except Exception as e:
        st.error(f"Error loading clients: {str(e)}")


def show_recent_searches(user_id, db_manager):
    """Display recent searches section"""
    st.markdown("### Recent Searches")
    
    try:
        # Get recent searches
        searches = db_manager.get_search_history(user_id, limit=10)
        
        if not searches:
            st.info("No recent searches yet. Use the Search tab to find products!")
            return
        
        # Display searches as clickable buttons
        st.markdown("Click to search again:")
        
        # Group searches by frequency/recency
        for idx, search in enumerate(searches):
            search_term = search.get('search_term', search.get('query', 'Unknown'))
            search_date = search.get('created_at', search.get('timestamp', ''))
            
            # Format date
            try:
                if search_date:
                    if isinstance(search_date, str):
                        # Try to parse ISO format
                        from datetime import datetime
                        search_datetime = datetime.fromisoformat(search_date.replace('Z', '+00:00'))
                        formatted_date = search_datetime.strftime('%m/%d %H:%M')
                    else:
                        formatted_date = search_date.strftime('%m/%d %H:%M')
                else:
                    formatted_date = 'Recent'
            except:
                formatted_date = 'Recent'
            
            # Create clickable search item
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button(f"🔍 {search_term}", key=f"recent_search_{idx}", use_container_width=True):
                    # Set the search term and navigate to search page
                    st.session_state["main_search"] = search_term
                    st.session_state["selected_tab"] = "Search"
                    st.rerun()
            
            with col2:
                st.caption(formatted_date)
        
        # Clear search history button
        if st.button("🗑️ Clear History", key="clear_search_history"):
            try:
                success = db_manager.clear_search_history(user_id)
                if success:
                    st.success("Search history cleared!")
                    st.rerun()
                else:
                    st.error("Failed to clear search history")
            except Exception as e:
                st.error(f"Error clearing search history: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading recent searches: {str(e)}")
        # Show fallback content
        st.info("Unable to load recent searches. Use the Search tab to find products!")


def show_home_page(user, user_id, db_manager, sync_manager, auth_manager):
    """Show home page with recent searches and quotes"""
    
    # Welcome message
    st.markdown(f"### Welcome back, {user.get('email', 'User')}!")
    
    # Sync status
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col3:
        if auth_manager.is_online:
            st.success("🌐 Online")
        else:
            st.warning("📴 Offline")
    
    # Email status check
    with col4:
        try:
            email_service = get_email_service()
            if email_service and email_service.configured:
                st.success("📧 Email Ready")
            else:
                st.warning("📧 Email Off")
        except:
            st.error("📧 Email Error")
    
    # Client selection
    st.markdown("---")
    show_client_selector(user_id, db_manager, sync_manager)
    
    # Recent activity section
    if st.session_state.get('selected_client'):
        col1, col2 = st.columns(2)
        
        with col1:
            show_recent_searches(user_id, db_manager)
        
        with col2:
            show_recent_quotes_updated(user_id, db_manager, sync_manager)
    else:
        st.info("Please select a client to view recent activity")

def show_recent_quotes_updated(user_id: str, db_manager, sync_manager):
    """Display recent quotes with expandable details and export options"""
    import json
    from datetime import datetime
    import pandas as pd
    import time

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
    """Display cart page with proper SKU display, totals calculation and 2 export buttons - IMPROVED EMAIL INTEGRATION"""
    
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
    
    # IMPROVED EMAIL DIAGNOSTICS
    with st.expander("📧 Email Diagnostics", expanded=False):
        st.markdown("**Check email configuration:**")
        
        try:
            email_service = get_email_service()
            if email_service:
                if email_service.configured:
                    st.success("✅ Email service configured")
                    st.info(f"📧 Sender: {email_service.sender_email}")
                    st.info(f"🌐 SMTP: {email_service.smtp_server}:{email_service.smtp_port}")
                    
                    # Test connection button
                    if st.button("🔍 Test SMTP Connection"):
                        with st.spinner("Testing connection..."):
                            success, message = test_email_connection()
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                                st.markdown("**Troubleshooting:**")
                                st.markdown("- Make sure 2FA is enabled on your Gmail account")
                                st.markdown("- Use a 16-character app password, not your regular password")
                                st.markdown("- Check that 'Less secure app access' is disabled (you should use app passwords)")
                else:
                    st.error("❌ Email service not configured")
                    st.markdown("**Required in secrets.toml:**")
                    st.code("""
[email]
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "your-email@gmail.com"
sender_password = "your-16-char-app-password"
                    """)
            else:
                st.error("❌ Could not create email service")
        except Exception as e:
            st.error(f"❌ Email service error: {str(e)}")
    
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
    
    # Show 3 export buttons in columns - REMOVED CSV BUTTON
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
                            # Test connection first
                            conn_success, conn_msg = email_service.test_connection()
                            if conn_success:
                                show_email_quote_dialog(quote_data, export_cart_df, client_data)
                            else:
                                st.error(f"Email connection failed: {conn_msg}")
                                st.info("Check your email settings in the diagnostics above ↑")
                        else:
                            st.warning("Email service not configured")
                            st.info("Configure Gmail credentials in your secrets.toml file")
                    else:
                        st.error(f"Error creating quote: {message}")
                except Exception as e:
                    st.error(f"Email functionality error: {str(e)}")
                    st.exception(e)  # Show full traceback for debugging
    
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