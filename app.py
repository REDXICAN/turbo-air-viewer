"""
Turbo Air Equipment Viewer - Mobile-First Application
iOS-style responsive equipment catalog and quote generation system
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
import sys

# Page configuration
st.set_page_config(
    page_title="Turbo Air",
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
        },
        'search_term': '',
        'last_quote': None
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

# Import custom modules with error handling
try:
    from auth import AuthManager, show_auth_form
    from database import DatabaseManager
    from sync_manager import SyncManager
except ImportError as e:
    st.error(f"Error importing core modules: {e}")
    st.stop()

# Import mobile UI components with error handling
try:
    from mobile_ui_components import (
        apply_mobile_css, mobile_header, mobile_search_bar, category_grid,
        quick_access_section, bottom_navigation, product_list_item, filter_row,
        metric_card, sync_status_bar, mobile_button, cart_item, summary_section,
        COLORS
    )
except ImportError as e:
    st.error(f"Error importing mobile_ui_components: {e}")
    st.info("Please ensure mobile_ui_components.py is in the root directory of your project.")
    st.stop()

# Keep the old UI components for functions not yet migrated
try:
    from ui_components import (
        quantity_selector, empty_state, format_price, truncate_text
    )
except ImportError as e:
    st.error(f"Error importing ui_components: {e}")
    st.stop()

# Import export utilities
try:
    from export_utils import export_quote_to_excel, export_quote_to_pdf
    from email_service import show_email_quote_dialog, get_email_service
except ImportError as e:
    st.warning(f"Export/Email features may be limited: {e}")
    # Define dummy functions if imports fail
    def export_quote_to_excel(*args, **kwargs):
        return "quote.xlsx"
    def export_quote_to_pdf(*args, **kwargs):
        return "quote.pdf"
    def show_email_quote_dialog(*args, **kwargs):
        st.error("Email service not available")
    def get_email_service():
        return None

# Initialize services
@st.cache_resource
def init_services():
    """Initialize all services"""
    supabase_client = None
    supabase_url = None
    supabase_key = None
    
    try:
        supabase_url = st.secrets["supabase"]["url"]
        supabase_key = st.secrets["supabase"]["anon_key"]
        
        if HAS_SUPABASE and supabase_url and supabase_key:
            try:
                supabase_client = create_client(supabase_url, supabase_key)
                supabase_client.table('products').select('id').limit(1).execute()
            except Exception as e:
                print(f"Supabase connection failed: {e}")
                supabase_client = None
    except Exception as e:
        print(f"Could not load Supabase credentials: {e}")
    
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

# Apply mobile CSS
apply_mobile_css()

# Main app container
with st.container():
    st.markdown('<div class="mobile-container">', unsafe_allow_html=True)

    # Check if user is authenticated
    if not auth_manager.is_authenticated():
        # Show authentication page
        mobile_header("Turbo Air")
        show_auth_form()
    else:
        # Update sync status
        try:
            sync_manager.update_sync_status()
        except Exception as e:
            print(f"Error updating sync status: {e}")
        
        # Get current user
        user = auth_manager.get_current_user()
        user_id = user['id'] if user else 'offline_user'
        
        # Update cart count
        if st.session_state.selected_client:
            try:
                cart_items = db_manager.get_cart_items(user_id, st.session_state.selected_client)
                st.session_state.cart_count = len(cart_items)
            except:
                st.session_state.cart_count = 0
        
        # Main content with padding for bottom nav
        st.markdown('<div class="main-content">', unsafe_allow_html=True)
        
        # Route to appropriate page
        if st.session_state.active_page == 'home':
            # Home Page
            mobile_header("Turbo Air")
            
            # Compact welcome section
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**Welcome to Turbo Air**")
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
            
            # Search bar
            mobile_search_bar()
            
            # Categories
            st.markdown("### Categories")
            try:
                # Get actual categories from database
                all_categories = db_manager.get_categories()
                if all_categories:
                    # Show only main categories on home
                    main_categories = []
                    for cat in all_categories:
                        if cat['name'] not in ['UNCATEGORIZED']:
                            main_categories.append({
                                "name": cat['name'],
                                "count": cat.get('count', 0)
                            })
                    if main_categories:
                        category_grid(main_categories[:4])  # Show top 4 categories
                else:
                    # Fallback categories
                    categories = [
                        {"name": "Refrigerators", "count": 0},
                        {"name": "Freezers", "count": 0}
                    ]
                    category_grid(categories)
            except Exception as e:
                print(f"Error loading categories: {e}")
                categories = [
                    {"name": "Refrigerators", "count": 0},
                    {"name": "Freezers", "count": 0}
                ]
                category_grid(categories)
            
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
                    
                    # Show client info
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
        
        elif st.session_state.active_page == 'search' or st.session_state.active_page == 'products':
            # Search/Products Page
            if st.button("← Back", key="back_to_home"):
                st.session_state.active_page = 'home'
                st.session_state.selected_category = None
                st.session_state.selected_subcategory = None
                st.rerun()
            
            mobile_header("Equipment Search", show_back=False)
            
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
                    
                    try:
                        categories = db_manager.get_categories()
                    except:
                        categories = []
                    
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
                    
                    # Get category data
                    try:
                        categories = db_manager.get_categories()
                        category_data = next((c for c in categories if c['name'] == st.session_state.selected_category), None)
                    except:
                        category_data = None
                    
                    if category_data and category_data.get('subcategories'):
                        # Show subcategories
                        cols = st.columns(2)
                        for idx, subcat in enumerate(category_data['subcategories']):
                            with cols[idx % 2]:
                                if st.button(subcat, key=f"subcat_{subcat}", use_container_width=True):
                                    st.session_state.selected_subcategory = subcat
                                    st.rerun()
                    
                    # Show products in category
                    try:
                        if st.session_state.selected_subcategory:
                            results_df = db_manager.get_products_by_category(
                                st.session_state.selected_category,
                                st.session_state.selected_subcategory
                            )
                        else:
                            results_df = db_manager.get_products_by_category(st.session_state.selected_category)
                    except:
                        results_df = pd.DataFrame()
            
            # Display products if we have results
            if not results_df.empty:
                st.markdown(f"### Results ({len(results_df)} items)")
                
                # Product list
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
        
        elif st.session_state.active_page == 'cart':
            # Cart Page
            if st.button("← Back", key="back_from_cart"):
                st.session_state.active_page = 'home'
                st.rerun()
                
            mobile_header("Cart", show_back=False)
            
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
                        # Product display
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"**{item['sku']}**")
                            st.caption(truncate_text(item.get('description', item.get('product_type', '')), 40))
                        with col2:
                            st.markdown(f"**{format_price(item['price'])}**")
                        
                        # Quantity and remove controls
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
                    if mobile_button("Generate Quote", key="generate_quote"):
                        with st.spinner("Generating quote..."):
                            client_data = db_manager.get_user_clients(user_id)
                            client_data = client_data[client_data['id'] == st.session_state.selected_client].iloc[0].to_dict()
                            
                            success, message, quote_number = db_manager.create_quote(
                                user_id, st.session_state.selected_client, cart_items_df
                            )
                            
                            if success:
                                st.success(message)
                                
                                # Prepare quote data
                                quote_data = {
                                    'quote_number': quote_number,
                                    'total_amount': summary_total,
                                    'created_at': datetime.now()
                                }
                                
                                # Store for quote summary page
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
                                
                                # Option to view quote summary
                                if st.button("View Quote Summary", use_container_width=True, type="primary"):
                                    st.session_state.active_page = 'quote_summary'
                                    st.rerun()
                                
                                # Clear cart option
                                if st.button("Clear Cart and Start New Quote", use_container_width=True):
                                    db_manager.clear_cart(user_id, st.session_state.selected_client)
                                    st.rerun()
                            else:
                                st.error(message)
        
        elif st.session_state.active_page == 'quote_summary' and st.session_state.last_quote:
            # Quote Summary Page
            if st.button("← Back", key="back_from_summary"):
                st.session_state.active_page = 'cart'
                st.rerun()
                
            mobile_header("Quote Summary", show_back=False)
            
            quote = st.session_state.last_quote
            
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
            # Calculate subtotal from total (remove tax)
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
                db_manager.clear_cart(user_id, st.session_state.selected_client)
                st.session_state.active_page = 'home'
                st.rerun()
        
        elif st.session_state.active_page == 'profile':
            # Profile Page
            mobile_header("Profile")
            
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
                
                if st.button("🔄 Refresh Product Database", use_container_width=True):
                    with st.spinner("Syncing products..."):
                        if sync_manager.sync_down_products():
                            st.success("Products updated successfully!")
                        else:
                            st.error("Failed to update products")
                
                if st.button("📊 View System Stats", use_container_width=True):
                    # Show system-wide statistics
                    try:
                        total_products = len(db_manager.get_all_products())
                        st.info(f"Total Products: {total_products}")
                    except:
                        st.error("Could not load system stats")
            
            # User actions
            st.markdown("### Actions")
            
            # Clear search history
            if st.button("🗑️ Clear Search History", use_container_width=True):
                success, message = db_manager.clear_search_history(user_id)
                if success:
                    st.success(message)
            
            # Test email configuration
            with st.expander("Email Settings"):
                if st.button("✉️ Test Email Configuration", use_container_width=True):
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
            if mobile_button("Sign Out", key="profile_signout"):
                auth_manager.sign_out()
                st.rerun()
        
        # Product Detail Modal
        if st.session_state.show_product_detail:
            product = st.session_state.show_product_detail
            
            # Back button
            if st.button("← Back to Products", key="back_from_detail"):
                st.session_state.show_product_detail = None
                st.rerun()
            
            mobile_header(product['sku'], show_back=False)
            
            # Product images
            col1, col2 = st.columns(2)
            
            with col1:
                image_path = f"pdf_screenshots/{product['sku']}/page_1.png"
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
                image_path = f"pdf_screenshots/{product['sku']}/page_2.png"
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
            st.markdown(f"**{product.get('product_type', 'N/A')}**")
            st.markdown(f"### {format_price(product.get('price', 0))}")
            
            # Description
            if product.get('description'):
                st.markdown(product['description'])
            
            # Specifications
            st.markdown("### Specifications")
            
            # Create two columns for specs
            specs_left = {
                "Capacity": product.get('capacity'),
                "Dimensions": product.get('dimensions'),
                "Weight": product.get('weight'),
                "Voltage": product.get('voltage'),
                "Amperage": product.get('amperage')
            }
            
            specs_right = {
                "Temperature Range": product.get('temperature_range'),
                "Refrigerant": product.get('refrigerant'),
                "Compressor": product.get('compressor'),
                "Shelves": product.get('shelves'),
                "Doors": product.get('doors')
            }
            
            col1, col2 = st.columns(2)
            
            with col1:
                for key, value in specs_left.items():
                    if value:
                        st.caption(key)
                        st.markdown(f"**{value}**")
            
            with col2:
                for key, value in specs_right.items():
                    if value:
                        st.caption(key)
                        st.markdown(f"**{value}**")
            
            # Additional features
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
            
            # Spacer
            st.markdown("### ")
            
            # Add to Cart button (fixed at bottom)
            if mobile_button("Add to Cart", key="detail_add_to_cart"):
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
        
        st.markdown('</div>', unsafe_allow_html=True)  # Close main-content
        
        # Bottom navigation (only show if not in product detail)
        if not st.session_state.show_product_detail:
            bottom_navigation(st.session_state.active_page)
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close mobile-container