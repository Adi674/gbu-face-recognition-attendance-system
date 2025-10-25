from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# ------------------ User schemas ------------------

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        orm_mode = True  # Fixed from_attributes -> orm_mode

# ------------------ Token schemas ------------------

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None
