"""Authentication routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta

from app.auth.schemas import UserCreate, UserLogin, UserResponse, TokenResponse
from app.auth.service import AuthService
from app.auth.security import (
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from shared.database import get_db
from shared.models import User

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Create a new user account with email, phone, and password"
)
def register(
    user_create: UserCreate,
    db: Session = Depends(get_db)
) -> User:
    """
    Register a new user.

    **Parameters:**
    - name: Full name (1-255 characters)
    - email: Unique email address
    - phone: Unique phone number (9-15 digits)
    - password: Password (minimum 8 characters)
    - role: User role (customer, staff, shop_owner, admin) - defaults to customer
    """
    user = AuthService.create_user(db, user_create)
    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Login with email and password to receive JWT token"
)
def login(
    user_login: UserLogin,
    db: Session = Depends(get_db)
) -> dict:
    """
    Login with email and password.

    Returns JWT access token valid for 24 hours.

    **Parameters:**
    - email: User email
    - password: User password
    """
    user = AuthService.authenticate_user(
        db, user_login.email, user_login.password)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    description="Get authenticated user's profile information"
)
def get_current_user_info(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current authenticated user's information.

    Requires a valid JWT token in the Authorization header:
    `Authorization: Bearer <token>`
    """
    return current_user
