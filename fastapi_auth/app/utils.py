from datetime import datetime, timedelta
from jose import jwt
import hashlib
import secrets
import string
import random
from .config import SECRET_KEY, ALGORITHM
from typing import Optional

def get_password_hash(password: str) -> str:
    """Simple SHA256 + salt password hashing"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify SHA256 + salt password"""
    try:
        salt, stored_hash = hashed_password.split(':')
        password_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return password_hash == stored_hash
    except:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ============================================
# Unique Code Generator
# ============================================

def generate_unique_attendance_code(
    class_id: int,
    section_id: int,
    teacher_id: int
) -> str:
    """
    Generate a unique 10-character attendance session code
    
    Format: XXYYZZZZZZ
    - XX: Class ID (2 digits)
    - YY: Section ID (2 digits)
    - ZZZZZZ: Random alphanumeric (6 chars)
    
    Args:
        class_id: Class identifier
        section_id: Section identifier
        teacher_id: Teacher identifier (used for randomization)
    
    Returns:
        10-character unique code
    """
    # Encode class and section (2 digits each, padded)
    class_part = str(class_id).zfill(2)[-2:]
    section_part = str(section_id).zfill(2)[-2:]
    
    # Generate random part with timestamp-based seed
    timestamp = int(datetime.utcnow().timestamp() * 1000)
    seed = f"{timestamp}{teacher_id}{class_id}{section_id}"
    random.seed(seed)
    
    # Use uppercase letters and digits
    chars = string.ascii_uppercase + string.digits
    random_part = ''.join(random.choice(chars) for _ in range(6))
    
    # Combine parts
    unique_code = f"{class_part}{section_part}{random_part}"
    
    return unique_code

def generate_collision_free_code() -> str:
    """
    Generate a completely random 10-character code (fallback method)
    Uses cryptographic randomness for collision-free generation
    
    Returns:
        10-character unique code
    """
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(10))

def is_code_expired(expires_at: datetime) -> bool:
    """Check if attendance session code has expired"""
    return datetime.utcnow() > expires_at

def calculate_expiry_time(duration_minutes: int) -> datetime:
    """Calculate expiry time from current time"""
    return datetime.utcnow() + timedelta(minutes=duration_minutes)

def get_remaining_minutes(expires_at: datetime) -> int:
    """Get remaining minutes until expiry"""
    now = datetime.utcnow()
    if now >= expires_at:
        return 0
    delta = expires_at - now
    return int(delta.total_seconds() / 60)

# ============================================
# Validation Helpers
# ============================================

def validate_roll_number(roll_no: str) -> str:
    """Validate and normalize roll number"""
    if not roll_no or len(roll_no.strip()) == 0:
        raise ValueError("Roll number cannot be empty")
    
    normalized = roll_no.strip().upper()
    
    # Check for valid characters (alphanumeric + hyphen/underscore)
    if not all(c.isalnum() or c in '-_' for c in normalized):
        raise ValueError("Roll number contains invalid characters")
    
    return normalized

def validate_unique_code_format(code: str) -> bool:
    """Validate unique code format"""
    if not code or len(code) != 10:
        return False
    
    # Check if all characters are alphanumeric
    return code.isalnum() and code.isupper()

# ============================================
# Time Helpers
# ============================================

def format_duration(minutes: int) -> str:
    """Format duration in human-readable form"""
    if minutes < 60:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    
    hours = minutes // 60
    remaining_minutes = minutes % 60
    
    if remaining_minutes == 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    
    return f"{hours} hour{'s' if hours != 1 else ''} {remaining_minutes} minute{'s' if remaining_minutes != 1 else ''}"

def get_current_academic_year() -> int:
    """Get current academic year"""
    now = datetime.utcnow()
    # Academic year typically starts in August
    if now.month >= 8:
        return now.year
    else:
        return now.year - 1

# ============================================
# Data Formatting Helpers
# ============================================

def format_student_info(student) -> dict:
    """Format student information for API response"""
    return {
        "roll_no": student.roll_no,
        "name": student.name,
        "email": student.email,
        "phone_number": student.phone_number,
        "semester": student.semester,
        "year": student.year,
        "face_enrolled": student.face_enrolled
    }

def format_session_info(session) -> dict:
    """Format session information for API response"""
    return {
        "session_id": session.session_id,
        "unique_code": session.unique_code,
        "class_id": session.class_id,
        "section_id": session.section_id,
        "course_code": session.course_code,
        "created_at": session.created_at,
        "expires_at": session.expires_at,
        "is_active": session.is_active,
        "expires_in_minutes": get_remaining_minutes(session.expires_at)
    }