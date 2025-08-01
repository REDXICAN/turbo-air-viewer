"""
Page components for Turbo Air Equipment Viewer
Fixed: Search bar position, removed welcome text, added live search
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Dict

from .ui import (
    mobile_search_bar, category_grid, quick_access_section,
    filter_row, product_list_item, metric_card, sync_status_bar,
    subcategory_list, summary_section, quantity_selector, empty_state,
    format_price, truncate_text, COLORS, TURBO_AIR_CATEGORIES
)
from .export import export_quote_to_excel, export_quote_to_pdf
from .email import show_email_quote_dialog

def show_home_page(user, user_id, db_manager, sync_manager, auth_manager):
    """Display home page with search at top"""
    
    # Search bar at the very top
    search_term = mobile_search_bar("Search products...")
    
    # User info and sync status row
    col1, col2 = st.columns([3, 1])
    with col1:
        st.caption(f"Hello, {user.get('email', 'User')}! • Role: {auth_manager.get_user_role().title()}")
    with col2:
        if st.button("Sign Out", key="signout", use_container_width=True):
            auth_manager.sign_out()
            st.rerun()
    
    # Sync status
    if sync_status_bar(
        st.session_state.sync_status.get('is_online', False),
        st.session_state.sync_status.get('pending_changes', 0) == 0
    ):
        sync_manager.sync_all()
        st.rerun()
    
    # Handle live search with thumbnails
    if search_term and len(search_term) >= 2:
        with st.spinner("Searching..."):
            results_df = db_manager.search_products(search_term)
            if not results_df.empty:
                st.markdown(f"### Search Results ({len(results_df)} items)")
                
                # Display results in a grid with thumbnails
                cols = st.columns(2)
                for idx, (_, product) in enumerate(results_df.iterrows()):
                    with cols[idx % 2]:
                        # Container for product card
                        with st.container():
                            # Try to show thumbnail
                            image_path = f"pdf_screenshots/{product['sku']}/{product['sku']} P.1.png"
                            if os.path.exists(image_path):
                                st.image(image_path, use_container_width=True)
                            else:
                                # Placeholder
                                st.markdown(f"""
                                <div style="height: 150px; background: #f0f0f0; 
                                            border-radius: 8px; display: flex; 
                                            align-items: center; justify-content: center;">
                                    <span style="color: #999;">No Image</span>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            st.markdown(f"**{product['sku']}**")
                            st.caption(f"{product.get('product_type', '-')}")
                            st.markdown(f"**${product.get('price', 0):,.2f}**")
                            
                            col_btn1, col_btn2 = st.columns(2)
                            with col_btn1:
                                if st.button("View", key=f"view_search_{product['id']}", use_container_width=True):
                                    st.session_state.show_product_detail = product.to_dict()
                                    st.rerun()
                            with col_btn2:
                                if st.button("Add to Cart", key=f"add_search_{product['id']}", use_container_width=True, type="primary"):
                                    if st.session_state.selected_client:
                                        success, message = db_manager.add_to_cart(
                                            user_id, product['id'], st.session_state.selected_client
                                        )
                                        if success:
                                            st.success("Added!")
                                            st.session_state.cart_count += 1
                                    else:
                                        st.error("Select a client first")
                
                st.divider()
                return  # Don't show categories when searching
    
    # Categories section (only show if not searching)
    st.markdown("### Categories")
    
    main_categories = []
    for cat_name, cat_info in TURBO_AIR_CATEGORIES.items():
        try:
            products_df = db_manager.get_products_by_category(cat_name)
            count = len(products_df) if products_df is not None else 0
        except:
            count = 0
        
        main_categories.append({
            "name": cat_name,
            "count": count,
            "icon": cat_info["icon"]
        })
    
    if main_categories:
        category_grid(main_categories)
    else:
        st.error("Failed to load categories")
    
    # Quick Access
    quick_access_section()
    
    # Clients section
    st.markdown("### Clients")
    
    try:
        clients_df = db_manager.get_user_clients(user_id)
    except:
        clients_df = pd.DataFrame()
    
    if not clients_df.empty:
        client_names = clients_df['company'].tolist()
        client_ids = clients_df['id'].tolist()
        
        selected_idx = st.selectbox(
            "Select Client",
            range(len(client_names)),
            format_func=lambda x: client_names[x],
            key="client_selector"
        )
        
        if selected_idx is not None:
            st.session_state.selected_client = client_ids[selected_idx]
            selected_client_data = clients_df.iloc[selected_idx]
            
            with st.expander("Client Details", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.text(f"Contact: {selected_client_data.get('contact_name', 'N/A')}")
                    st.text(f"Email: {selected_client_data.get('contact_email', 'N/A')}")
                with col2:
                    st.text(f"Phone: {selected_client_data.get('contact_number', 'N/A')}")
                    try:
                        quotes_df = db_manager.get_client_quotes(st.session_state.selected_client)
                        st.text(f"Quotes: {len(quotes_df)}")
                    except:
                        st.text("Quotes: 0")
    
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
    
    # Dashboard
    st.markdown("### Dashboard")
    try:
        stats = db_manager.get_dashboard_stats(user_id)
    except:
        stats = {
            'total_clients': 0,
            'total_quotes': 0,
            'recent_quotes': 0,
            'cart_items': 0
        }
    
    col1, col2 = st.columns(2)
    with col1:
        metric_card("Total Clients", stats['total_clients'])
        metric_card("Recent Quotes", stats['recent_quotes'])
    with col2:
        metric_card("Total Quotes", stats['total_quotes'])
        metric_card("Cart Items", stats['cart_items'])
    
    # Recent Search History
    try:
        search_history = db_manager.get_search_history(user_id)
        if search_history:
            st.markdown("### Recent Searches")
            for search_term in search_history[:5]:
                if st.button(f"🔍 {search_term}", key=f"recent_{search_term}", use_container_width=True):
                    st.session_state.search_term = search_term
                    st.session_state.active_page = 'search'
                    st.rerun()
    except:
        pass

def show_search_page(user_id, db_manager):
    """Display search/products page"""
    if st.button("← Back", key="back_to_home"):
        st.session_state.active_page = 'home'
        st.session_state.selected_category = None
        st.session_state.selected_subcategory = None
        st.rerun()
    
    # Search bar
    search_term = mobile_search_bar("Search by model or keyword")
    
    # Filters
    st.markdown("### Filters")
    filter_row()
    
    if search_term:
        # Add to search history
        if len(search_term) > 2:
            try:
                db_manager.add_search_history(user_id, search_term)
            except:
                pass
        
        # Search products
        try:
            results_df = db_manager.search_products(search_term)
        except Exception as e:
            st.error(f"Error searching products: {e}")
            results_df = pd.DataFrame()
    else:
        # Show categories if no search
        if not st.session_state.selected_category:
            st.markdown("### Browse by Category")
            
            categories = []
            for cat_name, cat_info in TURBO_AIR_CATEGORIES.items():
                try:
                    products_df = db_manager.get_products_by_category(cat_name)
                    count = len(products_df) if products_df is not None else 0
                except:
                    count = 0
                
                categories.append({
                    "name": cat_name,
                    "count": count,
                    "icon": cat_info["icon"]
                })
            
            if categories:
                category_grid(categories)
            results_df = pd.DataFrame()
        else:
            # Category is selected
            if st.button("← Back to Categories", key="back_to_categories"):
                st.session_state.selected_category = None
                st.session_state.selected_subcategory = None
                st.rerun()
            
            st.markdown(f"### {st.session_state.selected_category}")
            
            category_data = TURBO_AIR_CATEGORIES.get(st.session_state.selected_category, {})
            
            if category_data and category_data.get('subcategories'):
                if not st.session_state.selected_subcategory:
                    subcategory_list(category_data['subcategories'], st.session_state.selected_category)
                    results_df = pd.DataFrame()
                else:
                    if st.button("← Back to Subcategories", key="back_to_subcategories"):
                        st.session_state.selected_subcategory = None
                        st.rerun()
                    
                    st.markdown(f"#### {st.session_state.selected_subcategory}")
                    
                    try:
                        results_df = db_manager.get_products_by_category(
                            st.session_state.selected_category,
                            st.session_state.selected_subcategory
                        )
                    except:
                        results_df = pd.DataFrame()
            else:
                try:
                    results_df = db_manager.get_products_by_category(st.session_state.selected_category)
                except:
                    results_df = pd.DataFrame()
    
    # Display products
    if not results_df.empty:
        st.markdown(f"### Results ({len(results_df)} items)")
        
        for _, product in results_df.iterrows():
            st.markdown(product_list_item(product.to_dict()), unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Details", key=f"view_{product['id']}", use_container_width=True):
                    st.session_state.show_product_detail = product.to_dict()
            with col2:
                if st.button("Add to Cart", key=f"add_{product['id']}", use_container_width=True, type="primary"):
                    if st.session_state.selected_client:
                        success, message = db_manager.add_to_cart(
                            user_id, product['id'], st.session_state.selected_client
                        )
                        if success:
                            st.success("Added to cart!")
                            st.session_state.cart_count += 1
                            st.rerun()
                    else:
                        st.error("Please select a client first")
            st.divider()
    elif search_term:
        st.info("No products found")

def show_cart_page(user_id, db_manager):
    """Display cart page"""
    if st.button("← Back", key="back_from_cart"):
        st.session_state.active_page = 'home'
        st.rerun()
    
    if not st.session_state.selected_client:
        empty_state("🛒", "No Client Selected", "Please select a client to view cart", 
                   "Go to Home", lambda: setattr(st.session_state, 'active_page', 'home'))
    else:
        try:
            cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
        except:
            cart_items_df = pd.DataFrame()
        
        if cart_items_df.empty:
            empty_state("🛒", "Cart is Empty", "Add products to your cart to create a quote",
                       "Browse Products", lambda: setattr(st.session_state, 'active_page', 'search'))
        else:
            # Cart items
            total = 0
            for _, item in cart_items_df.iterrows():
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**{item['sku']}**")
                    st.caption(truncate_text(item.get('description', item.get('product_type', '')), 40))
                with col2:
                    st.markdown(f"**{format_price(item['price'])}**")
                
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    new_quantity = quantity_selector(item['quantity'], item['id'])
                    if new_quantity != item['quantity']:
                        db_manager.update_cart_quantity(item['id'], new_quantity)
                        st.rerun()
                with col2:
                    st.markdown(f"Subtotal: **{format_price(item['price'] * item['quantity'])}**")
                with col3:
                    if st.button("🗑️", key=f"remove_{item['id']}", help="Remove from cart"):
                        db_manager.remove_from_cart(item['id'])
                        st.rerun()
                
                total += item['price'] * item['quantity']
                st.divider()
            
            # Summary
            summary_total = summary_section(total)
            
            # Generate Quote button
            if st.button("Generate Quote", key="generate_quote", use_container_width=True, type="primary"):
                with st.spinner("Generating quote..."):
                    client_data = db_manager.get_user_clients(user_id)
                    client_data = client_data[client_data['id'] == st.session_state.selected_client].iloc[0].to_dict()
                    
                    success, message, quote_number = db_manager.create_quote(
                        user_id, st.session_state.selected_client, cart_items_df
                    )
                    
                    if success:
                        st.success(message)
                        
                        quote_data = {
                            'quote_number': quote_number,
                            'total_amount': summary_total,
                            'created_at': datetime.now()
                        }
                        
                        st.session_state.last_quote = {
                            'quote_number': quote_number,
                            'total_amount': summary_total,
                            'items': cart_items_df,
                            'client_data': client_data,
                            'quote_data': quote_data
                        }
                        
                        # Export options
                        st.markdown("### Export Quote")
                        
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            try:
                                excel_file = export_quote_to_excel(quote_data, cart_items_df, client_data)
                                with open(excel_file, 'rb') as f:
                                    st.download_button(
                                        "📊 Download Excel",
                                        f.read(),
                                        file_name=excel_file,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True
                                    )
                            except Exception as e:
                                st.error(f"Excel export error: {e}")
                        
                        with col2:
                            try:
                                pdf_file = export_quote_to_pdf(quote_data, cart_items_df, client_data)
                                with open(pdf_file, 'rb') as f:
                                    st.download_button(
                                        "📄 Download PDF",
                                        f.read(),
                                        file_name=pdf_file,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                            except Exception as e:
                                st.error(f"PDF export error: {e}")
                        
                        with col3:
                            if st.button("📧 Email Quote", use_container_width=True):
                                show_email_quote_dialog(quote_data, cart_items_df, client_data)
                        
                        if st.button("View Quote Summary", use_container_width=True, type="primary"):
                            st.session_state.active_page = 'quote_summary'
                            st.rerun()
                        
                        if st.button("Clear Cart and Start New Quote", use_container_width=True):
                            db_manager.clear_cart(user_id, st.session_state.selected_client)
                            st.rerun()
                    else:
                        st.error(message)

def show_profile_page(user, auth_manager, sync_manager, db_manager):
    """Display profile page with backup/restore options"""
    
    st.markdown("### Account Information")
    col1, col2 = st.columns(2)
    with col1:
        st.text("Email:")
        st.text("Role:")
    with col2:
        st.markdown(f"**{user.get('email', 'N/A')}**")
        st.markdown(f"**{auth_manager.get_user_role().title()}**")
    
    # Connection status
    st.markdown("### Connection Status")
    if auth_manager.is_online:
        st.success("🟢 Connected to Supabase")
    else:
        st.warning("🔴 Running in offline mode")
    
    # Settings
    st.markdown("### Settings")
    
    # Admin functions
    if auth_manager.is_admin():
        st.markdown("#### Admin Functions")
        
        # Database Backup/Restore
        with st.expander("📦 Database Backup & Restore"):
            # Initialize persistence manager if available
            if hasattr(st.session_state, 'persistence_manager'):
                persistence = st.session_state.persistence_manager
                
                # Show backup status
                status = persistence.get_backup_status()
                if status['last_backup']:
                    st.info(f"Last backup: {status['last_backup']}")
                st.text(f"Total backups: {status['backup_count']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button("🔄 Backup Now", use_container_width=True):
                        with st.spinner("Backing up database..."):
                            if persistence.manual_backup():
                                st.success("Database backed up successfully!")
                            else:
                                st.error("Backup failed")
                
                with col2:
                    if st.button("♻️ Restore Latest", use_container_width=True):
                        if st.checkbox("I understand this will overwrite current data"):
                            with st.spinner("Restoring database..."):
                                if persistence.manual_restore():
                                    st.success("Database restored! Please refresh the page.")
                                    st.rerun()
                                else:
                                    st.error("Restore failed")
                
                # Clean up old backups
                if st.button("🗑️ Clean Old Backups (>7 days)", use_container_width=True):
                    persistence.cleanup_old_backups(7)
                    st.success("Old backups cleaned")
            else:
                st.warning("Persistence manager not initialized")
        
        # Product Management
        with st.expander("📊 Product Management"):
            if st.button("🔄 Refresh Product Database", use_container_width=True):
                with st.spinner("Syncing products..."):
                    if sync_manager.sync_down_products():
                        st.success("Products updated successfully!")
                    else:
                        st.error("Failed to update products")
            
            if st.button("📤 Upload Products to Cloud", use_container_width=True):
                with st.spinner("Uploading products to Supabase..."):
                    success, message = db_manager.sync_products_to_supabase()
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
            
            if st.button("📥 Reload Products from Excel", use_container_width=True):
                with st.spinner("Loading products from Excel..."):
                    success, message = db_manager.load_products_from_excel()
                    if success:
                        st.success(message)
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(message)
            
            if st.button("📊 View System Stats", use_container_width=True):
                try:
                    total_products = len(db_manager.get_all_products())
                    st.info(f"Total Products: {total_products}")
                except:
                    st.error("Could not load system stats")
    
    # User actions
    st.markdown("### Actions")
    
    # Clear search history
    if st.button("🗑️ Clear Search History", use_container_width=True):
        success, message = db_manager.clear_search_history(user.get('id', 'offline_user'))
        if success:
            st.success(message)
    
    # Test email configuration
    with st.expander("Email Settings"):
        if st.button("✉️ Test Email Configuration", use_container_width=True):
            from .email import get_email_service
            email_service = get_email_service()
            if email_service:
                test_email = st.text_input("Test email address", value=user.get('email', ''))
                if test_email and st.button("Send Test Email", use_container_width=True):
                    if email_service.send_test_email(test_email):
                        st.success("Test email sent successfully!")
                    else:
                        st.error("Failed to send test email")
            else:
                st.error("Email service not configured")
    
    # Sign out
    st.markdown("### ")  # Spacer
    if st.button("Sign Out", key="profile_signout", use_container_width=True, type="primary"):
        auth_manager.sign_out()
        st.rerun()

def show_product_detail(product: Dict, user_id: str, db_manager):
    """Display product detail modal"""
    if st.button("← Back to Products", key="back_from_detail"):
        st.session_state.show_product_detail = None
        st.rerun()
    
    # Product images
    col1, col2 = st.columns(2)
    
    with col1:
        image_path = f"pdf_screenshots/{product['sku']}/{product['sku']} P.1.png"
        if os.path.exists(image_path):
            st.image(image_path, caption="Page 1", use_container_width=True)
        else:
            st.markdown(f"""
            <div style="height: 200px; background: {COLORS['surface']}; 
                        border-radius: 12px; display: flex; align-items: center; 
                        justify-content: center;">
                <span style="color: {COLORS['text_secondary']};">No Image</span>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        image_path = f"pdf_screenshots/{product['sku']}/{product['sku']} P.2.png"
        if os.path.exists(image_path):
            st.image(image_path, caption="Page 2", use_container_width=True)
        else:
            st.markdown(f"""
            <div style="height: 200px; background: {COLORS['surface']}; 
                        border-radius: 12px; display: flex; align-items: center; 
                        justify-content: center;">
                <span style="color: {COLORS['text_secondary']};">No Image</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Product info
    st.markdown(f"### {product['sku']}")
    st.markdown(f"**{product.get('product_type') or '-'}**")
    st.markdown(f"### {format_price(product.get('price', 0))}")
    
    if product.get('description'):
        st.markdown(product['description'])
    
    # Specifications
    st.markdown("### Specifications")
    
    # Helper function to display value or "-"
    def display_value(value):
        return value if value else "-"
    
    specs_left = {
        "Capacity": display_value(product.get('capacity')),
        "Dimensions": display_value(product.get('dimensions')),
        "Weight": display_value(product.get('weight')),
        "Voltage": display_value(product.get('voltage')),
        "Amperage": display_value(product.get('amperage'))
    }
    
    specs_right = {
        "Temperature Range": display_value(product.get('temperature_range')),
        "Refrigerant": display_value(product.get('refrigerant')),
        "Compressor": display_value(product.get('compressor')),
        "Shelves": display_value(product.get('shelves')),
        "Doors": display_value(product.get('doors'))
    }
    
    col1, col2 = st.columns(2)
    
    with col1:
        for key, value in specs_left.items():
            st.caption(key)
            st.markdown(f"**{value}**")
    
    with col2:
        for key, value in specs_right.items():
            st.caption(key)
            st.markdown(f"**{value}**")
    
    if product.get('features'):
        st.markdown("### Features")
        st.markdown(product['features'])
    
    if product.get('certifications'):
        st.markdown("### Certifications")
        st.markdown(product['certifications'])
    
    # Datasheet section
    st.markdown("### Datasheet")
    datasheet_col1, datasheet_col2 = st.columns([1, 3])
    with datasheet_col1:
        st.markdown(f"""
        <div style="width: 60px; height: 60px; background: {COLORS['primary']}; 
                   border-radius: 12px; display: flex; align-items: center; 
                   justify-content: center; color: white; font-size: 28px;">📄</div>
        """, unsafe_allow_html=True)
    with datasheet_col2:
        st.markdown(f"**{product['sku']} Datasheet**")
        st.caption("View detailed specifications and dimensions")
    
    st.markdown("### ")  # Spacer
    
    # Add to Cart button
    if st.button("Add to Cart", key="detail_add_to_cart", use_container_width=True, type="primary"):
        if st.session_state.selected_client:
            success, message = db_manager.add_to_cart(
                user_id, product['id'], st.session_state.selected_client
            )
            if success:
                st.success("Added to cart!")
                st.session_state.cart_count += 1
                st.session_state.show_product_detail = None
                st.rerun()
        else:
            st.error("Please select a client first")
            if st.button("Go to Home to Select Client", use_container_width=True):
                st.session_state.show_product_detail = None
                st.session_state.active_page = 'home'
                st.rerun()

def show_quote_summary(quote: Dict):
    """Display quote summary page"""
    if st.button("← Back", key="back_from_summary"):
        st.session_state.active_page = 'cart'
        st.rerun()
    
    st.markdown("### Equipment List")
    for _, item in quote['items'].iterrows():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**{item['sku']}**")
            st.caption(f"Model: {item.get('product_type', 'N/A')}")
        with col2:
            st.text(f"Qty: {item['quantity']}")
        with col3:
            st.text(f"{format_price(item['price'] * item['quantity'])}")
    
    st.markdown("### Pricing Details")
    subtotal = quote['total_amount'] / 1.075
    summary_section(subtotal)
    
    # Export buttons
    st.markdown("### Export Options")
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
            st.error(f"PDF export error: {e}")
    
    # Email option
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