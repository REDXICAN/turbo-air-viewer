"""
Page components for Turbo Air Equipment Viewer
Fixed with proper responsive design support and HTML-only categories
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from typing import Dict

from .ui import (
    app_header, search_bar_component, category_grid,
    product_list_item_compact, product_details_expanded, recent_searches_section,
    recent_quotes_section, metrics_section, cart_item_component,
    cart_summary, quote_export_buttons, empty_state, format_price,
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
    
    # Show metrics first to give immediate value
    try:
        stats = db_manager.get_dashboard_stats(user_id)
        if stats and (stats.get('total_clients', 0) > 0 or stats.get('total_quotes', 0) > 0):
            metrics_section(stats)
    except:
        pass
    
    # Recent searches
    try:
        searches = db_manager.get_search_history(user_id)
        if searches:
            recent_searches_section(searches)
    except:
        pass
    
    # Recent quotes
    try:
        quotes_df = db_manager.get_user_quotes(user_id, limit=5)
        if not quotes_df.empty:
            recent_quotes_section(quotes_df.to_dict('records'))
    except:
        pass
    
    # If no content, show empty state with action buttons
    has_content = False
    try:
        has_content = (
            bool(db_manager.get_search_history(user_id)) or
            not db_manager.get_user_quotes(user_id, limit=5).empty or
            db_manager.get_dashboard_stats(user_id).get('total_clients', 0) > 0
        )
    except:
        pass
    
    if not has_content:
        empty_state("🏠", "Start Your Quote", "Search for products or create a client to begin")
        
        # Add quick action buttons
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Browse Products", use_container_width=True, type="primary"):
                st.session_state.active_page = 'search'
                st.rerun()
        with col2:
            if st.button("👤 Add Client", use_container_width=True):
                st.session_state.active_page = 'profile'
                st.rerun()

def show_search_page(user_id, db_manager):
    """Display search/products page with HTML-only categories"""
    
    # Create sticky header with logo and search
    sticky_container = st.container()
    with sticky_container:
        st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
        
        # Logo
        logo_path = "Turboair_Logo_01.png"
        if os.path.exists(logo_path):
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.image(logo_path, use_container_width=True)
        else:
            st.markdown("""
            <h1 style='
                text-align: center; 
                margin: 0.5rem 0;
                font-size: 1.8rem;
            '>
                Turbo Air
            </h1>
            """, unsafe_allow_html=True)
        
        # Search title (will hide on scroll)
        st.markdown('<h3 class="search-title" style="text-align: center; margin: 0.5rem 0;">Search</h3>', unsafe_allow_html=True)
        
        # Search bar
        search_term = search_bar_component("Search by SKU, category or description")
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Content container
    st.markdown('<div style="padding: 0 16px;">', unsafe_allow_html=True)
    
    # Categories section with HTML-only implementation
    categories = []
    for cat_name, cat_info in TURBO_AIR_CATEGORIES.items():
        try:
            products_df = db_manager.get_products_by_category(cat_name)
            count = len(products_df) if products_df is not None and not products_df.empty else 0
        except:
            count = 0
        
        categories.append({
            "name": cat_name,
            "count": count,
            "icon": cat_info["icon"]
        })
    
    # Initialize categories state
    if 'categories_expanded' not in st.session_state:
        st.session_state.categories_expanded = True
    
    # HTML Categories section with proper styling
    st.markdown(f"""
    <div class="categories-section">
        <div class="categories-header">
            <h3 style="margin: 0;">Categories</h3>
            <span class="categories-toggle {'open' if st.session_state.categories_expanded else ''}">▼</span>
        </div>
        <div class="categories-content {'open' if st.session_state.categories_expanded else ''}">
            <div class="category-row">
    """, unsafe_allow_html=True)
    
    # Display category cards with proper HTML structure
    for i, category in enumerate(categories):
        category_html = f"""
        <div class="category-card" onclick="selectCategory('{category['name']}')">
            <div class="category-icon">{category['icon']}</div>
            <div class="category-name">{category['name']}</div>
            <div class="category-count">({category['count']} items)</div>
        </div>
        """
        
        if i % 2 == 0:  # Start new row every 2 items for mobile
            if i > 0:
                st.markdown('</div><div class="category-row">', unsafe_allow_html=True)
        
        st.markdown(category_html, unsafe_allow_html=True)
    
    st.markdown("""
            </div>
        </div>
    </div>
    
    <script>
        function selectCategory(categoryName) {
            // Store in sessionStorage for persistence
            sessionStorage.setItem('selectedCategory', categoryName);
            // Trigger page reload to handle category selection
            window.location.reload();
        }
        
        // Check for selected category on page load
        window.addEventListener('load', function() {
            const selectedCategory = sessionStorage.getItem('selectedCategory');
            if (selectedCategory) {
                sessionStorage.removeItem('selectedCategory');
                // Set session state for category
                fetch('/set_category', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({category: selectedCategory})
                });
            }
        });
    </script>
    """, unsafe_allow_html=True)
    
    # Handle search or category selection
    results_df = pd.DataFrame()
    
    # Check for category selection from JavaScript
    if 'temp_selected_category' in st.session_state:
        st.session_state.selected_category = st.session_state.temp_selected_category
        del st.session_state.temp_selected_category
    
    if search_term and len(search_term) >= 2:
        # Save to search history
        try:
            db_manager.add_search_history(user_id, search_term)
        except:
            pass
        
        # Search products
        st.markdown("### Search Results")
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
        # Show recent searches when no active search
        try:
            searches = db_manager.get_search_history(user_id)
            if searches:
                st.markdown("### Recent Searches")
                for search in searches[:5]:
                    if st.button(f"🔍 {search}", key=f"recent_search_{search}", use_container_width=True):
                        st.session_state.search_term = search
                        st.rerun()
        except:
            pass
    
    # Display results in compact format with images
    if not results_df.empty:
        st.markdown(f"### Results ({len(results_df)} items)")
        
        # Get current cart items
        cart_items = []
        if st.session_state.get('selected_client'):
            try:
                cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
                if not cart_items_df.empty:
                    cart_items = cart_items_df.to_dict('records')
            except:
                pass
        
        # Create list header
        st.markdown("""
        <div class="product-list-header">
            <div>Image</div>
            <div>SKU / Description</div>
            <div style="text-align: center;">Details</div>
            <div style="text-align: right;">Price</div>
            <div style="text-align: center;">Qty</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Display products with HTML-only controls
        for idx, product in results_df.iterrows():
            product_dict = product.to_dict()
            
            # Get current quantity
            current_qty = 0
            cart_item_id = None
            for item in cart_items:
                if item.get('product_id') == product['id']:
                    current_qty = item.get('quantity', 0)
                    cart_item_id = item.get('id')
                    break
            
            # Enhanced product row with quantity controls
            product_html = f"""
            <div class="product-row" id="product_{product['id']}">
                <div class="product-image-compact">
                    <img src="data:image/png;base64,{get_image_base64(f"pdf_screenshots/{product['sku']}/{product['sku']} P.1.png") or ''}" 
                         alt="{product['sku']}" onerror="this.parentElement.innerHTML='📷'">
                </div>
                <div class="product-info">
                    <div class="product-sku">{product['sku']}</div>
                    <div class="product-desc">{product.get('description', product.get('product_type', ''))}</div>
                </div>
                <div class="view-details-link" onclick="toggleDetails('{product['id']}')">View Details</div>
                <div class="product-price-compact">${product['price']:,.2f}</div>
                <div class="quantity-controls">
                    <button class="qty-btn" onclick="updateQuantity('{product['id']}', -1)" {'disabled' if current_qty == 0 else ''}>−</button>
                    <span class="qty-value" id="qty_{product['id']}">{current_qty}</span>
                    <button class="qty-btn" onclick="updateQuantity('{product['id']}', 1)">+</button>
                </div>
            </div>
            """
            
            st.markdown(product_html, unsafe_allow_html=True)
            
            # Show expanded details if toggled
            if st.session_state.get(f"expanded_{product['id']}", False):
                st.markdown(product_details_expanded(product_dict), unsafe_allow_html=True)
    
    # Add JavaScript for quantity controls and details toggle
    st.markdown("""
    <script>
        function updateQuantity(productId, change) {
            // Get current quantity
            const qtyElement = document.getElementById('qty_' + productId);
            let currentQty = parseInt(qtyElement.textContent);
            let newQty = Math.max(0, currentQty + change);
            
            // Update display
            qtyElement.textContent = newQty;
            
            // Update cart in backend (this would need to be implemented)
            // For now, we'll use sessionStorage to track changes
            const cartChanges = JSON.parse(sessionStorage.getItem('cartChanges') || '{}');
            cartChanges[productId] = { quantity: newQty, change: change };
            sessionStorage.setItem('cartChanges', JSON.stringify(cartChanges));
        }
        
        function toggleDetails(productId) {
            const detailsElement = document.getElementById('details_' + productId);
            if (detailsElement) {
                detailsElement.style.display = detailsElement.style.display === 'none' ? 'block' : 'none';
            } else {
                // Create details element if it doesn't exist
                // This would be handled by the backend in a real implementation
                console.log('Toggle details for product:', productId);
            }
        }
    </script>
    """, unsafe_allow_html=True)
    
    # Close content container
    st.markdown('</div>', unsafe_allow_html=True)

