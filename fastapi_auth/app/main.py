from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional, List
import secrets
import string

# Local imports
from . import models, schemas, utils, auth
from .database import Base, engine, get_db
from .config import ACCESS_TOKEN_EXPIRE_MINUTES, UserRole

security = HTTPBearer()

app = FastAPI(
    title="School Management & Attendance System",
    version="3.0.0",
    description="Complete role-based system with CRUD operations and attendance"
)

@app.on_event("startup")
def startup():
    """Create all database tables on startup."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

@app.get("/", summary="API root")
def root():
    return {
        "message": "🚀 School Management System v3.0 - Complete Implementation",
        "features": {
            "authentication": "JWT-based with role-based access",
            "schools": "CRUD operations",
            "departments": "CRUD operations",
            "classes": "CRUD operations",
            "subjects": "CRUD operations",
            "teachers": "Full management with email notifications",
            "students": "Full management with photo verification",
            "attendance": "Register creation and logging system"
        }
    }


# ============================================
# AUTHENTICATION ENDPOINTS
# ============================================
@app.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email and password."""
    
    if auth.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    hashed_password = utils.get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        role=UserRole.TEACHER,
        name=user_data.email.split('@')[0]
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Database error: {str(e)}"
        )
    
    return new_user


@app.post(
    "/login",
    response_model=schemas.Token,
    summary="Login with email and password"
)
def login(user_credentials: schemas.UserCreate, db: Session = Depends(get_db)):
    """Login with JSON body containing email and password."""
    user = auth.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@app.get(
    "/users/me",
    response_model=schemas.UserResponse,
    summary="Get current user"
)
async def read_users_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get current user info using Bearer token."""
    token = credentials.credentials
    user = await auth.get_current_user_simple(token, db)
    return user


# ============================================
# SCHOOL MANAGEMENT (Admin Only)
# ============================================
@app.post(
    "/schools",
    response_model=schemas.SchoolResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new school (Admin only)"
)
async def create_school(
    school_data: schemas.SchoolCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a new school."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    existing = db.query(models.School).filter(
        models.School.school_name == school_data.school_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="School already exists"
        )
    
    new_school = models.School(
        school_name=school_data.school_name,
        school_dean=school_data.school_dean
    )
    
    db.add(new_school)
    db.commit()
    db.refresh(new_school)
    
    return new_school


@app.get(
    "/schools",
    response_model=List[schemas.SchoolResponse],
    summary="Get all schools"
)
async def get_schools(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100
):
    """Get list of all schools."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    schools = db.query(models.School).offset(skip).limit(limit).all()
    return schools


