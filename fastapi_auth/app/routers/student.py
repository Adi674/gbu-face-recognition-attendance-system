from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
from pathlib import Path

from .. import models, schemas, auth, utils
from ..database import get_db

router = APIRouter(prefix="/student", tags=["Student"])
security = HTTPBearer()

# ============================================
# 3. STUDENT MODULE - ADD STUDENT
# ============================================

@router.post("/add", response_model=schemas.StudentResponse)
async def add_student(
    student_data: schemas.StudentCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Add a new student to the system
    
    Validates:
    - Duplicate roll numbers within section
    - Valid school, department, section
    - Email uniqueness
    """
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Normalize roll number
    try:
        normalized_roll = utils.validate_roll_number(student_data.roll_no)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    # Check for duplicate roll number
    existing_student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == normalized_roll
    ).first()
    
    if existing_student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Student with roll number {normalized_roll} already exists"
        )
    
    # Check email uniqueness
    if student_data.email:
        existing_email = db.query(models.StudentProfile).filter(
            models.StudentProfile.email == student_data.email
        ).first()
        
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {student_data.email} is already registered"
            )
    
    # Validate school exists
    school = db.query(models.School).filter(
        models.School.school_id == student_data.school_id
    ).first()
    
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School with ID {student_data.school_id} not found"
        )
    
    # Validate department exists
    department = db.query(models.Department).filter(
        models.Department.department_id == student_data.department_id
    ).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with ID {student_data.department_id} not found"
        )
    
    # Validate section if provided
    if student_data.section_id:
        section = db.query(models.Section).filter(
            models.Section.section_id == student_data.section_id
        ).first()
        
        if not section:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Section with ID {student_data.section_id} not found"
            )
    
    try:
        # Create student profile
        new_student = models.StudentProfile(
            roll_no=normalized_roll,
            name=student_data.name,
            phone_number=student_data.phone_number,
            email=student_data.email,
            semester=student_data.semester,
            year=student_data.year,
            school_id=student_data.school_id,
            department_id=student_data.department_id,
            section_id=student_data.section_id,
            profile_photo_url=student_data.profile_photo_url,
            face_enrolled=False
        )
        
        db.add(new_student)
        
        # Update section student count if section provided
        if student_data.section_id:
            section = db.query(models.Section).filter(
                models.Section.section_id == student_data.section_id
            ).first()
            section.total_students += 1
        
        # Log activity
        activity = models.SchoolActivity(
            activity_name=models.ActivityType.add_student,
            user_id=current_user.user_id,
            roll_no=normalized_roll
        )
        db.add(activity)
        
        db.commit()
        db.refresh(new_student)
        
        return new_student
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding student: {str(e)}"
        )

# ============================================
# UPDATE STUDENT PROFILE PHOTO
# ============================================

@router.put("/update-photo/{roll_no}")
async def update_student_photo(
    roll_no: str,
    profile_photo_url: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update student profile photo URL"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    # Find student
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no.upper()
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number {roll_no} not found"
        )
    
    try:
        student.profile_photo_url = profile_photo_url
        student.updated_at = datetime.utcnow()
        
        db.commit()
        
        return {
            "success": True,
            "message": "Profile photo updated successfully",
            "roll_no": student.roll_no,
            "profile_photo_url": student.profile_photo_url
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating photo: {str(e)}"
        )

# ============================================
# UPDATE STUDENT DETAILS
# ============================================

@router.put("/update/{roll_no}")
async def update_student(
    roll_no: str,
    update_data: schemas.StudentUpdate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Update student information"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Find student
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no.upper()
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number {roll_no} not found"
        )
    
    try:
        # Update fields if provided
        if update_data.name is not None:
            student.name = update_data.name
        
        if update_data.phone_number is not None:
            student.phone_number = update_data.phone_number
        
        if update_data.email is not None:
            # Check email uniqueness
            existing = db.query(models.StudentProfile).filter(
                models.StudentProfile.email == update_data.email,
                models.StudentProfile.roll_no != roll_no.upper()
            ).first()
            
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            
            student.email = update_data.email
        
        if update_data.semester is not None:
            student.semester = update_data.semester
        
        if update_data.year is not None:
            student.year = update_data.year
        
        if update_data.profile_photo_url is not None:
            student.profile_photo_url = update_data.profile_photo_url
        
        if update_data.section_id is not None:
            # Update section counts
            if student.section_id != update_data.section_id:
                # Decrease old section count
                if student.section_id:
                    old_section = db.query(models.Section).filter(
                        models.Section.section_id == student.section_id
                    ).first()
                    if old_section:
                        old_section.total_students -= 1
                
                # Increase new section count
                new_section = db.query(models.Section).filter(
                    models.Section.section_id == update_data.section_id
                ).first()
                if new_section:
                    new_section.total_students += 1
                
                student.section_id = update_data.section_id
        
        student.updated_at = datetime.utcnow()
        
        # Log activity
        activity = models.SchoolActivity(
            activity_name=models.ActivityType.update_student,
            user_id=current_user.user_id,
            roll_no=student.roll_no
        )
        db.add(activity)
        
        db.commit()
        db.refresh(student)
        
        return {
            "success": True,
            "message": "Student updated successfully",
            "student": utils.format_student_info(student)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating student: {str(e)}"
        )

# ============================================
# GET STUDENT BY ROLL NUMBER
# ============================================

@router.get("/{roll_no}", response_model=schemas.StudentResponse)
async def get_student(
    roll_no: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get student by roll number"""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no.upper()
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number {roll_no} not found"
        )
    
    return student

# ============================================
# GET STUDENTS BY SECTION
# ============================================

@router.get("/section/{section_id}/students")
async def get_students_by_section(
    section_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all students in a section"""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    students = db.query(models.StudentProfile).filter(
        models.StudentProfile.section_id == section_id
    ).order_by(models.StudentProfile.roll_no).all()
    
    return {
        "section_id": section_id,
        "total_students": len(students),
        "students": [utils.format_student_info(s) for s in students]
    }

# ============================================
# DELETE STUDENT
# ============================================

@router.delete("/{roll_no}")
async def delete_student(
    roll_no: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Delete student from system"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [1, 2]:  # Only admin and school
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or school can delete students"
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no.upper()
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number {roll_no} not found"
        )
    
    try:
        # Update section count
        if student.section_id:
            section = db.query(models.Section).filter(
                models.Section.section_id == student.section_id
            ).first()
            if section:
                section.total_students -= 1
        
        # Log activity
        activity = models.SchoolActivity(
            activity_name=models.ActivityType.remove_student,
            user_id=current_user.user_id,
            roll_no=student.roll_no
        )
        db.add(activity)
        
        db.delete(student)
        db.commit()
        
        return {
            "success": True,
            "message": f"Student {roll_no} deleted successfully"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting student: {str(e)}"
        )