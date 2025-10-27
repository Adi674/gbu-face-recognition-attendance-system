from sqlalchemy import (
    Column, Integer, String, SmallInteger, Boolean,
    TIMESTAMP, Text, ForeignKey, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum
from .database import Base


# ============================================
# ENUM Type Definition
# ============================================
class ActivityType(str, enum.Enum):
    add_student = "add_student"
    add_teacher = "add_teacher"
    remove_teacher = "remove_teacher"
    remove_student = "remove_student"
    update_teacher = "update_teacher"
    update_student = "update_student"


# ============================================
# TABLE 1: users (Authentication)
# ============================================
class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(SmallInteger, nullable=False)  # 1=Admin, 2=School, 3=Teacher
    name = Column(String(255), nullable=False)
    phone_number = Column(String(15))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('role IN (1, 2, 3)', name='check_user_role'),
    )

    # Relationships
    teacher_profile = relationship("TeacherProfile", back_populates="user", uselist=False)
    attendance_registers = relationship("AttendanceRegister", back_populates="user")
    school_activities = relationship("SchoolActivity", back_populates="user")


# ============================================
# TABLE 2: school
# ============================================
class School(Base):
    __tablename__ = "school"

    school_id = Column(Integer, primary_key=True, autoincrement=True)
    school_name = Column(String(255), unique=True, nullable=False)
    school_dean = Column(String(255))

    # Relationships
    departments = relationship("Department", back_populates="school", cascade="all, delete")
    students = relationship("StudentProfile", back_populates="school", cascade="all, delete")
    teachers = relationship("TeacherProfile", back_populates="school", cascade="all, delete")
    subjects = relationship("Subject", back_populates="school", cascade="all, delete")


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
    classes = relationship("Class", back_populates="department", cascade="all, delete")
    students = relationship("StudentProfile", back_populates="department", cascade="all, delete")


# ============================================
# TABLE 4: class
# ============================================
class Class(Base):
    __tablename__ = "class"

    class_id = Column(Integer, primary_key=True, autoincrement=True)
    class_name = Column(String(255), nullable=False)
    department_id = Column(Integer, ForeignKey('department.department_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    # Relationships
    department = relationship("Department", back_populates="classes")
    subjects = relationship("Subject", back_populates="class_", cascade="all, delete")
    attendance_registers = relationship("AttendanceRegister", back_populates="class_", cascade="all, delete")


# ============================================
# TABLE 5: subject
# ============================================
class Subject(Base):
    __tablename__ = "subject"

    course_code = Column(String(20), primary_key=True)
    subject_name = Column(String(255), nullable=False)
    school_id = Column(Integer, ForeignKey('school.school_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    semester = Column(Integer, nullable=False)
    class_id = Column(Integer, ForeignKey('class.class_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)

    __table_args__ = (
        CheckConstraint('semester BETWEEN 1 AND 8', name='check_semester_range'),
    )

    # Relationships
    school = relationship("School", back_populates="subjects")
    class_ = relationship("Class", back_populates="subjects")
    attendance_registers = relationship("AttendanceRegister", back_populates="subject", cascade="all, delete")


# ============================================
# TABLE 6: student_profile
# ============================================
class StudentProfile(Base):
    __tablename__ = "student_profile"

    roll_no = Column(String(50), primary_key=True)
    name = Column(String(255), nullable=False)
    phone_number = Column(String(15))
    email = Column(String(255), unique=True)
    semester = Column(Integer)
    year = Column(Integer)
    school_id = Column(Integer, ForeignKey('school.school_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    department_id = Column(Integer, ForeignKey('department.department_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    __table_args__ = (
        CheckConstraint('semester BETWEEN 1 AND 8', name='check_student_semester'),
    )

    # Relationships
    school = relationship("School", back_populates="students")
    department = relationship("Department", back_populates="students")
    attendance_logs = relationship("AttendanceLog", back_populates="student", cascade="all, delete")
    school_activities = relationship("SchoolActivity", back_populates="student", cascade="all, delete")


# ============================================
# TABLE 7: teacher_profile
# ============================================
class TeacherProfile(Base):
    __tablename__ = "teacher_profile"

    teacher_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), unique=True, nullable=False)
    school_id = Column(Integer, ForeignKey('school.school_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    teacher_name = Column(String(255), nullable=False)
    teacher_email = Column(String(255), unique=True)
    phone_number = Column(String(15))

    # Relationships
    user = relationship("User", back_populates="teacher_profile")
    school = relationship("School", back_populates="teachers")
    attendance_registers = relationship("AttendanceRegister", back_populates="teacher", cascade="all, delete")


# ============================================
# TABLE 8: attendance_register
# ============================================
class AttendanceRegister(Base):
    __tablename__ = "attendance_register"

    unique_code = Column(String(10), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    course_code = Column(String(20), ForeignKey('subject.course_code', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    class_id = Column(Integer, ForeignKey('class.class_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    teacher_id = Column(Integer, ForeignKey('teacher_profile.teacher_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="attendance_registers")
    subject = relationship("Subject", back_populates="attendance_registers")
    class_ = relationship("Class", back_populates="attendance_registers")
    teacher = relationship("TeacherProfile", back_populates="attendance_registers")
    attendance_logs = relationship("AttendanceLog", back_populates="register", cascade="all, delete")


# ============================================
# TABLE 9: attendance_logs
# ============================================
class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    unique_code = Column(String(10), ForeignKey('attendance_register.unique_code', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    roll_no = Column(String(50), ForeignKey('student_profile.roll_no', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    is_manual = Column(Boolean, default=False)
    is_rejected = Column(Boolean, default=False)
    is_proxy = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    register = relationship("AttendanceRegister", back_populates="attendance_logs")
    student = relationship("StudentProfile", back_populates="attendance_logs")


# ============================================
# TABLE 10: school_activity (Audit Log)
# ============================================
class SchoolActivity(Base):
    __tablename__ = "school_activity"

    activity_id = Column(Integer, primary_key=True, autoincrement=True)
    activity_name = Column(ENUM(ActivityType, name='activity_type'), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.user_id', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    roll_no = Column(String(50), ForeignKey('student_profile.roll_no', ondelete='SET NULL', onupdate='CASCADE'))
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="school_activities")
    student = relationship("StudentProfile", back_populates="school_activities")
