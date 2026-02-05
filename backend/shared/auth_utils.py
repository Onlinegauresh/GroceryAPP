"""Authentication utilities - Password hashing and session management"""
from passlib.context import CryptContext
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Password hashing setup - Use argon2 as primary scheme (no bcrypt version issues)
pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_session_user(request) -> Optional[Dict[str, Any]]:
    """Get authenticated user from session"""
    try:
        user_id = request.session.get("user_id")
        role = request.session.get("role")
        full_name = request.session.get("full_name")

        if user_id and role:
            return {
                "user_id": user_id,
                "role": role,
                "full_name": full_name
            }
    except:
        pass
    return None


def set_session_user(request, user_id: int, role: str, full_name: str):
    """Set authenticated user in session"""
    request.session["user_id"] = user_id
    request.session["role"] = role
    request.session["full_name"] = full_name


def clear_session_user(request):
    """Clear authenticated user from session"""
    try:
        request.session.clear()
    except:
        pass


def is_customer(request) -> bool:
    """Check if user is authenticated as customer"""
    user = get_session_user(request)
    return user is not None and user.get("role") == "customer"


def is_admin(request) -> bool:
    """Check if user is authenticated as admin"""
    user = get_session_user(request)
    return user is not None and user.get("role") == "admin"
