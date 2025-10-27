# 🎓 School Management & Attendance System

A comprehensive, production-ready FastAPI application for managing schools, students, teachers, and attendance tracking with facial recognition capabilities.

## 🌟 Features

### Core Functionality
- ✅ **Role-Based Authentication** - JWT-based auth with Admin, School, and Teacher roles
- 🏫 **School Management** - Complete CRUD operations for schools
- 🏢 **Department Management** - Organize departments within schools
- 📚 **Class Management** - Manage classes and sections
- 📖 **Subject Management** - Course and subject administration
- 👨‍🏫 **Teacher Management** - Add teachers with automatic credential generation and email delivery
- 👨‍🎓 **Student Management** - Student profiles with photo verification
- ✅ **Attendance System** - Dual-mode attendance (manual & photo-based)
- 🤖 **Proxy Detection** - AI-powered facial recognition for proxy prevention
- 📊 **Reports & Analytics** - Comprehensive attendance reports and statistics
- 📝 **Activity Logs** - Complete audit trail of all system actions

### Technical Features
- 🚀 **FastAPI Framework** - High-performance async API
- 🗄️ **PostgreSQL Database** - Robust relational database with proper relationships
- 🔐 **JWT Authentication** - Secure token-based authentication
- 📧 **Email Notifications** - Automated credential delivery
- 🎯 **Vector Database Integration** - Face recognition using embeddings
- 📈 **RESTful API** - Well-structured REST endpoints
- 📚 **Auto-generated Documentation** - Swagger/OpenAPI docs
- ✨ **Pydantic Validation** - Strong type checking and validation
- 🔄 **Database Migrations** - Alembic support for schema changes

---

## 📁 Project Structure

```
school-attendance-system/
│
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application and endpoints
│   ├── models.py               # SQLAlchemy database models
│   ├── schemas.py              # Pydantic request/response models
│   ├── database.py             # Database connection and session
│   ├── config.py               # Configuration and environment variables
│   ├── auth.py                 # Authentication and authorization logic
│   ├── utils.py                # Utility functions (passwords, email, etc.)
│   └── vector_db_service.py    # Vector database for face recognition
│
├── alembic/                    # Database migrations (optional)
│   ├── versions/
│   └── env.py
│
├── .env                        # Environment variables (not in git)
├── .env.example                # Environment variables template
├── .gitignore                  # Git ignore file
├── requirements.txt            # Python dependencies
├── test_api.py                 # Automated testing script
├── README.md                   # This file
├── SETUP_GUIDE.md             # Detailed setup instructions
└── API_DOCUMENTATION.md        # Complete API reference

```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- pip
- Virtual environment (recommended)

### Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd school-attendance-system
```

2. **Create and activate virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Set up PostgreSQL database:**
```bash
sudo -u postgres psql
CREATE DATABASE attendance_db;
CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO myuser;
\q
```

5. **Configure environment variables:**
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

6. **Run the application:**
```bash
uvicorn app.main:app --reload
```

7. **Access the API documentation:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📚 Documentation

- **[Setup Guide](SETUP_GUIDE.md)** - Detailed installation and configuration
- **[API Documentation](API_DOCUMENTATION.md)** - Complete API reference with examples
- **[Swagger UI](http://localhost:8000/docs)** - Interactive API documentation (when running)

---

## 🔑 API Overview

### Authentication
```bash
POST /register          # Register new user
POST /login             # Login and get JWT token
GET  /users/me          # Get current user info
```

### School Management (Admin)
```bash
POST   /schools         # Create school
GET    /schools         # Get all schools
GET    /schools/{id}    # Get school by ID
PUT    /schools/{id}    # Update school
DELETE /schools/{id}    # Delete school
```

### Department Management (Admin/School)
```bash
POST   /departments         # Create department
GET    /departments         # Get all departments
GET    /departments/{id}    # Get department by ID
PUT    /departments/{id}    # Update department
DELETE /departments/{id}    # Delete department
```

### Teacher Management (Admin/School)
```bash
POST   /teachers            # Add teacher (auto-generates credentials)
GET    /teachers            # Get all teachers
GET    /teachers/{id}       # Get teacher by ID
PUT    /teachers/{id}       # Update teacher
DELETE /teachers/{id}       # Delete teacher
```

### Student Management (Admin/School)
```bash
POST   /students            # Add student with photo
GET    /students            # Get all students
GET    /students/{roll_no}  # Get student by roll number
PUT    /students/{roll_no}  # Update student
DELETE /students/{roll_no}  # Delete student
```

### Attendance System (Teacher/Students)
```bash
POST /attendance/register           # Create attendance session (Teacher)
GET  /attendance/registers          # Get all registers (Teacher)
POST /attendance/mark               # Mark attendance (Students - no auth)
GET  /attendance/logs               # Get attendance logs
PUT  /attendance/logs/{id}          # Update attendance (reject proxy)
```

### Reports & Analytics
```bash
GET /reports/attendance-summary             # Overall statistics
GET /reports/student-attendance/{roll_no}   # Student-specific report
GET /activities                             # Activity logs (Admin)
```

---

## 🧪 Testing

### Automated Testing
Run the comprehensive test suite:

```bash
python test_api.py
```

This will test all endpoints systematically and provide a detailed report.

### Manual Testing with cURL

**1. Register and Login:**
```bash
# Register
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'

