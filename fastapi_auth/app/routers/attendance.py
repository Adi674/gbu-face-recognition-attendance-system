from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
from typing import List

from .. import models, schemas, auth, utils
from ..database import get_db

router = APIRouter(prefix="/attendance", tags=["Attendance"])
security = HTTPBearer()

# Import face recognition (optional)
try:
    from face_recognition_system.pipeline import UltraSimpleFaceRecognition
    FACE_RECOGNITION_AVAILABLE = True
except:
    FACE_RECOGNITION_AVAILABLE = False

# ============================================
# 2. STUDENT ATTENDANCE - CAMERA + FACE RECOGNITION
# ============================================

@router.post("/mark", response_model=schemas.AttendanceMarkResponse)
async def mark_attendance(
    attendance_request: schemas.AttendanceMarkRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Mark student attendance using unique code and face recognition
    
    Process:
    1. Validate unique code exists and is active
    2. Check code expiry time
    3. Verify student exists in section
    4. Run face recognition (placeholder)
    5. Mark attendance if all checks pass
    """
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    # Validate unique code format
    if not utils.validate_unique_code_format(attendance_request.unique_code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid code format"
        )
    
    # Find attendance session
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.unique_code == attendance_request.unique_code
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid attendance code"
        )
    
    # Check if session is active
    if not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance session has been closed"
        )
    
    # Check if code has expired
    if utils.is_code_expired(session.expires_at):
        # Auto-close expired session
        session.is_active = False
        session.closed_at = datetime.utcnow()
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance code has expired"
        )
    
    # Normalize and find student
    try:
        normalized_roll = utils.validate_roll_number(attendance_request.roll_no)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == normalized_roll
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student with roll number {normalized_roll} not found"
        )
    
    # Verify student belongs to the session's section
    if student.section_id != session.section_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student does not belong to this section"
        )
    
    # Check if student has already marked attendance
    existing_attendance = db.query(models.AttendanceRecord).filter(
        and_(
            models.AttendanceRecord.session_id == session.session_id,
            models.AttendanceRecord.roll_no == normalized_roll
        )
    ).first()
    
    if existing_attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already marked for this student"
        )
    
    try:
        # Face recognition placeholder
        face_confidence = 0.0
        face_match = False
        
        if FACE_RECOGNITION_AVAILABLE and student.face_enrolled:
            # TODO: Implement actual face recognition
            # face_system = UltraSimpleFaceRecognition()
            # result = face_system.recognize_student(image_path)
            # face_confidence = result['confidence']
            # face_match = result['is_match']
            pass
        
        # For now, accept attendance if student is enrolled or face recognition not available
        if not student.face_enrolled:
            # No face data enrolled, allow attendance but mark as manual
            face_confidence = None
            face_match = None
        
        # Create attendance record
        attendance_record = models.AttendanceRecord(
            session_id=session.session_id,
            roll_no=normalized_roll,
            status=models.AttendanceStatus.present,
            is_manual=False,
            is_proxy=False,
            face_confidence=face_confidence,
            face_match=face_match,
            marked_at=datetime.utcnow()
        )
        
        db.add(attendance_record)
        
        # Update session statistics
        session.total_present += 1
        
        db.commit()
        db.refresh(attendance_record)
        
        return schemas.AttendanceMarkResponse(
            success=True,
            message=f"Attendance marked successfully for {student.name}",
            attendance_id=attendance_record.attendance_id,
            student_name=student.name,
            marked_at=attendance_record.marked_at,
            status="present"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking attendance: {str(e)}"
        )

# ============================================
# 4. ATTENDANCE CHECK - REAL-TIME DASHBOARD
# ============================================

@router.post("/check", response_model=schemas.AttendanceCheckResponse)
async def check_attendance_status(
    check_request: schemas.AttendanceCheckRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Check real-time attendance status for a session
    
    Returns:
    - Total students in section
    - Number of present students
    - List of present students
    - List of absent students
    """
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:  # Only teachers
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can check attendance"
        )
    
    # Find session
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.unique_code == check_request.unique_code
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
            detail="You can only check your own sessions"
        )
    
    # Get all students in section
    all_students = db.query(models.StudentProfile).filter(
        models.StudentProfile.section_id == session.section_id
    ).all()
    
    total_students = len(all_students)
    
    # Get attendance records for this session
    attendance_records = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session.session_id
    ).all()
    
    # Build present students list
    present_roll_numbers = {record.roll_no for record in attendance_records}
    present_students = []
    
    for record in attendance_records:
        student = next((s for s in all_students if s.roll_no == record.roll_no), None)
        if student:
            present_students.append(schemas.StudentAttendanceInfo(
                roll_no=student.roll_no,
                name=student.name,
                status=record.status.value,
                marked_at=record.marked_at,
                is_manual=record.is_manual,
                is_proxy=record.is_proxy,
                face_confidence=record.face_confidence
            ))
    
    # Build absent students list
    absent_students = [
        {
            "roll_no": s.roll_no,
            "name": s.name,
            "email": s.email
        }
        for s in all_students
        if s.roll_no not in present_roll_numbers
    ]
    
    # Calculate time remaining
    expires_in = utils.get_remaining_minutes(session.expires_at)
    
    return schemas.AttendanceCheckResponse(
        session_info=utils.format_session_info(session),
        total_students=total_students,
        present_count=len(present_students),
        absent_count=len(absent_students),
        proxy_count=session.total_proxy,
        manual_count=session.total_manual,
        present_students=present_students,
        absent_students=absent_students,
        session_active=session.is_active,
        expires_in_minutes=expires_in if session.is_active else 0
    )

