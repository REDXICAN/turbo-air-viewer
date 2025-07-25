"""
Authentication module for Turbo Air Equipment Viewer
Handles Supabase authentication with email, Google, and Microsoft providers
"""

import streamlit as st
from supabase import create_client, Client
import sqlite3
from datetime import datetime, timedelta
import json
import hashlib
import secrets
import uuid

class AuthManager:
    def __init__(self, supabase_url=None, supabase_key=None):
        """Initialize authentication manager"""
        self.is_online = False
        self.supabase = None
        
        # Initialize session state BEFORE trying to use it
        if 'user' not in st.session_state:
            st.session_state.user = None
        if 'user_role' not in st.session_state:
            st.session_state.user_role = 'distributor'
        if 'auth_token' not in st.session_state:
            st.session_state.auth_token = None
        
        # Try to connect to Supabase
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                # Test the connection
                self.supabase.table('products').select('id').limit(1).execute()
                self.is_online = True
            except Exception as e:
                print(f"Failed to connect to Supabase: {e}")
                self.is_online = False
        
        # Check for existing auth token on initialization
        self._check_auth_token()
    
    def _generate_auth_token(self):
        """Generate a secure authentication token"""
        return secrets.token_urlsafe(32)
    
    def _save_auth_token(self, user_id, token, remember_days=30):
        """Save auth token to database"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            # Create auth_tokens table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    token TEXT UNIQUE NOT NULL,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Calculate expiration
            expires_at = datetime.now() + timedelta(days=remember_days)
            
            # Save token
            cursor.execute("""
                INSERT INTO auth_tokens (user_id, token, expires_at)
                VALUES (?, ?, ?)
            """, (user_id, token, expires_at))
            
            conn.commit()
            conn.close()
            
            # Store in session state
            st.session_state.auth_token = token
            
            # Store in query params for persistence
            st.query_params["auth_token"] = token
            
            return True
        except Exception as e:
            print(f"Error saving auth token: {e}")
            return False
    
    def _check_auth_token(self):
        """Check if user has a valid auth token"""
        # First check query params
        token = st.query_params.get("auth_token")
        
        if not token and 'auth_token' in st.session_state:
            token = st.session_state.auth_token
        
        if token:
            try:
                conn = sqlite3.connect('turbo_air_db_online.sqlite')
                cursor = conn.cursor()
                
                # Check if token exists and is valid
                cursor.execute("""
                    SELECT at.user_id, up.email, up.role 
                    FROM auth_tokens at
                    JOIN user_profiles up ON at.user_id = up.id
                    WHERE at.token = ? AND at.expires_at > ?
                """, (token, datetime.now()))
                
                result = cursor.fetchone()
                
                if result:
                    # Auto-login the user
                    user_id, email, role = result
                    self._set_user_session({
                        'id': user_id,
                        'email': email,
                        'created_at': datetime.now().isoformat()
                    })
                    st.session_state.user_role = role
                    st.session_state.auth_token = token
                    return True
                else:
                    # Token expired or invalid, remove it
                    if "auth_token" in st.query_params:
                        del st.query_params["auth_token"]
                
                conn.close()
            except Exception as e:
                print(f"Error checking auth token: {e}")
        
        return False
    
    def sign_in_with_email(self, email, password, remember_me=False):
        """Sign in with email and password"""
        if self.is_online and self.supabase:
            try:
                # First try to get user from user_profiles
                response = self.supabase.table('user_profiles').select("*").eq('email', email).execute()
                
                if response.data and len(response.data) > 0:
                    user = response.data[0]
                    # Simple password check for demo (in production use proper auth)
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    
                    # For admin user, check against known password
                    if email == 'andres.xbgo@outlook.com' and password == 'admin123':
                        self._set_user_session({
                            'id': user['id'],
                            'email': email,
                            'created_at': datetime.now().isoformat()
                        })
                        
                        # Handle remember me
                        if remember_me:
                            token = self._generate_auth_token()
                            self._save_auth_token(user['id'], token)
                        
                        return True, "Successfully signed in!"
                    
                    # For other users, you'd check against stored hash
                    return False, "Invalid credentials"
                else:
                    # User not found in Supabase
                    return self._offline_sign_in(email, password, remember_me)
            except Exception as e:
                # If Supabase fails, fall back to offline
                return self._offline_sign_in(email, password, remember_me)
        else:
            # Offline mode - check local database
            return self._offline_sign_in(email, password, remember_me)
    
    def sign_up_with_email(self, email, password, role='distributor', company=''):
        """Sign up with email and password"""
        if self.is_online and self.supabase:
            try:
                import uuid
                user_id = str(uuid.uuid4())
                
                # Create user profile
                profile_data = {
                    'id': user_id,
                    'email': email,
                    'role': role,
                    'company': company,
                    'password_hash': hashlib.sha256(password.encode()).hexdigest()
                }
                
                self.supabase.table('user_profiles').insert(profile_data).execute()
                
                return True, "Successfully signed up! You can now sign in."
            except Exception as e:
                if "duplicate" in str(e).lower():
                    return False, "Email already exists"
                return False, str(e)
        else:
            # Offline mode - create local user
            return self._offline_sign_up(email, password, role, company)
    
    def sign_out(self):
        """Sign out current user"""
        # Remove auth token
        if 'auth_token' in st.session_state:
            token = st.session_state.auth_token
            try:
                conn = sqlite3.connect('turbo_air_db_online.sqlite')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM auth_tokens WHERE token = ?", (token,))
                conn.commit()
                conn.close()
            except:
                pass
        
        # Clear query params
        if "auth_token" in st.query_params:
            del st.query_params["auth_token"]
        
        # Clear session state
        st.session_state.user = None
        st.session_state.user_role = 'distributor'
        st.session_state.auth_token = None
        
        # Clear other session state if needed
        for key in ['selected_client', 'cart_count', 'active_page']:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_current_user(self):
        """Get current user session"""
        return st.session_state.get('user')
    
    def get_user_role(self):
        """Get current user role"""
        if self.is_online and self.supabase and st.session_state.user:
            try:
                # Fetch user profile
                response = self.supabase.table('user_profiles').select('role').eq('id', st.session_state.user['id']).single().execute()
                if response.data:
                    return response.data.get('role', 'distributor')
            except:
                pass
        
        return st.session_state.get('user_role', 'distributor')
    
    def is_admin(self):
        """Check if current user is admin"""
        return self.get_user_role() == 'admin'
    
    def is_authenticated(self):
        """Check if user is authenticated"""
        # Make sure session state exists
        if 'user' not in st.session_state:
            st.session_state.user = None
        return st.session_state.user is not None
    
    def _set_user_session(self, user):
        """Set user session data"""
        st.session_state.user = {
            'id': user.get('id'),
            'email': user.get('email'),
            'created_at': user.get('created_at')
        }
        
        # Get user role
        if self.is_online and self.supabase:
            try:
                response = self.supabase.table('user_profiles').select('role').eq('id', user.get('id')).single().execute()
                if response.data:
                    st.session_state.user_role = response.data.get('role', 'distributor')
                else:
                    st.session_state.user_role = 'distributor'
            except:
                st.session_state.user_role = 'distributor'
        else:
            # For offline mode, set admin role for admin email
            if user.get('email') == 'andres.xbgo@outlook.com':
                st.session_state.user_role = 'admin'
            else:
                st.session_state.user_role = 'distributor'
    
    def _offline_sign_in(self, email, password, remember_me=False):
        """Handle offline sign in using local database"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            # For demo purposes, allow admin login
            if email == 'andres.xbgo@outlook.com' and password == 'admin123':
                # Check if admin exists in local DB
                cursor.execute("""
                    SELECT id, email, role FROM user_profiles 
                    WHERE email = ? 
                """, (email,))
                
                user = cursor.fetchone()
                
                if user:
                    self._set_user_session({
                        'id': user[0],
                        'email': user[1],
                        'created_at': datetime.now().isoformat()
                    })
                    st.session_state.user_role = user[2]
                    
                    # Handle remember me
                    if remember_me:
                        token = self._generate_auth_token()
                        self._save_auth_token(user[0], token)
                    
                    conn.close()
                    return True, "Signed in offline mode"
                else:
                    # Create admin user if not exists
                    admin_id = '227d00ff-082a-4530-8793-e590385605ab'
                    cursor.execute("""
                        INSERT INTO user_profiles (id, email, role, company)
                        VALUES (?, ?, ?, ?)
                    """, (admin_id, email, 'admin', 'Turbo Air Mexico'))
                    conn.commit()
                    
                    self._set_user_session({
                        'id': admin_id,
                        'email': email,
                        'created_at': datetime.now().isoformat()
                    })
                    st.session_state.user_role = 'admin'
                    
                    # Handle remember me
                    if remember_me:
                        token = self._generate_auth_token()
                        self._save_auth_token(admin_id, token)
                    
                    conn.close()
                    return True, "Signed in offline mode"
            
            conn.close()
            return False, "Invalid credentials"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def _offline_sign_up(self, email, password, role, company):
        """Handle offline sign up using local database"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            # Create user profile
            import uuid
            user_id = str(uuid.uuid4())
            
            cursor.execute("""
                INSERT INTO user_profiles (id, email, role, company)
                VALUES (?, ?, ?, ?)
            """, (user_id, email, role, company))
            
            conn.commit()
            conn.close()
            
            # Add to sync queue
            self._add_to_sync_queue('user_profiles', 'insert', {
                'id': user_id,
                'email': email,
                'role': role,
                'company': company
            })
            
            return True, "Account created in offline mode. Will sync when online."
        except sqlite3.IntegrityError:
            return False, "Email already exists"
        except Exception as e:
            return False, str(e)
    
    def _add_to_sync_queue(self, table_name, operation, data):
        """Add operation to sync queue for later synchronization"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO sync_queue (table_name, operation, data)
                VALUES (?, ?, ?)
            """, (table_name, operation, json.dumps(data)))
            
            conn.commit()
            conn.close()
        except:
            pass

def show_auth_form():
    """Display authentication form"""
    # Initialize session state if needed
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_role' not in st.session_state:
        st.session_state.user_role = 'distributor'
    
    auth_manager = st.session_state.get('auth_manager')
    
    if not auth_manager:
        st.error("Authentication system not initialized")
        return
    
    # Check if user is already authenticated
    if auth_manager.is_authenticated():
        st.success(f"Signed in as: {st.session_state.user['email']}")
        if st.button("Sign Out", key="signout_btn"):
            auth_manager.sign_out()
            st.rerun()
        return
    
    # Authentication tabs
    tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
    
    with tab1:
        st.subheader("Sign In")
        
        # Email/Password sign in
        with st.form("signin_form"):
            email = st.text_input("Email", key="signin_email")
            password = st.text_input("Password", type="password", key="signin_password")
            remember_me = st.checkbox("Remember me for 30 days", key="remember_me")
            
            # Center the sign in button
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                submit = st.form_submit_button("Sign In with Email", use_container_width=True, type="primary")
            
            if submit:
                if email and password:
                    success, message = auth_manager.sign_in_with_email(email, password, remember_me)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter email and password")
        
        # OAuth options
        st.divider()
        st.markdown("<p style='text-align: center; color: #666;'>Or sign in with:</p>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col2:
            # Google Sign In Button with official branding
            google_button_html = """
            <style>
            .google-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #ffffff;
                border: 1px solid #dadce0;
                border-radius: 4px;
                padding: 12px 24px;
                cursor: pointer;
                transition: background-color 0.3s, box-shadow 0.3s;
                width: 100%;
                margin-bottom: 12px;
                text-decoration: none;
                color: #3c4043;
                font-family: 'Roboto', arial, sans-serif;
                font-size: 14px;
                font-weight: 500;
            }
            .google-btn:hover {
                background-color: #f8f9fa;
                box-shadow: 0 1px 2px 0 rgba(60,64,67,0.3), 0 1px 3px 1px rgba(60,64,67,0.15);
            }
            .google-logo {
                width: 18px;
                height: 18px;
                margin-right: 8px;
            }
            </style>
            <button class="google-btn" onclick="document.getElementById('google_signin_btn').click()">
                <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" class="google-logo">
                Sign in with Google
            </button>
            """
            st.markdown(google_button_html, unsafe_allow_html=True)
            
            if st.button("", key="google_signin_btn", help="Sign in with Google", label_visibility="collapsed"):
                success, result = auth_manager.sign_in_with_google()
                if success:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={result}">', unsafe_allow_html=True)
                else:
                    st.error(result)
            
            # Microsoft Sign In Button with official branding
            microsoft_button_html = """
            <style>
            .microsoft-btn {
                display: flex;
                align-items: center;
                justify-content: center;
                background-color: #ffffff;
                border: 1px solid #8c8c8c;
                border-radius: 4px;
                padding: 12px 24px;
                cursor: pointer;
                transition: background-color 0.3s, box-shadow 0.3s;
                width: 100%;
                text-decoration: none;
                color: #5e5e5e;
                font-family: 'Segoe UI', system-ui, sans-serif;
                font-size: 14px;
                font-weight: 600;
            }
            .microsoft-btn:hover {
                background-color: #f8f8f8;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .microsoft-logo {
                width: 20px;
                height: 20px;
                margin-right: 8px;
            }
            </style>
            <button class="microsoft-btn" onclick="document.getElementById('microsoft_signin_btn').click()">
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 23 23" class="microsoft-logo">
                    <path fill="#f3f3f3" d="M0 0h23v23H0z"/>
                    <path fill="#f35325" d="M1 1h10v10H1z"/>
                    <path fill="#81bc06" d="M12 1h10v10H12z"/>
                    <path fill="#05a6f0" d="M1 12h10v10H1z"/>
                    <path fill="#ffba08" d="M12 12h10v10H12z"/>
                </svg>
                Sign in with Microsoft
            </button>
            """
            st.markdown(microsoft_button_html, unsafe_allow_html=True)
            
            if st.button("", key="microsoft_signin_btn", help="Sign in with Microsoft", label_visibility="collapsed"):
                success, result = auth_manager.sign_in_with_microsoft()
                if success:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={result}">', unsafe_allow_html=True)
                else:
                    st.error(result)
    
    with tab2:
        st.subheader("Create Account")
        
        # Sign up form
        with st.form("signup_form"):
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
            
            role = st.selectbox("Role", ["distributor", "sales"], key="signup_role")
            company = st.text_input("Company", key="signup_company")
            
            # Center the create account button
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
            
            if submit:
                if new_email and new_password:
                    if new_password == confirm_password:
                        success, message = auth_manager.sign_up_with_email(
                            new_email, new_password, role, company
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords do not match")
                else:
                    st.error("Please fill in all required fields")