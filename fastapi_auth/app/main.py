from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta

# Local imports
from . import models, schemas, utils, auth
from .database import Base, engine, get_db
from .config import ACCESS_TOKEN_EXPIRE_MINUTES

# Change OAuth2 to simple Bearer token
security = HTTPBearer()

app = FastAPI(
    title="FastAPI Authentication System",
    version="1.0.1",
    description="A simple user authentication system using FastAPI and SQLAlchemy"
)

@app.on_event("startup")
def startup():
    """Create all database tables on startup."""
    print("✅ Database initialized successfully!")

@app.get("/", summary="API root")
def root():
    return {
        "message": "🚀 FastAPI Authentication System is running!",
        "routes": {
            "register": "POST /register",
            "login": "POST /login",
            "me": "GET /users/me (Bearer token required)"
        }
    }

@app.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """Register a new user with email and password only."""
    
    # Check if email already exists
    if auth.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )

    # Hash password and create user
    hashed_password = utils.get_password_hash(user_data.password)
    new_user = models.User(
        email=user_data.email,
        password_hash=hashed_password,
        role=3,  # Default role: teacher
        name=user_data.email.split('@')[0]  # Use email prefix as name
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Database error: {str(e)}"
        )

    return new_user

# Simple JSON login - no OAuth2 form complexity
@app.post(
    "/login",
    response_model=schemas.Token,
    summary="Login with email and password (JSON)"
)
def login(user_credentials: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Simple login with JSON body containing email and password.
    """
    user = auth.authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.get(
    "/users/me",
    response_model=schemas.UserResponse,
    summary="Get current user (Bearer token required)"
)
async def read_users_me(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """
    Get current user info using Bearer token.
    """
    token = credentials.credentials
    user = await auth.get_current_user_simple(token, db)
    return user

@app.get("/health", summary="Health check")
def health_check():
    return {"status": "healthy", "service": "FastAPI Authentication System"}