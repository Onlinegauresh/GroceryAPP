"""JWT and password security utilities"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from shared.config import get_settings
import hashlib
import secrets

settings = get_settings()

# Password hashing context - Use argon2 which is more compatible
try:
    pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
except:
    # Fallback to plain hasher for compatibility
    pwd_context = None


def hash_password(password: str) -> str:
    """Hash password using argon2 or SHA-256 with salt"""
    if pwd_context:
        return pwd_context.hash(password)
    else:
        # Fallback: PBKDF2-style hashing
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256', password.encode(), salt.encode(), 100000)
        return f"pbkdf2_sha256${salt}${pwd_hash.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify plain password against hashed password"""
    if not hashed_password:
        return False
    try:
        if pwd_context:
            return pwd_context.verify(plain_password, hashed_password)
        else:
            # Fallback: PBKDF2-style verification
            if hashed_password.startswith("pbkdf2_sha256$"):
                parts = hashed_password.split("$")
                if len(parts) != 3:
                    return False
                salt, stored_hash = parts[1], parts[2]
                pwd_hash = hashlib.pbkdf2_hmac(
                    'sha256', plain_password.encode(), salt.encode(), 100000)
                return pwd_hash.hex() == stored_hash
            return False
    except:
        return False


# JWT Token models
class TokenData(BaseModel):
    """JWT token payload"""
    user_id: int
    shop_id: int
    role: str
    phone: str
    exp: Optional[datetime] = None


def create_access_token(
    user_id: int,
    shop_id: int,
    role: str,
    phone: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "user_id": user_id,
        "shop_id": shop_id,
        "role": role,
        "phone": phone,
        "exp": expire
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """Verify JWT token and extract payload"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id = payload.get("user_id")
        shop_id = payload.get("shop_id")
        role = payload.get("role")
        phone = payload.get("phone")

        if user_id is None or shop_id is None:
            raise JWTError("Invalid token payload")

        return TokenData(
            user_id=user_id,
            shop_id=shop_id,
            role=role,
            phone=phone
        )
    except JWTError as e:
        raise JWTError(f"Invalid token: {str(e)}")
