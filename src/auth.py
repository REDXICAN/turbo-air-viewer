"""
Authentication module for Turbo Air Equipment Viewer
Handles Supabase authentication with offline fallback
"""

import streamlit as st
from supabase import create_client, Client
import sqlite3
from datetime import datetime, timedelta
import json
import hashlib
import secrets
import uuid
from typing import Optional, Tuple, Dict

class AuthManager:
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        """Initialize authentication manager"""
        self.is_online = False
        self.supabase = None
        
        # Try to connect to Supabase
        if supabase_url and supabase_key:
            try:
                self.supabase = create_client(supabase_url, supabase_key)
                # Test connection
                self.supabase.table('products').select('id').limit(1).execute()
                self.is_online = True
            except Exception as e:
                print(f"Supabase connection failed: {e}")
                self.is_online = False
        
        # Check for existing auth token
        self._check_auth_token()
    
    def _generate_auth_token(self) -> str:
        """Generate a secure authentication token"""
        return secrets.token_urlsafe(32)
    
    def _save_auth_token(self, user_id: str, token: str, remember_days: int = 30) -> bool:
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
            
            return True
        except Exception as e:
            print(f"Error saving auth token: {e}")
            return False
    
    def _check_auth_token(self) -> bool:
        """Check if user has a valid auth token"""
        token = st.session_state.get('auth_token')
        
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
                    return True
                
                conn.close()
            except Exception as e:
                print(f"Error checking auth token: {e}")
        
        return False
    
    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = "turbo_air_salt_2024"
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def sign_in_with_email(self, email: str, password: str, remember_me: bool = False) -> Tuple[bool, str]:
        """Sign in with email and password"""
        if self.is_online and self.supabase:
            try:
                # First try to get user from user_profiles
                response = self.supabase.table('user_profiles').select("*").eq('email', email).execute()
                
                if response.data and len(response.data) > 0:
                    user = response.data[0]
                    password_hash = self._hash_password(password)
                    
                    if user.get('password_hash') == password_hash:
                        self._set_user_session({
                            'id': user['id'],
                            'email': email,
                            'created_at': datetime.now().isoformat()
                        })
                        
                        if remember_me:
                            token = self._generate_auth_token()
                            self._save_auth_token(user['id'], token)
                        
                        return True, "Successfully signed in!"
                    else:
                        return False, "Invalid credentials"
                else:
                    return self._offline_sign_in(email, password, remember_me)
            except Exception as e:
                return self._offline_sign_in(email, password, remember_me)
        else:
            return self._offline_sign_in(email, password, remember_me)
    
    def sign_up_with_email(self, email: str, password: str, role: str = 'distributor', company: str = '') -> Tuple[bool, str]:
        """Sign up with email and password"""
        user_id = str(uuid.uuid4())
        password_hash = self._hash_password(password)
        
        if self.is_online and self.supabase:
            try:
                profile_data = {
                    'id': user_id,
                    'email': email,
                    'role': role,
                    'company': company,
                    'password_hash': password_hash
                }
                
                self.supabase.table('user_profiles').insert(profile_data).execute()
                return True, "Successfully signed up! You can now sign in."
            except Exception as e:
                if "duplicate" in str(e).lower():
                    return False, "Email already exists"
                return self._offline_sign_up(email, password, role, company)
        else:
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
        
        # Clear session state
        st.session_state.user = None
        st.session_state.user_role = 'distributor'
        st.session_state.auth_token = None
        
        # Clear other session state
        for key in ['selected_client', 'cart_count', 'active_page']:
            if key in st.session_state:
                del st.session_state[key]
    
    def get_current_user(self) -> Optional[Dict]:
        """Get current user session"""
        return st.session_state.get('user')
    
    def get_user_role(self) -> str:
        """Get current user role"""
        if self.is_online and self.supabase and st.session_state.user:
            try:
                response = self.supabase.table('user_profiles').select('role').eq('id', st.session_state.user['id']).single().execute()
                if response.data:
                    return response.data.get('role', 'distributor')
            except:
                pass
        
        return st.session_state.get('user_role', 'distributor')
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.get_user_role() == 'admin'
    
    def is_authenticated(self) -> bool:
        """Check if user is authenticated"""
        return st.session_state.get('user') is not None
    
    def _set_user_session(self, user: Dict):
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
            try:
                conn = sqlite3.connect('turbo_air_db_online.sqlite')
                cursor = conn.cursor()
                cursor.execute("SELECT role FROM user_profiles WHERE id = ?", (user.get('id'),))
                result = cursor.fetchone()
                if result:
                    st.session_state.user_role = result[0]
                else:
                    st.session_state.user_role = 'distributor'
                conn.close()
            except:
                st.session_state.user_role = 'distributor'
    
    def _offline_sign_in(self, email: str, password: str, remember_me: bool = False) -> Tuple[bool, str]:
        """Handle offline sign in using local database"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            password_hash = self._hash_password(password)
            cursor.execute("""
                SELECT id, email, role FROM user_profiles 
                WHERE email = ? AND password_hash = ?
            """, (email, password_hash))
            
            user = cursor.fetchone()
            
            if user:
                self._set_user_session({
                    'id': user[0],
                    'email': user[1],
                    'created_at': datetime.now().isoformat()
                })
                st.session_state.user_role = user[2]
                
                if remember_me:
                    token = self._generate_auth_token()
                    self._save_auth_token(user[0], token)
                
                conn.close()
                return True, "Signed in (offline mode)"
            else:
                conn.close()
                return False, "Invalid credentials"
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def _offline_sign_up(self, email: str, password: str, role: str, company: str) -> Tuple[bool, str]:
        """Handle offline sign up using local database"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            user_id = str(uuid.uuid4())
            password_hash = self._hash_password(password)
            
            cursor.execute("""
                INSERT INTO user_profiles (id, email, role, company, password_hash)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, email, role, company, password_hash))
            
            conn.commit()
            
            # Add to sync queue
            self._add_to_sync_queue(conn, 'user_profiles', 'insert', {
                'id': user_id,
                'email': email,
                'role': role,
                'company': company,
                'password_hash': password_hash
            })
            
            conn.close()
            return True, "Account created (will sync when online)"
        except sqlite3.IntegrityError:
            return False, "Email already exists"
        except Exception as e:
            return False, str(e)
    
    def _add_to_sync_queue(self, conn, table_name: str, operation: str, data: Dict):
        """Add operation to sync queue for later synchronization"""
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_queue (table_name, operation, data)
                VALUES (?, ?, ?)
            """, (table_name, operation, json.dumps(data)))
            conn.commit()
        except:
            pass
    
    def show_auth_form(self):
        """Display authentication form"""
        # Authentication tabs
        tab1, tab2 = st.tabs(["Sign In", "Sign Up"])
        
        with tab1:
            st.subheader("Sign In")
            
            with st.form("signin_form"):
                email = st.text_input("Email", key="signin_email")
                password = st.text_input("Password", type="password", key="signin_password")
                remember_me = st.checkbox("Remember me for 30 days", key="remember_me")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    submit = st.form_submit_button("Sign In with Email", use_container_width=True, type="primary")
                
                if submit:
                    if email and password:
                        success, message = self.sign_in_with_email(email, password, remember_me)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Please enter email and password")
        
        with tab2:
            st.subheader("Create Account")
            
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                
                role = st.selectbox("Role", ["distributor", "sales"], key="signup_role")
                company = st.text_input("Company", key="signup_company")
                
                col1, col2, col3 = st.columns([1, 2, 1])
                
                with col2:
                    submit = st.form_submit_button("Create Account", use_container_width=True, type="primary")
                
                if submit:
                    if new_email and new_password:
                        if new_password == confirm_password:
                            success, message = self.sign_up_with_email(
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