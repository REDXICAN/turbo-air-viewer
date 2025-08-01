"""
Authentication module for Turbo Air Equipment Viewer
Handles Supabase authentication with offline fallback
Implements Option 3: Supabase Auth with local sync
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
    
    def _check_if_first_user(self) -> bool:
        """Check if this would be the first user in the system"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM user_profiles")
            count = cursor.fetchone()[0]
            conn.close()
            return count == 0
        except:
            return True
    
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
        """Hash password with salt (for offline fallback only)"""
        salt = "turbo_air_salt_2024"
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()
    
    def _sync_user_to_local(self, supabase_user: Dict, role: str = 'distributor', company: str = '') -> bool:
        """Sync Supabase user to local database"""
        try:
            conn = sqlite3.connect('turbo_air_db_online.sqlite')
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT id FROM user_profiles WHERE id = ?", (supabase_user['id'],))
            exists = cursor.fetchone() is not None
            
            if exists:
                # Update existing user
                cursor.execute("""
                    UPDATE user_profiles 
                    SET email = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (supabase_user['email'], supabase_user['id']))
            else:
                # Insert new user
                cursor.execute("""
                    INSERT INTO user_profiles (id, email, role, company, password_hash)
                    VALUES (?, ?, ?, ?, ?)
                """, (supabase_user['id'], supabase_user['email'], role, company, ''))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error syncing user to local: {e}")
            return False
    
    def sign_in_with_email(self, email: str, password: str, remember_me: bool = False) -> Tuple[bool, str]:
        """Sign in with email and password"""
        if self.is_online and self.supabase:
            try:
                # Try Supabase Auth first
                response = self.supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    # Get role from local database
                    conn = sqlite3.connect('turbo_air_db_online.sqlite')
                    cursor = conn.cursor()
                    cursor.execute("SELECT role FROM user_profiles WHERE id = ?", (response.user.id,))
                    result = cursor.fetchone()
                    
                    if result:
                        role = result[0]
                    else:
                        # First time login - sync user
                        role = 'distributor'
                        self._sync_user_to_local(response.user, role)
                    
                    conn.close()
                    
                    # Set session
                    self._set_user_session({
                        'id': response.user.id,
                        'email': response.user.email,
                        'created_at': datetime.now().isoformat()
                    })
                    st.session_state.user_role = role
                    
                    if remember_me:
                        token = self._generate_auth_token()
                        self._save_auth_token(response.user.id, token)
                    
                    return True, "Successfully signed in!"
                else:
                    return False, "Invalid credentials"
                    
            except Exception as e:
                error_msg = str(e)
                if "Invalid login credentials" in error_msg:
                    return False, "Invalid credentials"
                elif "Email not confirmed" in error_msg:
                    return False, "Please confirm your email before signing in"
                else:
                    # Fall back to offline login
                    return self._offline_sign_in(email, password, remember_me)
        else:
            return self._offline_sign_in(email, password, remember_me)
    
    def sign_up_with_email(self, email: str, password: str, role: str = 'distributor', company: str = '') -> Tuple[bool, str]:
        """Sign up with email and password"""
        # Check if this is the first user
        is_first_user = self._check_if_first_user()
        if is_first_user:
            role = 'admin'  # First user is always admin
        
        if self.is_online and self.supabase:
            try:
                # Create user in Supabase Auth
                response = self.supabase.auth.sign_up({
                    "email": email,
                    "password": password
                })
                
                if response.user:
                    # Sync to local database
                    self._sync_user_to_local(response.user, role, company)
                    
                    # Also save in user_profiles with password hash for offline
                    password_hash = self._hash_password(password)
                    conn = sqlite3.connect('turbo_air_db_online.sqlite')
                    cursor = conn.cursor()
                    cursor.execute("""
                        UPDATE user_profiles 
                        SET password_hash = ?
                        WHERE id = ?
                    """, (password_hash, response.user.id))
                    conn.commit()
                    conn.close()
                    
                    if is_first_user:
                        return True, "Admin account created successfully! Please check your email to confirm your account."
                    else:
                        return True, "Successfully signed up! Please check your email to confirm your account."
                else:
                    return False, "Failed to create account"
                    
            except Exception as e:
                error_msg = str(e)
                if "User already registered" in error_msg:
                    return False, "Email already exists"
                else:
                    # Fall back to offline signup
                    return self._offline_sign_up(email, password, role, company)
        else:
            return self._offline_sign_up(email, password, role, company)
    
    def sign_out(self):
        """Sign out current user"""
        # Sign out from Supabase if online
        if self.is_online and self.supabase:
            try:
                self.supabase.auth.sign_out()
            except:
                pass
        
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
            # Check if this is the first user
            is_first_user = self._check_if_first_user()
            if is_first_user:
                role = 'admin'  # First user is always admin
            
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
            
            if is_first_user:
                return True, "Admin account created (will sync when online)"
            else:
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
        # Check if this is the first user
        is_first_user = self._check_if_first_user()
        
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
            
            if is_first_user:
                st.info("🎉 Welcome! The first account will have admin privileges.")
            
            with st.form("signup_form"):
                new_email = st.text_input("Email", key="signup_email")
                new_password = st.text_input("Password", type="password", key="signup_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="confirm_password")
                
                if is_first_user:
                    st.info("Role: Admin (automatically assigned)")
                    role = "admin"
                else:
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