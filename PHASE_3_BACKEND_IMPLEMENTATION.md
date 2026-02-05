# SmartKirana AI - PHASE 3: BACKEND IMPLEMENTATION

**Last Updated:** February 4, 2026  
**Status:** In Progress  
**Version:** 1.0  
**Framework:** FastAPI + SQLAlchemy + PostgreSQL

---

## 1. PROJECT STRUCTURE

```
backend/
├── auth_service/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app
│   ├── models.py                # Pydantic schemas
│   ├── routes.py                # Endpoints
│   ├── service.py               # Business logic
│   └── dependencies.py          # JWT verification
│
├── product_service/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── service.py
│   └── schemas.py
│
├── order_service/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── service.py
│   └── invoice_generator.py    # PDF invoice logic
│
├── inventory_service/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── service.py
│   └── alerts.py                # Low-stock alerts
│
├── accounting_service/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   ├── ledger_engine.py         # Double-entry bookkeeping logic
│   ├── gst_calculator.py
│   └── khata_manager.py
│
├── shared/
│   ├── __init__.py
│   ├── config.py                # Settings (DB, auth, etc)
│   ├── database.py              # SQLAlchemy setup
│   ├── models.py                # ORM models (all)
│   ├── schemas.py               # Common Pydantic models
│   ├── security.py              # JWT, hashing
│   ├── exceptions.py            # Custom exceptions
│   ├── middleware.py            # CORS, error handling
│   └── logger.py                # Logging
│
├── api_gateway/
│   ├── __init__.py
│   ├── main.py                  # API Gateway (routes to microservices)
│   └── routes.py
│
├── tests/
│   ├── __init__.py
│   ├── test_auth.py
│   ├── test_products.py
│   ├── test_orders.py
│   ├── conftest.py              # pytest fixtures
│   └── factories.py             # Test data factories
│
├── migrations/
│   ├── versions/                # Alembic migrations
│   └── env.py
│
├── scripts/
│   ├── seed_data.py             # Bootstrap data
│   └── create_shop.py           # CLI to create shop
│
├── docker-compose.yml           # PostgreSQL, Redis, services
├── Dockerfile                   # API container
├── requirements.txt             # Dependencies
├── .env.example                 # Environment variables template
├── main.py                      # API Gateway entry point
└── README.md                    # Setup instructions
```

---

## 2. DEPENDENCIES (requirements.txt)

```
# Core Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database
sqlalchemy==2.0.23
psycopg2-binary==2.9.9          # PostgreSQL adapter
alembic==1.13.1                 # Migrations

# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.5.0
pydantic-settings==2.1.0
PyJWT==2.8.1

# Caching & Queue
redis==5.0.1
celery==5.3.4

# PDF Generation
reportlab==4.0.8                # Simple PDF generation
# OR weasyprint==60.0           # More advanced (slower)

# Data Processing
pandas==2.1.3
numpy==1.26.2

# ML & Analytics
scikit-learn==1.3.2
statsmodels==0.14.0             # ARIMA for forecasting

# Utilities
python-dotenv==1.0.0            # Environment variables
requests==2.31.0
httpx==0.25.2                   # Async HTTP
pydantic-extra-types==2.1.0

# Logging
python-json-logger==2.0.7

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
factory-boy==3.3.0

# Development
black==23.12.0                  # Code formatter
flake8==6.1.0                   # Linter
mypy==1.7.1                     # Type checker
```

---

## 3. CORE CONFIGURATION & SETUP

### 3.1 config.py (Settings)

```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # API
    API_TITLE: str = "SmartKirana AI Backend"
    API_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/smartkirana"
    SQLALCHEMY_ECHO: bool = False  # SQL logging

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
    return Settings()
```

### 3.2 database.py (SQLAlchemy Setup)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import NullPool
from shared.config import get_settings

settings = get_settings()

