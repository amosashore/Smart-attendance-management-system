"""
Enhanced face registration UI with preview and validation
"""
import streamlit as st
import cv2
import numpy as np
from PIL import Image

from face_utils import face_manager, FaceQualityChecker, FACE_RECOGNITION_AVAILABLE
from audio_utils import audio_manager, play_chime, get_time_based_greeting, speak_nigerian_greeting
from database import db
from logger import get_logger

logger = get_logger(__name__)


def registration_ui():
    """Face registration page"""
    st.title("📝 Face Registration")
    
    # Initialize session state for captured image
    if 'captured_image' not in st.session_state:
        st.session_state.captured_image = None
    
    # Check if face_recognition is available
    if not FACE_RECOGNITION_AVAILABLE:
        st.error("⚠️ **face_recognition library not installed**")
        st.info(r"""
        Face registration requires the `face_recognition` library.
        
        **To install:**
        1. Open PowerShell in the project directory
        2. Run: `.\install_face_recognition.bat`
        
        Or manually:
        ```
        pip install dlib-binary face-recognition
        ```
        
        After installation, restart the application.
        """)
        return
    
    st.markdown("""
    ### Register a new face in the system
    
    **Instructions:**
    1. Enter your full name and optional details
    2. Capture or upload a clear photo of your face
    3. Ensure good lighting and face the camera directly
    4. Only one face should be visible in the image
    """)
    
    # Registration form
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input(
                "Full Name *", 
                placeholder="John Doe",
                help="Enter your full name as it should appear in attendance"
            )
            email = st.text_input(
                "Email", 
                placeholder="john.doe@example.com"
            )
        
        with col2:
            phone = st.text_input(
                "Phone", 
                placeholder="+1 234 567 8900"
            )
            department = st.text_input(
                "Department", 
                placeholder="Engineering"
            )
        
        st.divider()
        
        # Image capture method
        capture_method = st.radio(
            "Choose capture method:",
            ["📷 Capture from Camera", "📁 Upload Image"],
            horizontal=True
        )
        
        image = st.session_state.captured_image
        
        if capture_method == "📷 Capture from Camera":
            st.info("Click 'Capture Image' to take a photo from your webcam")
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                camera_btn = st.form_submit_button("📸 Capture Image", use_container_width=True)
            
            if camera_btn:
                with st.spinner("Accessing camera..."):
                    image = _capture_from_camera()
                    st.session_state.captured_image = image
        
        else:  # Upload Image
            uploaded_file = st.file_uploader(
                "Upload a clear photo of your face",
                type=['jpg', 'jpeg', 'png'],
                help="Supported formats: JPG, JPEG, PNG"
            )
            
            if uploaded_file:
                image = Image.open(uploaded_file)
                image = np.array(image)
                # Convert RGB to BGR for OpenCV
                if len(image.shape) == 3 and image.shape[2] == 3:
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                st.session_state.captured_image = image
        
        st.divider()
        
        # Preview and quality check
        if image is not None:
            _show_image_preview(image)
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        if image is not None:
            with col1:
                clear_btn = st.form_submit_button(
                    "🔄 Clear Image",
                    use_container_width=True
                )
            with col3:
                register_btn = st.form_submit_button(
                    "✅ Register Face",
                    type="primary",
                    use_container_width=True
                )
        else:
            with col2:
                register_btn = st.form_submit_button(
                    "✅ Register Face",
                    type="primary",
                    use_container_width=True,
                    disabled=True
                )
            clear_btn = False
    
    # Handle clear button
    if clear_btn:
        st.session_state.captured_image = None
        st.rerun()
    
    # Handle registration
    if register_btn and image is not None:
        _process_registration(name, email, phone, department, image)
        # Clear captured image after successful registration
        st.session_state.captured_image = None


def _capture_from_camera() -> np.ndarray:
    """Capture image from camera"""
    try:
        from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT
        
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            st.error("❌ Cannot access camera. Please check your camera connection.")
            return None
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        
        # Warm up camera
        for _ in range(5):
            cap.read()
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            st.error("❌ Failed to capture image from camera")
            return None
        
        return frame
    
    except Exception as e:
        logger.error(f"Camera capture error: {e}")
        st.error(f"❌ Camera error: {e}")
        return None


