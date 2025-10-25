import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================
# JWT Configuration
# ============================================
SECRET_KEY = os.getenv(
    "SECRET_KEY", 
    "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"  # Change this!
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# ============================================
# Database Configuration - PostgreSQL (Supabase)
# ============================================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    # Fallback for local testing (update with your actual credentials)
    "postgresql://postgres:password@localhost:5432/attendance_db"
)

# ============================================
# Environment Info
# ============================================
ENV = os.getenv("ENV", "development")  # development, production
DEBUG = ENV == "development"