# Engine configuration
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    poolclass=NullPool if settings.DEBUG else None,
    connect_args={
        "connect_timeout": 10,
        "options": "-c statement_timeout=30000"  # 30s timeout
    }
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.3 security.py (JWT & Hashing)

```python
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from shared.config import get_settings

settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT Tokens
class TokenData(BaseModel):
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
    """Verify JWT token"""
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
    except JWTError:
        raise JWTError("Invalid token")
```

---

## 4. ORM MODELS (SQLAlchemy)

### 4.1 shared/models.py (Key Models)

```python
from sqlalchemy import (
    Column, Integer, String, Numeric, Text, Boolean,
    DateTime, ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database import Base
import enum

# ===== SHOPS =====
class Shop(Base):
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    gst_number = Column(String(15), unique=True)
    pan_number = Column(String(10), unique=True)

    subscription_plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    onboarded_at = Column(DateTime, default=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    users = relationship("User", back_populates="shop")
    products = relationship("Product", back_populates="shop")
    orders = relationship("Order", back_populates="shop")
    ledger_entries = relationship("LedgerEntry", back_populates="shop")

# ===== USERS =====
class RoleEnum(str, enum.Enum):
    CUSTOMER = "customer"
    STAFF = "staff"
    OWNER = "owner"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    phone = Column(String(20), nullable=False)
    email = Column(String(255))
    name = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.CUSTOMER)

    password_hash = Column(String(255))
    otp_secret = Column(String(100))

    address = Column(Text)
    city = Column(String(100))

    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    # Relationships
    shop = relationship("Shop", back_populates="users")

    __table_args__ = (
        UniqueConstraint("shop_id", "phone", name="unique_shop_phone"),
        Index("idx_users_role", "shop_id", "role"),
    )

# ===== PRODUCTS =====
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False)
    barcode = Column(String(50))

    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    unit = Column(String(50), nullable=False)

    cost_price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)

    gst_rate = Column(Numeric(5, 2), default=0)
    hsn_code = Column(String(8))

    current_stock = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=10)
    max_stock_level = Column(Integer)
    reorder_quantity = Column(Integer)

    is_active = Column(Boolean, default=True)
    is_perishable = Column(Boolean, default=False)
    expiry_date = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    # Relationships
    shop = relationship("Shop", back_populates="products")

    __table_args__ = (
        UniqueConstraint("shop_id", "sku", name="unique_shop_sku"),
        Index("idx_products_category", "shop_id", "category"),
    )

# ===== ORDERS =====
class OrderStatusEnum(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PACKED = "packed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PaymentStatusEnum(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"))

    order_number = Column(String(50), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)

    subtotal = Column(Numeric(15, 2), nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)

    payment_method = Column(String(50))
    payment_status = Column(Enum(PaymentStatusEnum), default=PaymentStatusEnum.PENDING)

    order_status = Column(Enum(OrderStatusEnum), default=OrderStatusEnum.PENDING)

    is_credit_sale = Column(Boolean, default=False)
    credit_duration_days = Column(Integer)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shop = relationship("Shop", back_populates="orders")
    items = relationship("OrderItem", back_populates="order")

    __table_args__ = (
        UniqueConstraint("shop_id", "order_number", name="unique_order_number"),
        Index("idx_orders_date", "shop_id", "order_date"),
    )

class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    gst_rate = Column(Numeric(5, 2))
    gst_amount = Column(Numeric(10, 2))

    discount_on_item = Column(Numeric(10, 2), default=0)
    line_total = Column(Numeric(15, 2), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="items")

# ===== INVENTORY =====
class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    movement_type = Column(String(50), nullable=False)  # 'inbound', 'sale', 'adjustment', 'damaged'
    quantity = Column(Integer, nullable=False)  # Can be negative

    reference_type = Column(String(50))  # 'order', 'manual'
    reference_id = Column(Integer)
    notes = Column(Text)

    moved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_stock_movements_product", "shop_id", "product_id", "created_at"),
    )

# ===== ACCOUNTING =====
class LedgerEntry(Base):
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    entry_date = Column(DateTime, nullable=False)
    description = Column(String(500), nullable=False)

    reference_type = Column(String(50))  # 'order', 'purchase', 'manual'
    reference_id = Column(Integer)

    debit_account = Column(String(100), nullable=False)
    debit_amount = Column(Numeric(15, 2), nullable=False)

    credit_account = Column(String(100), nullable=False)
    credit_amount = Column(Numeric(15, 2), nullable=False)

    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship("Shop", back_populates="ledger_entries")

    __table_args__ = (
        Index("idx_ledger_date", "shop_id", "entry_date"),
    )
```

