"""
Enhanced face recognition utilities with quality checks and better error handling
"""
import cv2
import os
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pickle

# Try to import face_recognition, but allow app to start without it
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("INFO: Using OpenCV-based face recognition (lightweight alternative).")
    
# Import simple face recognition as fallback
try:
    from face_utils_simple import simple_face_manager
    SIMPLE_FACE_AVAILABLE = True
except ImportError:
    SIMPLE_FACE_AVAILABLE = False
    print("ERROR: Face recognition unavailable - OpenCV module failed to load.")

from config import (
    KNOWN_FACES_DIR, FACE_TOLERANCE, FACE_MODEL, 
    MIN_FACE_SIZE, FACE_QUALITY_THRESHOLD,
    CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,
    LATE_THRESHOLD_HOUR, LATE_THRESHOLD_MINUTE,
    ALLOW_MULTIPLE_CHECKIN
)
from database import save_attendance_row, AttendanceRecord, db
from logger import get_logger, log_function_call

logger = get_logger(__name__)


class FaceQualityChecker:
    """Check face image quality"""
    
    @staticmethod
    def calculate_blur(image: np.ndarray) -> float:
        """Calculate image blur using Laplacian variance"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return cv2.Laplacian(gray, cv2.CV_64F).var()
    
    @staticmethod
    def calculate_brightness(image: np.ndarray) -> float:
        """Calculate average brightness"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return np.mean(gray)
    
    @staticmethod
    def is_face_quality_acceptable(image: np.ndarray, min_blur: float = FACE_QUALITY_THRESHOLD) -> Tuple[bool, str]:
        """
        Check if face image quality is acceptable
        
        Returns:
            Tuple of (is_acceptable, reason)
        """
        blur_score = FaceQualityChecker.calculate_blur(image)
        brightness = FaceQualityChecker.calculate_brightness(image)
        
        if blur_score < min_blur:
            return False, f"Image too blurry (score: {blur_score:.1f})"
        
        if brightness < 50:
            return False, "Image too dark"
        
        if brightness > 200:
            return False, "Image too bright"
        
        return True, "Quality acceptable"


