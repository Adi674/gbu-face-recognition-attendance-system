📖 API Documentation - School Management & Attendance System
🌐 Base URL
http://localhost:8000
🔐 Authentication
Most endpoints require JWT Bearer token authentication.

Authorization Header:

Authorization: Bearer <your_jwt_token>
📑 Table of Contents
Authentication Endpoints
School Management
Department Management
Class Management
Subject Management
Teacher Management
Student Management
Attendance System
Reports & Analytics
Activity Logs
🔑 Authentication Endpoints
1. Register User
POST /register

Create a new user account (default role: Teacher).

Request Body:

json
{
  "email": "user@example.com",
  "password": "password123"
}
Response (201):

json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "user",
  "role": 3,
  "created_at": "2024-01-15T10:30:00"
}
Role Values:

1 = Admin
2 = School
3 = Teacher
2. Login
POST /login

Authenticate user and receive JWT token.

Request Body:

json
{
  "email": "user@example.com",
  "password": "password123"
}
Response (200):

json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
3. Get Current User
GET /users/me

Get authenticated user's information.

Headers:

Authorization: Bearer <token>
Response (200):

json
{
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "name": "John Doe",
  "role": 3,
  "phone_number": "+1234567890",
  "created_at": "2024-01-15T10:30:00"
}
🏫 School Management
1. Create School
POST /schools

Access: Admin only

Request Body:

json
{
  "school_name": "ABC University",
  "school_dean": "Dr. John Smith"
}
Response (201):

json
{
  "school_id": 1,
  "school_name": "ABC University",
  "school_dean": "Dr. John Smith"
}
2. Get All Schools
GET /schools

Query Parameters:

skip (default: 0) - Pagination offset
limit (default: 100) - Maximum results
Response (200):

json
[
  {
    "school_id": 1,
    "school_name": "ABC University",
    "school_dean": "Dr. John Smith"
  },
  {
    "school_id": 2,
    "school_name": "XYZ College",
    "school_dean": "Dr. Jane Doe"
  }
]
3. Get School by ID
GET /schools/{school_id}

Response (200):

json
{
  "school_id": 1,
  "school_name": "ABC University",
  "school_dean": "Dr. John Smith"
}
4. Update School
PUT /schools/{school_id}

Access: Admin only

Request Body:

json
{
  "school_name": "ABC University Updated",
  "school_dean": "Dr. Jane Smith"
}
5. Delete School
DELETE /schools/{school_id}

Access: Admin only

Response (200):

json
{
  "message": "School 1 deleted successfully"
}
🏢 Department Management
1. Create Department
POST /departments

Access: Admin or School

Request Body:

json
{
  "department_name": "Computer Science",
  "school_id": 1,
  "hod": "Dr. Alan Turing"
}
Response (201):

json
{
  "department_id": 1,
  "department_name": "Computer Science",
  "hod": "Dr. Alan Turing",
  "school_id": 1
}
2. Get All Departments
GET /departments

Query Parameters:

school_id (optional) - Filter by school
skip (default: 0)
limit (default: 100)
Response (200):

json
[
  {
    "department_id": 1,
    "department_name": "Computer Science",
    "hod": "Dr. Alan Turing",
    "school_id": 1
  }
]
3. Update Department
PUT /departments/{department_id}

Request Body:

json
{
  "department_name": "Computer Science & Engineering",
  "hod": "Dr. Grace Hopper"
}
4. Delete Department
DELETE /departments/{department_id}

Access: Admin or School

📚 Class Management
1. Create Class
POST /classes

Access: Admin or School

Request Body:

json
{
  "class_name": "CSE-2024",
  "department_id": 1
}
Response (201):

json
{
  "class_id": 1,
  "class_name": "CSE-2024",
  "department_id": 1
}
2. Get All Classes
GET /classes

Query Parameters:

department_id (optional)
skip (default: 0)
limit (default: 100)
3. Update Class
PUT /classes/{class_id}

4. Delete Class
DELETE /classes/{class_id}

📖 Subject Management
1. Create Subject
POST /subjects

Access: Admin or School

Request Body:

json
{
  "course_code": "CS101",
  "subject_name": "Introduction to Programming",
  "school_id": 1,
  "semester": 1,
  "class_id": 1
}
Response (201):

json
{
  "course_code": "CS101",
  "subject_name": "Introduction to Programming",
  "school_id": 1,
  "semester": 1,
  "class_id": 1
}
2. Get All Subjects
GET /subjects

Query Parameters:

school_id (optional)
class_id (optional)
semester (optional)
skip (default: 0)
limit (default: 100)
3. Get Subject by Course Code
GET /subjects/{course_code}

4. Update Subject
PUT /subjects/{course_code}

