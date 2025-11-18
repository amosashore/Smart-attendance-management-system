"""
Simplified Face Recognition using OpenCV's built-in Haar Cascades
This is a lightweight alternative that works without dlib or MediaPipe
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import pickle
from datetime import datetime

from config import (
    KNOWN_FACES_DIR, FACE_TOLERANCE,
    MIN_FACE_SIZE, CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT,
    LATE_THRESHOLD_HOUR, LATE_THRESHOLD_MINUTE,
    ALLOW_MULTIPLE_CHECKIN
)
from database import save_attendance_row, AttendanceRecord, db
from logger import get_logger

logger = get_logger(__name__)


class SimpleFaceRecognition:
    """Simple face recognition using OpenCV Haar Cascades + template matching"""
    
    def __init__(self):
        self.known_faces: Dict[str, np.ndarray] = {}
        # Load Haar Cascade classifier
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Verify the cascade loaded correctly
        if self.face_cascade.empty():
            logger.error("Failed to load Haar Cascade classifier")
            raise RuntimeError("Could not load face detection model")
        
        self.load_known_faces()
    
    def load_known_faces(self) -> Dict[str, np.ndarray]:
        """Load all known faces from directory"""
        faces = {}
        KNOWN_FACES_DIR.mkdir(exist_ok=True)
        
        # Try to load from cache
        cache_file = KNOWN_FACES_DIR / "face_cache_opencv.pkl"
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
                name_parts = file.stem.split("_")
                if len(name_parts) >= 2 and name_parts[-1].isdigit():
                    name = "_".join(name_parts[:-2])
                else:
                    name = file.stem
                
                img = cv2.imread(str(file))
                if img is not None:
                    # Extract face and create feature vector
                    features = self._extract_face_features(img)
                    if features is not None:
                        faces[name] = features
                        logger.info(f"Loaded face: {name}")
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        # Save cache
        if faces:
            try:
                with open(cache_file, 'wb') as f:
                    pickle.dump(faces, f)
                logger.info(f"Saved {len(faces)} faces to cache")
            except Exception as e:
                logger.error(f"Failed to save cache: {e}")
        
        self.known_faces = faces
        return faces
    
    def _extract_face_features(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Extract face features using OpenCV"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect face
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE)
        )
        
        if len(faces) == 0:
            return None
        
        # Get first face
        x, y, w, h = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        
        # Resize to standard size
        face_resized = cv2.resize(face_roi, (100, 100))
        
        # Normalize
        face_normalized = cv2.equalizeHist(face_resized)
        
        # Create feature vector
        features = face_normalized.flatten().astype(np.float32) / 255.0
        
        return features
    
    def register_face(self, name: str, image: Optional[np.ndarray] = None,
                     capture_from_camera: bool = True) -> Tuple[bool, str]:
        """Register a new face"""
        try:
            if capture_from_camera:
                cap = cv2.VideoCapture(CAMERA_INDEX)
                if not cap.isOpened():
                    return False, "Cannot access camera"
                
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                
                # Warm up camera
                for _ in range(5):
                    cap.read()
                
                ret, frame = cap.read()
                cap.release()
                
                if not ret:
                    return False, "Failed to capture image"
                
                image = frame
            
            if image is None:
                return False, "No image provided"
            
            # Extract features
            features = self._extract_face_features(image)
            if features is None:
                return False, "No face detected in image. Please ensure your face is clearly visible."
            
            # Save image
            KNOWN_FACES_DIR.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}.jpg"
            filepath = KNOWN_FACES_DIR / filename
            cv2.imwrite(str(filepath), image)
            
            # Update known faces
            self.known_faces[name] = features
            
            # Invalidate cache
            cache_file = KNOWN_FACES_DIR / "face_cache_opencv.pkl"
            if cache_file.exists():
                cache_file.unlink()
            
            # Add to database
            try:
                db.add_user(name=name)
            except Exception as e:
                logger.warning(f"User may already exist in database: {e}")
            
            logger.info(f"Successfully registered face: {name}")
            return True, f"Face registered successfully for {name}"
            
        except Exception as e:
            logger.error(f"Error registering face: {e}", exc_info=True)
            return False, f"Registration failed: {str(e)}"
    
    def _compare_faces(self, features1: np.ndarray, features2: np.ndarray) -> float:
        """Compare two face feature vectors using multiple metrics"""
        # Euclidean distance
        euclidean_dist = np.linalg.norm(features1 - features2)
        
        # Cosine similarity
        dot_product = np.dot(features1, features2)
        norm_product = np.linalg.norm(features1) * np.linalg.norm(features2)
        cosine_sim = dot_product / norm_product if norm_product > 0 else 0
        
        # Correlation coefficient
        correlation = np.corrcoef(features1, features2)[0, 1]
        
        # Combined score (weighted average)
        # Lower euclidean distance and higher similarity is better
        normalized_dist = 1 / (1 + euclidean_dist)
        similarity_score = (0.3 * normalized_dist + 0.4 * cosine_sim + 0.3 * correlation)
        
        return float(max(0, min(1, similarity_score)))
    
    def recognize_faces(self, image: np.ndarray) -> List[Dict]:
        """Recognize faces in an image"""
        if not self.known_faces:
            logger.warning("No known faces loaded")
            return []
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Detect faces
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(MIN_FACE_SIZE, MIN_FACE_SIZE)
        )
        
        if len(faces) == 0:
            return []
        
        recognized = []
        
        for (x, y, w, h) in faces:
            # Extract face ROI
            face_roi = gray[y:y+h, x:x+w]
            face_resized = cv2.resize(face_roi, (100, 100))
            face_normalized = cv2.equalizeHist(face_resized)
            features = face_normalized.flatten().astype(np.float32) / 255.0
            
            # Compare with known faces
            best_match = "Unknown"
            best_similarity = 0.0
            
            for name, known_features in self.known_faces.items():
                similarity = self._compare_faces(features, known_features)
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = name
            
            # Only accept if similarity is high enough
            threshold = 0.6  # Adjustable threshold
            if best_similarity < threshold:
                best_match = "Unknown"
            
            recognized.append({
                'name': best_match,
                'confidence': best_similarity,
                'location': (y, x + w, y + h, x),  # top, right, bottom, left
                'distance': 1.0 - best_similarity
            })
        
        return recognized
    
    def mark_attendance(self, name: str, confidence: float) -> Tuple[bool, str]:
        """Mark attendance for a person"""
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
            notes=f"Auto-recognized with {confidence:.1%} confidence (OpenCV)"
        )
        
        db.save_attendance(record)
        logger.info(f"Marked attendance: {name} ({late_status})")
        
        return True, f"Attendance marked for {name}"
    
    def delete_face(self, name: str) -> Tuple[bool, str]:
        """Delete a registered face"""
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
            cache_file = KNOWN_FACES_DIR / "face_cache_opencv.pkl"
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


# Create the simple face recognition instance
simple_face_manager = SimpleFaceRecognition()
