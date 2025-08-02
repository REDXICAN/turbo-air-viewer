"""
Page components for Turbo Air Equipment Viewer
Updated for new UI with bottom navigation
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Dict

from .ui import (
    app_header, search_bar_component, category_grid,
    bottom_navigation, product_list_item, recent_searches_section,
    recent_quotes_section, metrics_section, cart_item_component,
    cart_summary, quote_export_buttons, empty_state, format_price,
    truncate_text, COLORS, TURBO_AIR_CATEGORIES
)
from .export import export_quote_to_excel, export_quote_to_pdf
from .email import show_email_quote_dialog

def show_home_page(user, user_id, db_manager, sync_manager, auth_manager):
    """Display home page with search and categories"""
    
    # App header
    app_header()
    
    # Search bar
    search_term = search_bar_component("Search for products")
    
    # Handle search
    if search_term and len(search_term) >= 2:
        # Save search term and redirect to search page
        st.session_state.search_term = search_term
        st.session_state.active_page = 'search'
        st.rerun()
    
    # Categories section
    st.markdown("### Categories")
    
    # Get categories with counts
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
    
    # Quick Access buttons
    st.markdown("### Quick Access")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("❄️ Refrigerators", use_container_width=True):
            st.session_state.selected_category = "REACH-IN REFRIGERATION"
            st.session_state.active_page = 'search'
            st.rerun()
    
    with col2:
        if st.button("❄️ Freezers", use_container_width=True):
            st.session_state.selected_category = "REACH-IN REFRIGERATION"
            st.session_state.active_page = 'search'
            st.rerun()
    
    col3, col4 = st.columns(2)
    with col3:
        if st.button("🍕 Pizza Prep", use_container_width=True):
            st.session_state.selected_category = "FOOD PREP TABLES"
            st.session_state.active_page = 'search'
            st.rerun()
    
    with col4:
        if st.button("🍔 Prep Tables", use_container_width=True):
            st.session_state.selected_category = "FOOD PREP TABLES"
            st.session_state.active_page = 'search'
            st.rerun()
    
    # Recent searches
    try:
        searches = db_manager.get_search_history(user_id)
        recent_searches_section(searches)
    except:
        pass
    
    # Recent quotes
    try:
        quotes_df = db_manager.get_client_quotes(st.session_state.get('selected_client'))
        if not quotes_df.empty:
            recent_quotes_section(quotes_df.to_dict('records'))
    except:
        pass
    
    # Metrics
    try:
        stats = db_manager.get_dashboard_stats(user_id)
        metrics_section(stats)
    except:
        pass

def show_search_page(user_id, db_manager):
    """Display search/products page"""
    
    # App header
    app_header()
    
    # Search bar
    search_term = search_bar_component("Search by model or keyword")
    
    results_df = pd.DataFrame()
    
    if search_term:
        # Save to search history
        if len(search_term) > 2:
            try:
                db_manager.add_search_history(user_id, search_term)
            except:
                pass
        
        # Search products
        try:
            results_df = db_manager.search_products(search_term)
        except:
            st.error("Error searching products")
    
    elif st.session_state.get('selected_category'):
        # Show category products
        category = st.session_state.selected_category
        
        st.markdown(f"### {category}")
        
        try:
            results_df = db_manager.get_products_by_category(category)
        except:
            st.error("Error loading category products")
    
    else:
        # Show all categories
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
    
    # Display results
    if not results_df.empty:
        st.markdown(f"### Results ({len(results_df)} items)")
        
        for _, product in results_df.iterrows():
            st.markdown(product_list_item(product.to_dict()), unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("View Details", key=f"view_{product['id']}", use_container_width=True):
                    st.session_state.show_product_detail = product.to_dict()
                    st.rerun()
            with col2:
                if st.button("Add to Cart", key=f"add_{product['id']}", use_container_width=True, type="primary"):
                    if st.session_state.get('selected_client'):
                        success, message = db_manager.add_to_cart(
                            user_id, product['id'], st.session_state.selected_client
                        )
                        if success:
                            st.success("Added to cart!")
                            st.session_state.cart_count = st.session_state.get('cart_count', 0) + 1
                    else:
                        st.error("Please select a client first")
            st.divider()

def show_cart_page(user_id, db_manager):
    """Display cart page"""
    
    # App header
    app_header()
    
    st.markdown("### Cart")
    
    if not st.session_state.get('selected_client'):
        empty_state("🛒", "No Client Selected", "Please select a client to view cart")
        return
    
    try:
        cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
    except:
        cart_items_df = pd.DataFrame()
    
    if cart_items_df.empty:
        empty_state("🛒", "Cart is Empty", "Add products to your cart to create a quote")
        return
    
    # Display cart items
    total = 0
    for _, item in cart_items_df.iterrows():
        cart_item_component(item.to_dict(), db_manager)
        total += item['price'] * item['quantity']
    
    # Summary
    final_total = cart_summary(total)
    
    # Generate Quote button
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
                    
                    st.session_state.active_page = 'quote_summary'
                    st.rerun()
                else:
                    st.error(message)
            except Exception as e:
                st.error(f"Error generating quote: {str(e)}")

def show_profile_page(user, auth_manager, sync_manager, db_manager):
    """Display profile page"""
    
    # App header
    app_header()
    
    st.markdown("### Profile")
    
    # User info
    st.markdown(f"**Email:** {user.get('email', 'N/A')}")
    st.markdown(f"**Role:** {auth_manager.get_user_role().title()}")
    
    # Connection status
    if auth_manager.is_online:
        st.success("🟢 Connected to Supabase")
    else:
        st.warning("🔴 Running in offline mode")
    
    # Admin functions
    if auth_manager.is_admin():
        st.markdown("#### Admin Functions")
        
        if st.button("🔄 Sync Database", use_container_width=True):
            with st.spinner("Syncing..."):
                result = sync_manager.sync_all()
                if result['success']:
                    st.success(result['message'])
                else:
                    st.error(result['message'])
    
    # Sign out
    st.markdown("### ")
    if st.button("Sign Out", use_container_width=True, type="primary"):
        auth_manager.sign_out()
        st.rerun()

def show_product_detail(product: Dict, user_id: str, db_manager):
    """Display product detail modal"""
    
    # App header
    app_header()
    
    # Back button
    if st.button("← Back", key="back_from_detail"):
        st.session_state.show_product_detail = None
        st.rerun()
    
    # Product image
    image_path = f"pdf_screenshots/{product['sku']}/{product['sku']} P.1.png"
    if os.path.exists(image_path):
        st.image(image_path, use_container_width=True)
    else:
        empty_state("📷", "No Image", "Product image not available")
    
    # Product info
    st.markdown(f"### {product['sku']}")
    st.markdown(f"**{product.get('product_type', 'N/A')}**")
    st.markdown(f"### {format_price(product.get('price', 0))}")
    
    if product.get('description'):
        st.markdown(product['description'])
    
    # Specifications
    st.markdown("### Specifications")
    
    specs = {
        "Capacity": product.get('capacity', '-'),
        "Dimensions": product.get('dimensions', '-'),
        "Weight": product.get('weight', '-'),
        "Voltage": product.get('voltage', '-'),
        "Temperature Range": product.get('temperature_range', '-'),
        "Refrigerant": product.get('refrigerant', '-')
    }
    
    for key, value in specs.items():
        st.markdown(f"**{key}:** {value}")
    
    # Add to Cart button
    if st.button("Add to Cart", use_container_width=True, type="primary"):
        if st.session_state.get('selected_client'):
            success, message = db_manager.add_to_cart(
                user_id, product['id'], st.session_state.selected_client
            )
            if success:
                st.success("Added to cart!")
                st.session_state.cart_count = st.session_state.get('cart_count', 0) + 1
                st.session_state.show_product_detail = None
                st.rerun()
        else:
            st.error("Please select a client first")

def show_quote_summary(quote: Dict):
    """Display quote summary page"""
    
    # App header
    app_header()
    
    st.markdown("### Quote Summary")
    
    # Equipment list
    st.markdown("### Equipment List")
    for _, item in quote['items'].iterrows():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.markdown(f"**{item['sku']}**")
            st.caption(f"Model: {item.get('product_type', 'N/A')}")
        with col2:
            st.text(f"Qty: {item['quantity']}")
        with col3:
            st.text(format_price(item['price'] * item['quantity']))
    
    # Pricing details
    st.markdown("### Pricing Details")
    cart_summary(quote['total_amount'] / 1.08)  # Assuming 8% tax
    
    # Export buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Export as Excel", use_container_width=True):
            try:
                excel_file = export_quote_to_excel(
                    quote['quote_data'], 
                    quote['items'], 
                    quote['client_data']
                )
                with open(excel_file, 'rb') as f:
                    st.download_button(
                        "📊 Download Excel",
                        f.read(),
                        file_name=excel_file,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Export error: {e}")
    
    with col2:
        if st.button("Export as PDF", use_container_width=True, type="primary"):
            try:
                pdf_file = export_quote_to_pdf(
                    quote['quote_data'], 
                    quote['items'], 
                    quote['client_data']
                )
                with open(pdf_file, 'rb') as f:
                    st.download_button(
                        "📄 Download PDF",
                        f.read(),
                        file_name=pdf_file,
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"Export error: {e}")
    
    # Back to home
    if st.button("Back to Home", use_container_width=True):
        # Clear cart
        db_manager = st.session_state.db_manager
        user_id = st.session_state.user['id']
        db_manager.clear_cart(user_id, st.session_state.selected_client)
        
        st.session_state.active_page = 'home'
        st.rerun()