---

## 5. AUTHENTICATION SERVICE

### 5.1 auth_service/routes.py (Endpoints)

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.security import create_access_token, hash_password, verify_password
from shared.models import User, Shop
from pydantic import BaseModel
from datetime import timedelta
import random

router = APIRouter(prefix="/auth", tags=["auth"])

# ===== SCHEMAS =====
class RegisterRequest(BaseModel):
    shop_id: int
    name: str
    phone: str
    email: Optional[str] = None
    role: str = "customer"
    password: Optional[str] = None

class RegisterResponse(BaseModel):
    user_id: int
    phone: str
    name: str
    role: str
    access_token: str
    token_type: str = "bearer"

class LoginRequest(BaseModel):
    shop_id: int
    phone: str
    password: Optional[str] = None
    use_otp: bool = False

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str

class OTPRequest(BaseModel):
    shop_id: int
    phone: str

class OTPVerifyRequest(BaseModel):
    shop_id: int
    phone: str
    otp: str

# ===== ENDPOINTS =====

@router.post("/register", response_model=RegisterResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register new user (customer or staff)"""

    # Check if shop exists
    shop = db.query(Shop).filter(Shop.id == request.shop_id).first()
    if not shop:
        raise HTTPException(status_code=404, detail="Shop not found")

    # Check if user already exists
    existing_user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone
    ).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")

    # Create user
    password_hash = hash_password(request.password) if request.password else None

    user = User(
        shop_id=request.shop_id,
        name=request.name,
        phone=request.phone,
        email=request.email,
        role=request.role,
        password_hash=password_hash,
        is_active=True
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    # Generate token
    access_token = create_access_token(
        user_id=user.id,
        shop_id=user.shop_id,
        role=user.role,
        phone=user.phone
    )

    return RegisterResponse(
        user_id=user.id,
        phone=user.phone,
        name=user.name,
        role=user.role,
        access_token=access_token
    )

@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login with phone + password or OTP"""

    user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Password-based login
    if request.password and not request.use_otp:
        if not verify_password(request.password, user.password_hash or ""):
            raise HTTPException(status_code=401, detail="Invalid password")

    # OTP-based login (simplified - in production, verify OTP)
    if request.use_otp:
        # In real implementation, verify OTP from Redis/DB
        pass

    # Generate token
    access_token = create_access_token(
        user_id=user.id,
        shop_id=user.shop_id,
        role=user.role,
        phone=user.phone
    )

    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role
    )

@router.post("/send-otp")
def send_otp(request: OTPRequest, db: Session = Depends(get_db)):
    """Send OTP to phone (mock implementation)"""

    user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate OTP (in production, store in Redis with expiry)
    otp = "".join([str(random.randint(0, 9)) for _ in range(6)])

    # TODO: Send OTP via SMS (mock for now)
    print(f"OTP for {request.phone}: {otp}")

    return {"message": "OTP sent successfully", "otp_for_testing": otp}

