"""
Authentication module for Turbo Air Equipment Viewer
Handles Supabase authentication with email, Google, and Microsoft providers
"""

import streamlit as st
from supabase import create_client, Client
import sqlite3
from datetime import datetime
import json
import hashlib

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
    
    def sign_in_with_email(self, email, password):
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
                        return True, "Successfully signed in!"
                    
                    # For other users, you'd check against stored hash
                    return False, "Invalid credentials"
                else:
                    # User not found in Supabase
                    return self._offline_sign_in(email, password)
            except Exception as e:
                # If Supabase fails, fall back to offline
                return self._offline_sign_in(email, password)
        else:
            # Offline mode - check local database
            return self._offline_sign_in(email, password)
    
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
    
    def sign_in_with_google(self):
        """Sign in with Google OAuth"""
        if self.is_online and self.supabase:
            try:
                # This will redirect to Google OAuth
                url = self.supabase.auth.sign_in_with_oauth({
                    "provider": "google",
                    "options": {
                        "redirect_to": st.secrets.get("app", {}).get("redirect_url", "http://localhost:8501")
                    }
                })
                return True, url.url
            except Exception as e:
                return False, str(e)
        return False, "Google sign-in requires internet connection"
    
    def sign_in_with_microsoft(self):
        """Sign in with Microsoft OAuth"""
        if self.is_online and self.supabase:
            try:
                # This will redirect to Microsoft OAuth
                url = self.supabase.auth.sign_in_with_oauth({
                    "provider": "azure",
                    "options": {
                        "redirect_to": st.secrets.get("app", {}).get("redirect_url", "http://localhost:8501")
                    }
                })
                return True, url.url
            except Exception as e:
                return False, str(e)
        return False, "Microsoft sign-in requires internet connection"
    
    def sign_out(self):
        """Sign out current user"""
        if self.is_online and self.supabase:
            try:
                self.supabase.auth.sign_out()
            except:
                pass
        
        st.session_state.user = None
        st.session_state.user_role = 'distributor'
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
    
    def _offline_sign_in(self, email, password):
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
        email = st.text_input("Email", key="signin_email")
        password = st.text_input("Password", type="password", key="signin_password")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Sign In with Email", key="email_signin", use_container_width=True):
                if email and password:
                    success, message = auth_manager.sign_in_with_email(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Please enter email and password")
        
        with col2:
            if st.button("Sign In with Google", key="google_signin", use_container_width=True):
                success, result = auth_manager.sign_in_with_google()
                if success:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={result}">', unsafe_allow_html=True)
                else:
                    st.error(result)
        
        with col3:
            if st.button("Sign In with Microsoft", key="microsoft_signin", use_container_width=True):
                success, result = auth_manager.sign_in_with_microsoft()
                if success:
                    st.markdown(f'<meta http-equiv="refresh" content="0;url={result}">', unsafe_allow_html=True)
                else:
                    st.error(result)
    
    with tab2:
        st.subheader("Create Account")
        
        # Sign up form
        new_email = st.text_input("Email", key="signup_email")
        new_password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
        
        role = st.selectbox("Role", ["distributor", "sales"], key="signup_role")
        company = st.text_input("Company", key="signup_company")
        
        if st.button("Create Account", key="create_account", use_container_width=True):
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