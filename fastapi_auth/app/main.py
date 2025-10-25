from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from . import models, schemas, utils, auth
from .database import Base, engine, get_db
from .config import ACCESS_TOKEN_EXPIRE_MINUTES

app = FastAPI(title="FastAPI Authentication", version="1.0.0")

# ------------------- Startup Event -------------------
@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

# ------------------- Register Endpoint -------------------
@app.post("/register", response_model=schemas.UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
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

# ------------------- Login Endpoint -------------------
@app.post("/login", response_model=schemas.Token)
def login(form_data: schemas.UserCreate, db: Session = Depends(get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(data={"sub": user.username}, expires_delta=expires)
    return {"access_token": access_token, "token_type": "bearer"}

# ------------------- Current User -------------------
@app.get("/users/me", response_model=schemas.UserResponse)
async def read_users_me(current_user=Depends(auth.get_current_user)):
    return current_user

# ------------------- Root -------------------
@app.get("/")
def root():
    return {
        "message": "FastAPI Authentication System",
        "routes": {
            "register": "POST /register",
            "login": "POST /login",
            "me": "GET /users/me (auth required)"
        }
    }
