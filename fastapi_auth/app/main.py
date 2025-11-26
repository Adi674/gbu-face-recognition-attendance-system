from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

# Local imports
from . import models, schemas, utils, auth
from .database import Base, engine, get_db
from .config import ACCESS_TOKEN_EXPIRE_MINUTES

# Import all routers
from .routers import teacher, student, attendance, reports

security = HTTPBearer()

app = FastAPI(
    title="Face Recognition Attendance System",
    version="3.0.0",
    description="Complete attendance management system with face recognition"
)

# =====================================================
# STARTUP INITIALIZATION
# =====================================================
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")
    print("✅ All modules loaded!")


# =====================================================
# ROOT ENDPOINT
# =====================================================
@app.get("/", summary="API Root")
def root():
    return {
        "message": "🚀 Face Recognition Attendance System",
        "version": "3.0.0",
        "features": [
            "Teacher attendance session management",
            "Student face recognition attendance",
            "Manual attendance marking",
            "Proxy detection and marking",
            "Real-time attendance dashboard",
            "Comprehensive attendance reports"
        ]
    }


# =====================================================
# AUTHENTICATION ENDPOINTS
# =====================================================
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    if auth.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = utils.get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        role=3,
        name=user_data.email.split('@')[0]
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return new_user


@app.post("/login", response_model=schemas.Token)
def login(user_credentials: schemas.UserCreate, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "user_id": str(user.user_id),
            "email": user.email,
            "name": user.name,
            "role": user.role
        }
    }


@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    user = await auth.get_current_user_simple(token, db)
    return user


# =====================================================
# ADD TEACHER (ADMIN ONLY)
# =====================================================
@app.post("/add-teacher", response_model=schemas.TeacherResponse, status_code=201)
async def add_teacher(
    teacher_data: schemas.TeacherCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)

    if current_user.role not in [1, 2]:
        raise HTTPException(status_code=403, detail="Only admin or school users can add teachers")

    if auth.get_user_by_email(db, teacher_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    school = db.query(models.School).filter(
        models.School.school_id == teacher_data.school_id
    ).first()

    if not school:
        raise HTTPException(status_code=404, detail=f"School with ID {teacher_data.school_id} not found")

    try:
        hashed_password = utils.get_password_hash(teacher_data.password)

        new_user = models.User(
            email=teacher_data.email,
            password_hash=hashed_password,
            role=3,
            name=teacher_data.name,
            phone_number=teacher_data.phone_number
        )
        db.add(new_user)
        db.flush()

        new_teacher = models.TeacherProfile(
            user_id=new_user.user_id,
            school_id=teacher_data.school_id,
            teacher_name=teacher_data.name,
            teacher_email=teacher_data.email
        )
        db.add(new_teacher)

        activity = models.SchoolActivity(
            activity_name=models.ActivityType.add_teacher,
            user_id=current_user.user_id
        )
        db.add(activity)

        db.commit()
        db.refresh(new_teacher)
        db.refresh(new_user)

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
        raise HTTPException(status_code=500, detail=f"Error adding teacher: {str(e)}")


# =====================================================
# SECTION MANAGEMENT
# =====================================================
@app.post("/section/create", response_model=schemas.SectionResponse)
async def create_section(
    section_data: schemas.SectionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)

    if current_user.role not in [1, 2]:
        raise HTTPException(status_code=403, detail="Only admin/school can create sections")

    class_obj = db.query(models.Class).filter(
        models.Class.class_id == section_data.class_id
    ).first()

    if not class_obj:
        raise HTTPException(status_code=404, detail=f"Class {section_data.class_id} not found")

    try:
        new_section = models.Section(
            section_name=section_data.section_name,
            class_id=section_data.class_id,
            total_students=0
        )

        db.add(new_section)
        db.commit()
        db.refresh(new_section)
        return new_section

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating section: {str(e)}")


@app.get("/sections/class/{class_id}")
async def get_sections_by_class(
    class_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)

    sections = db.query(models.Section).filter(
        models.Section.class_id == class_id
    ).all()

    return {
        "class_id": class_id,
        "total_sections": len(sections),
        "sections": [
            {
                "section_id": s.section_id,
                "section_name": s.section_name,
                "total_students": s.total_students
            }
            for s in sections
        ]
    }


# =====================================================
# HEALTH CHECK
# =====================================================
@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Face Recognition Attendance System",
        "version": "3.0.0"
    }


# =====================================================
# ROUTERS
# =====================================================
app.include_router(teacher.router)
app.include_router(student.router)
app.include_router(attendance.router)
app.include_router(reports.router)

# Face recognition inclusion
try:
    from face_recognition_system.integration import get_face_recognition_router
    app.include_router(get_face_recognition_router())
    print("✅ Face Recognition routes added!")
except Exception as e:
    print(f"⚠️ Face Recognition not available: {str(e)}")
