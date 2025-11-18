"""
Authentication and authorization module
"""
import streamlit as st
import bcrypt
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import SECRET_KEY, ADMIN_USERNAME, ADMIN_PASSWORD_HASH, SESSION_TIMEOUT_MINUTES
from logger import get_logger

logger = get_logger(__name__)


class AuthManager:
    """Manages authentication and session"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against a hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def initialize_session():
        """Initialize session state variables"""
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        if "username" not in st.session_state:
            st.session_state.username = None
        if "role" not in st.session_state:
            st.session_state.role = None
        if "login_time" not in st.session_state:
            st.session_state.login_time = None
        if "session_id" not in st.session_state:
            st.session_state.session_id = None
    
    @staticmethod
    def is_session_valid() -> bool:
        """Check if the current session is still valid"""
        if not st.session_state.authenticated:
            return False
        
        if st.session_state.login_time is None:
            return False
        
        # Check session timeout
        elapsed = datetime.now() - st.session_state.login_time
        if elapsed > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
            logger.info(f"Session expired for user: {st.session_state.username}")
            return False
        
        return True
    
    @staticmethod
    def login(username: str, password: str) -> bool:
        """Authenticate user and create session"""
        try:
            # Simple admin authentication (can be extended to database)
            if username == ADMIN_USERNAME:
                # If no hash is set, use default password
                if not ADMIN_PASSWORD_HASH:
                    if password == "admin":  # Default password
                        logger.warning("Using default admin password - CHANGE THIS!")
                        AuthManager._create_session(username, "admin")
                        return True
                else:
                    if AuthManager.verify_password(password, ADMIN_PASSWORD_HASH):
                        AuthManager._create_session(username, "admin")
                        logger.info(f"User logged in: {username}")
                        return True
            
            logger.warning(f"Failed login attempt for user: {username}")
            return False
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    @staticmethod
    def _create_session(username: str, role: str):
        """Create a new session"""
        st.session_state.authenticated = True
        st.session_state.username = username
        st.session_state.role = role
        st.session_state.login_time = datetime.now()
        st.session_state.session_id = f"{username}_{datetime.now().timestamp()}"
    
    @staticmethod
    def logout():
        """Clear session and logout"""
        username = st.session_state.get("username", "Unknown")
        logger.info(f"User logged out: {username}")
        st.session_state.clear()
        AuthManager.initialize_session()
    
    @staticmethod
    def require_auth():
        """Decorator-style function to require authentication"""
        AuthManager.initialize_session()
        
        if not AuthManager.is_session_valid():
            st.session_state.authenticated = False
            return False
        
        return True
    
    @staticmethod
    def get_current_user() -> Optional[Dict[str, str]]:
        """Get current user information"""
        if not st.session_state.authenticated:
            return None
        
        return {
            "username": st.session_state.username,
            "role": st.session_state.role,
            "login_time": st.session_state.login_time,
            "session_id": st.session_state.session_id
        }


def admin_login() -> bool:
    """Display login form and handle authentication"""
    st.title("🔐 Admin Login")
    
    AuthManager.initialize_session()
    
    # Check if already authenticated
    if AuthManager.is_session_valid():
        return True
    
    with st.form("login_form"):
        st.markdown("### Please enter your credentials")
        username = st.text_input("Username", placeholder="admin")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        submit = st.form_submit_button("Login")
        
        if submit:
            if not username or not password:
                st.error("Please enter both username and password")
                return False
            
            if AuthManager.login(username, password):
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("Invalid credentials. Please try again.")
                return False
    
    # Show info about default credentials
    with st.expander("ℹ️ First time user?"):
        st.info("""
        **Default credentials:**
        - Username: `admin`
        - Password: `admin`
        
        ⚠️ **Important:** Change the default password in production!
        
        To set a secure password:
        1. Generate a hash using the password utility
        2. Set ADMIN_PASSWORD_HASH in your .env file
        """)
    
    return False


def generate_password_hash_cli():
    """CLI utility to generate password hash"""
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "hash-password":
        password = input("Enter password to hash: ")
        hashed = AuthManager.hash_password(password)
        print(f"\nPassword hash:\n{hashed}\n")
        print("Add this to your .env file:")
        print(f"ADMIN_PASSWORD_HASH={hashed}")


if __name__ == "__main__":
    generate_password_hash_cli()
