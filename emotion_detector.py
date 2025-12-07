"""
Facial Expression/Emotion Detection Module
Detects emotions from facial expressions using OpenCV and deep learning
"""
import cv2
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict
from logger import get_logger

logger = get_logger(__name__)

class EmotionDetector:
    """Detects facial expressions and emotions"""
    
    # Emotion labels from the pre-trained model
    EMOTIONS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']
    
    def __init__(self):
        self.face_cascade = None
        self.emotion_model = None
        self.model_loaded = False
        self._init_detector()
    
    def _init_detector(self):
        """Initialize face cascade and emotion model"""
        try:
            # Load Haar Cascade for face detection
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(cascade_path)
            
            if self.face_cascade.empty():
                logger.warning("Failed to load face cascade for emotion detection")
                return
            
            logger.info("Emotion detector initialized (using feature-based approach)")
            self.model_loaded = True
            
        except Exception as e:
            logger.error(f"Failed to initialize emotion detector: {e}")
    
    def detect_emotion(self, image: np.ndarray, face_location: Optional[Tuple] = None) -> Dict:
        """
        Detect emotion from face in image
        
        Args:
            image: Image array (BGR format)
            face_location: Optional (top, right, bottom, left) coordinates
        
        Returns:
            Dict with emotion, confidence, and face location
        """
        if not self.model_loaded:
            return {'emotion': 'neutral', 'confidence': 0.5, 'method': 'default'}
        
        try:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Get face region
            if face_location:
                top, right, bottom, left = face_location
                face_roi = gray[top:bottom, left:right]
            else:
                # Detect face
                faces = self.face_cascade.detectMultiScale(
                    gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
                )
                
                if len(faces) == 0:
                    return {'emotion': 'neutral', 'confidence': 0.3, 'method': 'no_face'}
                
                # Use first detected face
                x, y, w, h = faces[0]
                face_roi = gray[y:y+h, x:x+w]
                face_location = (y, x+w, y+h, x)
            
            # Analyze facial features for emotion estimation
            emotion, confidence = self._analyze_facial_features(face_roi)
            
            return {
                'emotion': emotion,
                'confidence': confidence,
                'location': face_location,
                'method': 'feature_analysis'
            }
            
        except Exception as e:
            logger.error(f"Error detecting emotion: {e}")
            return {'emotion': 'neutral', 'confidence': 0.5, 'method': 'error'}
    
    def _analyze_facial_features(self, face_roi: np.ndarray) -> Tuple[str, float]:
        """
        Analyze facial features to estimate emotion
        Simple heuristic-based approach using image properties
        
        Args:
            face_roi: Grayscale face region
        
        Returns:
            Tuple of (emotion, confidence)
        """
        try:
            # Resize for consistent analysis
            face_roi = cv2.resize(face_roi, (48, 48))
            
            # Calculate various image statistics
            mean_intensity = np.mean(face_roi)
            std_intensity = np.std(face_roi)
            
            # Detect edges (smile/frown detection proxy)
            edges = cv2.Canny(face_roi, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size
            
            # Analyze upper vs lower face contrast
            upper_half = face_roi[:24, :]
            lower_half = face_roi[24:, :]
            upper_mean = np.mean(upper_half)
            lower_mean = np.mean(lower_half)
            contrast_ratio = abs(upper_mean - lower_mean) / (upper_mean + lower_mean + 1e-5)
            
            # Simple heuristic rules for emotion detection
            # This is a simplified approach - production would use trained ML model
            
            if edge_density > 0.15 and lower_mean > upper_mean:
                # High edge density in lower face suggests smile
                emotion = 'happy'
                confidence = min(0.85, 0.6 + edge_density)
            elif std_intensity > 50 and contrast_ratio > 0.2:
                # High variation suggests surprise or fear
                emotion = 'surprise'
                confidence = min(0.75, 0.5 + contrast_ratio)
            elif mean_intensity < 100 and std_intensity < 35:
                # Dark, low variation suggests sad
                emotion = 'sad'
                confidence = 0.65
            elif std_intensity > 60:
                # Very high variation could indicate anger
                emotion = 'angry'
                confidence = 0.60
            else:
                # Default to neutral
                emotion = 'neutral'
                confidence = 0.70
            
            return emotion, confidence
            
        except Exception as e:
            logger.error(f"Error in feature analysis: {e}")
            return 'neutral', 0.5
    
    def get_emotion_greeting(self, emotion: str, name: str) -> str:
        """
        Generate greeting based on detected emotion
        
        Args:
            emotion: Detected emotion
            name: Person's name
        
        Returns:
            Customized greeting message
        """
        from audio_utils import get_time_based_greeting
        
        base_greeting = get_time_based_greeting()
        
        emotion_greetings = {
            'happy': f"{base_greeting} {name}! You look cheerful today! Welcome!",
            'sad': f"{base_greeting} {name}. Hope you have a better day ahead. Welcome!",
            'angry': f"{base_greeting} {name}. Welcome! Hope everything is alright.",
            'surprise': f"{base_greeting} {name}! Nice to see you! Welcome!",
            'fear': f"{base_greeting} {name}. Welcome! No worries, you're in good hands.",
            'disgust': f"{base_greeting} {name}. Welcome!",
            'neutral': f"{base_greeting} {name}! Welcome! Your attendance has been marked successfully."
        }
        
        return emotion_greetings.get(emotion, emotion_greetings['neutral'])


# Global emotion detector instance
emotion_detector = EmotionDetector()
