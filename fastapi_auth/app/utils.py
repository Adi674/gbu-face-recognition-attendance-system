from datetime import datetime, timedelta
from jose import jwt
import hashlib
import secrets
import random
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from .config import SECRET_KEY, ALGORITHM, SMTP_SERVER, SMTP_PORT, SMTP_EMAIL, SMTP_PASSWORD
from typing import Optional

# Import vector database service
try:
    from .vector_db_service import (
        store_student_photo_in_vector_db as vector_store,
        verify_student_photo as vector_verify,
        delete_student_embedding as vector_delete
    )
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    print("⚠️ Vector DB service not available. Face recognition features will be limited.")


# ============================================
# PASSWORD UTILITIES
# ============================================
def get_password_hash(password: str) -> str:
    """Simple SHA256 + salt password hashing"""
    salt = secrets.token_hex(16)
    password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
    return f"{salt}:{password_hash}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify SHA256 + salt password"""
    try:
        salt, stored_hash = hashed_password.split(':')
        password_hash = hashlib.sha256((plain_password + salt).encode()).hexdigest()
        return password_hash == stored_hash
    except:
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ============================================
# PASSWORD GENERATOR FOR TEACHERS
# ============================================
def generate_teacher_password(teacher_name: str, school_id: int) -> str:
    """
    Generate password: teacherName + schoolID + random3Digits
    Example: JohnSCH123842
    """
    # Remove spaces and get first part of name
    clean_name = teacher_name.replace(" ", "").split()[0] if " " in teacher_name else teacher_name
    
    # Generate 3 random digits
    random_digits = random.randint(100, 999)
    
    # Format: Name + SCH + SchoolID + RandomDigits
    password = f"{clean_name}SCH{school_id}{random_digits}"
    
    return password


# ============================================
# EMAIL SERVICE
# ============================================
def send_teacher_credentials_email(
    teacher_email: str,
    teacher_name: str,
    plain_password: str,
    school_name: str = "Your School"
) -> bool:
    """
    Send login credentials to teacher's email
    Returns True if successful, False otherwise
    """
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Welcome to {school_name} - Your Login Credentials"
        msg['From'] = SMTP_EMAIL
        msg['To'] = teacher_email
        
        # HTML email body
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                        Welcome to {school_name}!
                    </h2>
                    <p>Dear <strong>{teacher_name}</strong>,</p>
                    <p>Your teacher account has been successfully created. Below are your login credentials:</p>
                    
                    <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin: 20px 0;">
                        <p style="margin: 5px 0;"><strong>Email:</strong> {teacher_email}</p>
                        <p style="margin: 5px 0;"><strong>Password:</strong> <code style="background-color: #e9ecef; padding: 2px 6px; border-radius: 3px;">{plain_password}</code></p>
                    </div>
                    
                    <p><strong>⚠️ Important Security Note:</strong></p>
                    <ul>
                        <li>Please change your password after your first login</li>
                        <li>Do not share your credentials with anyone</li>
                        <li>Keep this email secure</li>
                    </ul>
                    
                    <p>If you have any questions or did not request this account, please contact the administration immediately.</p>
                    
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="font-size: 12px; color: #777;">
                        This is an automated email. Please do not reply to this message.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Attach HTML body
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Email sent successfully to {teacher_email}")
        return True
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return False


