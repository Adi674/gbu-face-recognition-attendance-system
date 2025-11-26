from sqlalchemy import Column, Integer, String, SmallInteger, Boolean, TIMESTAMP, Text, ForeignKey, CheckConstraint, Float
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
from .database import Base
import enum

# ============================================
# ENUM Type Definitions
# ============================================

class ActivityType(str, enum.Enum):
    add_student = "add_student"
    add_teacher = "add_teacher"
    remove_teacher = "remove_teacher"
    remove_student = "remove_student"
    update_teacher = "update_teacher"
    update_student = "update_student"

class AttendanceStatus(str, enum.Enum):
    present = "present"
    absent = "absent"
    proxy = "proxy"
    manual = "manual"

# ============================================
# TABLE 1: users (Authentication)
# ============================================
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(SmallInteger, nullable=False)  # 1=admin, 2=school, 3=teacher
    name = Column(String(255), nullable=False)
    phone_number = Column(String(15))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('role IN (1, 2, 3)', name='check_user_role'),
    )
    
    # Relationships
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    attendance_sessions = relationship("AttendanceSession", back_populates="teacher_user")
    school_activities = relationship("SchoolActivity", back_populates="user")
    login_logs = relationship("LoginLog", back_populates="user")

# ============================================
# TABLE 2: school
# ============================================
class School(Base):
    __tablename__ = "school"
    
    school_id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(255), unique=True, nullable=False)
    school_dean = Column(String(255))
    
    # Relationships
    departments = relationship("Department", back_populates="school")
    students = relationship("StudentProfile", back_populates="school")
    teachers = relationship("TeacherProfile", back_populates="school")
    subjects = relationship("Subject", back_populates="school")

# ============================================
# TABLE 3: department
# ============================================
class Department(Base):
    __tablename__ = "department"
    
    department_id = Column(Integer, primary_key=True, autoincrement=True)
    department_name = Column(String(255), nullable=False)
    hod = Column(String(255))
    school_id = Column(Integer, ForeignKey('school.school_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    
    # Relationships
    school = relationship("School", back_populates="departments")
    classes = relationship("Class", back_populates="department")
    students = relationship("StudentProfile", back_populates="department")

# ============================================
# TABLE 4: class (renamed to avoid Python keyword)
# ============================================
class Class(Base):
    __tablename__ = "class"
    
    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey('department.department_id', ondelete='CASCADE'), nullable=False)
    
    # Relationships
    department = relationship("Department", back_populates="classes")
    sections = relationship("Section", back_populates="class_")
    subjects = relationship("Subject", back_populates="class_")

# ============================================
# TABLE 5: section (NEW)
# ============================================
class Section(Base):
    __tablename__ = "section"
    
    section_id = Column(Integer, primary_key=True, autoincrement=True)
    section_name = Column(String(50), nullable=False)  # A, B, C, etc.
    class_id = Column(Integer, ForeignKey('class.class_id', ondelete='CASCADE'), nullable=False)
    total_students = Column(Integer, default=0)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    class_ = relationship("Class", back_populates="sections")
    students = relationship("StudentProfile", back_populates="section")
    attendance_sessions = relationship("AttendanceSession", back_populates="section")

# ============================================
# TABLE 6: subject
# ============================================
class Subject(Base):
    __tablename__ = "subject"
    
    course_code = Column(String(20), primary_key=True)
    subject_name = Column(String(255), nullable=False)
    school_id = Column(Integer, ForeignKey('school.school_id', ondelete='CASCADE'), nullable=False)
    semester = Column(Integer, nullable=False)
    class_id = Column(Integer, ForeignKey('class.class_id', ondelete='CASCADE'), nullable=False)
    
    __table_args__ = (
        CheckConstraint('semester BETWEEN 1 AND 8', name='check_semester_range'),
    )
    
    # Relationships
    school = relationship("School", back_populates="subjects")
    class_ = relationship("Class", back_populates="subjects")
    attendance_sessions = relationship("AttendanceSession", back_populates="subject")

# ============================================
# TABLE 7: student_profile (UPDATED)
# ============================================
class StudentProfile(Base):
    __tablename__ = "student_profile"
    
    roll_no = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(15))
    email = Column(String(255), unique=True)
    semester = Column(Integer)
    year = Column(Integer)
    profile_photo_url = Column(Text)  # NEW: for face recognition
    face_enrolled = Column(Boolean, default=False)  # NEW: face recognition status
    school_id = Column(Integer, ForeignKey('school.school_id', ondelete='CASCADE'), nullable=False)
    department_id = Column(Integer, ForeignKey('department.department_id', ondelete='CASCADE'), nullable=False)
    section_id = Column(Integer, ForeignKey('section.section_id', ondelete='SET NULL'))  # NEW
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        CheckConstraint('semester BETWEEN 1 AND 8', name='check_student_semester'),
    )
    
    # Relationships
    school = relationship("School", back_populates="students")
    department = relationship("Department", back_populates="students")
    section = relationship("Section", back_populates="students")
    attendance_records = relationship("AttendanceRecord", back_populates="student")
    school_activities = relationship("SchoolActivity", back_populates="student")

