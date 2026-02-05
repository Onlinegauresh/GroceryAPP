# SmartKirana AI – Authentication & RBAC Implementation Guide

## Overview

This document outlines the complete Authentication and Role-Based Access Control (RBAC) system implemented for SmartKirana AI.

**Key Features:**

- ✅ JWT-based authentication
- ✅ Bcrypt password hashing (12 rounds)
- ✅ 4-tier role system (Customer, Staff, Shop Owner, Admin)
- ✅ Endpoint-level access control
- ✅ OAuth2 password flow
- ✅ 24-hour token expiry
- ✅ Stateless, scalable architecture

---

## Architecture

### User Roles

| Role           | Description          | Permissions                                   |
| -------------- | -------------------- | --------------------------------------------- |
| **CUSTOMER**   | Regular buyer        | Read products, view profile                   |
| **STAFF**      | Shop employee        | Read products, manage inventory, view reports |
| **SHOP_OWNER** | Business owner       | Full product CRUD, inventory, accounting      |
| **ADMIN**      | System administrator | All permissions, user management              |

### Authentication Flow

```
1. User Registration (POST /api/v1/auth/register)
   ↓
2. User provides: name, email, phone, password, role
   ↓
3. Password hashed with Bcrypt (12 rounds)
   ↓
4. User stored in database
   ↓
5. User Login (POST /api/v1/auth/login)
   ↓
6. Email & password validated
   ↓
7. JWT token generated (24-hour expiry)
   ↓
8. Token returned to client
   ↓
9. Client includes token in Authorization header
   ↓
10. Token validated on protected endpoints
    ↓
11. User role checked for endpoint access
```

---

## Database Schema

### Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid.uuid4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role ENUM('customer', 'staff', 'shop_owner', 'admin') DEFAULT 'customer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_phone ON users(phone);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
```

### Products Table (Updated)

```sql
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    sku VARCHAR(100) UNIQUE NOT NULL,
    category VARCHAR(100) NOT NULL,
    subcategory VARCHAR(100),
    description TEXT,
    unit VARCHAR(50) NOT NULL,
    cost_price DECIMAL(10,2) NOT NULL,
    selling_price DECIMAL(10,2) NOT NULL,
    mrp DECIMAL(10,2) NOT NULL,
    gst_rate DECIMAL(5,2) DEFAULT 0,
    hsn_code VARCHAR(20),
    current_stock INTEGER DEFAULT 0,
    min_stock_level INTEGER DEFAULT 10,
    reorder_quantity INTEGER DEFAULT 0,
    is_perishable BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER NOT NULL,  -- References users.id
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## File Structure

```
backend/
├── app/
│   └── auth/
│       ├── __init__.py           # Package initializer
│       ├── models.py             # SQLAlchemy User model
│       ├── schemas.py            # Pydantic request/response schemas
│       ├── service.py            # Business logic (AuthService)
│       ├── security.py           # JWT & password utilities
│       └── router.py             # FastAPI auth endpoints
├── product_service/
│   ├── models.py                 # Product model (updated)
│   ├── routes_rbac.py            # Products routes with RBAC
│   └── ...
├── shared/
│   ├── config.py                 # App configuration
│   ├── database.py               # SQLAlchemy setup
│   └── ...
├── main_with_auth.py             # Main app with auth integration
└── requirements.txt
```

---

## API Endpoints

### Authentication Endpoints

#### 1. Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "9876543210",
    "password": "secure_password_123",
    "role": "customer"
}
```

**Response (201 Created):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "9876543210",
  "role": "customer",
  "is_active": true,
  "created_at": "2024-02-05T10:30:00",
  "updated_at": "2024-02-05T10:30:00"
}
```

---

#### 2. Login User

```http
POST /api/v1/auth/login
Content-Type: application/json

{
    "email": "john@example.com",
    "password": "secure_password_123"
}
```

**Response (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6ImpvaG5AZXhhbXBsZS5jb20iLCJyb2xlIjoiY3VzdG9tZXIiLCJleHAiOjE3MDk4MDcwMDB9.signature",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "john@example.com",
    "phone": "9876543210",
    "role": "customer",
    "is_active": true,
    "created_at": "2024-02-05T10:30:00",
    "updated_at": "2024-02-05T10:30:00"
  }
}
```

---

#### 3. Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "email": "john@example.com",
  "phone": "9876543210",
  "role": "customer",
  "is_active": true,
  "created_at": "2024-02-05T10:30:00",
  "updated_at": "2024-02-05T10:30:00"
}
```

---

### Product Endpoints (with RBAC)

#### 1. List Products (All Users)

```http
GET /api/v1/products?skip=0&limit=10&category=dairy
Authorization: Bearer <token>
```

