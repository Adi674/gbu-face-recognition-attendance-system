import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# JWT CONFIGURATION
# ============================================
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-this-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ============================================
# DATABASE CONFIGURATION
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://myuser:mypassword@localhost:5432/attendance_db"
)

# ============================================
# EMAIL SMTP CONFIGURATION
# ============================================
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "your-email@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")

# ============================================
# VECTOR DATABASE CONFIGURATION
# ============================================
VECTOR_DB_URL = os.getenv("VECTOR_DB_URL", "http://localhost:6333")
VECTOR_DB_API_KEY = os.getenv("VECTOR_DB_API_KEY", "")
VECTOR_COLLECTION_NAME = os.getenv("VECTOR_COLLECTION_NAME", "student_faces")

# ============================================
# ROLE DEFINITIONS
# ============================================
class UserRole:
    ADMIN = 1
    SCHOOL = 2
    TEACHER = 3