def _show_image_preview(image: np.ndarray):
    """Show image preview with quality check"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📷 Preview")
        # Convert BGR to RGB for display
        display_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        st.image(display_image, use_container_width=True)
    
    with col2:
        st.subheader("✅ Quality Check")
        
        # Check image quality
        quality_ok, quality_msg = FaceQualityChecker.is_face_quality_acceptable(image)
        
        if quality_ok:
            st.success(f"✅ {quality_msg}")
        else:
            st.warning(f"⚠️ {quality_msg}")
        
        # Additional metrics
        blur_score = FaceQualityChecker.calculate_blur(image)
        brightness = FaceQualityChecker.calculate_brightness(image)
        
        metrics_col1, metrics_col2 = st.columns(2)
        with metrics_col1:
            st.metric("Blur Score", f"{blur_score:.1f}", 
                     delta="Good" if blur_score >= 30 else "Poor")
        with metrics_col2:
            st.metric("Brightness", f"{brightness:.0f}",
                     delta="Good" if 50 < brightness < 200 else "Adjust")


def _process_registration(name: str, email: str, phone: str, 
                          department: str, image: np.ndarray):
    """Process registration with validation"""
    
    # Validate input
    if not name or not name.strip():
        st.error("❌ Please enter a valid name")
        return
    
    name = name.strip()
    
    # Check if user already exists
    existing_users = db.get_all_users()
    if any(user['name'].lower() == name.lower() for user in existing_users):
        st.warning(f"⚠️ User '{name}' already exists. Choose a different name.")
        return
    
    # Register face
    with st.spinner("Processing registration..."):
        success, message = face_manager.register_face(
            name=name,
            image=image,
            capture_from_camera=False
        )
    
    if success:
        # Update user info if provided
        if email or phone or department:
            users = db.get_all_users()
            user = next((u for u in users if u['name'] == name), None)
            if user:
                update_data = {}
                if email:
                    update_data['email'] = email
                if phone:
                    update_data['phone'] = phone
                if department:
                    update_data['department'] = department
                
                db.update_user(user['id'], **update_data)
        
        # Success feedback
        st.success(f"✅ {message}")
        st.balloons()
        
        # Audio feedback - Play sound and announce name with greeting
        import time
        play_chime()
        time.sleep(0.5)  # Small delay between chime and speech
        speak_nigerian_greeting(name, context="registration")
        logger.info(f"Audio announcement triggered for registration: {name}")
        
        # Show summary
        with st.expander("📋 Registration Summary", expanded=True):
            st.write(f"**Name:** {name}")
            if email:
                st.write(f"**Email:** {email}")
            if phone:
                st.write(f"**Phone:** {phone}")
            if department:
                st.write(f"**Department:** {department}")
            st.write(f"**Registered:** {message}")
        
        logger.info(f"Successfully registered: {name}")
        
        # Option to register another
        if st.button("➕ Register Another Person"):
            st.rerun()
    
    else:
        st.error(f"❌ Registration failed: {message}")
        logger.error(f"Registration failed for {name}: {message}")
        
        # Show troubleshooting tips
        with st.expander("💡 Troubleshooting Tips"):
            st.markdown("""
            **Common issues and solutions:**
            
            - **No face detected:** Ensure your face is clearly visible and centered
            - **Multiple faces:** Only one person should be in the image
            - **Poor quality:** Improve lighting and use a higher quality camera
            - **Face too small:** Move closer to the camera
            - **Blurry image:** Hold steady and ensure camera is focused
            """)


def _delete_user(user_id: int, name: str):
    """Delete a user and their face data"""
    with st.spinner(f"Deleting {name}..."):
        # Delete from database
        db_success = db.delete_user(user_id)
        
        # Delete face data
        face_success, face_msg = face_manager.delete_face(name)
        
        if db_success and face_success:
            st.success(f"✅ Successfully deleted {name}")
            logger.info(f"Deleted user: {name} (ID: {user_id})")
            play_chime()
            st.rerun()
        elif db_success:
            st.warning(f"⚠️ User deleted but face data issue: {face_msg}")
            st.rerun()
        else:
            st.error(f"❌ Failed to delete user {name}")


def show_registered_users():
    """Show list of registered users with delete option"""
    st.subheader("👥 Registered Users")
    
    users = db.get_all_users()
    
    if not users:
        st.info("No users registered yet")
        return
    
    st.write(f"**Total registered:** {len(users)}")
    
    # Add search/filter
    search = st.text_input("🔍 Search users", placeholder="Enter name to search...")
    
    # Filter users based on search
    if search:
        users = [u for u in users if search.lower() in u['name'].lower()]
    
    if not users:
        st.warning("No users found matching your search")
        return
    
    # Display users with delete buttons
    for user in users:
        with st.expander(f"👤 {user['name']}", expanded=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**ID:** {user['id']}")
                if user.get('email'):
                    st.write(f"**Email:** {user['email']}")
                if user.get('phone'):
                    st.write(f"**Phone:** {user['phone']}")
                if user.get('department'):
                    st.write(f"**Department:** {user['department']}")
                st.write(f"**Registered:** {user['created_at']}")
            
            with col2:
                # Delete button with confirmation
                delete_key = f"delete_{user['id']}"
                confirm_key = f"confirm_{user['id']}"
                
                # Initialize confirmation state
                if confirm_key not in st.session_state:
                    st.session_state[confirm_key] = False
                
                if not st.session_state[confirm_key]:
                    if st.button(f"🗑️ Delete", key=delete_key, type="secondary", use_container_width=True):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("⚠️ Confirm?")
                    col_a, col_b = st.columns(2)
                    with col_a:
                        if st.button("✓", key=f"yes_{user['id']}", type="primary", use_container_width=True):
                            _delete_user(user['id'], user['name'])
                    with col_b:
                        if st.button("✗", key=f"no_{user['id']}", use_container_width=True):
                            st.session_state[confirm_key] = False
                            st.rerun()
