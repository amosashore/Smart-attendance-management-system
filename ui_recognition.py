"""
Enhanced real-time face recognition UI with live feedback
"""
import streamlit as st
import cv2
import numpy as np
from datetime import datetime
import time

from face_utils import face_manager, FACE_RECOGNITION_AVAILABLE
from audio_utils import audio_manager, play_chime, get_time_based_greeting, speak_nigerian_greeting
from config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT, ALLOW_MULTIPLE_CHECKIN
from database import db
from logger import get_logger

logger = get_logger(__name__)


def recognition_ui():
    """Face recognition and attendance marking page"""
    st.title("🎥 AMOS Real-Time Face Recognition")
    
    # Check if face_recognition is available
    if not FACE_RECOGNITION_AVAILABLE:
        st.error("⚠️ **face_recognition library not installed**")
        st.info(r"""
        Face recognition requires the `face_recognition` library.
        
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
    ### Automatic Attendance Marking
    
    This system will:
    - Detect faces in real-time from your camera
    - Recognize registered individuals
    - Automatically mark attendance
    - Provide audio feedback
    """)
    
    # Check if there are registered faces
    known_faces = face_manager.known_faces
    
    if not known_faces:
        st.warning("⚠️ No faces registered yet. Please register at least one face first.")
        st.info("👉 Please use the sidebar navigation to go to 'Register Face'")
        return
    
    st.success(f"✅ {len(known_faces)} face(s) registered and ready for recognition")
    
    # Recognition mode tabs
    tab1, tab2 = st.tabs(["📸 Single Capture", "🎥 Live Recognition"])
    
    with tab1:
        _single_capture_mode()
    
    with tab2:
        _live_recognition_mode()


def _single_capture_mode():
    """Single capture and recognition"""
    st.subheader("📸 Single Capture Mode")
    st.info("Click the button below to capture and recognize a single image")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col2:
        capture_btn = st.button("📷 Capture & Recognize", use_container_width=True, type="primary")
    
    if capture_btn:
        with st.spinner("Capturing image..."):
            image = _capture_image()
        
        if image is None:
            st.error("❌ Failed to capture image")
            return
        
        # Display captured image
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Captured Image")
            display_img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            st.image(display_img, use_container_width=True)
        
        with col2:
            st.subheader("Recognition Results")
            
            with st.spinner("Recognizing faces..."):
                results = face_manager.recognize_faces(image)
            
            if not results:
                st.warning("⚠️ No faces detected in the image")
                from audio_utils import _queue_speech
                _queue_speech("No faces detected")
            else:
                _process_recognition_results(results, image)


def _live_recognition_mode():
    """Live video recognition (simulated with multiple captures)"""
    st.subheader("🎥 Live Recognition Mode")
    st.info("This mode captures multiple frames for continuous recognition")
    
    col1, col2 = st.columns(2)
    
    with col1:
        duration = st.slider("Recognition Duration (seconds)", 5, 60, 10)
    
    with col2:
        interval = st.slider("Capture Interval (seconds)", 1, 5, 2)
    
    start_btn = st.button("▶️ Start Live Recognition", type="primary")
    
    if start_btn:
        _run_live_recognition(duration, interval)


def _capture_image() -> np.ndarray:
    """Capture single image from camera"""
    try:
        cap = cv2.VideoCapture(CAMERA_INDEX)
        if not cap.isOpened():
            logger.error("Cannot open camera")
            return None
        
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        
        # Warm up
        for _ in range(5):
            cap.read()
        
        ret, frame = cap.read()
        cap.release()
        
        if ret:
            return frame
        return None
    
    except Exception as e:
        logger.error(f"Camera capture error: {e}")
        return None


