# SmartKirana AI – Auth System Architecture & Flow Diagrams

## 1. Authentication Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     USER REGISTRATION                            │
└─────────────────────────────────────────────────────────────────┘

1. USER INPUT
   ↓
   ┌─────────────────────────────────────┐
   │ POST /api/v1/auth/register          │
   │ {                                   │
   │   "name": "John Doe",               │
   │   "email": "john@example.com",      │
   │   "phone": "9876543210",            │
   │   "password": "password123",        │
   │   "role": "shop_owner"              │
   │ }                                   │
   └─────────────────────────────────────┘
   ↓
2. VALIDATION
   ├─ Email uniqueness ✓
   ├─ Phone uniqueness ✓
   ├─ Password length ✓
   └─ Role valid ✓
   ↓
3. PASSWORD HASHING
   ├─ Input: "password123"
   ├─ Bcrypt (12 rounds)
   └─ Hash: "$2b$12$..."
   ↓
4. CREATE USER
   ├─ Save to database
   ├─ Set is_active = true
   └─ Generate UUID
   ↓
5. RESPONSE (201 Created)
   ┌─────────────────────────────────────┐
   │ {                                   │
   │   "id": "550e8400-e29b-41d4-...",   │
   │   "name": "John Doe",               │
   │   "email": "john@example.com",      │
   │   "phone": "9876543210",            │
   │   "role": "shop_owner",             │
   │   "is_active": true,                │
   │   "created_at": "2024-02-05..."     │
   │ }                                   │
   └─────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                       USER LOGIN                                 │
└─────────────────────────────────────────────────────────────────┘

1. USER INPUT
   ↓
   ┌─────────────────────────────────────┐
   │ POST /api/v1/auth/login             │
   │ {                                   │
   │   "email": "john@example.com",      │
   │   "password": "password123"         │
   │ }                                   │
   └─────────────────────────────────────┘
   ↓
2. FETCH USER
   ├─ Query: SELECT * FROM users WHERE email = ?
   └─ Check: User exists? ✓
   ↓
3. PASSWORD VERIFICATION
   ├─ Input: "password123"
   ├─ Stored Hash: "$2b$12$..."
   ├─ Bcrypt.verify()
   └─ Match? ✓
   ↓
4. CHECK ACTIVE STATUS
   ├─ is_active = true? ✓
   └─ User not inactive ✓
   ↓
5. GENERATE JWT TOKEN
   ├─ Payload:
   │  {
   │    "sub": "550e8400-e29b-41d4-...",
   │    "email": "john@example.com",
   │    "role": "shop_owner",
   │    "exp": 1709807000,
   │    "iat": 1709720600
   │  }
   ├─ Sign with SECRET_KEY (HMAC-SHA256)
   └─ Token: "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
   ↓
6. RESPONSE (200 OK)
   ┌──────────────────────────────────────────┐
   │ {                                        │
   │   "access_token": "eyJ...",              │
   │   "token_type": "bearer",                │
   │   "user": {                              │
   │     "id": "550e8400-...",                │
   │     "name": "John Doe",                  │
   │     "email": "john@example.com",         │
   │     "role": "shop_owner",                │
   │     ...                                  │
   │   }                                      │
   │ }                                        │
   └──────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────────┐
│                  PROTECTED ENDPOINT ACCESS                       │
└─────────────────────────────────────────────────────────────────┘

1. CLIENT REQUEST
   ↓
   ┌──────────────────────────────────────────┐
   │ GET /api/v1/auth/me                      │
   │ Headers: {                               │
   │   "Authorization": "Bearer eyJ..."       │
   │ }                                        │
   └──────────────────────────────────────────┘
   ↓
2. EXTRACT TOKEN
   ├─ Split: "Bearer eyJ..."
   └─ Token: "eyJ..."
   ↓
3. DECODE & VERIFY JWT
   ├─ Signature check (HMAC-SHA256)
   ├─ Expiry check (exp < now?)
   ├─ Required fields check (sub, email, role)
   └─ Valid? ✓
   ↓
4. EXTRACT CLAIMS
   ├─ sub (user_id): "550e8400-..."
   ├─ email: "john@example.com"
   ├─ role: "shop_owner"
   └─ exp: 1709807000
   ↓
5. FETCH USER FROM DB
   ├─ Query: SELECT * FROM users WHERE id = ?
   ├─ Check: User exists? ✓
   ├─ Check: is_active = true? ✓
   └─ User object loaded
   ↓
6. ENDPOINT EXECUTION
   ├─ current_user available in handler
   ├─ Request processed
   └─ Response sent
   ↓
7. RESPONSE (200 OK)
   ┌──────────────────────────────────────────┐
   │ {                                        │
   │   "id": "550e8400-...",                  │
   │   "name": "John Doe",                    │
   │   "email": "john@example.com",           │
   │   "role": "shop_owner",                  │
   │   ...                                    │
   │ }                                        │
   └──────────────────────────────────────────┘