**Required Role:** Any authenticated user

**Response (200 OK):**

```json
[
  {
    "id": 1,
    "name": "Organic Milk",
    "sku": "MILK-001",
    "category": "dairy",
    "selling_price": "45.00",
    "current_stock": 100,
    "gst_rate": "5.00",
    "is_active": true,
    "created_by": 1,
    "created_at": "2024-02-05T10:00:00",
    "updated_at": "2024-02-05T10:00:00"
  }
]
```

---

#### 2. Get Product by ID (All Users)

```http
GET /api/v1/products/1
Authorization: Bearer <token>
```

**Required Role:** Any authenticated user

---

#### 3. Create Product (SHOP_OWNER, ADMIN Only)

```http
POST /api/v1/products
Authorization: Bearer <token>
Content-Type: application/json

{
    "name": "Organic Milk 1L",
    "sku": "MILK-001",
    "category": "dairy",
    "subcategory": "liquid",
    "description": "Fresh organic cow milk",
    "unit": "liter",
    "cost_price": "30.00",
    "selling_price": "45.00",
    "mrp": "50.00",
    "gst_rate": "5.00",
    "hsn_code": "0401",
    "current_stock": 100,
    "min_stock_level": 20,
    "reorder_quantity": 50,
    "is_perishable": true
}
```

**Required Role:** SHOP_OWNER or ADMIN

**Response (201 Created):**

```json
{
  "id": 1,
  "name": "Organic Milk 1L",
  "sku": "MILK-001",
  "category": "dairy",
  "subcategory": "liquid",
  "selling_price": "45.00",
  "cost_price": "30.00",
  "mrp": "50.00",
  "current_stock": 100,
  "is_active": true,
  "created_by": 2,
  "created_at": "2024-02-05T10:30:00",
  "updated_at": "2024-02-05T10:30:00"
}
```

---

#### 4. Update Product (SHOP_OWNER, ADMIN Only)

```http
PUT /api/v1/products/1
Authorization: Bearer <token>
Content-Type: application/json

{
    "selling_price": "48.00",
    "min_stock_level": 25
}
```

**Required Role:** SHOP_OWNER or ADMIN

---

#### 5. Delete Product (SHOP_OWNER, ADMIN Only)

```http
DELETE /api/v1/products/1
Authorization: Bearer <token>
```

**Required Role:** SHOP_OWNER or ADMIN

**Response (204 No Content)**

---

#### 6. Get Low Stock Products (STAFF, SHOP_OWNER, ADMIN Only)

```http
GET /api/v1/products/category/dairy/low-stock
Authorization: Bearer <token>
```

**Required Role:** STAFF, SHOP_OWNER, or ADMIN

---

## JWT Token Payload

The JWT access token contains the following claims:

```json
{
  "sub": "550e8400-e29b-41d4-a716-446655440000", // User ID
  "email": "john@example.com",
  "role": "customer",
  "exp": 1709807000, // Expiry timestamp (24 hours)
  "iat": 1709720600 // Issued at timestamp
}
```

**Token Format:**

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi00NDY2NTU0NDAwMDAiLCJlbWFpbCI6ImpvaG5AZXhhbXBsZS5jb20iLCJyb2xlIjoiY3VzdG9tZXIiLCJleHAiOjE3MDk4MDcwMDB9.
signature_here
```

---

## Configuration

### Environment Variables

```bash
# JWT Configuration
SECRET_KEY=your-super-secret-key-min-32-chars-for-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./smartkirana.db
# DATABASE_URL=postgresql://user:pass@localhost:5432/smartkirana

# Debug Mode
DEBUG=true
```

### Security Best Practices

1. **Change SECRET_KEY in Production**

   ```bash
   # Generate a strong key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use HTTPS Only**
   - Always use TLS/SSL in production
   - Never send tokens over HTTP

3. **Token Rotation**
   - Implement refresh tokens for long-lived sessions
   - Rotate tokens periodically

4. **Password Policy**
   - Minimum 8 characters
   - Consider adding complexity requirements
   - Hash with Bcrypt (12 rounds minimum)

5. **CORS Configuration**
   - Restrict to specific domains in production
   - Current: `allow_origins=["*"]` – change this!

---

## Testing the Auth System

### Using cURL

```bash
# 1. Register a user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "9876543210",
    "password": "password123",
    "role": "shop_owner"
  }'

# 2. Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'

# 3. Get current user (use token from login response)
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer <your_token_here>"

# 4. Create a product (SHOP_OWNER only)
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer <your_token_here>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Product",
    "sku": "TEST-001",
    "category": "test",
    "unit": "piece",
    "cost_price": "10.00",
    "selling_price": "15.00",
    "mrp": "20.00",
    "current_stock": 50
  }'

# 5. List products
curl -X GET http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer <your_token_here>"
```

