from pydantic import BaseModel, EmailStr, ConfigDict, validator, Field
from datetime import datetime
from typing import Optional, List
import uuid

# ============================================
# USER SCHEMAS
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
    phone_number: Optional[str] = None
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None


# ============================================
# SCHOOL SCHEMAS
# ============================================
class SchoolCreate(BaseModel):
    school_name: str = Field(..., min_length=2, max_length=255)
    school_dean: Optional[str] = Field(None, max_length=255)
    
    @validator('school_name')
    def validate_school_name(cls, v):
        if not v.strip():
            raise ValueError('School name cannot be empty')
        return v.strip()

class SchoolUpdate(BaseModel):
    school_name: Optional[str] = Field(None, min_length=2, max_length=255)
    school_dean: Optional[str] = Field(None, max_length=255)

class SchoolResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    school_id: int
    school_name: str
    school_dean: Optional[str] = None


# ============================================
# DEPARTMENT SCHEMAS
# ============================================
class DepartmentCreate(BaseModel):
    department_name: str = Field(..., min_length=2, max_length=255)
    school_id: int = Field(..., gt=0)
    hod: Optional[str] = Field(None, max_length=255)
    
    @validator('department_name')
    def validate_department_name(cls, v):
        if not v.strip():
            raise ValueError('Department name cannot be empty')
        return v.strip()

class DepartmentUpdate(BaseModel):
    department_name: Optional[str] = Field(None, min_length=2, max_length=255)
    hod: Optional[str] = Field(None, max_length=255)

class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    department_id: int
    department_name: str
    hod: Optional[str] = None
    school_id: int


# ============================================
# CLASS SCHEMAS
# ============================================
class ClassCreate(BaseModel):
    class_name: str = Field(..., min_length=1, max_length=255)
    department_id: int = Field(..., gt=0)
    
    @validator('class_name')
    def validate_class_name(cls, v):
        if not v.strip():
            raise ValueError('Class name cannot be empty')
        return v.strip()

class ClassUpdate(BaseModel):
    class_name: Optional[str] = Field(None, min_length=1, max_length=255)

class ClassResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    class_id: int
    class_name: str
    department_id: int


# ============================================
# SUBJECT SCHEMAS
# ============================================
class SubjectCreate(BaseModel):
    course_code: str = Field(..., min_length=1, max_length=20)
    subject_name: str = Field(..., min_length=2, max_length=255)
    school_id: int = Field(..., gt=0)
    semester: int = Field(..., ge=1, le=8)
    class_id: int = Field(..., gt=0)
    
    @validator('course_code', 'subject_name')
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class SubjectUpdate(BaseModel):
    subject_name: Optional[str] = Field(None, min_length=2, max_length=255)
    semester: Optional[int] = Field(None, ge=1, le=8)

class SubjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    course_code: str
    subject_name: str
    school_id: int
    semester: int
    class_id: int


# ============================================
# TEACHER SCHEMAS
# ============================================
class TeacherCreate(BaseModel):
    teacher_name: str = Field(..., min_length=2, max_length=255)
    teacher_email: EmailStr
    school_id: int = Field(..., gt=0)
    phone_number: Optional[str] = Field(None, max_length=15)
    
    @validator('teacher_name')
    def validate_teacher_name(cls, v):
        if not v.strip():
            raise ValueError('Teacher name cannot be empty')
        return v.strip()

class TeacherUpdate(BaseModel):
    teacher_name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=15)

class TeacherResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    teacher_id: int
    user_id: uuid.UUID
    school_id: int
    teacher_name: str
    teacher_email: str
    message: str = "Teacher added successfully. Credentials sent to email."

class TeacherListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    teacher_id: int
    user_id: uuid.UUID
    school_id: int
    teacher_name: str
    teacher_email: str
    phone_number: Optional[str] = None


# ============================================
# STUDENT SCHEMAS
# ============================================
class StudentCreate(BaseModel):
    roll_no: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=15)
    semester: int = Field(..., ge=1, le=8)
    year: int = Field(..., ge=2000, le=2100)
    school_id: int = Field(..., gt=0)
    department_id: int = Field(..., gt=0)
    photo_base64: str = Field(..., description="Base64 encoded student photo for vector DB")
    
    @validator('name', 'roll_no')
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=15)
    semester: Optional[int] = Field(None, ge=1, le=8)
    year: Optional[int] = Field(None, ge=2000, le=2100)

class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    roll_no: str
    name: str
    email: str
    semester: int
    year: int
    school_id: int
    department_id: int
    created_at: datetime
    message: str = "Student added successfully and photo verified in vector database."

class StudentListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    roll_no: str
    name: str
    email: str
    phone_number: Optional[str] = None
    semester: int
    year: int
    school_id: int
    department_id: int
    created_at: datetime


# ============================================
# ATTENDANCE REGISTER SCHEMAS
# ============================================
class AttendanceRegisterCreate(BaseModel):
    course_code: str = Field(..., min_length=1, max_length=20)
    class_id: int = Field(..., gt=0)
    
    @validator('course_code')
    def validate_course_code(cls, v):
        if not v.strip():
            raise ValueError('Course code cannot be empty')
        return v.strip()

class AttendanceRegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    unique_code: str
    course_code: str
    class_id: int
    teacher_id: int
    created_at: datetime
    message: str = "Attendance register created successfully"

class AttendanceRegisterListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    unique_code: str
    course_code: str
    class_id: int
    teacher_id: int
    created_at: datetime

class AttendanceLogListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    attendance_id: int
    roll_no: str
    is_manual: bool
    is_rejected: bool
    is_proxy: bool
    created_at: datetime

class AttendanceRegisterDetailResponse(BaseModel):
    unique_code: str
    course_code: str
    class_id: int
    teacher_id: int
    created_at: datetime
    total_attendance: int
    attendance_logs: List[AttendanceLogListItem]


# ============================================
# ATTENDANCE LOG SCHEMAS
# ============================================
class AttendanceMarkCreate(BaseModel):
    unique_code: str = Field(..., min_length=6, max_length=10)
    roll_no: str = Field(..., min_length=1, max_length=50)
    photo_base64: Optional[str] = Field(None, description="Base64 encoded photo for verification")
    
    @validator('unique_code', 'roll_no')
    def validate_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip().upper()

class AttendanceLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    attendance_id: int
    unique_code: str
    roll_no: str
    is_manual: bool
    is_proxy: bool
    created_at: datetime
    message: str = "Attendance marked successfully"

class AttendanceLogListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    attendance_id: int
    unique_code: str
    roll_no: str
    is_manual: bool
    is_rejected: bool
    is_proxy: bool
    created_at: datetime


# ============================================
# ACTIVITY LOG SCHEMAS
# ============================================
class ActivityLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    activity_id: int
    activity_name: str
    user_id: uuid.UUID
    roll_no: Optional[str] = None
    created_at: datetime
    updated_at: datetime


# ============================================
# REPORT SCHEMAS
# ============================================
class AttendanceSummaryResponse(BaseModel):
    total_attendance: int
    manual_attendance: int
    photo_attendance: int
    proxy_detected: int
    rejected_attendance: int
    course_code: Optional[str] = None
    roll_no: Optional[str] = None

class StudentInfoResponse(BaseModel):
    roll_no: str
    name: str
    email: str
    semester: int
    year: int

class StudentAttendanceReportResponse(BaseModel):
    student_info: StudentInfoResponse
    total_attendance: int
    manual_attendance: int
    photo_attendance: int
    proxy_detected: int
    rejected: int
    attendance_logs: List[AttendanceLogListResponse]