```

---

## 2. Role-Based Access Control (RBAC) Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              PROTECTED ENDPOINT WITH RBAC                        │
└─────────────────────────────────────────────────────────────────┘

SCENARIO 1: CUSTOMER TRIES TO CREATE PRODUCT (DENIED)

1. CLIENT REQUEST
   ↓
   POST /api/v1/products
   Authorization: Bearer <customer_token>
   Body: { "name": "Product", ... }
   ↓
2. EXTRACT TOKEN
   ├─ Token valid? ✓
   ├─ User loaded? ✓
   └─ current_user.role = "customer"
   ↓
3. RBAC CHECK
   ├─ Endpoint requires: ["shop_owner", "admin"]
   ├─ User role: "customer"
   └─ Is "customer" in ["shop_owner", "admin"]? ✗
   ↓
4. RESPONSE (403 FORBIDDEN)
   ┌──────────────────────────────────────────┐
   │ HTTP 403 Forbidden                       │
   │ {                                        │
   │   "detail": "This operation requires     │
   │             one of these roles:          │
   │             shop_owner, admin"           │
   │ }                                        │
   └──────────────────────────────────────────┘

───────────────────────────────────────────────────────────────────

SCENARIO 2: SHOP_OWNER CREATES PRODUCT (ALLOWED)

1. CLIENT REQUEST
   ↓
   POST /api/v1/products
   Authorization: Bearer <owner_token>
   Body: { "name": "Product", ... }
   ↓
2. EXTRACT TOKEN
   ├─ Token valid? ✓
   ├─ User loaded? ✓
   └─ current_user.role = "shop_owner"
   ↓
3. RBAC CHECK
   ├─ Endpoint requires: ["shop_owner", "admin"]
   ├─ User role: "shop_owner"
   └─ Is "shop_owner" in ["shop_owner", "admin"]? ✓
   ↓
4. BUSINESS LOGIC
   ├─ Create product
   ├─ Set created_by = current_user.id
   ├─ Save to database
   └─ Generate response
   ↓
5. RESPONSE (201 CREATED)
   ┌──────────────────────────────────────────┐
   │ HTTP 201 Created                         │
   │ {                                        │
   │   "id": 1,                               │
   │   "name": "Product",                     │
   │   "created_by": "550e8400-...",          │
   │   ...                                    │
   │ }                                        │
   └──────────────────────────────────────────┘
```

---

## 3. Database Schema Diagram

```
┌──────────────────────────────────────┐
│           USERS TABLE                │
├──────────────────────────────────────┤
│ id (UUID, PK)                        │
│ name (VARCHAR)                       │
│ email (VARCHAR, UNIQUE) ────────┐   │
│ phone (VARCHAR, UNIQUE)    ──┐  │   │
│ password_hash (VARCHAR)    ──┼─┐│   │
│ role (ENUM)                ──┼─┼┼─┐ │
│ is_active (BOOLEAN)        ──┼─┼┼─┼┐│
│ created_at (TIMESTAMP)     ──┼─┼┼─┼┼│
│ updated_at (TIMESTAMP)     ──┼─┼┼─┼┼│
└──────────────────────────────────────┘
                       │  │ │ │ │ │
       ┌───────────────┘  │ │ │ │ │
       │     ┌────────────┘ │ │ │ │
       │     │   ┌──────────┘ │ │ │
       │     │   │  ┌─────────┘ │ │
       │     │   │  │  ┌────────┘ │
       │     │   │  │  │  ┌───────┘
       │     │   │  │  │  │
       ▼     ▼   ▼  ▼  ▼  ▼
    ┌──────────────────────────────────┐
    │         PRODUCTS TABLE           │
    ├──────────────────────────────────┤
    │ id (SERIAL, PK)                  │
    │ name (VARCHAR)                   │
    │ sku (VARCHAR, UNIQUE)            │
    │ category (VARCHAR)               │
    │ subcategory (VARCHAR)            │
    │ description (TEXT)               │
    │ unit (VARCHAR)                   │
    │ cost_price (DECIMAL)             │
    │ selling_price (DECIMAL)          │
    │ mrp (DECIMAL)                    │
    │ gst_rate (DECIMAL)               │
    │ hsn_code (VARCHAR)               │
    │ current_stock (INTEGER)          │
    │ min_stock_level (INTEGER)        │
    │ reorder_quantity (INTEGER)       │
    │ is_perishable (BOOLEAN)          │
    │ is_active (BOOLEAN)              │
    │ created_by (FK → users.id) ──────┼─────────┐
    │ created_at (TIMESTAMP)           │         │
    │ updated_at (TIMESTAMP)           │         │
    └──────────────────────────────────┘         │
                                                │
    Relationship:                               │
    One user can create many products ──────────┘
```

