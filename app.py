"""
Smart Attendance System - Main Application
Enhanced with modern features, error handling, and better UX
"""
import streamlit as st
from datetime import datetime
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import modules
from database import initialize_db, db
from ui_dashboard import dashboard
from ui_registration import registration_ui, show_registered_users
from ui_recognition import recognition_ui, show_today_attendance
from auth import admin_login, AuthManager
from config import PAGE_TITLE, PAGE_ICON, Config
from logger import get_logger
from audio_utils import play_chime, audio_manager, get_time_based_greeting, speak_nigerian_greeting

logger = get_logger(__name__)

# Configure Streamlit page
st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/yourusername/smart-attendance', 
        'Report a bug': 'https://github.com/yourusername/smart-attendance/issues',
        'About': """
        # Smart Attendance System
        
        An advanced face recognition-based attendance system built with:
        - Streamlit for the UI
        - face_recognition for face detection
        - SQLite for data storage
        
        Version 2.0
        """
    }
)


def initialize_app():
    """Initialize application components"""
    try:
        # Initialize database
        initialize_db()
        logger.info("Application initialized successfully")
        
        # Validate configuration
        config_errors = Config.validate()
        if config_errors:
            for error in config_errors:
                logger.warning(error)
        
        # Play welcome chime and announcement on first run
        if 'app_started' not in st.session_state:
            st.session_state.app_started = True
            play_chime()
            greeting = get_time_based_greeting()
            from audio_utils import _queue_speech
            _queue_speech(f"{greeting}! Welcome to the Smart Attendance System. Please log in to continue.")
        
        return True
    except Exception as e:
        logger.error(f"Application initialization failed: {e}", exc_info=True)
        st.error(f"❌ Failed to initialize application: {e}")
        return False


def render_sidebar():
    """Render sidebar with navigation and user info"""
    with st.sidebar:
        st.title("🎯 Smart Attendance")
        
        # User info
        user = AuthManager.get_current_user()
        if user:
            st.success(f"👤 Logged in as: **{user['username']}**")
            st.caption(f"Role: {user['role']}")
            
            if st.button("🚪 Logout", use_container_width=True):
                AuthManager.logout()
                st.rerun()
        
        st.divider()
        
        # Navigation
        st.subheader("📍 Navigation")
        choice = st.radio(
            "Go to:",
            ["Dashboard", "Register Face", "Start Recognition"],
            label_visibility="collapsed"
        )
        
        st.divider()
        
        # Quick stats
        st.subheader("📊 Quick Stats")
        try:
            stats = db.get_statistics()
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Today", stats['today_attendance'])
                st.metric("Total", stats['total_records'])
            with col2:
                st.metric("Employees", stats['unique_employees'])
                st.metric("Late %", f"{stats['late_percentage']}%")
        except Exception as e:
            st.error("Unable to load stats")
            logger.error(f"Stats loading error: {e}")
        
        st.divider()
        
        # System info
        with st.expander("⚙️ System Info"):
            st.caption(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
            st.caption(f"**Time:** {datetime.now().strftime('%H:%M:%S')}")
            st.caption(f"**Version:** 2.0")
        
        return choice


def main():
    """Main application entry point"""
    
    # Initialize app
    if not initialize_app():
        st.stop()
    
    # Authentication
    AuthManager.initialize_session()
    
    if not AuthManager.is_session_valid():
        # Show login page
        if not admin_login():
            st.stop()
        else:
            st.rerun()
    
    # Render sidebar and get navigation choice
    try:
        choice = render_sidebar()
    except Exception as e:
        logger.error(f"Sidebar rendering error: {e}", exc_info=True)
        st.error("Error rendering sidebar")
        st.stop()
    
    # Main content area
    try:
        if choice == "Dashboard":
            dashboard()
        
        elif choice == "Register Face":
            registration_ui()
            st.divider()
            show_registered_users()
        
        elif choice == "Start Recognition":
            recognition_ui()
            st.divider()
            show_today_attendance()
        
    except Exception as e:
        logger.error(f"Page rendering error: {e}", exc_info=True)
        st.error(f"❌ An error occurred: {e}")
        
        with st.expander("🔍 Error Details"):
            st.code(str(e))
            st.caption("Check logs for more information")
    
    # Footer
    st.divider()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("© 2025 Amos Smart Attendance System")
    with col2:
        st.caption("Powered by Streamlit & face_recognition")
    with col3:
        st.caption(f"Session: {datetime.now().strftime('%H:%M')}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application stopped by user")
    except Exception as e:
        logger.critical(f"Critical application error: {e}", exc_info=True)
        st.error("❌ Critical error occurred. Please check logs.")
        raise
