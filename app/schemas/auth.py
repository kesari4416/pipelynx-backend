from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserRegister(BaseModel):
    """User registration schema"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None
    organization_name: str

class UserLogin(BaseModel):
    """User login schema"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Token payload data"""
    sub: Optional[str] = None

class UserResponse(BaseModel):
    """User response schema"""
    id: str
    email: str
    full_name: Optional[str] = None
    organization_id: str
    role: str
    is_active: bool