class FaceRecognitionManager:
    """Manages face recognition operations"""
    
    def __init__(self):
        if not FACE_RECOGNITION_AVAILABLE:
            raise ImportError("face_recognition library not available")
        self.known_faces: Dict[str, np.ndarray] = {}
        self.face_encodings_cache: Dict[str, np.ndarray] = {}
        self.load_known_faces()
    
    @log_function_call
    def load_known_faces(self) -> Dict[str, np.ndarray]:
        """Load all known faces from directory"""
        if not FACE_RECOGNITION_AVAILABLE:
            logger.warning("face_recognition not available, cannot load faces")
            return {}
        
        faces = {}
        KNOWN_FACES_DIR.mkdir(exist_ok=True)
        
        # Try to load from cache first
        cache_file = KNOWN_FACES_DIR / "encodings_cache.pkl"
        if cache_file.exists():
            try:
                with open(cache_file, 'rb') as f:
                    faces = pickle.load(f)
                    logger.info(f"Loaded {len(faces)} faces from cache")
                    self.known_faces = faces
                    return faces
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        
        # Load from image files
        for file in KNOWN_FACES_DIR.glob("*.jpg"):
            try:
                # Extract name from filename (handle timestamps)
                name_parts = file.stem.split("_")
                if len(name_parts) >= 2 and name_parts[-1].isdigit():
                    # Remove timestamp from name
                    name = "_".join(name_parts[:-2])
                else:
                    name = file.stem
                
                img = face_recognition.load_image_file(str(file))
                encodings = face_recognition.face_encodings(img, model=FACE_MODEL)
                
                if encodings:
                    faces[name] = encodings[0]
                    logger.info(f"Loaded face: {name}")
                else:
                    logger.warning(f"No face found in {file}")
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        # Save cache
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(faces, f)
            logger.info(f"Saved {len(faces)} faces to cache")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
        
        self.known_faces = faces
        return faces
    
    @log_function_call
    def register_face(self, name: str, image: Optional[np.ndarray] = None, 
                     capture_from_camera: bool = True) -> Tuple[bool, str]:
        """
        Register a new face
        
        Args:
            name: Person's name
            image: Face image (if not capturing from camera)
            capture_from_camera: Whether to capture from camera
        
        Returns:
            Tuple of (success, message)
        """
        if not FACE_RECOGNITION_AVAILABLE:
            return False, "face_recognition library not installed. Please install it first."
        
        try:
            if capture_from_camera:
                cap = cv2.VideoCapture(CAMERA_INDEX)
                if not cap.isOpened():
                    return False, "Cannot access camera"
                
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    return False, "Failed to capture image"
                
                image = frame
            
            if image is None:
                return False, "No image provided"
            
            # Check image quality
            quality_ok, quality_msg = FaceQualityChecker.is_face_quality_acceptable(image)
            if not quality_ok:
                return False, f"Poor image quality: {quality_msg}"
            
            # Detect faces
            face_locations = face_recognition.face_locations(image, model=FACE_MODEL)
            if not face_locations:
                return False, "No face detected in image"
            
            if len(face_locations) > 1:
                return False, "Multiple faces detected. Please ensure only one face is visible"
            
            # Check face size
            top, right, bottom, left = face_locations[0]
            face_width = right - left
            face_height = bottom - top
            
            if face_width < MIN_FACE_SIZE or face_height < MIN_FACE_SIZE:
                return False, f"Face too small. Minimum size: {MIN_FACE_SIZE}px"
            
            # Get face encoding
            encodings = face_recognition.face_encodings(image, face_locations, model=FACE_MODEL)
            if not encodings:
                return False, "Could not encode face"
            
            # Save image
            KNOWN_FACES_DIR.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}.jpg"
            filepath = KNOWN_FACES_DIR / filename
            cv2.imwrite(str(filepath), image)
            
            # Update known faces
            self.known_faces[name] = encodings[0]
            
            # Invalidate cache
            cache_file = KNOWN_FACES_DIR / "encodings_cache.pkl"
            if cache_file.exists():
                cache_file.unlink()
            
            # Add to database
            db.add_user(name=name)
            
            logger.info(f"Successfully registered face: {name}")
            return True, f"Face registered successfully for {name}"
            
        except Exception as e:
            logger.error(f"Error registering face: {e}", exc_info=True)
            return False, f"Registration failed: {str(e)}"
    
    @log_function_call
    def delete_face(self, name: str) -> Tuple[bool, str]:
        """
        Delete a registered face
        
        Args:
            name: Person's name
        
        Returns:
            Tuple of (success, message)
        """
        try:
            # Remove from known_faces dictionary
            if name in self.known_faces:
                del self.known_faces[name]
            
            # Delete face image files
            deleted_files = 0
            if KNOWN_FACES_DIR.exists():
                for file in KNOWN_FACES_DIR.glob(f"{name}_*.jpg"):
                    file.unlink()
                    deleted_files += 1
                    logger.info(f"Deleted face file: {file.name}")
            
            # Invalidate cache
            cache_file = KNOWN_FACES_DIR / "encodings_cache.pkl"
            if cache_file.exists():
                cache_file.unlink()
                logger.info("Invalidated face encodings cache")
            
            if deleted_files > 0:
                logger.info(f"Successfully deleted face data for: {name}")
                return True, f"Deleted {deleted_files} face image(s) for {name}"
            else:
                return True, f"No face images found for {name}, but removed from system"
                
        except Exception as e:
            logger.error(f"Error deleting face for {name}: {e}", exc_info=True)
            return False, f"Failed to delete face: {str(e)}"
    
    @log_function_call
    def recognize_faces(self, image: np.ndarray) -> List[Dict]:
        """
        Recognize faces in an image
        
        Args:
            image: Input image
        
        Returns:
            List of recognized faces with info
        """
        if not FACE_RECOGNITION_AVAILABLE:
            logger.error("face_recognition not available")
            return []
        
        if not self.known_faces:
            logger.warning("No known faces loaded")
            return []
        
        # Find faces in image
        face_locations = face_recognition.face_locations(image, model=FACE_MODEL)
        if not face_locations:
            return []
        
        face_encodings = face_recognition.face_encodings(image, face_locations, model=FACE_MODEL)
        
        results = []
        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Compare with known faces
            matches = face_recognition.compare_faces(
                list(self.known_faces.values()),
                face_encoding,
                tolerance=FACE_TOLERANCE
            )
            
            face_distances = face_recognition.face_distance(
                list(self.known_faces.values()),
                face_encoding
            )
            
            name = "Unknown"
            confidence = 0.0
            
            if True in matches:
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = list(self.known_faces.keys())[best_match_index]
                    confidence = 1 - face_distances[best_match_index]
            
            results.append({
                'name': name,
                'confidence': round(float(confidence), 3),
                'location': face_location,
                'distance': float(face_distances[best_match_index]) if matches.count(True) > 0 else 1.0
            })
        
        return results
    
    @log_function_call
    def mark_attendance(self, name: str, confidence: float) -> Tuple[bool, str]:
        """
        Mark attendance for a person
        
        Args:
            name: Person's name
            confidence: Recognition confidence
        
        Returns:
            Tuple of (success, message)
        """
        if name == "Unknown":
            return False, "Cannot mark attendance for unknown person"
        
        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")
        
        # Check for duplicate
        if not ALLOW_MULTIPLE_CHECKIN:
            if db.check_duplicate_attendance(name, date_str):
                return False, f"{name} already marked present today"
        
        # Determine if late
        is_late = now.hour > LATE_THRESHOLD_HOUR or (
            now.hour == LATE_THRESHOLD_HOUR and now.minute > LATE_THRESHOLD_MINUTE
        )
        late_status = "Late" if is_late else "On Time"
        
        # Create attendance record
        record = AttendanceRecord(
            name=name,
            date=date_str,
            time=time_str,
            status="Present",
            last_seen=time_str,
            late=late_status,
            confidence=confidence,
            notes=f"Auto-recognized with {confidence:.1%} confidence"
        )
        
        db.save_attendance(record)
        logger.info(f"Marked attendance: {name} ({late_status})")
        
        return True, f"Attendance marked for {name}"


