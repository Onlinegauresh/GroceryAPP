# SmartKirana AI – Auth & RBAC Quick Start

## Prerequisites

```bash
# Ensure you're in the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# OR
.\venv\Scripts\Activate.ps1  # PowerShell

# Install dependencies (if not already done)
pip install -r requirements.txt
```

---

## Starting the Server with Auth

```bash
# Run the main app with authentication
python main_with_auth.py

# You should see:
# INFO:     Uvicorn running on http://0.0.0.0:8000 [press CTRL+C to quit]
```

---

## Testing in Swagger UI

1. **Open Swagger UI**
   - URL: http://localhost:8000/api/docs

2. **Register a User**
   - Click: `POST /api/v1/auth/register`
   - Click: `Try it out`
   - Enter JSON:

   ```json
   {
     "name": "John Doe",
     "email": "john@example.com",
     "phone": "9876543210",
     "password": "password123",
     "role": "shop_owner"
   }
   ```

   - Click: `Execute`

3. **Login**
   - Click: `POST /api/v1/auth/login`
   - Click: `Try it out`
   - Enter JSON:

   ```json
   {
     "email": "john@example.com",
     "password": "password123"
   }
   ```

   - Click: `Execute`
   - **Copy the access_token** from the response

4. **Authorize in Swagger**
   - Click: `Authorize` button (top right)
   - Paste: `Bearer <your_token_here>`
   - Click: `Authorize`
   - Click: `Close`

5. **Test Protected Endpoints**

   **Create a Product (SHOP_OWNER only):**
   - Click: `POST /api/v1/products`
   - Click: `Try it out`
   - Enter:

   ```json
   {
     "name": "Organic Milk",
     "sku": "MILK-001",
     "category": "dairy",
     "unit": "liter",
     "cost_price": "30.00",
     "selling_price": "45.00",
     "mrp": "50.00",
     "current_stock": 100
   }
   ```

   - Click: `Execute`
   - **Response:** 201 Created ✅

   **List Products (All users):**
   - Click: `GET /api/v1/products`
   - Click: `Try it out`
   - Click: `Execute`
   - **Response:** 200 OK with products ✅

   **Get Current User:**
   - Click: `GET /api/v1/auth/me`
   - Click: `Try it out`
   - Click: `Execute`
   - **Response:** Your user profile ✅

---

## Testing with cURL

### Register

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alice Smith",
    "email": "alice@example.com",
    "phone": "9876543211",
    "password": "secure_pass_123",
    "role": "customer"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "secure_pass_123"
  }' | jq '.access_token' -r > token.txt

TOKEN=$(cat token.txt)
echo $TOKEN
```

### Get Current User

```bash
curl -X GET http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer $TOKEN"
```

### Create Product (requires shop_owner or admin role)

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Fresh Tomatoes",
    "sku": "TOM-001",
    "category": "vegetables",
    "unit": "kg",
    "cost_price": "20.00",
    "selling_price": "35.00",
    "mrp": "40.00",
    "current_stock": 50
  }'
```

### List Products

```bash
curl -X GET http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN"
```

---

## Testing Role-Based Access

### Test 1: CUSTOMER (No Create Permission)

1. Register as CUSTOMER

```json
{
  "name": "Bob Customer",
  "email": "bob@example.com",
  "phone": "9876543212",
  "password": "password123",
  "role": "customer"
}
```

2. Login and get token

3. Try to create product:

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $CUSTOMER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Test", ...}'
```

**Expected Result:** ❌ 403 Forbidden

```json
{
  "detail": "This operation requires one of these roles: shop_owner, admin"
}
```

---

### Test 2: SHOP_OWNER (Full Permissions)

1. Register as SHOP_OWNER

```json
{
  "name": "Owner Charlie",
  "email": "charlie@example.com",
  "phone": "9876543213",
  "password": "password123",
  "role": "shop_owner"
}
```

2. Login and get token

3. Create product:

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Premium Cheese",
    "sku": "CHEESE-001",
    "category": "dairy",
    "unit": "kg",
    "cost_price": "200.00",
    "selling_price": "350.00",
    "mrp": "400.00"
  }'
```

**Expected Result:** ✅ 201 Created

4. Update product:

```bash
curl -X PUT http://localhost:8000/api/v1/products/1 \
  -H "Authorization: Bearer $OWNER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"selling_price": "380.00"}'
```

**Expected Result:** ✅ 200 OK

---

### Test 3: STAFF (Read & Inventory Permissions)

1. Register as STAFF

```json
{
  "name": "Staff Diana",
  "email": "diana@example.com",
  "phone": "9876543214",
  "password": "password123",
  "role": "staff"
}
```

2. Login and get token

3. Read products (✅ Allowed):

```bash
curl -X GET http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

4. Try to create product (❌ Forbidden):

```bash
curl -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Expected Result:** ❌ 403 Forbidden

5. View low-stock products (✅ Allowed):

```bash
curl -X GET http://localhost:8000/api/v1/products/category/dairy/low-stock \
  -H "Authorization: Bearer $STAFF_TOKEN"
```

---

## Database Verification

### Check Users Table

```bash
# Using SQLite (if on dev)
sqlite3 smartkirana.db "SELECT id, name, email, role, is_active FROM users;"
```

### Sample Output

```
| id | name | email | role | is_active |
|----|------|-------|------|-----------|
| 1  | John Doe | john@example.com | shop_owner | 1 |
| 2  | Alice Smith | alice@example.com | customer | 1 |
```

---

## Key Endpoints Summary

| Endpoint                                         | Method | Role Required            | Purpose          |
| ------------------------------------------------ | ------ | ------------------------ | ---------------- |
| `/api/v1/auth/register`                          | POST   | None                     | Create new user  |
| `/api/v1/auth/login`                             | POST   | None                     | Get JWT token    |
| `/api/v1/auth/me`                                | GET    | Authenticated            | Get user profile |
| `/api/v1/products`                               | GET    | Authenticated            | List products    |
| `/api/v1/products`                               | POST   | shop_owner, admin        | Create product   |
| `/api/v1/products/{id}`                          | PUT    | shop_owner, admin        | Update product   |
| `/api/v1/products/{id}`                          | DELETE | shop_owner, admin        | Delete product   |
| `/api/v1/products/category/{category}/low-stock` | GET    | staff, shop_owner, admin | Low stock alerts |

---

## Troubleshooting

### Error: "Could not validate credentials"

- ✅ **Solution:** Ensure you included `Bearer` before the token

  ```bash
  # ❌ Wrong
  curl -H "Authorization: $TOKEN"

  # ✅ Correct
  curl -H "Authorization: Bearer $TOKEN"
  ```

### Error: "This operation requires one of these roles..."

- ✅ **Solution:** Your user doesn't have the required role
  - Create a new user with the correct role
  - Or use an ADMIN/SHOP_OWNER account

### Error: "Email already registered"

- ✅ **Solution:** Use a different email address
  ```bash
  # Try: user123@example.com, user456@example.com, etc.
  ```

### Error: "Product with this SKU already exists"

- ✅ **Solution:** Use a unique SKU
  ```bash
  # Try: MILK-002, MILK-003, etc.
  ```

### Token Expired

- ✅ **Solution:** Login again to get a new token
- Token expires after **24 hours**

---

## Next Steps

1. **Test all 6 endpoints** in Swagger UI
2. **Try different roles** (Customer, Staff, Owner, Admin)
3. **Verify RBAC** by testing unauthorized access
4. **Check database** to see created users and products
5. **Ready for frontend:** Mobile/web apps can now use these endpoints

---

## Project Files

Key files created:

- `app/auth/models.py` - User model
- `app/auth/schemas.py` - Request/response schemas
- `app/auth/security.py` - JWT & password utilities
- `app/auth/service.py` - Business logic
- `app/auth/router.py` - Auth endpoints
- `product_service/models.py` - Product model
- `product_service/routes_rbac.py` - Products with RBAC
- `main_with_auth.py` - Integrated app
- `AUTH_IMPLEMENTATION_GUIDE.md` - Full documentation

---

## Questions?

Refer to:

- `AUTH_IMPLEMENTATION_GUIDE.md` - Complete implementation details
- Swagger UI at `/api/docs` - Interactive API exploration
- Source code comments - Implementation details

---

**Happy Testing! 🚀**