# ============================================
# 5. MANUAL ATTENDANCE (TEACHER ONLY)
# ============================================

@router.post("/manual", response_model=schemas.AttendanceMarkResponse)
async def mark_manual_attendance(
    manual_request: schemas.ManualAttendanceRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Teacher manually marks attendance without face recognition
    
    Validations:
    - Session exists and belongs to teacher
    - Session is active
    - Student belongs to section
    - Student hasn't already marked attendance
    """
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can mark manual attendance"
        )
    
    # Find session
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.unique_code == manual_request.unique_code
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
            detail="You can only mark attendance for your own sessions"
        )
    
    # Normalize and find student
    try:
        normalized_roll = utils.validate_roll_number(manual_request.roll_no)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == normalized_roll
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {normalized_roll} not found"
        )
    
    # Verify student belongs to section
    if student.section_id != session.section_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student does not belong to this section"
        )
    
    # Check duplicate attendance
    existing = db.query(models.AttendanceRecord).filter(
        and_(
            models.AttendanceRecord.session_id == session.session_id,
            models.AttendanceRecord.roll_no == normalized_roll
        )
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attendance already marked for this student"
        )
    
    try:
        # Create manual attendance record
        attendance_record = models.AttendanceRecord(
            session_id=session.session_id,
            roll_no=normalized_roll,
            status=models.AttendanceStatus.manual,
            is_manual=True,
            is_proxy=False,
            face_confidence=None,
            face_match=None,
            marked_at=datetime.utcnow()
        )
        
        db.add(attendance_record)
        
        # Update session statistics
        session.total_manual += 1
        session.total_present += 1
        
        db.commit()
        db.refresh(attendance_record)
        
        return schemas.AttendanceMarkResponse(
            success=True,
            message=f"Manual attendance marked for {student.name}",
            attendance_id=attendance_record.attendance_id,
            student_name=student.name,
            marked_at=attendance_record.marked_at,
            status="manual"
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking manual attendance: {str(e)}"
        )

# ============================================
# 6. PROXY ATTENDANCE MODULE
# ============================================

@router.post("/proxy", response_model=schemas.ProxyAttendanceResponse)
async def mark_proxy_attendance(
    proxy_request: schemas.ProxyAttendanceRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Teacher marks attendance as proxy (fraudulent)
    
    Creates both:
    1. Attendance record with proxy flag
    2. Proxy record for reporting
    """
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can mark proxy attendance"
        )
    
    # Get teacher profile
    teacher = db.query(models.TeacherProfile).filter(
        models.TeacherProfile.user_id == current_user.user_id
    ).first()
    
    # Find session
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.unique_code == proxy_request.unique_code
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )
    
    # Verify teacher owns session
    if session.teacher_user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only mark proxy for your own sessions"
        )
    
    # Normalize and find student
    try:
        normalized_roll = utils.validate_roll_number(proxy_request.roll_no)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == normalized_roll
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {normalized_roll} not found"
        )
    
    try:
        # Create or update attendance record
        existing = db.query(models.AttendanceRecord).filter(
            and_(
                models.AttendanceRecord.session_id == session.session_id,
                models.AttendanceRecord.roll_no == normalized_roll
            )
        ).first()
        
        if existing:
            # Update existing record to proxy
            existing.status = models.AttendanceStatus.proxy
            existing.is_proxy = True
            attendance_record = existing
        else:
            # Create new proxy record
            attendance_record = models.AttendanceRecord(
                session_id=session.session_id,
                roll_no=normalized_roll,
                status=models.AttendanceStatus.proxy,
                is_manual=False,
                is_proxy=True,
                face_confidence=None,
                face_match=False,
                marked_at=datetime.utcnow()
            )
            db.add(attendance_record)
        
        # Create proxy record
        proxy_record = models.ProxyRecord(
            session_id=session.session_id,
            roll_no=normalized_roll,
            marked_by_teacher_id=teacher.teacher_id,
            reason=proxy_request.reason,
            marked_at=datetime.utcnow()
        )
        
        db.add(proxy_record)
        
        # Update session statistics
        if not existing:
            session.total_proxy += 1
        
        db.commit()
        db.refresh(proxy_record)
        
        return schemas.ProxyAttendanceResponse(
            success=True,
            message=f"Proxy attendance marked for {student.name}",
            proxy_id=proxy_record.proxy_id,
            marked_at=proxy_record.marked_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error marking proxy: {str(e)}"
        )