### Using Python Requests

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(
    f"{BASE_URL}/api/v1/auth/register",
    json={
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "9876543210",
        "password": "secure_pass_123",
        "role": "shop_owner"
    }
)
user = response.json()
print(f"User created: {user['id']}")

# Login
response = requests.post(
    f"{BASE_URL}/api/v1/auth/login",
    json={
        "email": "john@example.com",
        "password": "secure_pass_123"
    }
)
token = response.json()["access_token"]
print(f"Token: {token}")

# Get current user
headers = {"Authorization": f"Bearer {token}"}
response = requests.get(
    f"{BASE_URL}/api/v1/auth/me",
    headers=headers
)
print(f"Current user: {response.json()}")

# Create product
product_data = {
    "name": "Milk",
    "sku": "MILK-001",
    "category": "dairy",
    "unit": "liter",
    "cost_price": "30.00",
    "selling_price": "45.00",
    "mrp": "50.00",
    "current_stock": 100
}
response = requests.post(
    f"{BASE_URL}/api/v1/products",
    headers=headers,
    json=product_data
)
print(f"Product created: {response.json()}")

# List products
response = requests.get(
    f"{BASE_URL}/api/v1/products",
    headers=headers
)
print(f"Products: {response.json()}")
```

---

## Swagger UI Integration

When you start the server with the new `main_with_auth.py`:

```bash
cd backend
python main_with_auth.py
```

Visit: **http://localhost:8000/api/docs**

You'll see:

1. **Auth Section**
   - POST /api/v1/auth/register
   - POST /api/v1/auth/login
   - GET /api/v1/auth/me

2. **Products Section**
   - GET /api/v1/products (all users)
   - GET /api/v1/products/{id} (all users)
   - POST /api/v1/products (shop_owner, admin)
   - PUT /api/v1/products/{id} (shop_owner, admin)
   - DELETE /api/v1/products/{id} (shop_owner, admin)
   - GET /api/v1/products/category/{category}/low-stock (staff, shop_owner, admin)

3. **Health Section**
   - GET /api/health

---

## Error Handling

### Common Errors

**400 Bad Request**

```json
{
  "detail": "Email already registered"
}
```

**401 Unauthorized** (Invalid/missing token)

```json
{
  "detail": "Could not validate credentials"
}
```

**403 Forbidden** (Insufficient permissions)

```json
{
  "detail": "This operation requires one of these roles: shop_owner, admin"
}
```

**404 Not Found**

```json
{
  "detail": "Product not found"
}
```

**409 Conflict** (Duplicate SKU)

```json
{
  "detail": "Product with this SKU already exists"
}
```

---

## Code Examples

### Creating a Role-Protected Endpoint

```python
from fastapi import APIRouter, Depends
from app.auth.security import get_current_user, require_role
from app.auth.models import User

router = APIRouter()

# Only shop_owner and admin can access
@router.post("/reports/export", dependencies=[Depends(require_role("shop_owner", "admin"))])
def export_reports(current_user: User = Depends(get_current_user)):
    """Export reports - shop_owner and admin only"""
    return {"message": f"Exporting for {current_user.name}"}

# All authenticated users can access
@router.get("/dashboard")
def dashboard(current_user: User = Depends(get_current_user)):
    """Dashboard - all authenticated users"""
    return {
        "user": current_user.name,
        "role": current_user.role.value,
        "message": f"Welcome {current_user.name}!"
    }

# Staff and above can access
@router.get("/inventory/alerts", dependencies=[Depends(require_role("staff", "shop_owner", "admin"))])
def inventory_alerts(current_user: User = Depends(get_current_user)):
    """Inventory alerts - staff and above"""
    return {"alerts": []}
```

---

## Production Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG=false`
- [ ] Update `CORS` origins to specific domains
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS/TLS
- [ ] Implement rate limiting on auth endpoints
- [ ] Add email verification for registration
- [ ] Implement password reset functionality
- [ ] Add refresh token rotation
- [ ] Enable API key authentication as alternative
- [ ] Set up logging and monitoring
- [ ] Add request/response validation
- [ ] Implement audit logging

---

## Summary

This authentication and RBAC system provides:

- ✅ Secure password hashing (Bcrypt)
- ✅ JWT-based stateless auth
- ✅ Role-based endpoint protection
- ✅ Scalable architecture
- ✅ Easy integration with existing FastAPI endpoints
- ✅ Clear error messages and validation
- ✅ Production-ready code

The system is ready to be extended with:

- Email verification
- Password reset
- Refresh tokens
- OAuth2 social login
- Multi-factor authentication