@app.get(
    "/schools/{school_id}",
    response_model=schemas.SchoolResponse,
    summary="Get school by ID"
)
async def get_school(
    school_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a specific school by ID."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    school = db.query(models.School).filter(
        models.School.school_id == school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    return school


@app.put(
    "/schools/{school_id}",
    response_model=schemas.SchoolResponse,
    summary="Update school (Admin only)"
)
async def update_school(
    school_id: int,
    school_data: schemas.SchoolUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update school details."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    school = db.query(models.School).filter(
        models.School.school_id == school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    if school_data.school_name:
        school.school_name = school_data.school_name
    if school_data.school_dean:
        school.school_dean = school_data.school_dean
    
    db.commit()
    db.refresh(school)
    
    return school


@app.delete(
    "/schools/{school_id}",
    summary="Delete school (Admin only)"
)
async def delete_school(
    school_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a school (cascades to all related data)."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    school = db.query(models.School).filter(
        models.School.school_id == school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    db.delete(school)
    db.commit()
    
    return {"message": f"School {school_id} deleted successfully"}


# ============================================
# DEPARTMENT MANAGEMENT (Admin/School)
# ============================================
@app.post(
    "/departments",
    response_model=schemas.DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new department"
)
async def create_department(
    dept_data: schemas.DepartmentCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a new department."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    school = db.query(models.School).filter(
        models.School.school_id == dept_data.school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    new_dept = models.Department(
        department_name=dept_data.department_name,
        school_id=dept_data.school_id,
        hod=dept_data.hod
    )
    
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    
    return new_dept


@app.get(
    "/departments",
    response_model=List[schemas.DepartmentResponse],
    summary="Get all departments"
)
async def get_departments(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    school_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get list of departments, optionally filtered by school."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    query = db.query(models.Department)
    
    if school_id:
        query = query.filter(models.Department.school_id == school_id)
    
    departments = query.offset(skip).limit(limit).all()
    return departments


@app.get(
    "/departments/{department_id}",
    response_model=schemas.DepartmentResponse,
    summary="Get department by ID"
)
async def get_department(
    department_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a specific department by ID."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    dept = db.query(models.Department).filter(
        models.Department.department_id == department_id
    ).first()
    
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    return dept


@app.put(
    "/departments/{department_id}",
    response_model=schemas.DepartmentResponse,
    summary="Update department"
)
async def update_department(
    department_id: int,
    dept_data: schemas.DepartmentUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update department details."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    dept = db.query(models.Department).filter(
        models.Department.department_id == department_id
    ).first()
    
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    if dept_data.department_name:
        dept.department_name = dept_data.department_name
    if dept_data.hod:
        dept.hod = dept_data.hod
    
    db.commit()
    db.refresh(dept)
    
    return dept


@app.delete(
    "/departments/{department_id}",
    summary="Delete department"
)
async def delete_department(
    department_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a department."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    dept = db.query(models.Department).filter(
        models.Department.department_id == department_id
    ).first()
    
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    db.delete(dept)
    db.commit()
    
    return {"message": f"Department {department_id} deleted successfully"}


# ============================================
# CLASS MANAGEMENT (Admin/School)
# ============================================
@app.post(
    "/classes",
    response_model=schemas.ClassResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new class"
)
async def create_class(
    class_data: schemas.ClassCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a new class."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    dept = db.query(models.Department).filter(
        models.Department.department_id == class_data.department_id
    ).first()
    
    if not dept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    new_class = models.Class(
        class_name=class_data.class_name,
        department_id=class_data.department_id
    )
    
    db.add(new_class)
    db.commit()
    db.refresh(new_class)
    
    return new_class


@app.get(
    "/classes",
    response_model=List[schemas.ClassResponse],
    summary="Get all classes"
)
async def get_classes(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    department_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get list of classes, optionally filtered by department."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    query = db.query(models.Class)
    
    if department_id:
        query = query.filter(models.Class.department_id == department_id)
    
    classes = query.offset(skip).limit(limit).all()
    return classes


@app.get(
    "/classes/{class_id}",
    response_model=schemas.ClassResponse,
    summary="Get class by ID"
)
async def get_class(
    class_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a specific class by ID."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    class_obj = db.query(models.Class).filter(
        models.Class.class_id == class_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    return class_obj


@app.put(
    "/classes/{class_id}",
    response_model=schemas.ClassResponse,
    summary="Update class"
)
async def update_class(
    class_id: int,
    class_data: schemas.ClassUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update class details."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    class_obj = db.query(models.Class).filter(
        models.Class.class_id == class_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    if class_data.class_name:
        class_obj.class_name = class_data.class_name
    
    db.commit()
    db.refresh(class_obj)
    
    return class_obj


@app.delete(
    "/classes/{class_id}",
    summary="Delete class"
)
async def delete_class(
    class_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a class."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    class_obj = db.query(models.Class).filter(
        models.Class.class_id == class_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    db.delete(class_obj)
    db.commit()
    
    return {"message": f"Class {class_id} deleted successfully"}


# ============================================
# SUBJECT MANAGEMENT (Admin/School)
# ============================================
@app.post(
    "/subjects",
    response_model=schemas.SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new subject"
)
async def create_subject(
    subject_data: schemas.SubjectCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a new subject."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    # Check if course code exists
    existing = db.query(models.Subject).filter(
        models.Subject.course_code == subject_data.course_code
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Course code already exists"
        )
    
    # Verify school and class exist
    school = db.query(models.School).filter(
        models.School.school_id == subject_data.school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    class_obj = db.query(models.Class).filter(
        models.Class.class_id == subject_data.class_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    new_subject = models.Subject(
        course_code=subject_data.course_code,
        subject_name=subject_data.subject_name,
        school_id=subject_data.school_id,
        semester=subject_data.semester,
        class_id=subject_data.class_id
    )
    
    db.add(new_subject)
    db.commit()
    db.refresh(new_subject)
    
    return new_subject


@app.get(
    "/subjects",
    response_model=List[schemas.SubjectResponse],
    summary="Get all subjects"
)
async def get_subjects(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    school_id: Optional[int] = None,
    class_id: Optional[int] = None,
    semester: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get list of subjects with optional filters."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    query = db.query(models.Subject)
    
    if school_id:
        query = query.filter(models.Subject.school_id == school_id)
    if class_id:
        query = query.filter(models.Subject.class_id == class_id)
    if semester:
        query = query.filter(models.Subject.semester == semester)
    
    subjects = query.offset(skip).limit(limit).all()
    return subjects


@app.get(
    "/subjects/{course_code}",
    response_model=schemas.SubjectResponse,
    summary="Get subject by course code"
)
async def get_subject(
    course_code: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a specific subject by course code."""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    subject = db.query(models.Subject).filter(
        models.Subject.course_code == course_code
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    return subject


@app.put(
    "/subjects/{course_code}",
    response_model=schemas.SubjectResponse,
    summary="Update subject"
)
async def update_subject(
    course_code: str,
    subject_data: schemas.SubjectUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update subject details."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    subject = db.query(models.Subject).filter(
        models.Subject.course_code == course_code
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    if subject_data.subject_name:
        subject.subject_name = subject_data.subject_name
    if subject_data.semester:
        subject.semester = subject_data.semester
    
    db.commit()
    db.refresh(subject)
    
    return subject


@app.delete(
    "/subjects/{course_code}",
    summary="Delete subject"
)
async def delete_subject(
    course_code: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a subject."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    subject = db.query(models.Subject).filter(
        models.Subject.course_code == course_code
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    db.delete(subject)
    db.commit()
    
    return {"message": f"Subject {course_code} deleted successfully"}


# ============================================
# TEACHER MANAGEMENT (Admin/School)
# ============================================
@app.post(
    "/teachers",
    response_model=schemas.TeacherResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new teacher"
)
async def add_teacher(
    teacher_data: schemas.TeacherCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Add a new teacher to the system."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    if auth.get_user_by_email(db, teacher_data.teacher_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    school = db.query(models.School).filter(
        models.School.school_id == teacher_data.school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    plain_password = utils.generate_teacher_password(
        teacher_data.teacher_name,
        teacher_data.school_id
    )
    hashed_password = utils.get_password_hash(plain_password)
    
    new_user = models.User(
        email=teacher_data.teacher_email,
        password_hash=hashed_password,
        role=UserRole.TEACHER,
        name=teacher_data.teacher_name,
        phone_number=teacher_data.phone_number
    )
    
    try:
        db.add(new_user)
        db.flush()
        
        new_teacher = models.TeacherProfile(
            user_id=new_user.user_id,
            school_id=teacher_data.school_id,
            teacher_name=teacher_data.teacher_name,
            teacher_email=teacher_data.teacher_email,
            phone_number=teacher_data.phone_number
        )
        db.add(new_teacher)
        
        activity = models.SchoolActivity(
            activity_name=models.ActivityType.add_teacher,
            user_id=current_user.user_id
        )
        db.add(activity)
        
        db.commit()
        db.refresh(new_teacher)
        
        email_sent = utils.send_teacher_credentials_email(
            teacher_email=teacher_data.teacher_email,
            teacher_name=teacher_data.teacher_name,
            plain_password=plain_password,
            school_name=school.school_name
        )
        
        return {
            "teacher_id": new_teacher.teacher_id,
            "user_id": new_teacher.user_id,
            "school_id": new_teacher.school_id,
            "teacher_name": new_teacher.teacher_name,
            "teacher_email": new_teacher.teacher_email,
            "message": "Teacher added successfully. Credentials sent to email." if email_sent 
                      else "Teacher added but email delivery failed."
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create teacher: {str(e)}"
        )


@app.get(
    "/teachers",
    response_model=List[schemas.TeacherListResponse],
    summary="Get all teachers"
)
async def get_teachers(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    school_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get list of all teachers."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    query = db.query(models.TeacherProfile)
    
    if school_id:
        query = query.filter(models.TeacherProfile.school_id == school_id)
    
    teachers = query.offset(skip).limit(limit).all()
    return teachers


@app.get(
    "/teachers/{teacher_id}",
    response_model=schemas.TeacherListResponse,
    summary="Get teacher by ID"
)
async def get_teacher(
    teacher_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a specific teacher by ID."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    teacher = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.teacher_id == teacher_id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    return teacher


@app.put(
    "/teachers/{teacher_id}",
    response_model=schemas.TeacherListResponse,
    summary="Update teacher"
)
async def update_teacher(
    teacher_id: int,
    teacher_data: schemas.TeacherUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update teacher details."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    teacher = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.teacher_id == teacher_id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    if teacher_data.teacher_name:
        teacher.teacher_name = teacher_data.teacher_name
        # Update user name as well
        user = db.query(models.User).filter(
            models.User.user_id == teacher.user_id
        ).first()
        if user:
            user.name = teacher_data.teacher_name
    
    if teacher_data.phone_number:
        teacher.phone_number = teacher_data.phone_number
    
    activity = models.SchoolActivity(
        activity_name=models.ActivityType.update_teacher,
        user_id=current_user.user_id
    )
    db.add(activity)
    
    db.commit()
    db.refresh(teacher)
    
    return teacher


@app.delete(
    "/teachers/{teacher_id}",
    summary="Delete teacher"
)
async def delete_teacher(
    teacher_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a teacher."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    teacher = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.teacher_id == teacher_id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher not found"
        )
    
    user_id = teacher.user_id
    
    # Delete teacher profile (cascades to attendance registers)
    db.delete(teacher)
    
    # Delete user account
    user = db.query(models.User).filter(models.User.user_id == user_id).first()
    if user:
        db.delete(user)
    
    activity = models.SchoolActivity(
        activity_name=models.ActivityType.remove_teacher,
        user_id=current_user.user_id
    )
    db.add(activity)
    
    db.commit()
    
    return {"message": f"Teacher {teacher_id} deleted successfully"}


# ============================================
# STUDENT MANAGEMENT (Admin/School)
# ============================================
@app.post(
    "/students",
    response_model=schemas.StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a new student"
)
async def add_student(
    student_data: schemas.StudentCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Add a new student to the system with photo verification."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    existing_student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == student_data.roll_no
    ).first()
    
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with roll number {student_data.roll_no} already exists"
        )
    
    if student_data.email:
        existing_email = db.query(models.StudentProfile).filter(
            models.StudentProfile.email == student_data.email
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    school = db.query(models.School).filter(
        models.School.school_id == student_data.school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="School not found"
        )
    
    department = db.query(models.Department).filter(
        models.Department.department_id == student_data.department_id
    ).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found"
        )
    
    new_student = models.StudentProfile(
        roll_no=student_data.roll_no,
        name=student_data.name,
        email=student_data.email,
        phone_number=student_data.phone_number,
        semester=student_data.semester,
        year=student_data.year,
        school_id=student_data.school_id,
        department_id=student_data.department_id
    )
    
    try:
        db.add(new_student)
        db.flush()
        
        photo_metadata = {
            "roll_no": student_data.roll_no,
            "name": student_data.name,
            "email": student_data.email,
            "school_id": student_data.school_id,
            "department_id": student_data.department_id
        }
        
        vector_db_success = await utils.store_student_photo_in_vector_db(
            roll_no=student_data.roll_no,
            photo_base64=student_data.photo_base64,
            metadata=photo_metadata
        )
        
        if not vector_db_success:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to store photo in vector database"
            )
        
        activity = models.SchoolActivity(
            activity_name=models.ActivityType.add_student,
            user_id=current_user.user_id,
            roll_no=student_data.roll_no
        )
        db.add(activity)
        
        db.commit()
        db.refresh(new_student)
        
        return {
            "roll_no": new_student.roll_no,
            "name": new_student.name,
            "email": new_student.email,
            "semester": new_student.semester,
            "year": new_student.year,
            "school_id": new_student.school_id,
            "department_id": new_student.department_id,
            "created_at": new_student.created_at,
            "message": "Student added successfully and photo verified in vector database."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create student: {str(e)}"
        )


@app.get(
    "/students",
    response_model=List[schemas.StudentListResponse],
    summary="Get all students"
)
async def get_students(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    school_id: Optional[int] = None,
    department_id: Optional[int] = None,
    semester: Optional[int] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get list of all students with optional filters."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    query = db.query(models.StudentProfile)
    
    if school_id:
        query = query.filter(models.StudentProfile.school_id == school_id)
    if department_id:
        query = query.filter(models.StudentProfile.department_id == department_id)
    if semester:
        query = query.filter(models.StudentProfile.semester == semester)
    
    students = query.offset(skip).limit(limit).all()
    return students


@app.get(
    "/students/{roll_no}",
    response_model=schemas.StudentListResponse,
    summary="Get student by roll number"
)
async def get_student(
    roll_no: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get a specific student by roll number."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    return student


@app.put(
    "/students/{roll_no}",
    response_model=schemas.StudentListResponse,
    summary="Update student"
)
async def update_student(
    roll_no: str,
    student_data: schemas.StudentUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update student details."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    if student_data.name:
        student.name = student_data.name
    if student_data.email:
        student.email = student_data.email
    if student_data.phone_number:
        student.phone_number = student_data.phone_number
    if student_data.semester:
        student.semester = student_data.semester
    if student_data.year:
        student.year = student_data.year
    
    activity = models.SchoolActivity(
        activity_name=models.ActivityType.update_student,
        user_id=current_user.user_id,
        roll_no=roll_no
    )
    db.add(activity)
    
    db.commit()
    db.refresh(student)
    
    return student


@app.delete(
    "/students/{roll_no}",
    summary="Delete student"
)
async def delete_student(
    roll_no: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete a student."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or School role required"
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    db.delete(student)
    
    activity = models.SchoolActivity(
        activity_name=models.ActivityType.remove_student,
        user_id=current_user.user_id,
        roll_no=roll_no
    )
    db.add(activity)
    
    db.commit()
    
    return {"message": f"Student {roll_no} deleted successfully"}


# ============================================
# ATTENDANCE REGISTER (Teacher)
# ============================================
@app.post(
    "/attendance/register",
    response_model=schemas.AttendanceRegisterResponse,
    summary="Create attendance register (Teacher)"
)
async def create_attendance_register(
    register_data: schemas.AttendanceRegisterCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Create a new attendance register with unique code."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role required"
        )
    
    teacher = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.user_id == current_user.user_id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Verify subject exists
    subject = db.query(models.Subject).filter(
        models.Subject.course_code == register_data.course_code
    ).first()
    
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    
    # Verify class exists
    class_obj = db.query(models.Class).filter(
        models.Class.class_id == register_data.class_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found"
        )
    
    # Generate unique 6-character code
    unique_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
    while db.query(models.AttendanceRegister).filter(
        models.AttendanceRegister.unique_code == unique_code
    ).first():
        unique_code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
    
    new_register = models.AttendanceRegister(
        unique_code=unique_code,
        user_id=current_user.user_id,
        course_code=register_data.course_code,
        class_id=register_data.class_id,
        teacher_id=teacher.teacher_id
    )
    
    db.add(new_register)
    db.commit()
    db.refresh(new_register)
    
    return {
        "unique_code": unique_code,
        "course_code": register_data.course_code,
        "class_id": register_data.class_id,
        "teacher_id": teacher.teacher_id,
        "created_at": new_register.created_at,
        "message": "Attendance register created successfully"
    }


@app.get(
    "/attendance/registers",
    response_model=List[schemas.AttendanceRegisterListResponse],
    summary="Get attendance registers (Teacher)"
)
async def get_attendance_registers(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    course_code: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get list of attendance registers created by the teacher."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role required"
        )
    
    query = db.query(models.AttendanceRegister).filter(
        models.AttendanceRegister.user_id == current_user.user_id
    )
    
    if course_code:
        query = query.filter(models.AttendanceRegister.course_code == course_code)
    
    registers = query.order_by(
        models.AttendanceRegister.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return registers


@app.get(
    "/attendance/register/{unique_code}",
    response_model=schemas.AttendanceRegisterDetailResponse,
    summary="Get attendance register details"
)
async def get_attendance_register(
    unique_code: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get details of a specific attendance register including all logs."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role required"
        )
    
    register = db.query(models.AttendanceRegister).filter(
        models.AttendanceRegister.unique_code == unique_code,
        models.AttendanceRegister.user_id == current_user.user_id
    ).first()
    
    if not register:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance register not found"
        )
    
    # Get all attendance logs for this register
    logs = db.query(models.AttendanceLog).filter(
        models.AttendanceLog.unique_code == unique_code
    ).all()
    
    return {
        "unique_code": register.unique_code,
        "course_code": register.course_code,
        "class_id": register.class_id,
        "teacher_id": register.teacher_id,
        "created_at": register.created_at,
        "total_attendance": len(logs),
        "attendance_logs": logs
    }


# ============================================
# ATTENDANCE LOGGING (Students)
# ============================================
@app.post(
    "/attendance/mark",
    response_model=schemas.AttendanceLogResponse,
    summary="Mark attendance (Student)"
)
async def mark_attendance(
    attendance_data: schemas.AttendanceMarkCreate,
    db: Session = Depends(get_db)
):
    """Mark student attendance (manual or photo-based)."""
    
    register = db.query(models.AttendanceRegister).filter(
        models.AttendanceRegister.unique_code == attendance_data.unique_code
    ).first()
    
    if not register:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid attendance code"
        )
    
    # Verify student exists
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == attendance_data.roll_no
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    existing = db.query(models.AttendanceLog).filter(
        models.AttendanceLog.unique_code == attendance_data.unique_code,
        models.AttendanceLog.roll_no == attendance_data.roll_no
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already marked for this student"
        )
    
    is_manual = attendance_data.photo_base64 is None
    is_proxy = False
    
    # If photo provided, verify with vector DB
    if attendance_data.photo_base64:
        verification = await utils.verify_student_photo(
            attendance_data.roll_no, 
            attendance_data.photo_base64
        )
        if not verification['verified'] or verification['confidence'] < 0.85:
            is_proxy = True
    
    new_log = models.AttendanceLog(
        unique_code=attendance_data.unique_code,
        roll_no=attendance_data.roll_no,
        is_manual=is_manual,
        is_proxy=is_proxy
    )
    
    db.add(new_log)
    db.commit()
    db.refresh(new_log)
    
    return {
        "attendance_id": new_log.attendance_id,
        "unique_code": new_log.unique_code,
        "roll_no": new_log.roll_no,
        "is_manual": new_log.is_manual,
        "is_proxy": new_log.is_proxy,
        "created_at": new_log.created_at,
        "message": "Attendance marked successfully" if not is_proxy else "Warning: Possible proxy detected"
    }


@app.get(
    "/attendance/logs",
    response_model=List[schemas.AttendanceLogListResponse],
    summary="Get attendance logs"
)
async def get_attendance_logs(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    unique_code: Optional[str] = None,
    roll_no: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    """Get attendance logs with optional filters."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(models.AttendanceLog)
    
    if unique_code:
        query = query.filter(models.AttendanceLog.unique_code == unique_code)
    if roll_no:
        query = query.filter(models.AttendanceLog.roll_no == roll_no)
    
    logs = query.order_by(
        models.AttendanceLog.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    return logs


@app.put(
    "/attendance/logs/{attendance_id}",
    summary="Update attendance log (Teacher)"
)
async def update_attendance_log(
    attendance_id: int,
    is_rejected: Optional[bool] = None,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update attendance log - mark as rejected if proxy detected."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.TEACHER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher role required"
        )
    
    log = db.query(models.AttendanceLog).filter(
        models.AttendanceLog.attendance_id == attendance_id
    ).first()
    
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance log not found"
        )
    
    if is_rejected is not None:
        log.is_rejected = is_rejected
    
    db.commit()
    db.refresh(log)
    
    return {"message": "Attendance log updated successfully", "attendance_log": log}


# ============================================
# ACTIVITY LOGS (Admin)
# ============================================
@app.get(
    "/activities",
    summary="Get activity logs (Admin only)"
)
async def get_activities(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 50
):
    """Get activity logs - audit trail of all actions."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin role required"
        )
    
    activities = db.query(models.SchoolActivity)\
        .order_by(models.SchoolActivity.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()
    
    return activities


# ============================================
# REPORTS & ANALYTICS
# ============================================
@app.get(
    "/reports/attendance-summary",
    summary="Get attendance summary report"
)
async def get_attendance_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
    course_code: Optional[str] = None,
    roll_no: Optional[str] = None
):
    """Get attendance summary statistics."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    query = db.query(models.AttendanceLog)
    
    if course_code:
        # Filter by course through attendance_register
        query = query.join(models.AttendanceRegister).filter(
            models.AttendanceRegister.course_code == course_code
        )
    
    if roll_no:
        query = query.filter(models.AttendanceLog.roll_no == roll_no)
    
    total_logs = query.count()
    manual_logs = query.filter(models.AttendanceLog.is_manual == True).count()
    photo_logs = query.filter(models.AttendanceLog.is_manual == False).count()
    proxy_logs = query.filter(models.AttendanceLog.is_proxy == True).count()
    rejected_logs = query.filter(models.AttendanceLog.is_rejected == True).count()
    
    return {
        "total_attendance": total_logs,
        "manual_attendance": manual_logs,
        "photo_attendance": photo_logs,
        "proxy_detected": proxy_logs,
        "rejected_attendance": rejected_logs,
        "course_code": course_code,
        "roll_no": roll_no
    }


@app.get(
    "/reports/student-attendance/{roll_no}",
    summary="Get student attendance report"
)
async def get_student_attendance_report(
    roll_no: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get detailed attendance report for a specific student."""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [UserRole.ADMIN, UserRole.SCHOOL, UserRole.TEACHER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    logs = db.query(models.AttendanceLog).filter(
        models.AttendanceLog.roll_no == roll_no
    ).all()
    
    return {
        "student_info": {
            "roll_no": student.roll_no,
            "name": student.name,
            "email": student.email,
            "semester": student.semester,
            "year": student.year
        },
        "total_attendance": len(logs),
        "manual_attendance": sum(1 for log in logs if log.is_manual),
        "photo_attendance": sum(1 for log in logs if not log.is_manual),
        "proxy_detected": sum(1 for log in logs if log.is_proxy),
        "rejected": sum(1 for log in logs if log.is_rejected),
        "attendance_logs": logs
    }


# ============================================
# HEALTH CHECK
# ============================================
@app.get("/health", summary="Health check")
def health_check():
    return {
        "status": "healthy",
        "service": "School Management & Attendance System",
        "version": "3.0.0",
        "features": [
            "Authentication & Authorization",
            "School Management",
            "Department Management",
            "Class Management",
            "Subject Management",
            "Teacher Management",
            "Student Management",
            "Attendance System",
            "Reports & Analytics"
        ]
    }