@router.post("/verify-otp", response_model=LoginResponse)
def verify_otp(request: OTPVerifyRequest, db: Session = Depends(get_db)):
    """Verify OTP and return token"""

    user = db.query(User).filter(
        User.shop_id == request.shop_id,
        User.phone == request.phone
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # TODO: Verify OTP from Redis

    access_token = create_access_token(
        user_id=user.id,
        shop_id=user.shop_id,
        role=user.role,
        phone=user.phone
    )

    return LoginResponse(
        access_token=access_token,
        user_id=user.id,
        role=user.role
    )
```

---

## 6. PRODUCT SERVICE

### 6.1 product_service/routes.py (CRUD)

```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.models import Product, User, RoleEnum
from shared.security import verify_token
from shared.exceptions import UnauthorizedException
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

router = APIRouter(prefix="/products", tags=["products"])

# ===== SCHEMAS =====
class ProductCreate(BaseModel):
    name: str
    sku: str
    category: str
    unit: str
    cost_price: Decimal
    mrp: Decimal
    selling_price: Decimal
    gst_rate: Decimal = 0
    hsn_code: Optional[str] = None
    min_stock_level: int = 10
    reorder_quantity: int = 0

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    selling_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    min_stock_level: Optional[int] = None

class ProductResponse(BaseModel):
    id: int
    name: str
    sku: str
    category: str
    selling_price: Decimal
    current_stock: int
    is_active: bool
    gst_rate: Decimal

    class Config:
        from_attributes = True

# ===== HELPER =====
def check_shop_access(token: str, db: Session, required_role: Optional[str] = None):
    """Verify JWT and check shop access"""
    try:
        from shared.security import verify_token
        token_data = verify_token(token)
    except:
        raise UnauthorizedException("Invalid token")

    user = db.query(User).filter(User.id == token_data.user_id).first()
    if not user or user.deleted_at:
        raise UnauthorizedException("User not found")

    if required_role and user.role != required_role:
        raise UnauthorizedException(f"Requires {required_role} role")

    return token_data

# ===== ENDPOINTS =====

@router.get("", response_model=List[ProductResponse])
def list_products(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, le=100)
):
    """List products for a shop (any authenticated user)"""
    token_data = check_shop_access(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    query = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.deleted_at == None,
        Product.is_active == True
    )

    if category:
        query = query.filter(Product.category == category)

    offset = (page - 1) * limit
    products = query.offset(offset).limit(limit).all()

    return products

@router.post("", response_model=ProductResponse)
def create_product(
    shop_id: int,
    request: ProductCreate,
    token: str,
    db: Session = Depends(get_db)
):
    """Create product (owner/staff only)"""
    token_data = check_shop_access(token, db, required_role="owner")

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot create products for other shops")

    # Check SKU uniqueness
    existing = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.sku == request.sku,
        Product.deleted_at == None
    ).first()

    if existing:
        raise HTTPException(status_code=409, detail="SKU already exists")

    product = Product(
        shop_id=shop_id,
        name=request.name,
        sku=request.sku,
        category=request.category,
        unit=request.unit,
        cost_price=request.cost_price,
        mrp=request.mrp,
        selling_price=request.selling_price,
        gst_rate=request.gst_rate,
        hsn_code=request.hsn_code,
        min_stock_level=request.min_stock_level,
        reorder_quantity=request.reorder_quantity
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product

@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    shop_id: int,
    product_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get product details"""
    token_data = check_shop_access(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id,
        Product.deleted_at == None
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    shop_id: int,
    product_id: int,
    request: ProductUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    """Update product (owner only)"""
    token_data = check_shop_access(token, db, required_role="owner")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id,
        Product.deleted_at == None
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update only provided fields
    if request.name:
        product.name = request.name
    if request.selling_price:
        product.selling_price = request.selling_price
    if request.cost_price:
        product.cost_price = request.cost_price
    if request.is_active is not None:
        product.is_active = request.is_active
    if request.min_stock_level:
        product.min_stock_level = request.min_stock_level

    db.commit()
    db.refresh(product)

    return product

@router.delete("/{product_id}")
def delete_product(
    shop_id: int,
    product_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Soft delete product"""
    token_data = check_shop_access(token, db, required_role="owner")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id,
        Product.deleted_at == None
    ).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Soft delete
    from datetime import datetime
    product.deleted_at = datetime.utcnow()

    db.commit()

    return {"message": "Product deleted successfully"}