# Login
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'
```

**2. Create School (use token from login):**
```bash
curl -X POST "http://localhost:8000/schools" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"school_name":"Test University","school_dean":"Dr. Test"}'
```

---

## 🗄️ Database Schema

### Core Tables
1. **users** - User accounts with roles
2. **school** - School information
3. **department** - Departments within schools
4. **class** - Classes/sections
5. **subject** - Course subjects
6. **teacher_profile** - Teacher details
7. **student_profile** - Student details
8. **attendance_register** - Attendance sessions
9. **attendance_logs** - Individual attendance records
10. **school_activity** - Audit trail

### Relationships
- School → Departments (1:N)
- Department → Classes (1:N)
- Class → Subjects (1:N)
- School → Teachers (1:N)
- School → Students (1:N)
- Teacher → Attendance Registers (1:N)
- Attendance Register → Attendance Logs (1:N)

---

## 🔒 Security Features

- **JWT Authentication** - Secure token-based auth with expiration
- **Password Hashing** - SHA256 + salt for password storage
- **Role-Based Access Control** - Admin, School, Teacher roles with proper permissions
- **Input Validation** - Pydantic models for request validation
- **SQL Injection Prevention** - SQLAlchemy ORM with parameterized queries
- **Email Verification** - Credential delivery via secure email
- **Activity Logging** - Complete audit trail of all actions

---

## 🤖 Vector Database Integration

The system supports multiple vector database providers for face recognition:

### Supported Providers
- **Qdrant** (Recommended) - Open source, high performance
- **Pinecone** - Cloud-based, managed service
- **Weaviate** - Open source, GraphQL support
- **ChromaDB** - Lightweight, embedded
- **Local Storage** - Fallback for development

### Configuration
Set in `.env`:
```env
VECTOR_DB_PROVIDER=qdrant  # or pinecone, weaviate, chromadb, local
VECTOR_DB_URL=http://localhost:6333
VECTOR_DB_API_KEY=your-api-key
```

### Face Recognition Flow
1. Student photo uploaded → Face embedding generated
2. Embedding stored in vector database with metadata
3. During attendance → Student's face captured
4. Face embedding generated and compared
5. If confidence > 85% → Attendance approved
6. If confidence < 85% → Marked as proxy

---

## 📊 Role Hierarchy

### 1. Admin (role=1)
- Full system access
- Create/manage schools
- Create/manage departments, classes, subjects
- Add/manage teachers and students
- View all reports and activity logs

### 2. School (role=2)
- Manage departments within their school
- Add/manage teachers
- Add/manage students
- View school-specific reports

### 3. Teacher (role=3)
- Create attendance registers
- View attendance logs for their classes
- Mark/reject attendance
- View student reports

---

## 📧 Email Configuration

### Gmail Setup
1. Enable 2-Factor Authentication
2. Generate App Password:
   - Google Account → Security → App Passwords
   - Select "Mail" and generate
3. Add to `.env`:
```env
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
```

### Email Features
- Automatic credential delivery to new teachers
- Attendance reports (optional)
- System notifications (optional)

---

## 🐛 Troubleshooting

### Common Issues

**1. Database Connection Error**
```
Solution: Check PostgreSQL is running and DATABASE_URL is correct
```

**2. Email Sending Fails**
```
Solution: Use Gmail App Password, not regular password
```

**3. Token Expired**
```
Solution: Login again to get a new token (default: 30 min expiry)
```

**4. Face Recognition Not Working**
```
Solution: Ensure vector DB is running and configured properly
```

**5. Port Already in Use**
```
Solution: Kill process or use different port:
uvicorn app.main:app --reload --port 8001
```

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed troubleshooting.

---

## 🔄 Development Workflow

### Adding New Features
1. Define database model in `models.py`
2. Create Pydantic schemas in `schemas.py`
3. Implement endpoints in `main.py`
4. Add authentication/authorization in `auth.py`
5. Update tests in `test_api.py`
6. Document in API_DOCUMENTATION.md

### Database Migrations
```bash
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 📈 Performance Considerations

- **Database Indexing** - Primary keys and foreign keys are indexed
- **Connection Pooling** - SQLAlchemy connection pool configured
- **Async Operations** - FastAPI async support for I/O operations
- **Pagination** - All list endpoints support skip/limit parameters
- **Caching** - Consider Redis for frequently accessed data (future)

---

## 🚀 Deployment

### Production Checklist
- [ ] Change SECRET_KEY to secure random value
- [ ] Update DATABASE_URL with production credentials
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Set up proper logging
- [ ] Enable rate limiting
- [ ] Set up automated backups
- [ ] Configure monitoring and alerts
- [ ] Use production WSGI server (Gunicorn)
- [ ] Set up reverse proxy (Nginx)

### Docker Deployment (Example)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Update documentation
6. Submit a pull request

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 📞 Support

For issues, questions, or contributions:
- GitHub Issues: [Create an issue]
- Email: support@example.com
- Documentation: See SETUP_GUIDE.md and API_DOCUMENTATION.md

---

## 🙏 Acknowledgments

- FastAPI framework by Sebastián Ramírez
- SQLAlchemy ORM
- PostgreSQL database
- Pydantic for data validation
- Community contributors

---

## 📌 Version

**Current Version:** 3.0.0  
**Last Updated:** January 2024

---

**Built with ❤️ for educational institutions worldwide**