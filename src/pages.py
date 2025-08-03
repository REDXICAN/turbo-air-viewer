"""
Page components for Turbo Air Equipment Viewer
Phase 1: Restored to Streamlit-native components with proper error handling
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
    """Display home page with recent activity and metrics"""
    
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
    
    # If no content, show empty state with action buttons
    if not has_content:
        empty_state("🏠", "Start Your Quote", "Search for products or create a client to begin")
        
        st.markdown("### Quick Actions")
        # Add quick action buttons
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🔍 Browse Products**")
            st.caption("Use the Search tab above to browse products")
        with col2:
            st.markdown("**👤 Add Client**") 
            st.caption("Use the Profile tab above to manage clients")

def show_search_page(user_id, db_manager):
    """Display search/products page with Streamlit-native components"""
    
    st.markdown("### Search Products")
    
    # Search bar
    search_term = search_bar_component("Search by SKU, category or description")
    
    # Categories section
    st.markdown("### Categories")
    
    # Build categories list
    categories = []
    for cat_name, cat_info in TURBO_AIR_CATEGORIES.items():
        try:
            products_df = db_manager.get_products_by_category(cat_name)
            count = len(products_df) if products_df is not None and not products_df.empty else 0
        except Exception as e:
            st.warning(f"Error loading category {cat_name}: {str(e)}")
            count = 0
        
        categories.append({
            "name": cat_name,
            "count": count,
            "icon": cat_info["icon"]
        })
    
    # Display categories
    if categories:
        category_grid(categories)
    else:
        st.warning("No categories available")
    
    # Handle search or category selection
    results_df = pd.DataFrame()
    
    if search_term and len(search_term) >= 2:
        # Save to search history
        try:
            db_manager.add_search_history(user_id, search_term)
        except Exception as e:
            st.warning(f"Could not save search history: {str(e)}")
        
        # Search products
        st.markdown(f"### Search Results for '{search_term}'")
        try:
            results_df = db_manager.search_products(search_term)
            if results_df.empty:
                st.info("No products found matching your search.")
        except Exception as e:
            st.error(f"Error searching products: {str(e)}")
    
    elif st.session_state.get('selected_category'):
        # Show category products
        category = st.session_state.selected_category
        st.markdown(f"### {category}")
        
        # Clear category selection button
        if st.button("← Back to Categories", key="clear_category"):
            if 'selected_category' in st.session_state:
                del st.session_state.selected_category
            st.rerun()
        
        try:
            results_df = db_manager.get_products_by_category(category)
            if results_df.empty:
                st.info(f"No products found in {category}")
        except Exception as e:
            st.error(f"Error loading category products: {str(e)}")
    
    else:
        # Show recent searches when no active search
        try:
            searches = db_manager.get_search_history(user_id)
            if searches:
                st.markdown("### Recent Searches")
                for search in searches[:5]:
                    if st.button(f"🔍 {search}", key=f"recent_search_{search}", use_container_width=True):
                        # Set search term and rerun
                        st.session_state["main_search"] = search
                        st.rerun()
        except Exception as e:
            st.warning(f"Could not load search history: {str(e)}")
    
    # Display results
    if not results_df.empty:
        st.markdown(f"**Found {len(results_df)} products**")
        
        # Get current cart items
        cart_items = []
        if st.session_state.get('selected_client'):
            try:
                cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
                if not cart_items_df.empty:
                    cart_items = cart_items_df.to_dict('records')
            except Exception as e:
                st.warning(f"Could not load cart items: {str(e)}")
        
        # Display products with add to cart functionality
        for idx, product in results_df.iterrows():
            with st.container():
                # Display product info
                st.markdown(product_list_item_compact(product.to_dict(), cart_items, user_id, db_manager), unsafe_allow_html=True)
                
                # Action buttons
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    if st.button(f"View Details", key=f"view_{product['id']}", use_container_width=True):
                        st.session_state.show_product_detail = product.to_dict()
                        st.rerun()
                
                with col2:
                    # Get current quantity
                    current_qty = 0
                    cart_item_id = None
                    for item in cart_items:
                        if item.get('product_id') == product['id']:
                            current_qty = item.get('quantity', 0)
                            cart_item_id = item.get('id')
                            break
                    
                    if current_qty > 0:
                        if st.button("−", key=f"minus_{product['id']}"):
                            if current_qty == 1:
                                # Remove from cart
                                try:
                                    db_manager.remove_from_cart(cart_item_id)
                                    st.success("Removed from cart")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error removing from cart: {str(e)}")
                            else:
                                # Decrease quantity
                                try:
                                    db_manager.update_cart_quantity(cart_item_id, current_qty - 1)
                                    st.success("Updated quantity")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating quantity: {str(e)}")
                    else:
                        st.markdown(f"**Qty: {current_qty}**")
                
                with col3:
                    if st.button("+ Add", key=f"plus_{product['id']}", type="primary"):
                        if st.session_state.get('selected_client'):
                            if current_qty == 0:
                                # Add to cart
                                try:
                                    success, message = db_manager.add_to_cart(
                                        user_id, product['id'], st.session_state.selected_client
                                    )
                                    if success:
                                        st.success("Added to cart!")
                                        st.rerun()
                                    else:
                                        st.error(message)
                                except Exception as e:
                                    st.error(f"Error adding to cart: {str(e)}")
                            else:
                                # Increase quantity
                                try:
                                    db_manager.update_cart_quantity(cart_item_id, current_qty + 1)
                                    st.success("Updated quantity")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error updating quantity: {str(e)}")
                        else:
                            st.error("Please select a client first")
                
                st.divider()

def show_cart_page(user_id, db_manager):
    """Display cart page"""
    
    st.markdown("### Shopping Cart")
    
    if not st.session_state.get('selected_client'):
        empty_state("🛒", "No Client Selected", "Please select a client in the Profile tab to view cart")
        return
    
    try:
        cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
    except Exception as e:
        st.error(f"Error loading cart: {str(e)}")
        cart_items_df = pd.DataFrame()
    
    if cart_items_df.empty:
        empty_state("🛒", "Cart is Empty", "Add products using the Search tab to create a quote")
        return
    
    # Display cart items
    st.markdown("#### Items in Cart")
    total = 0
    for _, item in cart_items_df.iterrows():
        cart_item_component(item.to_dict(), db_manager)
        total += item['price'] * item['quantity']
    
    # Summary
    final_total = cart_summary(total)
    
    # Generate Quote button
    st.markdown("### ")
    if st.button("Generate Quote", use_container_width=True, type="primary"):
        with st.spinner("Generating quote..."):
            try:
                # Get client data
                client_data = db_manager.get_user_clients(user_id)
                client_data = client_data[client_data['id'] == st.session_state.selected_client].iloc[0].to_dict()
                
                # Create quote
                success, message, quote_number = db_manager.create_quote(
                    user_id, st.session_state.selected_client, cart_items_df
                )
                
                if success:
                    st.success(message)
                    
                    quote_data = {
                        'quote_number': quote_number,
                        'total_amount': final_total,
                        'created_at': datetime.now()
                    }
                    
                    st.session_state.last_quote = {
                        'quote_number': quote_number,
                        'total_amount': final_total,
                        'items': cart_items_df,
                        'client_data': client_data,
                        'quote_data': quote_data
                    }
                    
                    # Show quote details inline instead of navigating
                    st.markdown("---")
                    st.markdown("### Generated Quote")
                    st.success(f"Quote #{quote_number} created successfully!")
                    st.info("Quote export options are available in future updates.")
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error generating quote: {str(e)}")

def show_profile_page(user, auth_manager, sync_manager, db_manager):
    """Display profile page with client management"""
    
    st.markdown("### Profile")
    
    # User info section
    with st.expander("User Information", expanded=True):
        st.markdown(f"**Email:** {user.get('email', 'N/A')}")
        st.markdown(f"**Role:** {auth_manager.get_user_role().title()}")
        
        # Connection status
        if auth_manager.is_online:
            st.success("🟢 Connected to Supabase")
        else:
            st.warning("🔴 Running in offline mode")
    
    # Client Management Section
    st.markdown("### Client Management")
    
    # Add new client form
    with st.expander("Add New Client"):
        with st.form("add_client_form"):
            company = st.text_input("Company Name*", key="new_company")
            contact_name = st.text_input("Contact Name", key="new_contact_name")
            contact_email = st.text_input("Contact Email", key="new_contact_email")
            contact_number = st.text_input("Contact Phone", key="new_contact_number")
            
            if st.form_submit_button("Add Client", use_container_width=True):
                if company:
                    try:
                        success, message = db_manager.create_client(
                            user['id'], company, contact_name, contact_email, contact_number
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
    
    # Client list with quotes
    st.markdown("### My Clients")
    
    try:
        clients_df = db_manager.get_user_clients(user['id'])
        
        if clients_df.empty:
            empty_state("👥", "No Clients Yet", "Add your first client above")
        else:
            # Show current selected client
            if st.session_state.get('selected_client'):
                selected_client = clients_df[clients_df['id'] == st.session_state.selected_client]
                if not selected_client.empty:
                    st.info(f"✅ Selected Client: **{selected_client.iloc[0]['company']}**")
            
            # List all clients
            for _, client in clients_df.iterrows():
                with st.expander(f"**{client['company']}**"):
                    # Client details
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**Contact:** {client.get('contact_name', 'N/A')}")
                        st.markdown(f"**Email:** {client.get('contact_email', 'N/A')}")
                    with col2:
                        st.markdown(f"**Phone:** {client.get('contact_number', 'N/A')}")
                        st.markdown(f"**Added:** {pd.to_datetime(client['created_at']).strftime('%Y-%m-%d')}")
                    
                    # Select client button
                    if st.button(f"Select Client", key=f"select_{client['id']}", use_container_width=True, type="primary"):
                        st.session_state.selected_client = client['id']
                        st.success(f"Selected {client['company']}")
                        st.rerun()
                    
                    # Show client quotes
                    st.markdown("#### Quotes")
                    try:
                        quotes_df = db_manager.get_client_quotes(client['id'])
                        
                        if quotes_df.empty:
                            st.caption("No quotes for this client yet")
                        else:
                            for _, quote in quotes_df.iterrows():
                                col1, col2, col3 = st.columns([2, 1, 1])
                                with col1:
                                    st.markdown(f"**{quote['quote_number']}**")
                                    st.caption(pd.to_datetime(quote['created_at']).strftime('%Y-%m-%d'))
                                with col2:
                                    st.markdown(f"${quote['total_amount']:,.2f}")
                                with col3:
                                    if st.button("View", key=f"view_quote_{quote['id']}", use_container_width=True):
                                        # Load quote details for viewing
                                        st.session_state.view_quote_id = quote['id']
                                        st.info("Quote viewing coming soon!")
                    except Exception as e:
                        st.caption(f"Error loading quotes: {str(e)}")
    
    except Exception as e:
        st.error(f"Error loading clients: {str(e)}")
    
    # Admin functions (if applicable)
    try:
        if auth_manager.is_admin():
            with st.expander("Admin Functions"):
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
    except Exception as e:
        st.warning(f"Could not check admin status: {str(e)}")
    
    # Sign out
    st.markdown("### ")
    if st.button("Sign Out", use_container_width=True, type="secondary"):
        try:
            auth_manager.sign_out()
            st.rerun()
        except Exception as e:
            st.error(f"Error signing out: {str(e)}")

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
    if st.button("Add to Cart", use_container_width=True, type="primary"):
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
            st.markdown(f"**{item['sku']}**")
            if item.get('product_type'):
                st.caption(f"Model: {item['product_type']}")
        with col2:
            st.markdown(f"Qty: {item['quantity']}")
        with col3:
            st.markdown(format_price(item['price'] * item['quantity']))
    
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