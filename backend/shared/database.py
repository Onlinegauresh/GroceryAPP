"""Database setup and session management"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker
from shared.config import get_settings

settings = get_settings()

# Engine configuration
engine_kwargs = {
    "echo": settings.SQLALCHEMY_ECHO,
}

# Add SQLite-specific settings if using SQLite
if "sqlite" in settings.DATABASE_URL:
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["connect_args"] = {"connect_timeout": 10}

engine = create_engine(settings.DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency for FastAPI - provides database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
