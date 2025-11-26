from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime

from .. import models, schemas, auth, utils
from ..database import get_db

router = APIRouter(prefix="/reports", tags=["Reports"])
security = HTTPBearer()

# ============================================
# 7. ATTENDANCE REPORTS
# ============================================

@router.post("/session", response_model=schemas.AttendanceReportResponse)
async def get_session_report(
    report_request: schemas.AttendanceReportRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive attendance report for a session
    
    Returns:
    - Session information
    - Statistics (present, absent, proxy, manual counts)
    - List of present students
    - List of absent students
    - Proxy records
    - Manual entries
    """
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Find session
    session = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.unique_code == report_request.unique_code
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance session not found"
        )
    
    # Get all students in section
    all_students = db.query(models.StudentProfile).filter(
        models.StudentProfile.section_id == session.section_id
    ).order_by(models.StudentProfile.roll_no).all()
    
    total_students = len(all_students)
    
    # Get attendance records
    attendance_records = db.query(models.AttendanceRecord).filter(
        models.AttendanceRecord.session_id == session.session_id
    ).all()
    
    # Build present students list
    present_roll_numbers = set()
    present_students = []
    manual_entries = []
    
    for record in attendance_records:
        present_roll_numbers.add(record.roll_no)
        student = next((s for s in all_students if s.roll_no == record.roll_no), None)
        
        if student:
            student_data = {
                "roll_no": student.roll_no,
                "name": student.name,
                "email": student.email,
                "marked_at": record.marked_at,
                "status": record.status.value,
                "is_manual": record.is_manual,
                "is_proxy": record.is_proxy,
                "face_confidence": record.face_confidence
            }
            
            present_students.append(student_data)
            
            if record.is_manual:
                manual_entries.append(student_data)
    
    # Build absent students list
    absent_students = [
        {
            "roll_no": s.roll_no,
            "name": s.name,
            "email": s.email,
            "phone_number": s.phone_number
        }
        for s in all_students
        if s.roll_no not in present_roll_numbers
    ]
    
    # Get proxy records
    proxy_records_query = db.query(models.ProxyRecord).filter(
        models.ProxyRecord.session_id == session.session_id
    ).all()
    
    proxy_records = []
    for proxy in proxy_records_query:
        student = next((s for s in all_students if s.roll_no == proxy.roll_no), None)
        teacher = db.query(models.TeacherProfile).filter(
            models.TeacherProfile.teacher_id == proxy.marked_by_teacher_id
        ).first()
        
        proxy_records.append({
            "roll_no": proxy.roll_no,
            "student_name": student.name if student else "Unknown",
            "reason": proxy.reason,
            "marked_by": teacher.teacher_name if teacher else "Unknown",
            "marked_at": proxy.marked_at
        })
    
    # Get class and section info
    class_obj = db.query(models.Class).filter(
        models.Class.class_id == session.class_id
    ).first()
    
    section = db.query(models.Section).filter(
        models.Section.section_id == session.section_id
    ).first()
    
    subject = None
    if session.course_code:
        subject = db.query(models.Subject).filter(
            models.Subject.course_code == session.course_code
        ).first()
    
    # Build session info
    session_info = {
        "session_id": session.session_id,
        "unique_code": session.unique_code,
        "class_name": class_obj.class_name if class_obj else "Unknown",
        "section_name": section.section_name if section else "Unknown",
        "subject_name": subject.subject_name if subject else "N/A",
        "course_code": session.course_code,
        "created_at": session.created_at,
        "expires_at": session.expires_at,
        "closed_at": session.closed_at,
        "is_active": session.is_active,
        "teacher_id": session.teacher_id
    }
    
    # Calculate statistics
    present_count = len(present_students)
    absent_count = len(absent_students)
    proxy_count = len(proxy_records)
    manual_count = len(manual_entries)
    
    attendance_percentage = (present_count / total_students * 100) if total_students > 0 else 0
    
    statistics = {
        "total_students": total_students,
        "present_count": present_count,
        "absent_count": absent_count,
        "proxy_count": proxy_count,
        "manual_count": manual_count,
        "attendance_percentage": round(attendance_percentage, 2),
        "duration_minutes": utils.get_remaining_minutes(session.created_at) if session.closed_at else 0
    }
    
    return schemas.AttendanceReportResponse(
        session_info=session_info,
        statistics=statistics,
        present_students=present_students,
        absent_students=absent_students,
        proxy_records=proxy_records,
        manual_entries=manual_entries,
        generated_at=datetime.utcnow()
    )

# ============================================
# TEACHER ATTENDANCE SUMMARY
# ============================================

@router.get("/teacher/summary")
async def get_teacher_attendance_summary(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get attendance summary for current teacher"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role != 3:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only teachers can view this summary"
        )
    
    # Get all sessions for teacher
    sessions = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.teacher_user_id == current_user.user_id
    ).all()
    
    total_sessions = len(sessions)
    active_sessions = sum(1 for s in sessions if s.is_active)
    
    # Calculate totals
    total_present = sum(s.total_present for s in sessions)
    total_absent = sum(s.total_absent for s in sessions)
    total_proxy = sum(s.total_proxy for s in sessions)
    total_manual = sum(s.total_manual for s in sessions)
    
    return {
        "teacher_info": {
            "name": current_user.name,
            "email": current_user.email
        },
        "summary": {
            "total_sessions_conducted": total_sessions,
            "active_sessions": active_sessions,
            "total_students_marked_present": total_present,
            "total_students_marked_absent": total_absent,
            "total_proxy_detected": total_proxy,
            "total_manual_entries": total_manual
        },
        "recent_sessions": [
            {
                "session_id": s.session_id,
                "unique_code": s.unique_code,
                "created_at": s.created_at,
                "is_active": s.is_active,
                "statistics": {
                    "present": s.total_present,
                    "absent": s.total_absent,
                    "proxy": s.total_proxy,
                    "manual": s.total_manual
                }
            }
            for s in sorted(sessions, key=lambda x: x.created_at, reverse=True)[:10]
        ]
    }

# ============================================
# SECTION ATTENDANCE ANALYTICS
# ============================================

@router.get("/section/{section_id}/analytics")
async def get_section_analytics(
    section_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get attendance analytics for a section"""
    token = credentials.credentials
    current_user = await auth.get_current_user_simple(token, db)
    
    if current_user.role not in [1, 2, 3]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )
    
    # Get section info
    section = db.query(models.Section).filter(
        models.Section.section_id == section_id
    ).first()
    
    if not section:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Section {section_id} not found"
        )
    
    # Get all sessions for this section
    sessions = db.query(models.AttendanceSession).filter(
        models.AttendanceSession.section_id == section_id
    ).all()
    
    # Get all students in section
    students = db.query(models.StudentProfile).filter(
        models.StudentProfile.section_id == section_id
    ).all()
    
    # Calculate per-student attendance
    student_attendance = []
    
    for student in students:
        # Count attendance records for this student
        attendance_count = db.query(models.AttendanceRecord).filter(
            and_(
                models.AttendanceRecord.roll_no == student.roll_no,
                models.AttendanceRecord.session_id.in_([s.session_id for s in sessions])
            )
        ).count()
        
        total_sessions = len(sessions)
        attendance_percentage = (attendance_count / total_sessions * 100) if total_sessions > 0 else 0
        
        student_attendance.append({
            "roll_no": student.roll_no,
            "name": student.name,
            "sessions_attended": attendance_count,
            "total_sessions": total_sessions,
            "attendance_percentage": round(attendance_percentage, 2)
        })
    
    # Sort by attendance percentage
    student_attendance.sort(key=lambda x: x['attendance_percentage'], reverse=True)
    
    return {
        "section_info": {
            "section_id": section.section_id,
            "section_name": section.section_name,
            "total_students": len(students)
        },
        "overall_statistics": {
            "total_sessions_conducted": len(sessions),
            "average_attendance_percentage": round(
                sum(s['attendance_percentage'] for s in student_attendance) / len(student_attendance), 2
            ) if student_attendance else 0
        },
        "student_attendance": student_attendance
    }