def _process_recognition_results(results: list, image: np.ndarray):
    """Process and display recognition results"""
    recognized_count = 0
    unknown_count = 0
    
    # Draw boxes on image
    annotated_image = image.copy()
    
    for result in results:
        name = result['name']
        confidence = result['confidence']
        location = result['location']
        
        top, right, bottom, left = location
        
        # Determine color
        if name == "Unknown":
            color = (0, 0, 255)  # Red
            unknown_count += 1
        else:
            color = (0, 128, 0)  # Darker green
            recognized_count += 1
        
        # Draw rectangle
        cv2.rectangle(annotated_image, (left, top), (right, bottom), color, 2)
        
        # Draw label
        label = f"{name} ({confidence:.1%})" if name != "Unknown" else "Unknown"
        cv2.rectangle(annotated_image, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(annotated_image, label, (left + 6, bottom - 6),
                   cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)
    
    # Display annotated image
    st.image(cv2.cvtColor(annotated_image, cv2.COLOR_BGR2RGB), 
             caption="Recognition Results", use_container_width=True)
    
    # Display results
    st.write(f"**Detected:** {len(results)} face(s)")
    st.write(f"**Recognized:** {recognized_count}")
    st.write(f"**Unknown:** {unknown_count}")
    
    # Mark attendance for recognized faces
    attendance_marked = []
    greeting = get_time_based_greeting()
    
    for result in results:
        if result['name'] != "Unknown":
            success, message = face_manager.mark_attendance(
                result['name'],
                result['confidence']
            )
            
            if success:
                attendance_marked.append(result['name'])
                st.success(f"✅ {message}")
                # Play sound and announce with female voice
                import time
                play_chime()
                time.sleep(0.5)  # Small delay between chime and speech
                speak_nigerian_greeting(result['name'], context="recognition")
                logger.info(f"Audio announcement triggered for {result['name']}")
            else:
                st.info(f"ℹ️ {message}")
                # Still announce the person even if already marked today
                if "already marked" in message.lower():
                    play_chime()
                    import time
                    time.sleep(0.5)
                    from audio_utils import _queue_speech
                    _queue_speech(f"{greeting} {result['name']}! Your attendance is already recorded for today.")
                    logger.info(f"Already marked announcement for {result['name']}")
    
    # Summary
    if attendance_marked:
        with st.expander("📋 Attendance Summary", expanded=True):
            for name in attendance_marked:
                st.write(f"✓ {name}")
    
    # Show individual results
    with st.expander("🔍 Detailed Results"):
        for i, result in enumerate(results, 1):
            st.write(f"**Face {i}:**")
            st.write(f"- Name: {result['name']}")
            st.write(f"- Confidence: {result['confidence']:.1%}")
            st.write(f"- Distance: {result['distance']:.3f}")
            st.divider()


def _run_live_recognition(duration: int, interval: int):
    """Run live recognition for specified duration"""
    st.info(f"🔴 Recognition active for {duration} seconds...")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    results_container = st.container()
    
    start_time = time.time()
    recognized_faces = set()
    capture_count = 0
    greeting = get_time_based_greeting()
    
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        progress = min(elapsed / duration, 1.0)
        progress_bar.progress(progress)
        
        remaining = duration - int(elapsed)
        status_text.text(f"⏱️ Time remaining: {remaining}s | Captures: {capture_count}")
        
        # Capture and recognize
        image = _capture_image()
        if image is not None:
            results = face_manager.recognize_faces(image)
            capture_count += 1
            
            for result in results:
                if result['name'] != "Unknown" and result['name'] not in recognized_faces:
                    success, message = face_manager.mark_attendance(
                        result['name'],
                        result['confidence']
                    )
                    
                    if success:
                        recognized_faces.add(result['name'])
                        
                        with results_container:
                            st.success(f"✅ {result['name']} - Attendance marked")
                        
                        # Play sound and announce with female voice
                        play_chime()
                        speak_nigerian_greeting(result['name'], context="recognition")
                    else:
                        # Mark as recognized even if attendance already marked
                        recognized_faces.add(result['name'])
                        with results_container:
                            st.info(f"ℹ️ {result['name']} - {message}")
                        # Still announce the person
                        play_chime()
                        from audio_utils import _queue_speech
                        import time
                        time.sleep(0.5)
                        _queue_speech(f"{greeting} {result['name']}! Welcome.")
        
        time.sleep(interval)
    
    progress_bar.progress(1.0)
    status_text.text(f"✅ Recognition complete! Captures: {capture_count}")
    
    # Final summary
    st.success(f"""
    **Session Summary:**
    - Duration: {duration} seconds
    - Total captures: {capture_count}
    - Recognized individuals: {len(recognized_faces)}
    """)
    
    if recognized_faces:
        st.write("**Attendance marked for:**")
        for name in recognized_faces:
            st.write(f"- {name}")


def show_today_attendance():
    """Show today's attendance"""
    st.subheader("📅 Today's Attendance")
    
    today = datetime.now().strftime("%Y-%m-%d")
    records = db.get_attendance(date_from=today, date_to=today)
    
    if not records:
        st.info("No attendance marked today")
        return
    
    st.write(f"**Total present:** {len(records)}")
    
    for record in records:
        status_icon = "🟢" if record.late == "On Time" else "🟡"
        st.write(f"{status_icon} {record.name} - {record.time} ({record.late})")
