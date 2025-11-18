"""
Utility functions and helpers
"""
import re
from typing import Optional, Tuple
from datetime import datetime, timedelta
import hashlib
from pathlib import Path


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Validate phone number format"""
    # Remove common separators
    cleaned = re.sub(r'[\s\-\(\)]', '', phone)
    # Check if it's a valid phone number (10-15 digits, optional + prefix)
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, cleaned))


def validate_name(name: str) -> Tuple[bool, str]:
    """
    Validate person name
    
    Returns:
        Tuple of (is_valid, message)
    """
    if not name or not name.strip():
        return False, "Name cannot be empty"
    
    name = name.strip()
    
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    
    if len(name) > 100:
        return False, "Name is too long (max 100 characters)"
    
    # Check for invalid characters
    if not re.match(r'^[a-zA-Z\s\-\.\']+$', name):
        return False, "Name contains invalid characters"
    
    return True, "Valid name"


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
    name = name[:100]
    return f"{name}.{ext}" if ext else name


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime object to string"""
    return dt.strftime(format_str)


def parse_datetime(dt_str: str, format_str: str = "%Y-%m-%d %H:%M:%S") -> Optional[datetime]:
    """Parse datetime string to datetime object"""
    try:
        return datetime.strptime(dt_str, format_str)
    except (ValueError, TypeError):
        return None


def get_time_ago(dt: datetime) -> str:
    """Get human-readable time ago string"""
    now = datetime.now()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return "just now"
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    else:
        days = int(seconds / 86400)
        return f"{days} day{'s' if days != 1 else ''} ago"


def calculate_file_hash(file_path: Path, algorithm: str = 'sha256') -> str:
    """Calculate hash of a file"""
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as f:
        while chunk := f.read(8192):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()


def format_file_size(size_bytes: int) -> str:
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def truncate_string(text: str, max_length: int = 50, suffix: str = '...') -> str:
    """Truncate string to maximum length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def generate_unique_id() -> str:
    """Generate unique identifier"""
    from uuid import uuid4
    return str(uuid4())


def is_business_hours(dt: Optional[datetime] = None, 
                      start_hour: int = 8, 
                      end_hour: int = 18) -> bool:
    """Check if datetime is within business hours"""
    if dt is None:
        dt = datetime.now()
    
    # Check if weekday
    if dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    # Check hour range
    return start_hour <= dt.hour < end_hour


def get_week_range(dt: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """Get start and end of week for given datetime"""
    if dt is None:
        dt = datetime.now()
    
    # Monday = 0, Sunday = 6
    start = dt - timedelta(days=dt.weekday())
    end = start + timedelta(days=6)
    
    return start.replace(hour=0, minute=0, second=0), \
           end.replace(hour=23, minute=59, second=59)


def get_month_range(dt: Optional[datetime] = None) -> Tuple[datetime, datetime]:
    """Get start and end of month for given datetime"""
    if dt is None:
        dt = datetime.now()
    
    start = dt.replace(day=1, hour=0, minute=0, second=0)
    
    # Get last day of month
    if dt.month == 12:
        end = dt.replace(year=dt.year + 1, month=1, day=1)
    else:
        end = dt.replace(month=dt.month + 1, day=1)
    
    end = end - timedelta(days=1)
    end = end.replace(hour=23, minute=59, second=59)
    
    return start, end


def retry_on_failure(func, max_attempts: int = 3, delay: float = 1.0):
    """Retry function on failure"""
    import time
    
    for attempt in range(max_attempts):
        try:
            return func()
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            time.sleep(delay)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers"""
    try:
        return numerator / denominator if denominator != 0 else default
    except (TypeError, ZeroDivisionError):
        return default


class Timer:
    """Context manager for timing code execution"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
        self.elapsed = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"{self.name} took {self.elapsed:.3f} seconds")
        return False