# ============================================
# STUDENT INDIVIDUAL REPORT
# ============================================

@router.get("/student/{roll_no}")
async def get_student_attendance_report(
    roll_no: str,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    """Get detailed attendance report for a student"""
    token = credentials.credentials
    await auth.get_current_user_simple(token, db)
    
    # Find student
    student = db.query(models.StudentProfile).filter(
        models.StudentProfile.roll_no == roll_no.upper()
    ).first()
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {roll_no} not found"
        )
    
    # Get all attendance records for student
    attendance_records = db.query(models.AttendanceRecord).join(
        models.AttendanceSession
    ).filter(
        models.AttendanceRecord.roll_no == student.roll_no
    ).order_by(models.AttendanceRecord.marked_at.desc()).all()
    
    # Get all sessions in student's section
    if student.section_id:
        total_sessions = db.query(models.AttendanceSession).filter(
            models.AttendanceSession.section_id == student.section_id
        ).count()
    else:
        total_sessions = 0
    
    sessions_attended = len(attendance_records)
    attendance_percentage = (sessions_attended / total_sessions * 100) if total_sessions > 0 else 0
    
    # Build detailed records
    detailed_records = []
    for record in attendance_records:
        session = db.query(models.AttendanceSession).filter(
            models.AttendanceSession.session_id == record.session_id
        ).first()
        
        if session:
            detailed_records.append({
                "session_code": session.unique_code,
                "marked_at": record.marked_at,
                "status": record.status.value,
                "is_manual": record.is_manual,
                "is_proxy": record.is_proxy,
                "face_confidence": record.face_confidence,
                "course_code": session.course_code
            })
    
    return {
        "student_info": {
            "roll_no": student.roll_no,
            "name": student.name,
            "email": student.email,
            "semester": student.semester,
            "section_id": student.section_id
        },
        "attendance_summary": {
            "total_sessions": total_sessions,
            "sessions_attended": sessions_attended,
            "sessions_missed": total_sessions - sessions_attended,
            "attendance_percentage": round(attendance_percentage, 2),
            "proxy_count": sum(1 for r in attendance_records if r.is_proxy),
            "manual_count": sum(1 for r in attendance_records if r.is_manual)
        },
        "detailed_records": detailed_records
    }