# ============================================
# TABLE 8: teacher_profile
# ============================================
class TeacherProfile(Base):
    __tablename__ = "teacher_profile"
    
    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), unique=True, nullable=False)
    school_id = Column(Integer, ForeignKey('school.school_id', ondelete='CASCADE'), nullable=False)
    teacher_name = Column(String(255), nullable=False)
    teacher_email = Column(String(255), unique=True)
    
    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    school = relationship("School", back_populates="teachers")
    attendance_sessions = relationship("AttendanceSession", back_populates="teacher")

# ============================================
# TABLE 9: attendance_session (NEW - replaces attendance_register)
# ============================================
class AttendanceSession(Base):
    __tablename__ = "attendance_session"
    
    session_id = Column(Integer, primary_key=True, autoincrement=True)
    unique_code = Column(String(10), unique=True, nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey('teacher_profile.teacher_id', ondelete='CASCADE'), nullable=False)
    teacher_user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('class.class_id', ondelete='CASCADE'), nullable=False)
    section_id = Column(Integer, ForeignKey('section.section_id', ondelete='CASCADE'), nullable=False)
    course_code = Column(String(20), ForeignKey('subject.course_code', ondelete='CASCADE'))
    
    # Time management
    created_at = Column(TIMESTAMP, default=datetime.utcnow, nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    is_active = Column(Boolean, default=True)
    closed_at = Column(TIMESTAMP)
    
    # Stats
    total_present = Column(Integer, default=0)
    total_absent = Column(Integer, default=0)
    total_proxy = Column(Integer, default=0)
    total_manual = Column(Integer, default=0)
    
    # Relationships
    teacher = relationship("TeacherProfile", back_populates="attendance_sessions")
    teacher_user = relationship("User", back_populates="attendance_sessions")
    section = relationship("Section", back_populates="attendance_sessions")
    subject = relationship("Subject", back_populates="attendance_sessions")
    attendance_records = relationship("AttendanceRecord", back_populates="session")
    proxy_records = relationship("ProxyRecord", back_populates="session")

# ============================================
# TABLE 10: attendance_record (UPDATED)
# ============================================
class AttendanceRecord(Base):
    __tablename__ = "attendance_record"
    
    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('attendance_session.session_id', ondelete='CASCADE'), nullable=False)
    roll_no = Column(String(50), ForeignKey('student_profile.roll_no', ondelete='CASCADE'), nullable=False)
    
    # Attendance details
    status = Column(ENUM(AttendanceStatus, name='attendance_status_enum'), default=AttendanceStatus.present)
    is_manual = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    
    # Face recognition details
    face_confidence = Column(Float)  # 0-100
    face_match = Column(Boolean)
    
    # Timestamps
    marked_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    session = relationship("AttendanceSession", back_populates="attendance_records")
    student = relationship("StudentProfile", back_populates="attendance_records")

# ============================================
# TABLE 11: proxy_record (NEW)
# ============================================
class ProxyRecord(Base):
    __tablename__ = "proxy_record"
    
    proxy_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey('attendance_session.session_id', ondelete='CASCADE'), nullable=False)
    roll_no = Column(String(50), ForeignKey('student_profile.roll_no', ondelete='CASCADE'), nullable=False)
    marked_by_teacher_id = Column(Integer, ForeignKey('teacher_profile.teacher_id', ondelete='CASCADE'), nullable=False)
    reason = Column(Text)
    marked_at = Column(TIMESTAMP, default=datetime.utcnow)
    
    # Relationships
    session = relationship("AttendanceSession", back_populates="proxy_records")

# ============================================
# TABLE 12: login_log (NEW)
# ============================================
class LoginLog(Base):
    __tablename__ = "login_log"
    
    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    login_time = Column(TIMESTAMP, default=datetime.utcnow)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User", back_populates="login_logs")

# ============================================
# TABLE 13: school_activity (Audit Log)
# ============================================
class SchoolActivity(Base):
    __tablename__ = "school_activity"
    
    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    activity_name = Column(ENUM(ActivityType, name='activity_type'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    roll_no = Column(String(50), ForeignKey('student_profile.roll_no', ondelete='SET NULL'))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="school_activities")
    student = relationship("StudentProfile", back_populates="school_activities")