# ============================================
# VECTOR DATABASE SERVICE INTEGRATION
# ============================================
async def store_student_photo_in_vector_db(
    roll_no: str,
    photo_base64: str,
    metadata: dict
) -> bool:
    """
    Store student photo in vector database with embeddings
    
    Args:
        roll_no: Student's roll number
        photo_base64: Base64 encoded photo
        metadata: Additional metadata (name, email, etc.)
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    if not VECTOR_DB_AVAILABLE:
        print("⚠️ Vector DB not configured. Using mock storage.")
        return True  # Return True to not block student creation
    
    try:
        # Call vector database service
        result = await vector_store(roll_no, photo_base64, metadata)
        
        if result:
            print(f"✅ Photo stored successfully for roll_no: {roll_no}")
        else:
            print(f"❌ Failed to store photo for roll_no: {roll_no}")
        
        return result
        
    except Exception as e:
        print(f"❌ Vector DB storage error: {str(e)}")
        return False


async def verify_student_photo(roll_no: str, photo_base64: str) -> dict:
    """
    Verify student photo against vector database
    
    Args:
        roll_no: Expected student's roll number
        photo_base64: Base64 encoded photo to verify
    
    Returns:
        dict: {
            'verified': bool,
            'confidence': float,
            'matched_roll_no': str,
            'is_match': bool,
            'message': str
        }
    """
    
    if not VECTOR_DB_AVAILABLE:
        print("⚠️ Vector DB not configured. Using mock verification.")
        return {
            'verified': True,
            'confidence': 0.95,
            'matched_roll_no': roll_no,
            'is_match': True,
            'message': 'Mock verification (Vector DB not configured)'
        }
    
    try:
        # Call vector database service
        result = await vector_verify(roll_no, photo_base64)
        
        if result['verified']:
            print(f"✅ Photo verified for roll_no: {roll_no} (confidence: {result['confidence']:.2f})")
        else:
            print(f"⚠️ Photo verification failed for roll_no: {roll_no}")
        
        return result
        
    except Exception as e:
        print(f"❌ Photo verification error: {str(e)}")
        return {
            'verified': False,
            'confidence': 0.0,
            'matched_roll_no': None,
            'is_match': False,
            'message': f'Verification error: {str(e)}'
        }


async def delete_student_photo_from_vector_db(roll_no: str) -> bool:
    """
    Delete student's photo embedding from vector database
    
    Args:
        roll_no: Student's roll number
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    if not VECTOR_DB_AVAILABLE:
        print("⚠️ Vector DB not configured. Skipping deletion.")
        return True
    
    try:
        result = await vector_delete(roll_no)
        
        if result:
            print(f"✅ Photo deleted successfully for roll_no: {roll_no}")
        else:
            print(f"⚠️ Failed to delete photo for roll_no: {roll_no}")
        
        return result
        
    except Exception as e:
        print(f"❌ Photo deletion error: {str(e)}")
        return False


# ============================================
# ATTENDANCE UTILITIES
# ============================================
def calculate_attendance_percentage(total_classes: int, attended_classes: int) -> float:
    """Calculate attendance percentage"""
    if total_classes == 0:
        return 0.0
    return round((attended_classes / total_classes) * 100, 2)


def is_attendance_satisfactory(percentage: float, threshold: float = 75.0) -> bool:
    """Check if attendance meets minimum threshold"""
    return percentage >= threshold