---

## 4. JWT Token Structure

```
┌─────────────────────────────────────────────────────────────┐
│         JWT TOKEN: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.    │
│         eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi0...      │
│         signature_here                                       │
└─────────────────────────────────────────────────────────────┘

PART 1: HEADER (Base64 Encoded)
┌──────────────────────────┐
│ {                        │
│   "alg": "HS256",        │ ← HMAC with SHA-256
│   "typ": "JWT"           │ ← Token type
│ }                        │
└──────────────────────────┘
                │
                ▼
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"

───────────────────────────────────────────────

PART 2: PAYLOAD (Base64 Encoded)
┌──────────────────────────────────────────────┐
│ {                                            │
│   "sub": "550e8400-e29b-41d4-a716-...",    │ ← User ID (subject)
│   "email": "john@example.com",              │ ← User email
│   "role": "shop_owner",                     │ ← User role
│   "exp": 1709807000,                        │ ← Expiration time
│   "iat": 1709720600                         │ ← Issued at time
│ }                                            │
└──────────────────────────────────────────────┘
                │
                ▼
    "eyJzdWIiOiI1NTBlODQwMC1lMjliLTQxZDQtYTcxNi0..."

───────────────────────────────────────────────

PART 3: SIGNATURE (HMAC-SHA256)
┌──────────────────────────────────────────────┐
│ HMACSHA256(                                  │
│   header + "." + payload,                    │
│   "your-secret-key-change-in-production"    │
│ )                                            │
└──────────────────────────────────────────────┘
                │
                ▼
        "jvk5h3j5h35jhk3h5j3h5jh3jh5"

───────────────────────────────────────────────

FULL TOKEN: "eyJ..." . "eyJ..." . "jvk..."
```

---

## 5. Request/Response Cycle

```
┌──────────────────────┐
│   CLIENT (Browser)   │
└──────────────────────┘
        │
        │ 1. POST /register
        ▼
┌──────────────────────────────────────┐
│      FastAPI Application             │
│  ┌────────────────────────────────┐  │
│  │  @router.post("/register")     │  │
│  │  ├─ UserCreate validation      │  │
│  │  ├─ Email uniqueness check     │  │
│  │  ├─ Phone uniqueness check     │  │
│  │  ├─ Password hashing (Bcrypt)  │  │
│  │  └─ Save to DB                 │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
        │
        │ 2. User created (201)
        ▼
┌──────────────────────────────────────┐
│      DATABASE (PostgreSQL)           │
│  ┌────────────────────────────────┐  │
│  │  INSERT INTO users VALUES (... │  │
│  └────────────────────────────────┘  │
│         └─ User stored                │
└──────────────────────────────────────┘
        │
        │ 3. POST /login
        ▼
┌──────────────────────────────────────┐
│      FastAPI Application             │
│  ┌────────────────────────────────┐  │
│  │  @router.post("/login")        │  │
│  │  ├─ Fetch user by email        │  │
│  │  ├─ Verify password (Bcrypt)   │  │
│  │  ├─ Create JWT token           │  │
│  │  └─ Return token + user info   │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
        │
        │ 4. Token returned (200)
        │    access_token: "eyJ..."
        ▼
┌──────────────────────────────────────┐
│   CLIENT (Browser)                   │
│   └─ Stores token in localStorage    │
└──────────────────────────────────────┘
        │
        │ 5. GET /products
        │    Headers: Authorization: Bearer eyJ...
        ▼
┌──────────────────────────────────────┐
│      FastAPI Application             │
│  ┌────────────────────────────────┐  │
│  │  get_current_user (dependency) │  │
│  │  ├─ Extract token from header  │  │
│  │  ├─ Verify JWT signature       │  │
│  │  ├─ Check expiration           │  │
│  │  ├─ Extract user_id from JWT   │  │
│  │  ├─ Fetch user from DB         │  │
│  │  └─ Return User object         │  │
│  │                                │  │
│  │  @router.get("/products")      │  │
│  │  ├─ Check RBAC (if needed)     │  │
│  │  ├─ Execute business logic     │  │
│  │  └─ Return response            │  │
│  └────────────────────────────────┘  │
└──────────────────────────────────────┘
        │
        │ 6. Products list (200)
        ▼
┌──────────────────────────────────────┐
│   CLIENT (Browser)                   │
│   └─ Displays products               │
└──────────────────────────────────────┘
```

---

## 6. Role-Based Access Matrix

