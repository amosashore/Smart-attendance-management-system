"""
Enhanced database module with models and better practices
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, date, time as dt_time
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass, asdict
import pandas as pd
from pathlib import Path
import shutil

from config import DB_FILE, DB_BACKUP_DIR, LATE_THRESHOLD_HOUR, LATE_THRESHOLD_MINUTE
from logger import get_logger, log_function_call

logger = get_logger(__name__)


@dataclass
class AttendanceRecord:
    """Attendance record model"""
    id: Optional[int] = None
    name: str = ""
    date: str = ""
    time: str = ""
    status: str = "Present"
    last_seen: str = ""
    late: str = "On Time"
    confidence: float = 0.0
    notes: str = ""
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AttendanceRecord':
        """Create from dictionary"""
        return cls(**data)
    
    def is_late(self) -> bool:
        """Check if attendance is marked as late"""
        return self.late == "Late"


class DatabaseManager:
    """Manages database operations with context managers"""
    
    def __init__(self, db_file: Path = DB_FILE):
        self.db_file = db_file
        self._ensure_database()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}", exc_info=True)
            raise
        finally:
            if conn:
                conn.close()
    
    @log_function_call
    def _ensure_database(self):
        """Initialize database with tables"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Attendance table with enhanced schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT NOT NULL,
                    time TEXT NOT NULL,
                    status TEXT DEFAULT 'Present',
                    last_seen TEXT,
                    late TEXT DEFAULT 'On Time',
                    confidence REAL DEFAULT 0.0,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Users table for future expansion
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    email TEXT,
                    phone TEXT,
                    department TEXT,
                    role TEXT DEFAULT 'employee',
                    face_encoding_path TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better query performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_attendance_name 
                ON attendance(name)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_attendance_date 
                ON attendance(date)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_users_name 
                ON users(name)
            """)
            
            logger.info("Database initialized successfully")
    
    @log_function_call
    def save_attendance(self, record: AttendanceRecord) -> int:
        """
        Save attendance record
        
        Args:
            record: AttendanceRecord instance
        
        Returns:
            ID of inserted record
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO attendance 
                (name, date, time, status, last_seen, late, confidence, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                record.name,
                record.date,
                record.time,
                record.status,
                record.last_seen,
                record.late,
                record.confidence,
                record.notes
            ))
            record_id = cursor.lastrowid
            logger.info(f"Saved attendance record: {record.name} on {record.date}")
            return record_id
    
    @log_function_call
    def get_attendance(self, 
                       name: Optional[str] = None, 
                       date_from: Optional[str] = None,
                       date_to: Optional[str] = None,
                       status: Optional[str] = None) -> List[AttendanceRecord]:
        """
        Query attendance records with filters
        
        Args:
            name: Filter by name
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            status: Filter by status
        
        Returns:
            List of AttendanceRecord objects
        """
        with self.get_connection() as conn:
            query = "SELECT * FROM attendance WHERE 1=1"
            params = []
            
            if name:
                query += " AND name = ?"
                params.append(name)
            if date_from:
                query += " AND date >= ?"
                params.append(date_from)
            if date_to:
                query += " AND date <= ?"
                params.append(date_to)
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY date DESC, time DESC"
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                record = AttendanceRecord(
                    id=row['id'],
                    name=row['name'],
                    date=row['date'],
                    time=row['time'],
                    status=row['status'],
                    last_seen=row['last_seen'],
                    late=row['late'],
                    confidence=row['confidence'],
                    notes=row['notes'],
                    created_at=row['created_at']
                )
                records.append(record)
            
            return records
    
    @log_function_call
    def load_attendance_df(self) -> pd.DataFrame:
        """Load all attendance as DataFrame"""
        with self.get_connection() as conn:
            df = pd.read_sql_query("SELECT * FROM attendance ORDER BY date DESC, time DESC", conn)
            return df
    
    @log_function_call
    def check_duplicate_attendance(self, name: str, date: str) -> bool:
        """
        Check if attendance already exists for name on date
        
        Args:
            name: Person name
            date: Date string (YYYY-MM-DD)
        
        Returns:
            True if duplicate exists
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM attendance 
                WHERE name = ? AND date = ?
            """, (name, date))
            count = cursor.fetchone()[0]
            return count > 0
    
    @log_function_call
    def delete_attendance(self, record_id: int) -> bool:
        """Delete attendance record by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance WHERE id = ?", (record_id,))
            return cursor.rowcount > 0
    
    @log_function_call
    def clear_all_attendance(self) -> int:
        """Clear all attendance records"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM attendance")
            count = cursor.rowcount
            logger.warning(f"Cleared {count} attendance records")
            return count
    
    @log_function_call
    def get_statistics(self) -> Dict:
        """Get attendance statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) FROM attendance")
            total = cursor.fetchone()[0]
            
            # Unique employees
            cursor.execute("SELECT COUNT(DISTINCT name) FROM attendance")
            unique_employees = cursor.fetchone()[0]
            
            # Late arrivals
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE late = 'Late'")
            late_count = cursor.fetchone()[0]
            
            # Today's attendance
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (today,))
            today_count = cursor.fetchone()[0]
            
            # Average confidence
            cursor.execute("SELECT AVG(confidence) FROM attendance WHERE confidence > 0")
            avg_confidence = cursor.fetchone()[0] or 0.0
            
            return {
                'total_records': total,
                'unique_employees': unique_employees,
                'late_arrivals': late_count,
                'today_attendance': today_count,
                'average_confidence': round(avg_confidence, 2),
                'late_percentage': round((late_count / total * 100) if total > 0 else 0, 2)
            }
    
    @log_function_call
    def backup_database(self) -> Path:
        """Create database backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = DB_BACKUP_DIR / f"attendance_backup_{timestamp}.db"
        shutil.copy2(self.db_file, backup_file)
        logger.info(f"Database backed up to: {backup_file}")
        return backup_file
    
    @log_function_call
    def restore_database(self, backup_file: Path) -> bool:
        """Restore database from backup"""
        try:
            shutil.copy2(backup_file, self.db_file)
            logger.info(f"Database restored from: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore database: {e}")
            return False
    
    # User management methods
    @log_function_call
    def add_user(self, name: str, email: str = "", phone: str = "", 
                 department: str = "", role: str = "employee") -> int:
        """Add a new user"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (name, email, phone, department, role)
                VALUES (?, ?, ?, ?, ?)
            """, (name, email, phone, department, role))
            user_id = cursor.lastrowid
            logger.info(f"Added new user: {name}")
            return user_id
    
    @log_function_call
    def get_all_users(self) -> List[Dict]:
        """Get all users"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE is_active = 1 ORDER BY name")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    @log_function_call
    def update_user(self, user_id: int, **kwargs) -> bool:
        """Update user information"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Build dynamic update query
            fields = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [user_id]
            
            cursor.execute(f"""
                UPDATE users 
                SET {fields}, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            """, values)
            
            return cursor.rowcount > 0
    
    @log_function_call
    def delete_user(self, user_id: int) -> bool:
        """Delete a user and their attendance records"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get user name first
                cursor.execute("SELECT name FROM users WHERE id = ?", (user_id,))
                result = cursor.fetchone()
                
                if not result:
                    logger.warning(f"User ID {user_id} not found")
                    return False
                
                user_name = result[0]
                
                # Delete attendance records first (by name)
                cursor.execute("DELETE FROM attendance WHERE name = ?", (user_name,))
                deleted_attendance = cursor.rowcount
                logger.info(f"Deleted {deleted_attendance} attendance record(s) for {user_name}")
                
                # Delete user
                cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Deleted user: {user_name} (ID: {user_id})")
                return success
        except Exception as e:
            logger.error(f"Error deleting user {user_id}: {e}", exc_info=True)
            return False


# Global database instance
db = DatabaseManager()


# Helper functions for backward compatibility
def initialize_db():
    """Initialize database (backward compatible)"""
    global db
    db = DatabaseManager()
    logger.info("Database initialized")


def load_attendance() -> pd.DataFrame:
    """Load attendance as DataFrame (backward compatible)"""
    return db.load_attendance_df()


def save_attendance_row(row: Tuple):
    """Save attendance row (backward compatible)"""
    record = AttendanceRecord(
        name=row[0],
        date=row[1],
        time=row[2],
        status=row[3],
        last_seen=row[4],
        late=row[5],
        confidence=row[6] if len(row) > 6 else 0.0,
        notes=row[7] if len(row) > 7 else ""
    )
    return db.save_attendance(record)


def clear_attendance_records():
    """Clear all records (backward compatible)"""
    return db.clear_all_attendance()