def generate_attendance_report_html(
    student_name: str,
    roll_no: str,
    attendance_data: dict
) -> str:
    """Generate HTML attendance report for email"""
    
    html = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
                    Attendance Report
                </h2>
                
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p style="margin: 5px 0;"><strong>Student Name:</strong> {student_name}</p>
                    <p style="margin: 5px 0;"><strong>Roll Number:</strong> {roll_no}</p>
                </div>
                
                <h3>Attendance Summary</h3>
                <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
                    <tr style="background-color: #3498db; color: white;">
                        <th style="padding: 10px; text-align: left; border: 1px solid #ddd;">Metric</th>
                        <th style="padding: 10px; text-align: right; border: 1px solid #ddd;">Value</th>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Total Classes</td>
                        <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{attendance_data.get('total_classes', 0)}</td>
                    </tr>
                    <tr style="background-color: #f8f9fa;">
                        <td style="padding: 10px; border: 1px solid #ddd;">Classes Attended</td>
                        <td style="padding: 10px; text-align: right; border: 1px solid #ddd;">{attendance_data.get('attended', 0)}</td>
                    </tr>
                    <tr>
                        <td style="padding: 10px; border: 1px solid #ddd;">Attendance Percentage</td>
                        <td style="padding: 10px; text-align: right; border: 1px solid #ddd; font-weight: bold;">{attendance_data.get('percentage', 0)}%</td>
                    </tr>
                </table>
                
                <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                <p style="font-size: 12px; color: #777;">
                    This is an automated report generated by the School Management System.
                </p>
            </div>
        </body>
    </html>
    """
    
    return html


def send_attendance_report_email(
    student_email: str,
    student_name: str,
    roll_no: str,
    attendance_data: dict
) -> bool:
    """Send attendance report to student email"""
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Attendance Report - {roll_no}"
        msg['From'] = SMTP_EMAIL
        msg['To'] = student_email
        
        html_body = generate_attendance_report_html(student_name, roll_no, attendance_data)
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ Attendance report sent to {student_email}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to send attendance report: {str(e)}")
        return False


# ============================================
# DATA VALIDATION UTILITIES
# ============================================
def validate_phone_number(phone: str) -> bool:
    """Validate phone number format"""
    import re
    # Basic validation: 10-15 digits, optional + prefix
    pattern = r'^\+?[1-9]\d{9,14}$'
    return bool(re.match(pattern, phone.replace('-', '').replace(' ', '')))


def validate_roll_number_format(roll_no: str, format_pattern: str = r'^[A-Z0-9]{5,20}$') -> bool:
    """Validate roll number format"""
    import re
    return bool(re.match(format_pattern, roll_no))


def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '|', '`']
    sanitized = text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    return sanitized.strip()


# ============================================
# DATE/TIME UTILITIES
# ============================================
def get_current_semester() -> int:
    """Get current semester based on date"""
    current_month = datetime.utcnow().month
    
    # Odd semester: July-December (months 7-12)
    # Even semester: January-June (months 1-6)
    if 1 <= current_month <= 6:
        return 2  # Even semester
    else:
        return 1  # Odd semester


def get_academic_year() -> int:
    """Get current academic year"""
    current_date = datetime.utcnow()
    current_month = current_date.month
    current_year = current_date.year
    
    # Academic year starts in July
    if current_month >= 7:
        return current_year
    else:
        return current_year - 1


def format_timestamp(dt: datetime) -> str:
    """Format datetime to readable string"""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


# ============================================
# FILE HANDLING UTILITIES
# ============================================
def validate_base64_image(base64_string: str) -> bool:
    """Validate if string is valid base64 encoded image"""
    import base64
    import re
    
    try:
        # Check if it's valid base64
        decoded = base64.b64decode(base64_string)
        
        # Check for common image file signatures
        image_signatures = {
            b'\xff\xd8\xff': 'jpeg',
            b'\x89PNG\r\n\x1a\n': 'png',
            b'GIF87a': 'gif',
            b'GIF89a': 'gif',
        }
        
        for signature in image_signatures:
            if decoded.startswith(signature):
                return True
        
        return False
        
    except Exception:
        return False


def get_image_format_from_base64(base64_string: str) -> str:
    """Get image format from base64 string"""
    import base64
    
    try:
        decoded = base64.b64decode(base64_string)
        
        if decoded.startswith(b'\xff\xd8\xff'):
            return 'jpeg'
        elif decoded.startswith(b'\x89PNG'):
            return 'png'
        elif decoded.startswith(b'GIF'):
            return 'gif'
        else:
            return 'unknown'
            
    except Exception:
        return 'invalid'


# ============================================
# LOGGING UTILITIES
# ============================================
def log_activity(activity_type: str, user_id: str, details: dict = None):
    """Log activity for audit trail"""
    log_entry = {
        'timestamp': datetime.utcnow().isoformat(),
        'activity_type': activity_type,
        'user_id': str(user_id),
        'details': details or {}
    }
    
    print(f"📝 Activity Log: {log_entry}")
    # In production, you might want to write this to a file or logging service


# ============================================
# EXPORT UTILITIES
# ============================================
def export_attendance_to_csv(attendance_data: list) -> str:
    """Export attendance data to CSV format"""
    import csv
    from io import StringIO
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(['Roll No', 'Name', 'Date', 'Status', 'Type', 'Proxy Detected'])
    
    # Write data
    for record in attendance_data:
        writer.writerow([
            record.get('roll_no'),
            record.get('name'),
            record.get('date'),
            'Present' if not record.get('is_rejected') else 'Rejected',
            'Manual' if record.get('is_manual') else 'Photo',
            'Yes' if record.get('is_proxy') else 'No'
        ])
    
    return output.getvalue()


def generate_qr_code_for_attendance(unique_code: str) -> str:
    """Generate QR code for attendance (returns base64)"""
    # Placeholder - integrate with qrcode library if needed
    # import qrcode
    # from io import BytesIO
    # import base64
    # 
    # qr = qrcode.QRCode(version=1, box_size=10, border=5)
    # qr.add_data(unique_code)
    # qr.make(fit=True)
    # 
    # img = qr.make_image(fill_color="black", back_color="white")
    # buffer = BytesIO()
    # img.save(buffer, format='PNG')
    # 
    # return base64.b64encode(buffer.getvalue()).decode()
    
    return f"QR_CODE_PLACEHOLDER_{unique_code}"