```

---

## 7. ORDER SERVICE (With Auto-Inventory Deduction)

### 7.1 order_service/service.py (Business Logic)

```python
from sqlalchemy.orm import Session
from shared.models import Order, OrderItem, Product, StockMovement, LedgerEntry
from shared.exceptions import ValidationException
from decimal import Decimal
from datetime import datetime

class OrderService:
    """Business logic for orders"""

    @staticmethod
    def create_order(
        shop_id: int,
        customer_id: int,
        items: list,  # [{"product_id": 1, "quantity": 5}, ...]
        payment_method: str,
        created_by: int,
        is_credit_sale: bool = False,
        credit_duration_days: int = None,
        db: Session = None
    ) -> Order:
        """Create order with automatic inventory deduction"""

        # Validate stock availability
        for item in items:
            product = db.query(Product).filter(
                Product.id == item["product_id"],
                Product.shop_id == shop_id
            ).first()

            if not product:
                raise ValidationException(f"Product {item['product_id']} not found")

            if product.current_stock < item["quantity"]:
                raise ValidationException(
                    f"{product.name} has only {product.current_stock} units, "
                    f"but {item['quantity']} requested"
                )

        # Calculate order amounts
        subtotal = Decimal(0)
        tax_amount = Decimal(0)
        order_items_data = []

        for item in items:
            product = db.query(Product).filter(
                Product.id == item["product_id"]
            ).first()

            unit_price = product.selling_price
            qty = item["quantity"]

            gst_rate = product.gst_rate
            gst_amount = (unit_price * qty * gst_rate) / Decimal(100)
            line_total = (unit_price * qty) + gst_amount

            subtotal += unit_price * qty
            tax_amount += gst_amount

            order_items_data.append({
                "product": product,
                "quantity": qty,
                "unit_price": unit_price,
                "gst_rate": gst_rate,
                "gst_amount": gst_amount,
                "line_total": line_total
            })

        total_amount = subtotal + tax_amount

        # Generate order number
        from datetime import date
        today = date.today()
        order_count = db.query(Order).filter(
            Order.shop_id == shop_id,
            Order.order_date >= f"{today}T00:00:00"
        ).count()
        order_number = f"ORD-{today.strftime('%Y%m%d')}-{order_count + 1:04d}"

        # Create order
        order = Order(
            shop_id=shop_id,
            customer_id=customer_id,
            order_number=order_number,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_method=payment_method,
            created_by=created_by,
            is_credit_sale=is_credit_sale,
            credit_duration_days=credit_duration_days
        )

        db.add(order)
        db.flush()  # Get order.id without committing

        # Add order items
        for item_data in order_items_data:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product"].id,
                shop_id=shop_id,
                product_name=item_data["product"].name,
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                gst_rate=item_data["gst_rate"],
                gst_amount=item_data["gst_amount"],
                line_total=item_data["line_total"]
            )
            db.add(order_item)

        # ===== AUTO-INVENTORY DEDUCTION =====
        for item_data in order_items_data:
            product = item_data["product"]
            quantity = item_data["quantity"]

            # Update product stock
            product.current_stock -= quantity

            # Log stock movement
            movement = StockMovement(
                shop_id=shop_id,
                product_id=product.id,
                movement_type="sale",
                quantity=-quantity,  # Negative for outbound
                reference_type="order",
                reference_id=order.id,
                moved_by=created_by
            )
            db.add(movement)

        # ===== CREATE LEDGER ENTRIES (Double-Entry Bookkeeping) =====
        # Debit: Sales Revenue (increases revenue)
        # Credit: Cash/Bank (decreases cash)

        ledger_entry = LedgerEntry(
            shop_id=shop_id,
            entry_date=datetime.utcnow(),
            description=f"Sale - Order {order_number}",
            reference_type="order",
            reference_id=order.id,
            debit_account="1001",  # Cash account
            debit_amount=total_amount,
            credit_account="4001",  # Sales revenue
            credit_amount=total_amount,
            created_by=created_by
        )
        db.add(ledger_entry)

        # If credit sale, create khata entry (future implementation)
        if is_credit_sale:
            pass  # TODO: Update khata table

        db.commit()
        db.refresh(order)

        return order