# Global instance - use advanced if available, otherwise use simple
if FACE_RECOGNITION_AVAILABLE:
    try:
        face_manager = FaceRecognitionManager()
        logger.info("Using advanced face_recognition library")
    except Exception as e:
        logger.warning(f"Failed to initialize face_recognition: {e}")
        if SIMPLE_FACE_AVAILABLE:
            face_manager = simple_face_manager
            logger.info("Falling back to simple OpenCV-based face recognition")
            # Update the flag for UI purposes
            FACE_RECOGNITION_AVAILABLE = True  # Allow UI to show face features
        else:
            face_manager = None
elif SIMPLE_FACE_AVAILABLE:
    face_manager = simple_face_manager
    logger.info("Using simple OpenCV-based face recognition")
    FACE_RECOGNITION_AVAILABLE = True  # Allow UI to show face features
else:
    face_manager = None
    logger.warning("No face recognition available")
    FACE_RECOGNITION_AVAILABLE = False


# Backward compatible functions
def get_known_faces() -> Dict[str, np.ndarray]:
    """Get known faces (backward compatible)"""
    return face_manager.load_known_faces()


def register_face(name: str, save_dir=None) -> bool:
    """Register face (backward compatible)"""
    success, message = face_manager.register_face(name)
    if not success:
        logger.error(message)
    return success
