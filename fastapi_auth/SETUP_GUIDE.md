🚀 School Management & Attendance System - Complete Setup Guide
📋 Table of Contents
Prerequisites
Database Setup
Environment Configuration
Installation Steps
Vector Database Setup
Running the Application
API Testing
Troubleshooting
🔧 Prerequisites
Required Software
Python 3.9+ (recommended: 3.10 or 3.11)
PostgreSQL 13+ (recommended: 14 or 15)
pip (Python package manager)
Git (for version control)
Optional Software
Postman or Thunder Client (for API testing)
pgAdmin (PostgreSQL GUI)
Docker (optional, for containerization)
🗄️ Database Setup
Step 1: Install PostgreSQL
On Ubuntu/Debian:

bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
On macOS (using Homebrew):

bash
brew install postgresql@15
brew services start postgresql@15
On Windows: Download and install from PostgreSQL Official Website

Step 2: Create Database and User
bash
# Switch to postgres user
sudo -u postgres psql

# Inside PostgreSQL shell:
CREATE DATABASE attendance_db;
CREATE USER myuser WITH ENCRYPTED PASSWORD 'mypassword';
GRANT ALL PRIVILEGES ON DATABASE attendance_db TO myuser;

# Grant schema privileges
\c attendance_db
GRANT ALL ON SCHEMA public TO myuser;

# Exit
\q
Step 3: Verify Database Connection
bash
psql -U myuser -d attendance_db -h localhost
# Enter password when prompted
⚙️ Environment Configuration
Step 1: Create .env File
Create a .env file in your project root:

bash
# Copy from .env.example
cp .env.example .env
Step 2: Configure Environment Variables
Edit .env file with your actual credentials:

env
# JWT Configuration
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars

# Database Configuration
DATABASE_URL=postgresql://myuser:mypassword@localhost:5432/attendance_db

# SMTP Email Configuration (Gmail example)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_EMAIL=your-email@gmail.com
SMTP_PASSWORD=your-gmail-app-password

# Vector Database Configuration (Optional)
VECTOR_DB_PROVIDER=local
VECTOR_DB_URL=http://localhost:6333
VECTOR_DB_API_KEY=
VECTOR_COLLECTION_NAME=student_faces
Step 3: Generate Secret Key
python
# Run this in Python shell to generate a secure secret key
import secrets
print(secrets.token_urlsafe(32))
Step 4: Gmail SMTP Setup (for Email Features)
Go to Google Account Settings
Enable 2-Factor Authentication
Go to App Passwords
Create a new app password for "Mail"
Use this 16-character password in .env as SMTP_PASSWORD
📦 Installation Steps
Step 1: Clone Repository (if applicable)
bash
git clone <your-repository-url>
cd school-attendance-system
Step 2: Create Virtual Environment
bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
Step 3: Install Dependencies
bash
# Install all required packages
pip install -r requirements.txt

# If you encounter issues, upgrade pip first:
pip install --upgrade pip
Step 4: Verify Installation
bash
pip list | grep fastapi
pip list | grep sqlalchemy
pip list | grep psycopg2
🤖 Vector Database Setup (Optional but Recommended)
Option 1: Qdrant (Recommended)
Using Docker:

bash
docker pull qdrant/qdrant
docker run -p 6333:6333 qdrant/qdrant
Update .env:

env
VECTOR_DB_PROVIDER=qdrant
VECTOR_DB_URL=http://localhost:6333
Install Python Client:

bash
pip install qdrant-client
Option 2: Pinecone (Cloud-based)
Sign up at Pinecone.io
Get API key from dashboard
Update .env:
env
VECTOR_DB_PROVIDER=pinecone
VECTOR_DB_API_KEY=your-pinecone-api-key
Install Python Client:

bash
pip install pinecone-client
Option 3: ChromaDB (Lightweight)
Install:

bash
pip install chromadb
Update .env:

env
VECTOR_DB_PROVIDER=chromadb
Option 4: Local Storage (No Setup Required)
Update .env:

env
VECTOR_DB_PROVIDER=local
Face Recognition Library Setup
For face_recognition library:

bash
# Install dependencies
# On Ubuntu:
sudo apt install cmake libboost-all-dev

# On macOS:
brew install cmake boost

# Install face_recognition
pip install face_recognition
🏃 Running the Application
Step 1: Initialize Database
bash
# The database tables will be created automatically on first run
# But you can also use Alembic for migrations:

# Initialize Alembic (optional)
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial migration"

# Apply migration
alembic upgrade head
Step 2: Start the Server
bash
# Development mode (with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Step 3: Verify Server is Running
Open your browser and navigate to:

API Docs (Swagger): http://localhost:8000/docs
Alternative API Docs (ReDoc): http://localhost:8000/redoc
Health Check: http://localhost:8000/health
🧪 API Testing
Using Swagger UI (Recommended for Beginners)
Navigate to http://localhost:8000/docs
Click on any endpoint to expand
Click "Try it out"
Fill in the parameters
Click "Execute"
Using cURL
1. Register a User
bash
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@school.com",
    "password": "admin123"
  }'
2. Login
bash
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@school.com",
    "password": "admin123"
  }'
Save the access_token from the response.

3. Create a School (Admin only)
bash
curl -X POST "http://localhost:8000/schools" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "school_name": "ABC University",
    "school_dean": "Dr. John Doe"
  }'
Using Postman
Create a new collection
Set base URL: http://localhost:8000
Add authorization header: Bearer YOUR_ACCESS_TOKEN
Import the API schema from /docs (OpenAPI/Swagger JSON)
🔍 Troubleshooting
Database Connection Issues
Error: psycopg2.OperationalError: connection failed

Solution:

bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify credentials
psql -U myuser -d attendance_db -h localhost

# Check DATABASE_URL in .env
echo $DATABASE_URL
Import Errors
Error: ModuleNotFoundError: No module named 'fastapi'

Solution:

bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
Email Sending Fails
Error: SMTPAuthenticationError

Solution:

Enable 2FA on Gmail
Generate App Password
Update SMTP_PASSWORD in .env with app password (not regular password)
Check SMTP_SERVER and SMTP_PORT are correct
Port Already in Use
Error: OSError: [Errno 48] Address already in use

Solution:

bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn app.main:app --reload --port 8001
Face Recognition Issues
Error: No face detected in image

Solutions:

Ensure image quality is good (minimum 200x200 pixels)
Face should be clearly visible and well-lit
Image should be front-facing
Try with a different photo
📊 Database Schema Verification
sql
-- Connect to database
psql -U myuser -d attendance_db

-- List all tables
\dt

-- Expected tables:
-- users
-- school
-- department
-- class
-- subject
-- teacher_profile
-- student_profile
-- attendance_register
-- attendance_logs
-- school_activity

-- Check a table structure
\d users
🎯 Quick Start Testing Flow
bash
# 1. Start server
uvicorn app.main:app --reload

# 2. Register admin user (in another terminal)
curl -X POST "http://localhost:8000/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'

# 3. Login and get token
curl -X POST "http://localhost:8000/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.com","password":"admin123"}'

# 4. Use the token to access protected endpoints
# Copy the access_token from step 3 and use in Authorization header
🔒 Security Best Practices
Change Default Credentials - Never use default passwords in production
Use Strong SECRET_KEY - Generate a secure random key
Enable HTTPS - Use SSL/TLS in production
Restrict CORS - Configure allowed origins
Rate Limiting - Implement request rate limiting
Input Validation - Always validate and sanitize user input
Regular Backups - Set up automated database backups
📚 Additional Resources
FastAPI Documentation
SQLAlchemy Documentation
PostgreSQL Documentation
Pydantic Documentation
JWT Documentation
🆘 Getting Help
If you encounter issues:

Check the error logs
Verify all environment variables
Ensure all services are running
Check the Troubleshooting section
Review API documentation at /docs