```

### 7.1 order_service/routes.py (Endpoints)

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from shared.database import get_db
from pydantic import BaseModel
from typing import List
from order_service.service import OrderService
from shared.exceptions import ValidationException

router = APIRouter(prefix="/orders", tags=["orders"])

class OrderItemRequest(BaseModel):
    product_id: int
    quantity: int

class CreateOrderRequest(BaseModel):
    customer_id: int
    items: List[OrderItemRequest]
    payment_method: str = "cash"
    is_credit_sale: bool = False
    credit_duration_days: int = None

class OrderResponse(BaseModel):
    id: int
    order_number: str
    total_amount: float
    order_status: str
    created_at: str

    class Config:
        from_attributes = True

@router.post("", response_model=OrderResponse)
def create_order(
    shop_id: int,
    request: CreateOrderRequest,
    token: str,
    db: Session = Depends(get_db)
):
    """Create new order with auto inventory deduction"""

    from shared.security import verify_token
    token_data = verify_token(token)

    if token_data.shop_id != shop_id:
        raise HTTPException(status_code=403, detail="Cannot create orders for other shops")

    try:
        order = OrderService.create_order(
            shop_id=shop_id,
            customer_id=request.customer_id,
            items=[{"product_id": item.product_id, "quantity": item.quantity} for item in request.items],
            payment_method=request.payment_method,
            created_by=token_data.user_id,
            is_credit_sale=request.is_credit_sale,
            credit_duration_days=request.credit_duration_days,
            db=db
        )
        return order
    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    shop_id: int,
    order_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get order details"""
    from shared.models import Order
    from shared.security import verify_token
    token_data = verify_token(token)

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.shop_id == shop_id
    ).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order
```

---

## 8. API GATEWAY (Entry Point)

### 8.1 main.py (FastAPI App Setup)

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from shared.config import get_settings
from shared.database import engine, Base
import logging

settings = get_settings()

# Create tables
Base.metadata.create_all(bind=engine)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SmartKirana AI Backend Starting...")
    yield
    logger.info("SmartKirana AI Backend Shutting Down...")

# Initialize FastAPI
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from auth_service.routes import router as auth_router
from product_service.routes import router as product_router
from order_service.routes import router as order_router
from inventory_service.routes import router as inventory_router
from accounting_service.routes import router as accounting_router

app.include_router(auth_router, prefix="/api/v1")
app.include_router(product_router, prefix="/api/v1")
app.include_router(order_router, prefix="/api/v1")
app.include_router(inventory_router, prefix="/api/v1")
app.include_router(accounting_router, prefix="/api/v1")

