from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List

from .. import models, schemas, auth, utils
from ..database import get_db

router = APIRouter(prefix="/teacher", tags=["Teacher"])
security = HTTPBearer()

# ============================================
# 1. TEACHER LOGIN & UNIQUE CODE GENERATION
# ============================================

@router.post("/start-attendance", response_model=schemas.AttendanceSessionResponse)
async def start_attendance_session(
    session_data: schemas.AttendanceSessionCreate,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Teacher starts attendance session and generates unique code
    
    Process:
    1. Verify teacher authentication
    2. Validate class and section
    3. Generate unique 10-character code
    4. Set expiry time (default: 10 minutes)
    5. Create attendance session
    """
    # Authenticate teacher
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:  # Must be teacher
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can start attendance sessions"
        )
    
    # Get teacher profile
    teacher = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.user_id == current_user.user_id
    ).first()
    
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Teacher profile not found"
        )
    
    # Validate class exists
    class_obj = db.query(models.Class).filter(
        models.Class.class_id == session_data.class_id
    ).first()
    
    if not class_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class with ID {session_data.class_id} not found"
        )
    
    # Validate section exists and belongs to class
    section = db.query(models.Section).filter(
        and_(
            models.Section.section_id == session_data.section_id,
            models.Section.class_id == session_data.class_id
        )
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section with ID {session_data.section_id} not found in class {session_data.class_id}"
        )
    
    # Validate subject if provided
    if session_data.course_code:
        subject = db.query(models.Subject).filter(
            models.Subject.course_code == session_data.course_code
        ).first()
        
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject with course code {session_data.course_code} not found"
            )
    
    try:
        # Generate unique code
        max_attempts = 10
        unique_code = None
        
        for _ in range(max_attempts):
            code = utils.generate_unique_attendance_code(
                class_id=session_data.class_id,
                section_id=session_data.section_id,
                teacher_id=teacher.teacher_id
            )
            
            # Check if code already exists
            existing = db.query(models.AttendanceSession).filter(
                models.AttendanceSession.unique_code == code
            ).first()
            
            if not existing:
                unique_code = code
                break
        
        if not unique_code:
            # Fallback to completely random code
            unique_code = utils.generate_collision_free_code()
        
        # Calculate expiry time
        expires_at = utils.calculate_expiry_time(session_data.duration_minutes)
        
        # Create attendance session
        new_session = models.AttendanceSession(
            unique_code=unique_code,
            teacher_id=teacher.teacher_id,
            teacher_user_id=current_user.user_id,
            class_id=session_data.class_id,
            section_id=session_data.section_id,
            course_code=session_data.course_code,
            expires_at=expires_at,
            is_active=True
        )
        
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        
        return schemas.AttendanceSessionResponse(
            session_id=new_session.session_id,
            unique_code=new_session.unique_code,
            class_id=new_session.class_id,
            section_id=new_session.section_id,
            course_code=new_session.course_code,
            created_at=new_session.created_at,
            expires_at=new_session.expires_at,
            is_active=new_session.is_active,
            total_present=new_session.total_present,
            total_absent=new_session.total_absent,
            total_proxy=new_session.total_proxy,
            total_manual=new_session.total_manual
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating attendance session: {str(e)}"
        )

# ============================================
# CLOSE ATTENDANCE SESSION
# ============================================

@router.post("/close-attendance/{unique_code}")
async def close_attendance_session(
    unique_code: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Teacher closes attendance session manually"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can close sessions"
        )
    
    # Find session
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.unique_code == unique_code
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )
    
    # Verify teacher owns this session
    if session.teacher_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only close your own attendance sessions"
        )
    
    try:
        # Mark session as inactive
        session.is_active = False
        session.closed_at = datetime.utcnow()
        
        # Calculate absent students
        total_students = db.query(models.StudentProfile).filter(
            models.StudentProfile.section_id == session.section_id
        ).count()
        
        session.total_absent = total_students - (
            session.total_present + session.total_proxy + session.total_manual
        )
        
        db.commit()
        
        return {
            "success": True,
            "message": "Attendance session closed successfully",
            "session_id": session.session_id,
            "unique_code": session.unique_code,
            "closed_at": session.closed_at,
            "statistics": {
                "total_students": total_students,
                "present": session.total_present,
                "absent": session.total_absent,
                "proxy": session.total_proxy,
                "manual": session.total_manual
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error closing session: {str(e)}"
        )

# ============================================
# GET TEACHER'S ACTIVE SESSIONS
# ============================================

@router.get("/active-sessions", response_model=List[schemas.AttendanceSessionResponse])
async def get_active_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get all active attendance sessions for current teacher"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view sessions"
        )
    
    # Get active sessions
    sessions = db.query(models.AttendanceSession).filter(
        and_(
            models.AttendanceSession.teacher_user_id == current_user.user_id,
            models.AttendanceSession.is_active == True
        )
    ).order_by(models.AttendanceSession.created_at.desc()).all()
    
    return sessions

# ============================================
# GET TEACHER'S SESSION HISTORY
# ============================================

@router.get("/session-history")
async def get_session_history(
    limit: int = 20,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get teacher's session history"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view session history"
        )
    
    sessions = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.teacher_user_id == current_user.user_id
    ).order_by(
        models.AttendanceSession.created_at.desc()
    ).limit(limit).all()
    
    return {
        "total_sessions": len(sessions),
        "sessions": [
            {
                "session_id": s.session_id,
                "unique_code": s.unique_code,
                "class_id": s.class_id,
                "section_id": s.section_id,
                "course_code": s.course_code,
                "created_at": s.created_at,
                "expires_at": s.expires_at,
                "closed_at": s.closed_at,
                "is_active": s.is_active,
                "statistics": {
                    "present": s.total_present,
                    "absent": s.total_absent,
                    "proxy": s.total_proxy,
                    "manual": s.total_manual
                }
            }
            for s in sessions
        ]
    }