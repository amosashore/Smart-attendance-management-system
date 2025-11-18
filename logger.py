"""
Logging configuration and utilities
"""
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from config import LOG_FILE, LOG_LEVEL, LOG_FORMAT, LOG_MAX_BYTES, LOG_BACKUP_COUNT

# Ensure logs directory exists
LOG_FILE.parent.mkdir(exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper()),
    format=LOG_FORMAT,
    handlers=[
        # Console handler
        logging.StreamHandler(sys.stdout),
        # File handler with rotation
        RotatingFileHandler(
            LOG_FILE,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
    ]
)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class StreamlitLogHandler(logging.Handler):
    """Custom log handler for Streamlit"""
    
    def __init__(self):
        super().__init__()
        self.logs = []
        self.max_logs = 100
    
    def emit(self, record):
        log_entry = self.format(record)
        self.logs.append({
            'timestamp': record.created,
            'level': record.levelname,
            'message': log_entry,
            'name': record.name
        })
        
        # Keep only recent logs
        if len(self.logs) > self.max_logs:
            self.logs.pop(0)
    
    def get_logs(self, level=None):
        """Get stored logs, optionally filtered by level"""
        if level:
            return [log for log in self.logs if log['level'] == level]
        return self.logs
    
    def clear_logs(self):
        """Clear stored logs"""
        self.logs.clear()


# Global Streamlit log handler
streamlit_handler = StreamlitLogHandler()
streamlit_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logging.getLogger().addHandler(streamlit_handler)


def log_function_call(func):
    """Decorator to log function calls"""
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}", exc_info=True)
            raise
    
    return wrapper


def get_recent_logs(count: int = 50):
    """Get recent log entries"""
    return streamlit_handler.get_logs()[-count:]