```
┌────────────────┬──────────┬─────────┬──────────────┬───────┐
│ Endpoint       │ Customer │  Staff  │ Shop Owner   │ Admin │
├────────────────┼──────────┼─────────┼──────────────┼───────┤
│ POST /register │    ✅    │   ✅    │      ✅      │   ✅  │
│ POST /login    │    ✅    │   ✅    │      ✅      │   ✅  │
│ GET /auth/me   │    ✅    │   ✅    │      ✅      │   ✅  │
├────────────────┼──────────┼─────────┼──────────────┼───────┤
│ GET /products  │    ✅    │   ✅    │      ✅      │   ✅  │
│ GET /products/ │    ✅    │   ✅    │      ✅      │   ✅  │
│ {id}           │          │         │              │       │
├────────────────┼──────────┼─────────┼──────────────┼───────┤
│ POST /products │    ❌    │   ❌    │      ✅      │   ✅  │
├────────────────┼──────────┼─────────┼──────────────┼───────┤
│ PUT /products/ │    ❌    │   ❌    │      ✅      │   ✅  │
│ {id}           │          │         │              │       │
├────────────────┼──────────┼─────────┼──────────────┼───────┤
│ DELETE         │    ❌    │   ❌    │      ✅      │   ✅  │
│ /products/{id} │          │         │              │       │
├────────────────┼──────────┼─────────┼──────────────┼───────┤
│ GET            │    ❌    │   ✅    │      ✅      │   ✅  │
│ /products/     │          │         │              │       │
│ category/      │          │         │              │       │
│ {cat}/         │          │         │              │       │
│ low-stock      │          │         │              │       │
└────────────────┴──────────┴─────────┴──────────────┴───────┘

Legend:
✅ = Access Allowed
❌ = Access Denied (403 Forbidden)
```

---

## 7. Error Handling Flow

```
┌─────────────────────────┐
│   Invalid Request       │
└─────────────────────────┘
        │
        ▼
┌──────────────────────────────────────────┐
│         Error Validation Check           │
├──────────────────────────────────────────┤
│ ✗ Email already registered?              │
│   └─→ 400 Bad Request                    │
├──────────────────────────────────────────┤
│ ✗ Phone already registered?              │
│   └─→ 400 Bad Request                    │
├──────────────────────────────────────────┤
│ ✗ Invalid email format?                  │
│   └─→ 422 Unprocessable Entity           │
├──────────────────────────────────────────┤
│ ✗ Password < 8 characters?               │
│   └─→ 422 Unprocessable Entity           │
├──────────────────────────────────────────┤
│ ✗ Invalid credentials (login)?           │
│   └─→ 401 Unauthorized                   │
├──────────────────────────────────────────┤
│ ✗ User inactive?                         │
│   └─→ 403 Forbidden                      │
├──────────────────────────────────────────┤
│ ✗ Missing/Invalid token?                 │
│   └─→ 401 Unauthorized                   │
├──────────────────────────────────────────┤
│ ✗ Token expired?                         │
│   └─→ 401 Unauthorized                   │
├──────────────────────────────────────────┤
│ ✗ Insufficient role permissions?         │
│   └─→ 403 Forbidden                      │
├──────────────────────────────────────────┤
│ ✗ Resource not found?                    │
│   └─→ 404 Not Found                      │
├──────────────────────────────────────────┤
│ ✗ Duplicate SKU?                         │
│   └─→ 409 Conflict                       │
└──────────────────────────────────────────┘
```

---

## 8. Security Flow

```
INPUT
  │
  ▼
┌─────────────────────────────────────────┐
│  Pydantic Validation Layer              │
│  ├─ Type checking                       │
│  ├─ Email format                        │
│  ├─ Phone format                        │
│  ├─ String length                       │
│  └─ Pattern matching                    │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Database Integrity Checks              │
│  ├─ Unique email constraint             │
│  ├─ Unique phone constraint             │
│  └─ Foreign key validation              │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Password Security (Registration)       │
│  ├─ Bcrypt hash (12 rounds)             │
│  ├─ Salt generated                      │
│  ├─ Hash stored (not password)          │
│  └─ Original password discarded         │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Token Security (Login)                 │
│  ├─ JWT generated with HMAC-SHA256      │
│  ├─ Signature includes SECRET_KEY       │
│  ├─ 24-hour expiration                  │
│  └─ Stateless (no session)              │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Request Authentication (Protected)     │
│  ├─ Extract token from header           │
│  ├─ Verify signature                    │
│  ├─ Check expiration                    │
│  ├─ Fetch user from DB                  │
│  └─ Validate user status                │
└─────────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────────┐
│  Role-Based Access Control (RBAC)       │
│  ├─ Extract role from JWT               │
│  ├─ Check endpoint requirements         │
│  ├─ Grant/Deny access                   │
│  └─ Log access attempt                  │
└─────────────────────────────────────────┘
  │
  ▼
OUTPUT (Secure)
```

---

This document provides visual representations of all major flows in the authentication and RBAC system!
