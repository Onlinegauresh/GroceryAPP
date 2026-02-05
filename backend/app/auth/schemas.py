"""Pydantic schemas for authentication"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class RoleEnum(str):
    """User role enum"""
    CUSTOMER = "customer"
    STAFF = "staff"
    OWNER = "owner"
    ADMIN = "admin"


class UserBase(BaseModel):
    """Base user schema"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    role: str = Field(default=RoleEnum.CUSTOMER)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, max_length=255)


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class UserResponse(UserBase):
    """Schema for user response"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TokenData(BaseModel):
    """JWT token payload data"""
    sub: str  # user_id
    email: str
    role: str
    exp: Optional[int] = None


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
