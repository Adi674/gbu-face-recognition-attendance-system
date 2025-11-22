from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import uuid

# Local imports
from . import models, schemas, utils, auth
from .database import Base, engine, get_db
from .config import ACCESS_TOKEN_EXPIRE_MINUTES

security = HTTPBearer()

app = FastAPI(
    title="School Management System",
    version="2.0.0",
    description="Simplified system with only Add Teacher and Add Student endpoints"
)

@app.on_event("startup")
def startup():
    """Create all database tables on startup."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

@app.get("/", summary="API root")
def root():
    return {
        "message": "🚀 School Management System is running!",
        "endpoints": {
            "add_teacher": "POST /add-teacher (Bearer token required)",
            "add_student": "POST /add-student (Bearer token required)"
        }
    }

@app.post(
    "/add-teacher",
    response_model=schemas.TeacherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new teacher with user account"
)
async def add_teacher(
    teacher_data: schemas.TeacherCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Add a new teacher to the system.
    This endpoint:
    1. Creates a user account (email + password)
    2. Creates a teacher profile linked to the user
    3. Logs the activity
    
    Requires: Bearer token authentication (admin or school role)
    """
    # Verify current user
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    # Check if user has permission (admin=1 or school=2)
    if current_user.role not in [1, 2]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or school users can add teachers"
        )
    
    # Check if email already exists
    existing_user = auth.get_user_by_email(db, teacher_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if school exists
    school = db.query(models.School).filter(models.School.school_id == teacher_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with ID {teacher_data.school_id} not found"
        )
    
    try:
        # 1. Create user account
        hashed_password = utils.get_password_hash(teacher_data.password)
        new_user = models.User(
            email=teacher_data.email,
            password_hash=hashed_password,
            role=3,  # Teacher role
            name=teacher_data.name,
            phone_number=teacher_data.phone_number
        )
        db.add(new_user)
        db.flush()  # Get user_id without committing
        
        # 2. Create teacher profile
        new_teacher = models.TeacherProfile(
            user_id=new_user.user_id,
            school_id=teacher_data.school_id,
            teacher_name=teacher_data.name,
            teacher_email=teacher_data.email
        )
        db.add(new_teacher)
        db.flush()  # Get teacher_id
        
        # 3. Log activity
        activity = models.SchoolActivity(
            activity_name=models.ActivityType.add_teacher,
            user_id=current_user.user_id
        )
        db.add(activity)
        
        db.commit()
        db.refresh(new_teacher)
        
        return {
            "teacher_id": new_teacher.teacher_id,
            "user_id": new_user.user_id,
            "name": new_teacher.teacher_name,
            "email": new_teacher.teacher_email,
            "school_id": new_teacher.school_id,
            "phone_number": new_user.phone_number,
            "message": "Teacher added successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding teacher: {str(e)}"
        )

@app.post(
    "/add-student",
    response_model=schemas.StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new student"
)
async def add_student(
    student_data: schemas.StudentCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Add a new student to the system.
    This endpoint:
    1. Creates a student profile
    2. Logs the activity
    
    Requires: Bearer token authentication (admin, school, or teacher role)
    """
    # Verify current user
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    # All authenticated users can add students
    if current_user.role not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid user role"
        )
    
    # Check if roll number already exists
    existing_student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == student_data.roll_no
    ).first()
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with roll number {student_data.roll_no} already exists"
        )
    
    # Check if email already exists (if provided)
    if student_data.email:
        existing_email = db.query(models.StudentProfile).filter(
            models.StudentProfile.email == student_data.email
        ).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {student_data.email} already registered"
            )
    
    # Verify school exists
    school = db.query(models.School).filter(models.School.school_id == student_data.school_id).first()
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with ID {student_data.school_id} not found"
        )
    
    # Verify department exists
    department = db.query(models.Department).filter(
        models.Department.department_id == student_data.department_id
    ).first()
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {student_data.department_id} not found"
        )
    
    # Validate semester
    if student_data.semester < 1 or student_data.semester > 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Semester must be between 1 and 8"
        )
    
    try:
        # 1. Create student profile
        new_student = models.StudentProfile(
            roll_no=student_data.roll_no,
            name=student_data.name,
            phone_number=student_data.phone_number,
            email=student_data.email,
            semester=student_data.semester,
            year=student_data.year,
            school_id=student_data.school_id,
            department_id=student_data.department_id
        )
        db.add(new_student)
        db.flush()
        
        # 2. Log activity
        activity = models.SchoolActivity(
            activity_name=models.ActivityType.add_student,
            user_id=current_user.user_id,
            roll_no=new_student.roll_no
        )
        db.add(activity)
        
        db.commit()
        db.refresh(new_student)
        
        return {
            "roll_no": new_student.roll_no,
            "name": new_student.name,
            "email": new_student.email,
            "phone_number": new_student.phone_number,
            "semester": new_student.semester,
            "year": new_student.year,
            "school_id": new_student.school_id,
            "department_id": new_student.department_id,
            "message": "Student added successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding student: {str(e)}"
        )

@app.get("/health", summary="Health check")
def health_check():
    return {"status": "healthy", "service": "School Management System"}
