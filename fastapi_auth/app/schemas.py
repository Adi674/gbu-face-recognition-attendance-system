from pydantic import BaseModel, EmailStr, ConfigDict, validator, Field
from datetime import datetime
from typing import Optional, List
import uuid

# ============================================
# Authentication Schemas
# ============================================

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: uuid.UUID
    email: str
    name: str
    role: int
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: Optional[dict] = None

# ============================================
# Teacher Schemas
# ============================================

class TeacherCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    phone_number: Optional[str] = None
    school_id: int
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class TeacherResponse(BaseModel):
    teacher_id: int
    user_id: uuid.UUID
    name: str
    email: str
    school_id: int
    phone_number: Optional[str] = None
    message: str

# ============================================
# Student Schemas
# ============================================

class StudentCreate(BaseModel):
    roll_no: str
    name: str
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    semester: int
    year: int
    school_id: int
    department_id: int
    section_id: Optional[int] = None
    profile_photo_url: Optional[str] = None
    
    @validator('semester')
    def validate_semester(cls, v):
        if v < 1 or v > 8:
            raise ValueError('Semester must be between 1 and 8')
        return v
    
    @validator('roll_no')
    def validate_roll_no(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Roll number cannot be empty')
        return v.strip().upper()

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    semester: Optional[int] = None
    year: Optional[int] = None
    section_id: Optional[int] = None
    profile_photo_url: Optional[str] = None

class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    roll_no: str
    name: str
    email: Optional[str]
    phone_number: Optional[str]
    semester: int
    year: int
    school_id: int
    department_id: int
    section_id: Optional[int]
    profile_photo_url: Optional[str]
    face_enrolled: bool
    created_at: datetime

# ============================================
# Section Schemas
# ============================================

class SectionCreate(BaseModel):
    section_name: str
    class_id: int

class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    section_id: int
    section_name: str
    class_id: int
    total_students: int

# ============================================
# Attendance Session Schemas
# ============================================

class AttendanceSessionCreate(BaseModel):
    class_id: int
    section_id: int
    course_code: Optional[str] = None
    duration_minutes: int = Field(default=10, ge=5, le=120)  # 5-120 minutes

class AttendanceSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    session_id: int
    unique_code: str
    class_id: int
    section_id: int
    course_code: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_active: bool
    total_present: int
    total_absent: int
    total_proxy: int
    total_manual: int

# ============================================
# Attendance Marking Schemas
# ============================================

class AttendanceMarkRequest(BaseModel):
    unique_code: str
    roll_no: str

class FaceRecognitionResult(BaseModel):
    roll_no: str
    confidence: float
    matched: bool

class AttendanceMarkResponse(BaseModel):
    success: bool
    message: str
    attendance_id: Optional[int] = None
    student_name: Optional[str] = None
    marked_at: Optional[datetime] = None
    status: Optional[str] = None

# ============================================
# Manual Attendance Schemas
# ============================================

class ManualAttendanceRequest(BaseModel):
    unique_code: str
    roll_no: str
    reason: Optional[str] = "Manual entry by teacher"

# ============================================
# Proxy Attendance Schemas
# ============================================

class ProxyAttendanceRequest(BaseModel):
    unique_code: str
    roll_no: str
    reason: str = "Proxy detected by teacher"

class ProxyAttendanceResponse(BaseModel):
    success: bool
    message: str
    proxy_id: Optional[int] = None
    marked_at: Optional[datetime] = None

# ============================================
# Attendance Check/Dashboard Schemas
# ============================================

class AttendanceCheckRequest(BaseModel):
    unique_code: str

class StudentAttendanceInfo(BaseModel):
    roll_no: str
    name: str
    status: str
    marked_at: Optional[datetime]
    is_manual: bool
    is_proxy: bool
    face_confidence: Optional[float]

class AttendanceCheckResponse(BaseModel):
    session_info: dict
    total_students: int
    present_count: int
    absent_count: int
    proxy_count: int
    manual_count: int
    present_students: List[StudentAttendanceInfo]
    absent_students: List[dict]
    session_active: bool
    expires_in_minutes: Optional[int]

# ============================================
# Attendance Report Schemas
# ============================================

class AttendanceReportRequest(BaseModel):
    unique_code: str

class AttendanceReportResponse(BaseModel):
    session_info: dict
    statistics: dict
    present_students: List[dict]
    absent_students: List[dict]
    proxy_records: List[dict]
    manual_entries: List[dict]
    generated_at: datetime

# ============================================
# Bulk Operations Schemas
# ============================================

class BulkStudentCreate(BaseModel):
    students: List[StudentCreate]

class BulkStudentResponse(BaseModel):
    success_count: int
    failed_count: int
    errors: List[dict]
    created_students: List[str]  # roll numbers

# ============================================
# Error Response Schema
# ============================================

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: datetime
    error_code: Optional[str] = None
