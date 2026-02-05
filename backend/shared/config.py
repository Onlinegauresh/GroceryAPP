"""Application configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # API
    API_TITLE: str = "SmartKirana AI Backend"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database (SQLite for local development, PostgreSQL for production)
    DATABASE_URL: str = "sqlite:///./smartkirana.db"
    SQLALCHEMY_ECHO: bool = True

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # OTP
    OTP_EXPIRE_MINUTES: int = 10
    OTP_LENGTH: int = 6
    OTP_DIGITS_ONLY: bool = True

    # Email (if implemented)
    EMAIL_ENABLED: bool = False
    EMAIL_BACKEND: str = "mock"  # 'mock', 'smtp'

    # SMS (if implemented)
    SMS_ENABLED: bool = False
    SMS_BACKEND: str = "mock"  # 'mock', 'twilio'

    # AI/ML
    FORECAST_DAYS: int = 30
    FORECAST_MIN_HISTORY_DAYS: int = 90
    ANOMALY_DETECTION_ENABLED: bool = True

    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    """Get cached settings instance"""
    return Settings()
