from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# ============================================
# PostgreSQL Engine Configuration
# ============================================
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # Check connection health before using
    pool_size=10,               # Connection pool size
    max_overflow=20,            # Max connections beyond pool_size
    echo=False                  # Set True for SQL query logging (dev only)
)

# ============================================
# Session Factory
# ============================================
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# ============================================
# Base Class for Models
# ============================================
Base = declarative_base()

# ============================================
# Database Dependency (for FastAPI)
# ============================================
def get_db():
    """
    Database session dependency for FastAPI endpoints.
    Automatically closes connection after request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
