"""
Configuration management for Smart Attendance System
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"

# Create directories if they don't exist
DATA_DIR.mkdir(exist_ok=True)
ASSETS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database configuration
DB_FILE = DATA_DIR / "attendance.db"
DB_BACKUP_DIR = DATA_DIR / "backups"
DB_BACKUP_DIR.mkdir(exist_ok=True)

# Face recognition settings
KNOWN_FACES_DIR = DATA_DIR / "known_faces"
KNOWN_FACES_DIR.mkdir(exist_ok=True)
FACE_TOLERANCE = float(os.getenv("FACE_TOLERANCE", "0.6"))
FACE_MODEL = os.getenv("FACE_MODEL", "hog")  # 'hog' or 'cnn'
MIN_FACE_SIZE = int(os.getenv("MIN_FACE_SIZE", "50"))
FACE_QUALITY_THRESHOLD = float(os.getenv("FACE_QUALITY_THRESHOLD", "30.0"))

# Audio settings
CHIME_PATH = ASSETS_DIR / "chime.mp3"
ENABLE_AUDIO = os.getenv("ENABLE_AUDIO", "true").lower() == "true"
SPEECH_RATE = int(os.getenv("SPEECH_RATE", "170"))
AUDIO_VOLUME = float(os.getenv("AUDIO_VOLUME", "0.7"))

# Attendance settings
LATE_THRESHOLD_HOUR = int(os.getenv("LATE_THRESHOLD_HOUR", "10"))
LATE_THRESHOLD_MINUTE = int(os.getenv("LATE_THRESHOLD_MINUTE", "0"))
ALLOW_MULTIPLE_CHECKIN = os.getenv("ALLOW_MULTIPLE_CHECKIN", "false").lower() == "true"

# Authentication settings
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-secret-key-in-production")
SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "amos")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")  # Set via environment

# Camera settings
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))
CAMERA_WIDTH = int(os.getenv("CAMERA_WIDTH", "640"))
CAMERA_HEIGHT = int(os.getenv("CAMERA_HEIGHT", "480"))
CAMERA_FPS = int(os.getenv("CAMERA_FPS", "30"))

# Logging settings
LOG_FILE = LOGS_DIR / "app.log"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", "10485760"))  # 10MB
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", "5"))

# UI settings
PAGE_TITLE = "Smart Attendance System"
PAGE_ICON = "📸"
THEME_PRIMARY_COLOR = "#FF4B4B"
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", "10"))  # MB

# Export settings
EXPORT_FORMATS = ["xlsx", "csv", "json"]
DEFAULT_EXPORT_FORMAT = os.getenv("DEFAULT_EXPORT_FORMAT", "xlsx")

# Performance settings
ENABLE_CACHE = os.getenv("ENABLE_CACHE", "true").lower() == "true"
CACHE_TTL_SECONDS = int(os.getenv("CACHE_TTL_SECONDS", "300"))

class Config:
    """Configuration class with validation"""
    
    @staticmethod
    def validate():
        """Validate critical configuration"""
        errors = []
        
        if not SECRET_KEY or SECRET_KEY == "change-this-secret-key-in-production":
            errors.append("WARNING: Using default SECRET_KEY. Set a secure key in production!")
        
        if not CHIME_PATH.exists() and ENABLE_AUDIO:
            errors.append(f"Audio file not found: {CHIME_PATH}")
        
        if not 0 <= FACE_TOLERANCE <= 1:
            errors.append(f"FACE_TOLERANCE must be between 0 and 1, got {FACE_TOLERANCE}")
        
        return errors
    
    @staticmethod
    def get_db_connection_string():
        """Get database connection string"""
        return f"sqlite:///{DB_FILE}"
    
    @staticmethod
    def to_dict():
        """Convert config to dictionary"""
        return {
            "db_file": str(DB_FILE),
            "known_faces_dir": str(KNOWN_FACES_DIR),
            "face_tolerance": FACE_TOLERANCE,
            "enable_audio": ENABLE_AUDIO,
            "late_threshold": f"{LATE_THRESHOLD_HOUR}:{LATE_THRESHOLD_MINUTE:02d}",
            "camera_index": CAMERA_INDEX,
            "log_level": LOG_LEVEL,
        }
