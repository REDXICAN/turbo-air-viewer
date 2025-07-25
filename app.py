"""
Turbo Air Equipment Viewer - Main Application
Mobile-first responsive equipment catalog and quote generation system
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Page configuration MUST be first Streamlit command
st.set_page_config(
    page_title="Turbo Air Equipment Viewer",
    page_icon="❄️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize database if it doesn't exist
if not os.path.exists('turbo_air_db_online.sqlite'):
    try:
        import create_database
        create_database.main()
    except Exception as e:
        st.error(f"Error creating database: {e}")

# Initialize session state variables
def init_session_state():
    """Initialize all session state variables"""
    defaults = {
        'user': None,
        'user_role': 'distributor',
        'active_page': 'home',
        'selected_category': None,
        'selected_subcategory': None,
        'selected_client': None,
        'view_mode': 'grid',
        'cart_count': 0,
        'show_product_detail': None,
        'auth_manager': None,
        'db_manager': None,
        'sync_manager': None,
        'sync_status': {
            'is_online': False,
            'last_sync': None,
            'pending_changes': 0,
            'sync_errors': []
        }
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

# Call this before anything else
init_session_state()

# Import after session state is initialized
try:
    from supabase import create_client
    HAS_SUPABASE = True
except ImportError:
    HAS_SUPABASE = False
    st.warning("Supabase not available - running in offline mode")

# Import custom modules
from auth import AuthManager, show_auth_form
from database import DatabaseManager
from sync_manager import SyncManager, show_sync_status, manual_sync_button
from ui_components import (
    apply_custom_css, mobile_navigation, desktop_navigation,
    product_card, search_bar, category_grid, quantity_selector,
    success_message, loading_spinner, empty_state, confirm_dialog,
    format_price, truncate_text, COLORS
)
from export_utils import export_quote_to_excel, export_quote_to_pdf
from email_service import show_email_quote_dialog, get_email_service

# Initialize services
@st.cache_resource
def init_services():
    """Initialize all services"""
    supabase_client = None
    supabase_url = None
    supabase_key = None
    
    try:
        # Get Supabase credentials from secrets
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["anon_key"]
        
        if HAS_SUPABASE and supabase_url and supabase_key:
            try:
                supabase_client = create_client(supabase_url, supabase_key)
                # Test connection with a simple query
                supabase_client.table('products').select('id').limit(1).execute()
                print("Successfully connected to Supabase")
            except Exception as e:
                print(f"Supabase connection failed: {e}")
                supabase_client = None
    except Exception as e:
        print(f"Could not load Supabase credentials: {e}")
    
    # Initialize managers with whatever we have (online or offline)
    auth_manager = AuthManager(supabase_url, supabase_key)
    db_manager = DatabaseManager(supabase_client)
    sync_manager = SyncManager(db_manager, supabase_client)
    
    return auth_manager, db_manager, sync_manager

# Initialize services
try:
    auth_manager, db_manager, sync_manager = init_services()
    st.session_state.auth_manager = auth_manager
    st.session_state.db_manager = db_manager
    st.session_state.sync_manager = sync_manager
except Exception as e:
    st.error(f"Failed to initialize services: {e}")
    st.stop()

# Apply custom CSS
apply_custom_css()

# Check if user is authenticated
if not auth_manager.is_authenticated():
    # Show authentication page
    st.markdown(f"<h1 style='text-align: center; color: {COLORS['turbo_blue']}'>Turbo Air Equipment Viewer</h1>", 
                unsafe_allow_html=True)
    show_auth_form()
else:
    # Update sync status safely
    try:
        sync_manager.update_sync_status()
    except Exception as e:
        st.error(f"Error updating sync status: {e}")
    
    # Get current user
    user = auth_manager.get_current_user()
    user_id = user['id'] if user else 'offline_user'
    
    # Update cart count
    if st.session_state.selected_client:
        try:
            cart_items = db_manager.get_cart_items(user_id, st.session_state.selected_client)
            st.session_state.cart_count = len(cart_items)
        except Exception as e:
            st.error(f"Error loading cart: {e}")
            st.session_state.cart_count = 0
    
    # Detect device type (simplified)
    is_mobile = st.session_state.get('is_mobile', True)
    
    # Navigation
    if is_mobile:
        mobile_navigation(st.session_state.active_page)
    else:
        desktop_navigation(st.session_state.active_page)
    
    # Route to appropriate page
    if st.session_state.active_page == 'home':
        # Home Page
        st.title("Welcome to Turbo Air")
        
        # User Profile Card
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"### Hello, {user.get('email', 'User')}!")
                st.caption(f"Role: {auth_manager.get_user_role().title()}")
            with col2:
                if st.button("Sign Out", use_container_width=True):
                    auth_manager.sign_out()
                    st.rerun()
        
        # Sync Status
        show_sync_status()
        manual_sync_button(sync_manager)
        
        # Client Selection/Creation
        st.markdown("### Clients")
        
        try:
            clients_df = db_manager.get_user_clients(user_id)
        except Exception as e:
            st.error(f"Error loading clients: {e}")
            clients_df = pd.DataFrame()
        
        if not clients_df.empty:
            # Show existing clients
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
                
                # Show client info
                with st.expander("Client Details", expanded=True):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.text(f"Contact: {selected_client_data.get('contact_name', 'N/A')}")
                        st.text(f"Email: {selected_client_data.get('contact_email', 'N/A')}")
                    with col2:
                        st.text(f"Phone: {selected_client_data.get('contact_number', 'N/A')}")
                        
                        # Show quotes for this client
                        try:
                            quotes_df = db_manager.get_client_quotes(st.session_state.selected_client)
                            st.text(f"Quotes: {len(quotes_df)}")
                        except:
                            st.text("Quotes: 0")
        
        # Create new client form
        with st.expander("Create New Client"):
            with st.form("new_client_form"):
                company = st.text_input("Company Name*", key="new_company")
                contact_name = st.text_input("Contact Name", key="new_contact")
                contact_email = st.text_input("Contact Email", key="new_email")
                contact_number = st.text_input("Contact Phone", key="new_phone")
                
                if st.form_submit_button("Create Client", type="primary"):
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
        
        # Dashboard Stats
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
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Clients", stats['total_clients'])
        with col2:
            st.metric("Total Quotes", stats['total_quotes'])
        with col3:
            st.metric("Recent Quotes", stats['recent_quotes'])
        with col4:
            st.metric("Cart Items", stats['cart_items'])
        
        # Recent Search History
        try:
            search_history = db_manager.get_search_history(user_id)
            if search_history:
                st.markdown("### Recent Searches")
                for search_term in search_history[:5]:
                    if st.button(f"🔍 {search_term}", key=f"recent_{search_term}"):
                        st.session_state.search_term = search_term
                        st.session_state.active_page = 'search'
                        st.rerun()
        except:
            pass
    
    elif st.session_state.active_page == 'search' or st.session_state.active_page == 'products':
        # Search/Products Page
        st.title("Products")
        
        # Search bar
        search_term = st.text_input("", placeholder="Search products...", key="product_search")
        
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
            
            if not results_df.empty:
                st.markdown(f"Found {len(results_df)} products")
                
                # View mode toggle
                col1, col2 = st.columns([1, 1])
                with col2:
                    view_mode = st.radio("View", ["Grid", "List"], horizontal=True, key="view_toggle")
                    st.session_state.view_mode = view_mode.lower()
                
                # Display results
                if st.session_state.view_mode == 'grid':
                    # Grid view
                    cols = st.columns(3 if not is_mobile else 2)
                    for idx, (_, product) in enumerate(results_df.iterrows()):
                        with cols[idx % (3 if not is_mobile else 2)]:
                            # Product card
                            with st.container():
                                # Try to show product image
                                image_path = f"pdf_screenshots/{product['sku']}/page_1.png"
                                if os.path.exists(image_path):
                                    st.image(image_path, use_container_width=True)
                                else:
                                    st.markdown(f"""
                                    <div style="background: {COLORS['background_light']}; 
                                                height: 200px; display: flex; align-items: center; 
                                                justify-content: center; border-radius: 8px;">
                                        <span>No Image</span>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                st.markdown(f"**{product['sku']}**")
                                st.caption(truncate_text(product.get('product_type', ''), 30))
                                st.markdown(f"**{format_price(product.get('price', 0))}**")
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("View", key=f"view_{product['id']}", use_container_width=True):
                                        st.session_state.show_product_detail = product.to_dict()
                                with col2:
                                    if st.button("Add +", key=f"add_{product['id']}", type="primary", use_container_width=True):
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
                else:
                    # List view
                    for _, product in results_df.iterrows():
                        with st.container():
                            col1, col2, col3, col4 = st.columns([1, 3, 1, 1])
                            
                            with col1:
                                # Thumbnail
                                image_path = f"pdf_screenshots/{product['sku']}/page_1.png"
                                if os.path.exists(image_path):
                                    st.image(image_path, width=60)
                            
                            with col2:
                                st.markdown(f"**{product['sku']}**")
                                st.caption(product.get('product_type', ''))
                            
                            with col3:
                                st.markdown(format_price(product.get('price', 0)))
                            
                            with col4:
                                if st.button("Add", key=f"add_list_{product['id']}"):
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
            else:
                st.info("No products found")
        
        else:
            # Show categories
            st.markdown("### Browse by Category")
            
            try:
                categories = db_manager.get_categories()
            except:
                categories = []
            
            if st.session_state.selected_category:
                # Show subcategories or products
                st.button("← Back to Categories", key="back_to_categories", 
                         on_click=lambda: setattr(st.session_state, 'selected_category', None))
                
                st.markdown(f"### {st.session_state.selected_category}")
                
                # Get category data
                category_data = next((c for c in categories if c['name'] == st.session_state.selected_category), None)
                
                if category_data and category_data['subcategories']:
                    # Show subcategories
                    cols = st.columns(2 if is_mobile else 3)
                    for idx, subcat in enumerate(category_data['subcategories']):
                        with cols[idx % (2 if is_mobile else 3)]:
                            if st.button(subcat, key=f"subcat_{subcat}", use_container_width=True):
                                st.session_state.selected_subcategory = subcat
                                st.rerun()
                
                # Show products in category
                try:
                    if st.session_state.selected_subcategory:
                        products_df = db_manager.get_products_by_category(
                            st.session_state.selected_category,
                            st.session_state.selected_subcategory
                        )
                    else:
                        products_df = db_manager.get_products_by_category(st.session_state.selected_category)
                except:
                    products_df = pd.DataFrame()
                
                if not products_df.empty:
                    # Similar display logic as search results
                    pass
            else:
                # Show main categories
                category_grid(categories)
    
    elif st.session_state.active_page == 'cart':
        # Cart Page
        st.title("Cart")
        
        if not st.session_state.selected_client:
            empty_state("🛒", "No Client Selected", "Please select a client to view cart", 
                       "Go to Home", lambda: setattr(st.session_state, 'active_page', 'home'))
        else:
            # Get cart items
            try:
                cart_items = db_manager.get_cart_items(user_id, st.session_state.selected_client)
            except Exception as e:
                st.error(f"Error loading cart: {e}")
                cart_items = pd.DataFrame()
            
            if cart_items.empty:
                empty_state("🛒", "Cart is Empty", "Add products to your cart to create a quote",
                           "Browse Products", lambda: setattr(st.session_state, 'active_page', 'search'))
            else:
                # Display cart items
                total = 0
                
                for _, item in cart_items.iterrows():
                    with st.container():
                        col1, col2, col3, col4, col5 = st.columns([1, 3, 1, 1, 1])
                        
                        with col1:
                            # Product image
                            image_path = f"pdf_screenshots/{item['sku']}/page_1.png"
                            if os.path.exists(image_path):
                                st.image(image_path, width=60)
                        
                        with col2:
                            st.markdown(f"**{item['sku']}**")
                            st.caption(truncate_text(item.get('description', ''), 40))
                        
                        with col3:
                            st.markdown(format_price(item['price']))
                        
                        with col4:
                            # Quantity controls
                            new_quantity = quantity_selector(item['quantity'], item['id'])
                            if new_quantity != item['quantity']:
                                db_manager.update_cart_quantity(item['id'], new_quantity)
                                st.rerun()
                        
                        with col5:
                            if st.button("🗑️", key=f"remove_{item['id']}"):
                                db_manager.remove_from_cart(item['id'])
                                st.rerun()
                        
                        item_total = item['price'] * item['quantity']
                        total += item_total
                        st.caption(f"Subtotal: {format_price(item_total)}")
                    
                    st.divider()
                
                # Summary section
                st.markdown("### Summary")
                st.markdown(f"**Total: {format_price(total)}**")
                
                # Generate Quote button
                if st.button("Generate Quote", type="primary", use_container_width=True):
                    with st.spinner("Generating quote..."):
                        # Get client data
                        client_data = db_manager.get_user_clients(user_id)
                        client_data = client_data[client_data['id'] == st.session_state.selected_client].iloc[0].to_dict()
                        
                        # Create quote
                        success, message, quote_number = db_manager.create_quote(
                            user_id, st.session_state.selected_client, cart_items
                        )
                        
                        if success:
                            st.success(message)
                            
                            # Prepare quote data
                            quote_data = {
                                'quote_number': quote_number,
                                'total_amount': total,
                                'created_at': datetime.now()
                            }
                            
                            # Export options
                            st.markdown("### Export Quote")
                            
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                excel_file = export_quote_to_excel(quote_data, cart_items, client_data)
                                with open(excel_file, 'rb') as f:
                                    st.download_button(
                                        "📊 Download Excel",
                                        f.read(),
                                        file_name=excel_file,
                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                        use_container_width=True
                                    )
                            
                            with col2:
                                pdf_file = export_quote_to_pdf(quote_data, cart_items, client_data)
                                with open(pdf_file, 'rb') as f:
                                    st.download_button(
                                        "📄 Download PDF",
                                        f.read(),
                                        file_name=pdf_file,
                                        mime="application/pdf",
                                        use_container_width=True
                                    )
                            
                            with col3:
                                if st.button("📧 Email Quote", use_container_width=True):
                                    show_email_quote_dialog(quote_data, cart_items, client_data)
                            
                            # Clear cart option
                            if st.button("Clear Cart", use_container_width=True):
                                db_manager.clear_cart(user_id, st.session_state.selected_client)
                                st.rerun()
                        else:
                            st.error(message)
    
    elif st.session_state.active_page == 'profile':
        # Profile Page
        st.title("Profile")
        
        # User info
        st.markdown("### Account Information")
        st.text(f"Email: {user.get('email', 'N/A')}")
        st.text(f"Role: {auth_manager.get_user_role().title()}")
        
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
            
            if st.button("🔄 Refresh Product Database"):
                with st.spinner("Syncing products..."):
                    if sync_manager.sync_down_products():
                        st.success("Products updated successfully!")
                    else:
                        st.error("Failed to update products")
            
            if st.button("📊 View System Stats"):
                # Show system-wide statistics
                pass
        
        # Clear search history
        if st.button("🗑️ Clear Search History"):
            success, message = db_manager.clear_search_history(user_id)
            if success:
                st.success(message)
        
        # Test email configuration
        if st.button("✉️ Test Email Configuration"):
            email_service = get_email_service()
            if email_service:
                test_email = st.text_input("Test email address", value=user.get('email', ''))
                if test_email and st.button("Send Test Email"):
                    if email_service.send_test_email(test_email):
                        st.success("Test email sent successfully!")
                    else:
                        st.error("Failed to send test email")
            else:
                st.error("Email service not configured")
        
        # Sign out
        if st.button("Sign Out", type="primary", use_container_width=True):
            auth_manager.sign_out()
            st.rerun()
    
    # Product Detail Modal
    if st.session_state.show_product_detail:
        product = st.session_state.show_product_detail
        
        # Create modal-like view
        st.markdown("---")
        
        if st.button("✕ Close", key="close_detail"):
            st.session_state.show_product_detail = None
            st.rerun()
        
        # Product images
        col1, col2 = st.columns(2)
        
        with col1:
            image_path = f"pdf_screenshots/{product['sku']}/page_1.png"
            if os.path.exists(image_path):
                st.image(image_path, caption="Page 1", use_container_width=True)
        
        with col2:
            image_path = f"pdf_screenshots/{product['sku']}/page_2.png"
            if os.path.exists(image_path):
                st.image(image_path, caption="Page 2", use_container_width=True)
        
        # Product details
        st.markdown(f"### {product['sku']}")
        st.markdown(f"**{product.get('product_type', 'N/A')}**")
        st.markdown(f"**Price: {format_price(product.get('price', 0))}**")
        
        # Specifications in expandable sections
        with st.expander("Specifications", expanded=True):
            specs = {
                "Description": product.get('description'),
                "Capacity": product.get('capacity'),
                "Dimensions": product.get('dimensions'),
                "Weight": product.get('weight'),
                "Temperature Range": product.get('temperature_range'),
                "Voltage": product.get('voltage'),
                "Refrigerant": product.get('refrigerant'),
                "Features": product.get('features'),
                "Certifications": product.get('certifications')
            }
            
            for key, value in specs.items():
                if value:
                    st.text(f"{key}: {value}")
        
        # Add to cart button
        if st.button("Add to Cart", type="primary", use_container_width=True, key="detail_add_to_cart"):
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