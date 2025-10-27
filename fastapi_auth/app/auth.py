from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from typing import List
from . import models, utils
from .config import SECRET_KEY, ALGORITHM, UserRole

security = HTTPBearer()

# ============================================
# USER AUTHENTICATION
# ============================================
def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def authenticate_user(db: Session, email: str, password: str):
    """Authenticate user with email and password"""
    user = get_user_by_email(db, email)
    if not user or not utils.verify_password(password, user.password_hash):
        return False
    return user

async def get_current_user_simple(token: str, db: Session):
    """Get current user from Bearer token - simplified"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_email(db, email=email)
    if user is None:
        raise credentials_exception
    return user


# ============================================
# ROLE-BASED ACCESS CONTROL
# ============================================
def verify_user_role(user: models.User, allowed_roles: List[int]) -> bool:
    """
    Verify if user has one of the allowed roles
    
    Args:
        user: User model instance
        allowed_roles: List of allowed role IDs
    
    Returns:
        bool: True if user has allowed role, False otherwise
    """
    return user.role in allowed_roles


async def get_current_user_with_role(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = None,
    allowed_roles: List[int] = None
):
    """
    Dependency to get current user and verify role
    
    Usage:
        @app.post("/add-teacher")
        def add_teacher(
            user: models.User = Depends(lambda c, d: get_current_user_with_role(c, d, [1, 2]))
        ):
            # Only Admin (1) and School (2) can access
            pass
    """
    token = credentials.credentials
    user = await get_current_user_simple(token, db)
    
    if allowed_roles and not verify_user_role(user, allowed_roles):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required roles: {allowed_roles}. Your role: {user.role}"
        )
    
    return user


def require_admin_or_school(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = None
):
    """
    Dependency to require Admin (1) or School (2) role
    """
    return get_current_user_with_role(
        credentials,
        db,
        allowed_roles=[UserRole.ADMIN, UserRole.SCHOOL]
    )


def require_admin_only(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = None
):
    """
    Dependency to require Admin (1) role only
    """
    return get_current_user_with_role(
        credentials,
        db,
        allowed_roles=[UserRole.ADMIN]
    )


# ============================================
# HELPER FUNCTIONS
# ============================================
def get_user_role_name(role: int) -> str:
    """Get human-readable role name"""
    role_names = {
        UserRole.ADMIN: "Admin",
        UserRole.SCHOOL: "School",
        UserRole.TEACHER: "Teacher"
    }
    return role_names.get(role, "Unknown")