def show_cart_page(user_id, db_manager):
    """Display cart page"""
    
    st.markdown("### Cart")
    
    if not st.session_state.get('selected_client'):
        empty_state("🛒", "No Client Selected", "Please select a client to view cart")
        if st.button("Go to Profile", use_container_width=True):
            st.session_state.active_page = 'profile'
            st.rerun()
        return
    
    try:
        cart_items_df = db_manager.get_cart_items(user_id, st.session_state.selected_client)
    except:
        cart_items_df = pd.DataFrame()
    
    if cart_items_df.empty:
        empty_state("🛒", "Cart is Empty", "Add products to your cart to create a quote")
        if st.button("Browse Products", use_container_width=True):
            st.session_state.active_page = 'search'
            st.rerun()
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
                    success, message = db_manager.create_client(
                        user['id'], company, contact_name, contact_email, contact_number
                    )
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
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
                    st.info(f"Selected Client: **{selected_client.iloc[0]['company']}**")
            
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
                    if st.button(f"Select Client", key=f"select_{client['id']}", use_container_width=True):
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
                    except:
                        st.caption("Error loading quotes")
    
    except Exception as e:
        st.error(f"Error loading clients: {str(e)}")
    
    # Admin functions (if applicable)
    if auth_manager.is_admin():
        with st.expander("Admin Functions"):
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
    
    # Back button
    if st.button("← Back", key="back_from_detail"):
        st.session_state.show_product_detail = None
        st.rerun()
    
    # Product image
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
                st.markdown(f"""
                <div style="width: 100%; height: 200px; overflow: hidden; border-radius: 8px;">
                    <img src="data:image/png;base64,{image_base64}" 
                         style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                """, unsafe_allow_html=True)
                image_found = True
                break
        
        if not image_found:
            empty_state("📷", "No Image", "Product image not available")
    
    with col2:
        # Product info
        st.markdown(f"### {product['sku']}")
        st.markdown(f"**{product.get('product_type', 'N/A')}**")
        st.markdown(f"### {format_price(product.get('price', 0))}")
        
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
    
    for key, value in specs.items():
        if value and value != '-':
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
                # Don't close detail view, let user continue browsing
            else:
                st.error(message)
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
            except:
                st.warning("Email functionality not available")
    
    # Action buttons
    st.markdown("### ")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Create New Quote", use_container_width=True):
            # Clear cart and go to search
            try:
                db_manager = st.session_state.db_manager
                user_id = st.session_state.user['id']
                db_manager.clear_cart(user_id, st.session_state.selected_client)
                st.session_state.cart_count = 0
                st.session_state.active_page = 'search'
                st.rerun()
            except:
                st.session_state.active_page = 'search'
                st.rerun()
    
    with col2:
        if st.button("Back to Home", use_container_width=True, type="primary"):
            # Clear cart
            try:
                db_manager = st.session_state.db_manager
                user_id = st.session_state.user['id']
                db_manager.clear_cart(user_id, st.session_state.selected_client)
                st.session_state.cart_count = 0
            except:
                pass
            st.session_state.active_page = 'home'
            st.rerun()