Request Body:

json
{
  "subject_name": "Advanced Programming",
  "semester": 2
}
5. Delete Subject
DELETE /subjects/{course_code}

👨‍🏫 Teacher Management
1. Add Teacher
POST /teachers

Access: Admin or School

Request Body:

json
{
  "teacher_name": "John Doe",
  "teacher_email": "john.doe@school.com",
  "school_id": 1,
  "phone_number": "+1234567890"
}
Response (201):

json
{
  "teacher_id": 1,
  "user_id": "123e4567-e89b-12d3-a456-426614174000",
  "school_id": 1,
  "teacher_name": "John Doe",
  "teacher_email": "john.doe@school.com",
  "message": "Teacher added successfully. Credentials sent to email."
}
Note: Password is auto-generated and emailed to the teacher.

2. Get All Teachers
GET /teachers

Access: Admin or School

Query Parameters:

school_id (optional)
skip (default: 0)
limit (default: 100)
Response (200):

json
[
  {
    "teacher_id": 1,
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "school_id": 1,
    "teacher_name": "John Doe",
    "teacher_email": "john.doe@school.com",
    "phone_number": "+1234567890"
  }
]
3. Get Teacher by ID
GET /teachers/{teacher_id}

4. Update Teacher
PUT /teachers/{teacher_id}

Request Body:

json
{
  "teacher_name": "John Doe Updated",
  "phone_number": "+9876543210"
}
5. Delete Teacher
DELETE /teachers/{teacher_id}

Access: Admin or School

👨‍🎓 Student Management
1. Add Student
POST /students

Access: Admin or School

Request Body:

json
{
  "roll_no": "CS2024001",
  "name": "Alice Johnson",
  "email": "alice@student.com",
  "phone_number": "+1234567890",
  "semester": 1,
  "year": 2024,
  "school_id": 1,
  "department_id": 1,
  "photo_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
Response (201):

json
{
  "roll_no": "CS2024001",
  "name": "Alice Johnson",
  "email": "alice@student.com",
  "semester": 1,
  "year": 2024,
  "school_id": 1,
  "department_id": 1,
  "created_at": "2024-01-15T10:30:00",
  "message": "Student added successfully and photo verified in vector database."
}
2. Get All Students
GET /students

Access: Admin or School

Query Parameters:

school_id (optional)
department_id (optional)
semester (optional)
skip (default: 0)
limit (default: 100)
Response (200):

json
[
  {
    "roll_no": "CS2024001",
    "name": "Alice Johnson",
    "email": "alice@student.com",
    "phone_number": "+1234567890",
    "semester": 1,
    "year": 2024,
    "school_id": 1,
    "department_id": 1,
    "created_at": "2024-01-15T10:30:00"
  }
]
3. Get Student by Roll Number
GET /students/{roll_no}

4. Update Student
PUT /students/{roll_no}

Request Body:

json
{
  "name": "Alice Johnson Updated",
  "email": "alice.new@student.com",
  "phone_number": "+9876543210",
  "semester": 2,
  "year": 2024
}
5. Delete Student
DELETE /students/{roll_no}

Access: Admin or School

✅ Attendance System
1. Create Attendance Register
POST /attendance/register

Access: Teacher only

Request Body:

json
{
  "course_code": "CS101",
  "class_id": 1
}
Response (201):

json
{
  "unique_code": "ABC123",
  "course_code": "CS101",
  "class_id": 1,
  "teacher_id": 1,
  "created_at": "2024-01-15T10:30:00",
  "message": "Attendance register created successfully"
}
Note: Share the unique_code with students for attendance marking.

2. Get Attendance Registers
GET /attendance/registers

Access: Teacher only

Query Parameters:

course_code (optional)
skip (default: 0)
limit (default: 100)
Response (200):

json
[
  {
    "unique_code": "ABC123",
    "course_code": "CS101",
    "class_id": 1,
    "teacher_id": 1,
    "created_at": "2024-01-15T10:30:00"
  }
]
3. Get Attendance Register Details
GET /attendance/register/{unique_code}

Access: Teacher only

Response (200):

json
{
  "unique_code": "ABC123",
  "course_code": "CS101",
  "class_id": 1,
  "teacher_id": 1,
  "created_at": "2024-01-15T10:30:00",
  "total_attendance": 25,
  "attendance_logs": [
    {
      "attendance_id": 1,
      "roll_no": "CS2024001",
      "is_manual": false,
      "is_rejected": false,
      "is_proxy": false,
      "created_at": "2024-01-15T10:35:00"
    }
  ]
}
4. Mark Attendance
POST /attendance/mark

Access: Public (no authentication required)

Request Body (Manual Attendance):

json
{
  "unique_code": "ABC123",
  "roll_no": "CS2024001",
  "photo_base64": null
}
Request Body (Photo-based Attendance):

json
{
  "unique_code": "ABC123",
  "roll_no": "CS2024001",
  "photo_base64": "iVBORw0KGgoAAAANSUhEUgAA..."
}
Response (200):

json
{
  "attendance_id": 1,
  "unique_code": "ABC123",
  "roll_no": "CS2024001",
  "is_manual": false,
  "is_proxy": false,
  "created_at": "2024-01-15T10:35:00",
  "message": "Attendance marked successfully"
}
Proxy Detection Response:

json
{
  "attendance_id": 2,
  "unique_code": "ABC123",
  "roll_no": "CS2024002",
  "is_manual": false,
  "is_proxy": true,
  "created_at": "2024-01-15T10:36:00",
  "message": "Warning: Possible proxy detected"
}
5. Get Attendance Logs
GET /attendance/logs

Access: Admin, School, or Teacher

Query Parameters:

unique_code (optional)
roll_no (optional)
skip (default: 0)
limit (default: 100)
Response (200):

json
[
  {
    "attendance_id": 1,
    "unique_code": "ABC123",
    "roll_no": "CS2024001",
    "is_manual": false,
    "is_rejected": false,
    "is_proxy": false,
    "created_at": "2024-01-15T10:35:00"
  }
]
6. Update Attendance Log
PUT /attendance/logs/{attendance_id}

Access: Teacher only

Query Parameters:

is_rejected (boolean) - Mark attendance as rejected
Response (200):

json
{
  "message": "Attendance log updated successfully",
  "attendance_log": {
    "attendance_id": 1,
    "unique_code": "ABC123",
    "roll_no": "CS2024001",
    "is_manual": false,
    "is_rejected": true,
    "is_proxy": false,
    "created_at": "2024-01-15T10:35:00"
  }
}
📊 Reports & Analytics
1. Get Attendance Summary
GET /reports/attendance-summary

Access: Admin, School, or Teacher

Query Parameters:

course_code (optional)
roll_no (optional)
Response (200):

json
{
  "total_attendance": 100,
  "manual_attendance": 30,
  "photo_attendance": 70,
  "proxy_detected": 5,
  "rejected_attendance": 3,
  "course_code": "CS101",
  "roll_no": null
}
2. Get Student Attendance Report
GET /reports/student-attendance/{roll_no}

Access: Admin, School, or Teacher

Response (200):

json
{
  "student_info": {
    "roll_no": "CS2024001",
    "name": "Alice Johnson",
    "email": "alice@student.com",
    "semester": 1,
    "year": 2024
  },
  "total_attendance": 25,
  "manual_attendance": 5,
  "photo_attendance": 20,
  "proxy_detected": 1,
  "rejected": 0,
  "attendance_logs": [
    {
      "attendance_id": 1,
      "unique_code": "ABC123",
      "roll_no": "CS2024001",
      "is_manual": false,
      "is_rejected": false,
      "is_proxy": false,
      "created_at": "2024-01-15T10:35:00"
    }
  ]
}
📋 Activity Logs
Get Activity Logs
GET /activities

Access: Admin only

Query Parameters:

skip (default: 0)
limit (default: 50)
Response (200):

json
[
  {
    "activity_id": 1,
    "activity_name": "add_student",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "roll_no": "CS2024001",
    "created_at": "2024-01-15T10:30:00",
    "updated_at": "2024-01-15T10:30:00"
  },
  {
    "activity_id": 2,
    "activity_name": "add_teacher",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "roll_no": null,
    "created_at": "2024-01-15T10:25:00",
    "updated_at": "2024-01-15T10:25:00"
  }
]
Activity Types:

add_student
add_teacher
remove_teacher
remove_student
update_teacher
update_student
🔍 Health Check
Health Check Endpoint
GET /health

Access: Public

Response (200):

json
{
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
❌ Error Responses
400 Bad Request
json
{
  "detail": "Email already registered"
}
401 Unauthorized
json
{
  "detail": "Could not validate credentials"
}
403 Forbidden
json
{
  "detail": "Access denied. Admin or School role required"
}
404 Not Found
json
{
  "detail": "Student not found"
}
500 Internal Server Error
json
{
  "detail": "Database error: connection failed"
}
📝 Notes
Token Expiration: JWT tokens expire after 30 minutes by default
Pagination: Use skip and limit parameters for large datasets
Base64 Images: Photos should be base64 encoded without data URI prefix
Role Hierarchy: Admin (1) > School (2) > Teacher (3)
Proxy Detection: Confidence threshold is 0.85 (85%)
