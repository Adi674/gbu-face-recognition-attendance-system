from pydantic import BaseModel, EmailStr, ConfigDict, validator
from datetime import datetime
from typing import Optional
import uuid

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password cannot be longer than 72 bytes')
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    user_id: uuid.UUID
    email: str
    name: str
    role: int
    created_at: datetime

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None