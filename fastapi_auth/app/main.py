from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

# Absolute imports
from . import models
from . import schemas
from . import utils
from . import auth
from .database import Base, engine, get_db
from .config import ACCESS_TOKEN_EXPIRE_MINUTES
# --------------------------------------------------------
# Initialize FastAPI App
# --------------------------------------------------------
app = FastAPI(
    title="FastAPI Authentication",
    version="1.0.1",
    description="A simple user authentication system using FastAPI and SQLAlchemy"
)

# --------------------------------------------------------
# Startup Event → Create Database Tables
# --------------------------------------------------------
@app.on_event("startup")
def startup():
    """
    Create all database tables on startup.
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

# --------------------------------------------------------
# Register Endpoint
# --------------------------------------------------------
@app.post(
    "/register",
    response_model=schemas.UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user in the system.
    
    Checks if username or email already exists, hashes the password, 
    and stores the new user in the database.
    """
    if auth.get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    if auth.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = utils.get_password_hash(user_data.password)
    new_user = models.User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return new_user

# --------------------------------------------------------
# Login Endpoint
# --------------------------------------------------------
@app.post(
    "/login",
    response_model=schemas.Token,
    summary="Authenticate user and get JWT token"
)
def login(form_data: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.
    """
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# --------------------------------------------------------
# Current Logged-in User Endpoint
# --------------------------------------------------------
@app.get(
    "/users/me",
    response_model=schemas.UserResponse,
    summary="Get current logged-in user"
)
async def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    """
    Return details of the currently authenticated user.
    """
    return current_user

# --------------------------------------------------------
# API Root Endpoint
# --------------------------------------------------------
@app.get("/", summary="API root")
def root():
    """
    Root endpoint with API routes overview.
    """
    return {
        "message": "🚀 FastAPI Authentication System is running!",
        "routes": {
            "register": "POST /register",
            "login": "POST /login",
            "me": "GET /users/me (auth required)"
        }
    }
