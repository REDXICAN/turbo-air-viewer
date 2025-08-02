"""
Page components for Turbo Air Equipment Viewer
Redesigned with bottom navigation structure
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Dict

from .ui_components import (
    app_header, search_bar_component, bottom_navigation, category_grid,
    product_list_item, recent_searches_section, recent_quotes_section,
    metrics_section, cart_item_component, cart_summary, quote_export_buttons,
    empty_state, format_price, truncate_text, COLORS, TURBO_AIR_CATEGORIES
)
from .export import export_quote_to_excel, export_quote_to_pdf
from .email import show_email_quote_dialog

def show_home_page(user, user_id, db_manager, sync_manager, auth_manager):
    """Display home page with recent items and metrics"""
    # Header and search bar
    app_header()
    search_term = search_bar_component("Search for products")
    
    # Handle search redirect
    if search_term:
        st.session_state.search_term = search_term
        st.session_state.active_page = 'search'
        st.rerun()
    
    # Content area
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # Get dashboard data
    try:
        # Get metrics
        stats = db_manager.get_dashboard_stats(user_id)
        metrics_section(stats)
        
        # Get recent searches
        search_history = db_manager.get_search_history(user_id, limit=5)
        recent_searches_section(search_history)
        
        # Get recent quotes
        quotes_df = db_manager.get_user_quotes(user_id, limit=5)
        if not quotes_df.empty:
            recent_quotes = quotes_df.to_dict('records')
            recent_quotes_section(recent_quotes)
        
    except Exception as e:
        st.error(f"Error loading dashboard data: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom navigation
    bottom_navigation()

def show_search_page(user_id, db_manager):
    """Display search page with categories and results"""
    # Header and search bar
    app_header()
    search_term = search_bar_component("Search by model or keyword")
    
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # Show categories if no search or show_category_products
    if not search_term and not st.session_state.get('show_category_products'):
        st.markdown("### Categories", unsafe_allow_html=True)
        
        # Get categories with counts
        categories = []
        for cat_name in TURBO_AIR_CATEGORIES:
            try:
                products_df = db_manager.get_products_by_category(cat_name)
                count = len(products_df) if products_df is not None else 0
                categories.append({"name": cat_name, "count": count})
            except:
                categories.append({"name": cat_name, "count": 0})
        
        category_grid(categories)
    
    # Show search results
    elif search_term:
        # Add to search history
        if len(search_term) > 2:
            try:
                db_manager.add_search_history(user_id, search_term)
            except:
                pass
        
        # Search products
        try:
            results_df = db_manager.search_products(search_term)
            
            if not results_df.empty:
                st.markdown(f"### Results ({len(results_df)} items)", unsafe_allow_html=True)
                
                for _, product in results_df.iterrows():
                    st.markdown(product_list_item(product.to_dict()), unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("View Details", key=f"view_{product['id']}", use_container_width=True):
                            st.session_state.show_product_detail = product.to_dict()
                            st.rerun()
                    with col2:
                        if st.button("Add to Cart", key=f"add_{product['id']}", use_container_width=True):
                            if st.session_state.get('selected_client'):
                                success, message = db_manager.add_to_cart(
                                    user_id, product['id'], st.session_state.selected_client
                                )
                                if success:
                                    st.success("Added to cart!")
                                    st.rerun()
                            else:
                                st.error("Please select a client first")
            else:
                empty_state("🔍", "No Results Found", "Try searching with different keywords")
        except Exception as e:
            st.error(f"Search error: {e}")
    
    # Show category products
    elif st.session_state.get('show_category_products') and st.session_state.get('selected_category'):
        category = st.session_state.selected_category
        
        # Back button
        if st.button("← Back to Categories"):
            st.session_state.show_category_products = False
            st.session_state.selected_category = None
            st.rerun()
        
        st.markdown(f"### {category}", unsafe_allow_html=True)
        
        # Show type filter (Refrigerator/Freezer)
        category_info = TURBO_AIR_CATEGORIES.get(category, {})
        if category_info.get('types'):
            selected_type = st.selectbox("Filter by Type", ["All"] + category_info['types'])
        else:
            selected_type = "All"
        
        try:
            # Get products for category
            products_df = db_manager.get_products_by_category(category)
            
            # Filter by type if selected
            if selected_type != "All" and not products_df.empty:
                products_df = products_df[products_df['product_type'].str.contains(selected_type, case=False, na=False)]
            
            if not products_df.empty:
                st.markdown(f"### Products ({len(products_df)} items)", unsafe_allow_html=True)
                
                for _, product in products_df.iterrows():
                    st.markdown(product_list_item(product.to_dict()), unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([1, 1])
                    with col1:
                        if st.button("View Details", key=f"view_{product['id']}", use_container_width=True):
                            st.session_state.show_product_detail = product.to_dict()
                            st.rerun()
                    with col2:
                        if st.button("Add to Cart", key=f"add_{product['id']}", use_container_width=True):
                            if st.session_state.get('selected_client'):
                                success, message = db_manager.add_to_cart(
                                    user_id, product['id'], st.session_state.selected_client
                                )
                                if success:
                                    st.success("Added to cart!")
                                    st.rerun()
                            else:
                                st.error("Please select a client first")
            else:
                empty_state("📦", "No Products", f"No products found in {category}")
                
        except Exception as e:
            st.error(f"Error loading products: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom navigation
    bottom_navigation()

def show_cart_page(user_id, db_manager):
    """Display cart page with items and summary"""
    # Header and search bar
    app_header()
    search_term = search_bar_component("Search for products")
    
    if search_term:
        st.session_state.search_term = search_term
        st.session_state.active_page = 'search'
        st.rerun()
    
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # Check if client is selected
    if not st.session_state.get('selected_client'):
        empty_state("🛒", "No Client Selected", "Please select a client from Profile page")
    else:
        try:
            # Get cart items
            cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
            
            if cart_items_df.empty:
                empty_state("🛒", "Cart is Empty", "Add products from the Search page")
            else:
                st.markdown("### Cart", unsafe_allow_html=True)
                
                # Display cart items
                total = 0
                for _, item in cart_items_df.iterrows():
                    cart_item_component(item.to_dict())
                    total += item['price'] * item['quantity']
                    st.divider()
                
                # Summary section
                final_total = cart_summary(total)
                
                # Generate Quote button
                if st.button("Generate Quote", key="generate_quote", use_container_width=True, type="primary"):
                    with st.spinner("Generating quote..."):
                        # Get client data
                        client_data = db_manager.get_user_clients(user_id)
                        client_data = client_data[client_data['id'] == st.session_state.selected_client].iloc[0].to_dict()
                        
                        # Create quote
                        success, message, quote_number = db_manager.create_quote(
                            user_id, st.session_state.selected_client, cart_items_df
                        )
                        
                        if success:
                            st.success(message)
                            
                            # Store quote data
                            st.session_state.last_quote = {
                                'quote_number': quote_number,
                                'total_amount': final_total,
                                'items': cart_items_df,
                                'client_data': client_data,
                                'quote_data': {
                                    'quote_number': quote_number,
                                    'total_amount': final_total,
                                    'created_at': datetime.now()
                                }
                            }
                            
                            # Redirect to quote summary
                            st.session_state.active_page = 'quote_summary'
                            st.rerun()
                        else:
                            st.error(message)
                            
        except Exception as e:
            st.error(f"Error loading cart: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom navigation
    bottom_navigation()

def show_profile_page(user, auth_manager, sync_manager, db_manager):
    """Display profile page with clients and quotes"""
    # Header and search bar
    app_header()
    search_term = search_bar_component("Search for products")
    
    if search_term:
        st.session_state.search_term = search_term
        st.session_state.active_page = 'search'
        st.rerun()
    
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # User info
    st.markdown("### Account", unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.text(f"Email: {user.get('email', 'N/A')}")
    with col2:
        st.text(f"Role: {auth_manager.get_user_role().title()}")
    
    # Client management
    st.markdown("### Clients", unsafe_allow_html=True)
    
    try:
        # Get user clients
        user_id = user.get('id', 'offline_user')
        clients_df = db_manager.get_user_clients(user_id)
        
        if not clients_df.empty:
            # Client selector
            client_names = clients_df['company'].tolist()
            client_ids = clients_df['id'].tolist()
            
            selected_idx = st.selectbox(
                "Select Client",
                range(len(client_names)),
                format_func=lambda x: client_names[x],
                key="profile_client_selector"
            )
            
            if selected_idx is not None:
                selected_client_id = client_ids[selected_idx]
                st.session_state.selected_client = selected_client_id
                
                # Show client details
                selected_client = clients_df.iloc[selected_idx]
                with st.expander("Client Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text(f"Contact: {selected_client.get('contact_name', 'N/A')}")
                        st.text(f"Email: {selected_client.get('contact_email', 'N/A')}")
                    with col2:
                        st.text(f"Phone: {selected_client.get('contact_number', 'N/A')}")
                
                # Show client quotes
                st.markdown("### Client Quotes", unsafe_allow_html=True)
                try:
                    quotes_df = db_manager.get_client_quotes(selected_client_id)
                    
                    if not quotes_df.empty:
                        for _, quote in quotes_df.iterrows():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            with col1:
                                st.text(f"Quote #{quote['quote_number']}")
                                st.caption(f"Created: {quote['created_at']}")
                            with col2:
                                st.text(f"${quote['total_amount']:,.2f}")
                            with col3:
                                if st.button("View", key=f"view_quote_{quote['id']}", use_container_width=True):
                                    # Load quote details
                                    st.session_state.selected_quote = quote['id']
                                    st.session_state.active_page = 'quote_detail'
                                    st.rerun()
                    else:
                        st.info("No quotes for this client")
                        
                except Exception as e:
                    st.error(f"Error loading quotes: {e}")
        else:
            st.info("No clients yet. Create one below.")
            
    except Exception as e:
        st.error(f"Error loading clients: {e}")
    
    # Create new client
    with st.expander("Create New Client"):
        with st.form("new_client_form"):
            company = st.text_input("Company Name*")
            contact_name = st.text_input("Contact Name")
            contact_email = st.text_input("Contact Email")
            contact_number = st.text_input("Contact Phone")
            
            if st.form_submit_button("Create Client", type="primary", use_container_width=True):
                if company:
                    success, message = db_manager.create_client(
                        user_id, company, contact_name, contact_email, contact_number
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Company name is required")
    
    # Sign out button
    st.markdown("### ")
    if st.button("Sign Out", key="signout", use_container_width=True):
        auth_manager.sign_out()
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom navigation
    bottom_navigation()

def show_quote_summary(quote: Dict):
    """Display quote summary with export options"""
    # Header
    app_header()
    
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back"):
        st.session_state.active_page = 'cart'
        st.rerun()
    
    st.markdown("### Quote Summary", unsafe_allow_html=True)
    st.markdown(f"Quote Number: **{quote['quote_number']}**", unsafe_allow_html=True)
    
    # Equipment list
    st.markdown("### Equipment List", unsafe_allow_html=True)
    
    for _, item in quote['items'].iterrows():
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            st.markdown(f"**{item['sku']}**")
            st.caption(f"Model: {item.get('product_type', 'N/A')}")
        with col2:
            st.text(f"Qty: {item['quantity']}")
        with col3:
            st.text(format_price(item['price'] * item['quantity']))
        st.divider()
    
    # Pricing details
    st.markdown("### Pricing Details", unsafe_allow_html=True)
    subtotal = quote['total_amount'] / 1.08
    cart_summary(subtotal)
    
    # Export options
    st.markdown("### Export Options", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        try:
            excel_file = export_quote_to_excel(
                quote['quote_data'],
                quote['items'],
                quote['client_data']
            )
            with open(excel_file, 'rb') as f:
                st.download_button(
                    "Export as Excel",
                    f.read(),
                    file_name=excel_file,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except Exception as e:
            if st.button("Export as Excel", use_container_width=True):
                st.error(f"Excel export error: {e}")
    
    with col2:
        try:
            pdf_file = export_quote_to_pdf(
                quote['quote_data'],
                quote['items'],
                quote['client_data']
            )
            with open(pdf_file, 'rb') as f:
                st.download_button(
                    "Export as PDF",
                    f.read(),
                    file_name=pdf_file,
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
        except Exception as e:
            if st.button("Export as PDF", use_container_width=True, type="primary"):
                st.error(f"PDF export error: {e}")
    
    # Email button
    if st.button("📧 Email Quote", use_container_width=True):
        show_email_quote_dialog(
            quote['quote_data'],
            quote['items'],
            quote['client_data']
        )
    
    # New quote button
    if st.button("Start New Quote", use_container_width=True):
        db_manager = st.session_state.db_manager
        user_id = st.session_state.user['id']
        db_manager.clear_cart(user_id, st.session_state.selected_client)
        st.session_state.active_page = 'home'
        st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom navigation
    bottom_navigation()

def show_product_detail(product: Dict, user_id: str, db_manager):
    """Display product detail page"""
    # Header
    app_header()
    
    st.markdown('<div class="content-area">', unsafe_allow_html=True)
    
    # Back button
    if st.button("← Back"):
        st.session_state.show_product_detail = None
        st.rerun()
    
    # Product images
    col1, col2 = st.columns(2)
    
    image_path1 = f"pdf_screenshots/{product['sku']}/{product['sku']} P.1.png"
    image_path2 = f"pdf_screenshots/{product['sku']}/{product['sku']} P.2.png"
    
    with col1:
        if os.path.exists(image_path1):
            st.image(image_path1, caption="Page 1", use_container_width=True)
        else:
            empty_state("📷", "No Image", "")
    
    with col2:
        if os.path.exists(image_path2):
            st.image(image_path2, caption="Page 2", use_container_width=True)
        else:
            empty_state("📷", "No Image", "")
    
    # Product info
    st.markdown(f"### {product['sku']}", unsafe_allow_html=True)
    st.markdown(f"{product.get('description', '')}", unsafe_allow_html=True)
    st.markdown(f"### {format_price(product.get('price', 0))}", unsafe_allow_html=True)
    
    # Specifications
    st.markdown("### Specifications", unsafe_allow_html=True)
    
    specs = {
        "Capacity": product.get('capacity', '-'),
        "Dimensions": product.get('dimensions', '-'),
        "Weight": product.get('weight', '-'),
        "Voltage": product.get('voltage', '-'),
        "Amps": product.get('amperage', '-'),
        "Refrigerant": product.get('refrigerant', '-')
    }
    
    col1, col2 = st.columns(2)
    specs_items = list(specs.items())
    
    with col1:
        for key, value in specs_items[:3]:
            st.text(f"{key}: {value}")
    
    with col2:
        for key, value in specs_items[3:]:
            st.text(f"{key}: {value}")
    
    # Datasheet
    st.markdown("### Datasheet", unsafe_allow_html=True)
    st.markdown(f"**{product['sku']} Datasheet**")
    st.caption("View detailed specifications and dimensions")
    
    # Add to Cart button
    if st.button("Add to Cart", key="detail_add_to_cart", use_container_width=True, type="primary"):
        if st.session_state.get('selected_client'):
            success, message = db_manager.add_to_cart(
                user_id, product['id'], st.session_state.selected_client
            )
            if success:
                st.success("Added to cart!")
                st.session_state.show_product_detail = None
                st.session_state.active_page = 'cart'
                st.rerun()
        else:
            st.error("Please select a client first")
            if st.button("Go to Profile to Select Client", use_container_width=True):
                st.session_state.show_product_detail = None
                st.session_state.active_page = 'profile'
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Bottom navigation
    bottom_navigation()