@app.get("/")
def root():
    return {
        "name": "SmartKirana AI",
        "version": settings.API_VERSION,
        "status": "running"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
```

---

## 9. ROLE-BASED ACCESS CONTROL

### 9.1 shared/exceptions.py

```python
from fastapi import HTTPException, status

class CustomException(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class UnauthorizedException(CustomException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(detail, status_code=status.HTTP_401_UNAUTHORIZED)

class ForbiddenException(CustomException):
    def __init__(self, detail: str = "Forbidden"):
        super().__init__(detail, status_code=status.HTTP_403_FORBIDDEN)

class NotFoundException(CustomException):
    def __init__(self, detail: str = "Not found"):
        super().__init__(detail, status_code=status.HTTP_404_NOT_FOUND)

class ValidationException(CustomException):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
```

### 9.2 RBAC Matrix

| Action           | Customer | Staff | Owner | Admin |
| ---------------- | -------- | ----- | ----- | ----- |
| Browse products  | ✓        | ✓     | ✓     | ✓     |
| Create order     | ✓        | ✓     | ✓     | -     |
| View own orders  | ✓        | ✓     | ✓     | -     |
| View all orders  | -        | ✓     | ✓     | -     |
| Create product   | -        | -     | ✓     | ✓     |
| Update pricing   | -        | -     | ✓     | ✓     |
| View ledger      | -        | -     | ✓     | ✓     |
| Generate reports | -        | -     | ✓     | ✓     |

---

## 10. DOCKER SETUP

### 10.1 docker-compose.yml

```yaml
version: "3.9"

services:
  # PostgreSQL
  db:
    image: postgres:16
    environment:
      POSTGRES_USER: smartkirana
      POSTGRES_PASSWORD: secure_password_change_me
      POSTGRES_DB: smartkirana
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U smartkirana"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Redis
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  backend:
    build: .
    environment:
      DATABASE_URL: postgresql://smartkirana:secure_password_change_me@db:5432/smartkirana
      REDIS_URL: redis://redis:6379
      SECRET_KEY: ${SECRET_KEY:-change-in-production}
      DEBUG: ${DEBUG:-false}
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    volumes:
      - .:/app
    command: uvicorn main:app --host 0.0.0.0 --reload

volumes:
  postgres_data:
  redis_data:
```

### 10.2 .env.example

```bash
# Database
DATABASE_URL=postgresql://smartkirana:password@localhost:5432/smartkirana

# Redis
REDIS_URL=redis://localhost:6379

# JWT
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# API
DEBUG=true
API_TITLE=SmartKirana AI Backend

# SMS/Email (mockable)
EMAIL_BACKEND=mock
SMS_BACKEND=mock

# AI
FORECAST_DAYS=30
FORECAST_MIN_HISTORY_DAYS=90
```

---

## 11. LOCAL DEVELOPMENT SETUP

### Quick Start

```bash
# 1. Clone and setup
git clone <repo>
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Setup environment
cp .env.example .env

# 4. Start Docker services
docker-compose up -d

# 5. Run migrations
alembic upgrade head

# 6. Seed data
python scripts/seed_data.py

# 7. Start FastAPI
python main.py

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

---

## 12. API EXAMPLES

### Register

```bash
POST /api/v1/auth/register
{
  "shop_id": 1,
  "name": "Rajesh Kumar",
  "phone": "9876543210",
  "email": "rajesh@kirana.local",
  "role": "customer",
  "password": "secure_password"
}
```

### Create Product

```bash
POST /api/v1/products?shop_id=1
Authorization: Bearer <token>
{
  "name": "Basmati Rice 1kg",
  "sku": "RIC-001",
  "category": "Rice",
  "unit": "kg",
  "cost_price": 50.00,
  "mrp": 80.00,
  "selling_price": 75.00,
  "gst_rate": 5,
  "min_stock_level": 10,
  "reorder_quantity": 50
}
```

### Create Order

```bash
POST /api/v1/orders?shop_id=1
Authorization: Bearer <token>
{
  "customer_id": 5,
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 2, "quantity": 1}
  ],
  "payment_method": "cash"
}
```

---

## PHASE 3 PROGRESS ✓ (Partial)

**Completed:**
✓ FastAPI project structure  
✓ Database models (SQLAlchemy)  
✓ Authentication (JWT, OTP framework)  
✓ Product CRUD  
✓ Order creation with auto-inventory deduction  
✓ Ledger entry creation (accounting)  
✓ RBAC framework  
✓ Docker setup

**Still Needed (Will be automated):**

- Invoice PDF generation
- Inventory alerts
- GST calculation
- Khata management
- Complete accounting service
- AI forecasting endpoints
- Testing & validation

**Next Phase:** PHASE 4 – ACCOUNTING ENGINE (Tally-like features)

---

**Status:** Ready for accounting implementation  
**Review Date:** Feb 4, 2026
