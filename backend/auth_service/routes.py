"""Authentication routes and endpoints"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import random

from shared.database import get_db
from shared.models import User, Shop, RoleEnum
from shared.security import (
    create_access_token, hash_password, verify_password, verify_token
)
from shared.exceptions import UnauthorizedException, ValidationException, ConflictException

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ===== REQUEST/RESPONSE SCHEMAS =====
class RegisterRequest(BaseModel):
    """User registration request"""
    shop_id: int
    name: str
    phone: str
    email: Optional[str] = None
    password: Optional[str] = None
    role: str = "customer"


class RegisterResponse(BaseModel):
    """Registration response"""
    user_id: int
    phone: str
    name: str
    role: str
    access_token: str
    token_type: str = "bearer"

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    """Login request"""
    shop_id: int
    phone: str
    password: Optional[str] = None


class LoginResponse(BaseModel):
    """Login response"""
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    shop_id: int


class OTPRequest(BaseModel):
    """OTP request"""
    shop_id: int
    phone: str


class OTPVerifyRequest(BaseModel):
    """OTP verification request"""
    shop_id: int
    phone: str
    otp: str


class MeResponse(BaseModel):
    """Current user info response"""
    user_id: int
    phone: str
    name: str
    email: Optional[str]
    role: str
    shop_id: int

    class Config:
        from_attributes = True


# ===== ENDPOINTS =====

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register new user (customer or staff).

    - **shop_id**: ID of the shop
    - **name**: User's full name
    - **phone**: 10-digit phone number
    - **password**: Optional password (can use OTP instead)
    """

    # Check if shop exists
    shop = db.query(Shop).filter(Shop.id == request.shop_id,
                                 Shop.deleted_at == None).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Check if user already exists
    existing_user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone,
        User.deleted_at == None
    ).first()
    if existing_user:
        raise ConflictException(
            f"User with phone {request.phone} already exists in this shop")

    # Create user
    password_hash = hash_password(
        request.password) if request.password else None

    user = User(
        shop_id=request.shop_id,
        name=request.name,
        phone=request.phone,
        email=request.email,
        role=RoleEnum(request.role),
        password_hash=password_hash,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate access token
    access_token = create_access_token(
        user_id=user.id,
        shop_id=user.shop_id,
        role=user.role.value,
        phone=user.phone
    )

    return RegisterResponse(
        user_id=user.id,
        phone=user.phone,
        name=user.name,
        role=user.role.value,
        access_token=access_token
    )


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with phone and password.

    - **shop_id**: ID of the shop
    - **phone**: User's phone number
    - **password**: User's password
    """

    # Find user
    user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone,
        User.deleted_at == None,
        User.is_active == True
    ).first()

    if not user:
        raise UnauthorizedException("Invalid phone or shop ID")

    # Verify password
    if not user.password_hash or not verify_password(request.password or "", user.password_hash):
        raise UnauthorizedException("Invalid password")

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Generate token
    access_token = create_access_token(
        user_id=user.id,
        shop_id=user.shop_id,
        role=user.role.value,
        phone=user.phone
    )

    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role.value,
        shop_id=user.shop_id
    )


@router.post("/send-otp")
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """
    Send OTP to user's phone (mock implementation).

    In production, integrate with SMS provider (Twilio, AWS SNS, etc).
    """

    # Check if shop exists
    shop = db.query(Shop).filter(Shop.id == request.shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Find or create user
    user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone
    ).first()

    # Generate OTP (6 digits)
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])

    # TODO: In production, store OTP in Redis with 10-minute expiry
    # redis_client.setex(f"otp:{request.shop_id}:{request.phone}", 600, otp)

    # TODO: Send OTP via SMS
    # sms_service.send(request.phone, f"Your OTP is {otp}")

    return {
        "message": "OTP sent successfully",
        "otp_for_testing": otp  # Remove in production
    }


@router.post("/verify-otp", response_model=LoginResponse)
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """
    Verify OTP and login user.

    - **shop_id**: ID of the shop
    - **phone**: User's phone number
    - **otp**: 6-digit OTP received via SMS
    """

    # TODO: Verify OTP from Redis
    # stored_otp = redis_client.get(f"otp:{request.shop_id}:{request.phone}")
    # if not stored_otp or stored_otp != request.otp:
    #     raise UnauthorizedException("Invalid or expired OTP")

    # For now, accept any OTP for testing
    if len(request.otp) != 6 or not request.otp.isdigit():
        raise ValidationException("Invalid OTP format")

    # Find user or create new
    user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone,
        User.deleted_at == None
    ).first()

    if not user:
        raise HTTPException(
            status_code=404, detail="User not found. Please register first.")

    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()

    # Generate token
    access_token = create_access_token(
        user_id=user.id,
        shop_id=user.shop_id,
        role=user.role.value,
        phone=user.phone
    )

    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role.value,
        shop_id=user.shop_id
    )


@router.get("/me", response_model=MeResponse)
def get_current_user(
    token: str,
    db: Session = Depends(get_db)
):
    """Get current authenticated user's information"""

    # Verify token
    try:
        token_data = verify_token(token)
    except Exception as e:
        raise UnauthorizedException(str(e))

    # Get user
    user = db.query(User).filter(
        User.id == token_data.user_id,
        User.deleted_at == None
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return MeResponse(
        user_id=user.id,
        phone=user.phone,
        name=user.name,
        email=user.email,
        role=user.role.value,
        shop_id=user.shop_id
    )
