"""
PHASE G: SHOP & INVENTORY MANAGEMENT - COMPLETE API DOCUMENTATION

This document provides sample API requests and responses for the Shop Management
and Inventory Management modules implemented in SmartKirana AI.

The complete implementation includes:
✅ PHASE A: Database Design (Inventory model added to shared/models.py)
✅ PHASE B: Project Structure (app/shops/ and app/inventory/ modules created)
✅ PHASE C: Shop APIs (5 endpoints implemented)
✅ PHASE D: Inventory APIs (4 endpoints implemented)
✅ PHASE E: Security & RBAC (Role-based access control enforced)
✅ PHASE F: Integration (Routers registered in main_with_auth.py)
✅ PHASE G: Documentation (This file + inline code comments)

================================================================================
AUTHENTICATION SETUP (Required for all requests)
================================================================================

All Shop and Inventory endpoints require JWT authentication.

Step 1: Register a user
POST /api/v1/auth/register
Content-Type: application/json

{
"email": "shopowner@example.com",
"name": "John's Grocery Store",
"phone": "9876543210",
"password": "SecurePass123!"
}

Response:
{
"id": 1,
"email": "shopowner@example.com",
"name": "John's Grocery Store",
"phone": "9876543210",
"role": "customer",
"is_active": true,
"created_at": "2026-02-05T12:00:00",
"updated_at": "2026-02-05T12:00:00"
}

Step 2: Login to get JWT token
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

email=shopowner@example.com&password=SecurePass123!

Response:
{
"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
"token_type": "bearer",
"user": {
"id": 1,
"email": "shopowner@example.com",
"name": "John's Grocery Store",
"phone": "9876543210",
"role": "customer",
"is_active": true,
"created_at": "2026-02-05T12:00:00",
"updated_at": "2026-02-05T12:00:00"
}
}

Step 3: Use Bearer token for all subsequent requests
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

================================================================================
SHOP MANAGEMENT APIS (POST /api/v1/shops)
================================================================================

ENDPOINT 1: Create a Shop
────────────────────────

POST /api/v1/shops
Authorization: Bearer {jwt_token}
Content-Type: application/json

IMPORTANT: User must have OWNER or ADMIN role to create a shop

Request Body:
{
"name": "Fresh Produce Market",
"address": "123 Market Street, Ground Floor",
"city": "Mumbai",
"state": "Maharashtra",
"pincode": "400001",
"phone": "9876543210",
"email": "freshproduce@example.com",
"delivery_radius_km": 5,
"shop_category": "Grocery",
"gst_number": "27AABCH1234G1Z0",
"pan_number": "AAAAA0000A"
}

Response (201 Created):
{
"id": 1,
"name": "Fresh Produce Market",
"address": "123 Market Street, Ground Floor",
"city": "Mumbai",
"state": "Maharashtra",
"pincode": "400001",
"phone": "9876543210",
"email": "freshproduce@example.com",
"delivery_radius_km": 5,
"shop_category": "Grocery",
"gst_number": "27AABCH1234G1Z0",
"pan_number": "AAAAA0000A",
"is_active": true,
"subscription_plan": "free",
"created_at": "2026-02-05T12:00:00Z",
"updated_at": "2026-02-05T12:00:00Z"
}

Error Responses:

- 403 Forbidden: User is not OWNER or ADMIN
- 409 Conflict: Email already exists
- 400 Bad Request: Invalid input data

────────────────────────────────────────────────────────────────────────────────

ENDPOINT 2: Get Shop Details
────────────────────────────

GET /api/v1/shops/{shop_id}
Authorization: Bearer {jwt_token}

Example: GET /api/v1/shops/1

Response (200 OK):
{
"id": 1,
"name": "Fresh Produce Market",
"address": "123 Market Street, Ground Floor",
"city": "Mumbai",
"state": "Maharashtra",
"pincode": "400001",
"phone": "9876543210",
"email": "freshproduce@example.com",
"delivery_radius_km": 5,
"shop_category": "Grocery",
"gst_number": "27AABCH1234G1Z0",
"pan_number": "AAAAA0000A",
"is_active": true,
"subscription_plan": "free",
"created_at": "2026-02-05T12:00:00Z",
"updated_at": "2026-02-05T12:00:00Z",
"product_count": 45,
"active_products": 42
}

Access Rules:

- OWNER: Can only view their own shop
- STAFF: Can view their shop
- ADMIN: Can view any shop
- CUSTOMER: 403 Forbidden

Error Responses:

- 403 Forbidden: No access to this shop
- 404 Not Found: Shop doesn't exist

────────────────────────────────────────────────────────────────────────────────

ENDPOINT 3: List All Shops (Admin Only)
───────────────────────────────────────

GET /api/v1/shops?skip=0&limit=20
Authorization: Bearer {admin_token}

Query Parameters:

- skip: Number of shops to skip (default: 0)
- limit: Number of shops to return (default: 20, max: 100)

Response (200 OK):
{
"data": [
{
"id": 1,
"name": "Fresh Produce Market",
"address": "123 Market Street",
"city": "Mumbai",
"state": "Maharashtra",
"pincode": "400001",
"phone": "9876543210",
"email": "freshproduce@example.com",
"delivery_radius_km": 5,
"shop_category": "Grocery",
"gst_number": "27AABCH1234G1Z0",
"pan_number": "AAAAA0000A",
"is_active": true,
"subscription_plan": "free",
"created_at": "2026-02-05T12:00:00Z",
"updated_at": "2026-02-05T12:00:00Z"
},
{
"id": 2,
"name": "Daily Essentials Shop",
...
}
],
"total": 50,
"skip": 0,
"limit": 20
}

Access: Only ADMIN role

────────────────────────────────────────────────────────────────────────────────

ENDPOINT 4: Update Shop
──────────────────────

PUT /api/v1/shops/{shop_id}
Authorization: Bearer {jwt_token}
Content-Type: application/json

Example: PUT /api/v1/shops/1

Request Body (all fields optional):
{
"name": "Fresh Produce Market - Expanded",
"address": "123 Market Street, Building A",
"city": "Mumbai",
"state": "Maharashtra",
"pincode": "400002",
"phone": "9876543211",
"delivery_radius_km": 10,
"shop_category": "Super Market"
}

Response (200 OK):
{
"id": 1,
"name": "Fresh Produce Market - Expanded",
"address": "123 Market Street, Building A",
"city": "Mumbai",
"state": "Maharashtra",
"pincode": "400002",
"phone": "9876543211",
"email": "freshproduce@example.com",
"delivery_radius_km": 10,
"shop_category": "Super Market",
"gst_number": "27AABCH1234G1Z0",
"pan_number": "AAAAA0000A",
"is_active": true,
"subscription_plan": "free",
"created_at": "2026-02-05T12:00:00Z",
"updated_at": "2026-02-05T12:05:00Z"
}

Access Rules:

- OWNER: Can only update their own shop
- ADMIN: Can update any shop
- Others: 403 Forbidden

Error Responses:

- 403 Forbidden: No ownership rights
- 404 Not Found: Shop doesn't exist
- 400 Bad Request: Invalid data

────────────────────────────────────────────────────────────────────────────────

ENDPOINT 5: Deactivate Shop
───────────────────────────

PATCH /api/v1/shops/{shop_id}/deactivate
Authorization: Bearer {jwt_token}

Example: PATCH /api/v1/shops/1/deactivate

No Request Body Required

Response (200 OK):
{
"id": 1,
"name": "Fresh Produce Market",
"address": "123 Market Street, Ground Floor",
"city": "Mumbai",
"state": "Maharashtra",
"pincode": "400001",
"phone": "9876543210",
"email": "freshproduce@example.com",
"delivery_radius_km": 5,
"shop_category": "Grocery",
"gst_number": "27AABCH1234G1Z0",
"pan_number": "AAAAA0000A",
"is_active": false,
"subscription_plan": "free",
"created_at": "2026-02-05T12:00:00Z",
"updated_at": "2026-02-05T12:10:00Z"
}

Business Rules:

- Deactivation is permanent (no reactivation via API)
- Shop remains in database but marked inactive
- All associated products become inaccessible

Access Rules:

- OWNER: Can only deactivate their own shop
- ADMIN: Can deactivate any shop
- Others: 403 Forbidden

================================================================================
INVENTORY MANAGEMENT APIS (POST /api/v1/inventory)
================================================================================

ENDPOINT 1: Add Product to Inventory
────────────────────────────────────

POST /api/v1/inventory
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request Body:
{
"product_id": 5,
"quantity": 100,
"min_quantity": 20,
"cost_price": 45.50,
"selling_price": 65.00,
"batch_no": "BATCH2024001",
"expiry_date": "2026-08-05T00:00:00Z"
}

Response (201 Created):
{
"id": 1,
"shop_id": 1,
"product_id": 5,
"quantity": 100,
"min_quantity": 20,
"cost_price": 45.50,
"selling_price": 65.00,
"batch_no": "BATCH2024001",
"expiry_date": "2026-08-05T00:00:00Z",
"last_updated": "2026-02-05T12:00:00Z",
"created_at": "2026-02-05T12:00:00Z"
}

Business Rules:

- Product must belong to user's shop
- Cannot add duplicate product + batch combinations
- Selling price must be >= cost price
- Batch number is optional (null = single batch)

Access: OWNER, STAFF, ADMIN (of user's shop)

Error Responses:

- 404 Not Found: Product or shop doesn't exist
- 409 Conflict: Inventory already exists
- 400 Bad Request: Selling price < cost price or invalid data
- 403 Forbidden: No access to this shop

────────────────────────────────────────────────────────────────────────────────

ENDPOINT 2: Update Stock Quantity
──────────────────────────────────

PATCH /api/v1/inventory/update-stock
Authorization: Bearer {jwt_token}
Content-Type: application/json

Request Body:
{
"product_id": 5,
"quantity_change": 50,
"batch_no": "BATCH2024001",
"notes": "Received from supplier"
}

Response (200 OK):
{
"id": 1,
"shop_id": 1,
"product_id": 5,
"quantity": 150,
"min_quantity": 20,
"cost_price": 45.50,
"selling_price": 65.00,
"batch_no": "BATCH2024001",
"expiry_date": "2026-08-05T00:00:00Z",
"last_updated": "2026-02-05T12:02:00Z",
"created_at": "2026-02-05T12:00:00Z"
}

Examples:

- Add 50 units: quantity_change = 50
- Remove 20 units: quantity_change = -20
- Adjust for damage: quantity_change = -5

Business Rules:

- Prevents negative stock (validates before update)
- Updates last_updated timestamp automatically
- batch_no is optional (uses first available if not specified)
- No order processing here (orders handle stock later)

Use Cases:

- Receiving new stock: positive quantity_change
- Damage adjustments: negative quantity_change
- Stock counts/reconciliation: set quantity_change to correct discrepancy
- Return from customer: positive quantity_change

Access: OWNER, STAFF, ADMIN (of user's shop)

Error Responses:

- 404 Not Found: Inventory not found
- 400 Bad Request: Would result in negative stock
- 403 Forbidden: No access to this shop

Example Responses for Negative Stock Error:
{
"detail": "Cannot reduce stock below 0. Current: 10, Change: -20"
}

────────────────────────────────────────────────────────────────────────────────

ENDPOINT 3: Get Shop Inventory
──────────────────────────────

GET /api/v1/inventory/shop/{shop_id}?skip=0&limit=20
Authorization: Bearer {jwt_token}

Example: GET /api/v1/inventory/shop/1?skip=0&limit=20

Query Parameters:

- skip: Number of items to skip (default: 0)
- limit: Number of items to return (default: 20, max: 100)

Response (200 OK):
{
"shop_id": 1,
"data": [
{
"id": 1,
"shop_id": 1,
"product_id": 5,
"product_name": "Basmati Rice 1kg",
"product_sku": "RICE001",
"quantity": 150,
"min_quantity": 20,
"cost_price": 45.50,
"selling_price": 65.00,
"batch_no": "BATCH2024001",
"expiry_date": "2026-08-05T00:00:00Z",
"stock_status": "in_stock",
"last_updated": "2026-02-05T12:02:00Z",
"created_at": "2026-02-05T12:00:00Z"
},
{
"id": 2,
"shop_id": 1,
"product_id": 6,
"product_name": "Wheat Flour 5kg",
"product_sku": "FLOUR001",
"quantity": 15,
"min_quantity": 20,
"cost_price": 65.00,
"selling_price": 95.00,
"batch_no": "BATCH2024002",
"expiry_date": "2026-06-05T00:00:00Z",
"stock_status": "low_stock",
"last_updated": "2026-02-05T11:50:00Z",
"created_at": "2026-02-04T10:00:00Z"
}
],
"total": 45,
"skip": 0,
"limit": 20,
"summary": {
"total_products": 45,
"in_stock": 40,
"low_stock": 3,
"out_of_stock": 2,
"total_inventory_value": 12450.75
}
}

Stock Status Values:

- "in_stock": quantity > min_quantity
- "low_stock": 0 < quantity <= min_quantity
- "out_of_stock": quantity = 0

Summary Statistics:

- total_products: Count of products in inventory
- in_stock: Products with adequate stock
- low_stock: Products below minimum level (reorder trigger)
- out_of_stock: Products with zero quantity
- total_inventory_value: Sum of (cost_price × quantity) for all items

Access Rules:

- OWNER: Can only view their own shop inventory
- STAFF: Can view their shop inventory
- ADMIN: Can view any shop inventory
- CUSTOMER: 403 Forbidden

Error Responses:

- 404 Not Found: Shop doesn't exist
- 403 Forbidden: No access to this shop

────────────────────────────────────────────────────────────────────────────────

ENDPOINT 4: Get Low Stock Alerts
────────────────────────────────

GET /api/v1/inventory/low-stock/{shop_id}
Authorization: Bearer {jwt_token}

Example: GET /api/v1/inventory/low-stock/1

Response (200 OK):
{
"shop_id": 1,
"alert_count": 3,
"alerts": [
{
"product_id": 12,
"product_name": "Sunflower Oil 1L",
"product_sku": "OIL001",
"current_quantity": 2,
"min_quantity": 20,
"shortage": 18,
"last_updated": "2026-02-05T09:00:00Z"
},
{
"product_id": 15,
"product_name": "Black Pepper 500g",
"product_sku": "PEPPER001",
"current_quantity": 8,
"min_quantity": 15,
"shortage": 7,
"last_updated": "2026-02-04T14:30:00Z"
},
{
"product_id": 6,
"product_name": "Wheat Flour 5kg",
"product_sku": "FLOUR001",
"current_quantity": 15,
"min_quantity": 20,
"shortage": 5,
"last_updated": "2026-02-05T11:50:00Z"
}
]
}

Shortage Calculation:
shortage = min_quantity - current_quantity

Results are sorted by severity (lowest stock first).

Business Rules:

- Alerts only for items with quantity <= min_quantity
- Sorted by shortage amount (highest priority first)
- Useful for daily inventory review and reordering

Use Cases:

- Generate purchase orders
- Daily inventory dashboard
- Automated reorder triggers
- Critical stock alerts

Access Rules:

- OWNER: Can only view their own shop alerts
- STAFF: Can view their shop alerts
- ADMIN: Can view any shop alerts
- CUSTOMER: 403 Forbidden

Error Responses:

- 404 Not Found: Shop doesn't exist
- 403 Forbidden: No access to this shop

================================================================================
RBAC (ROLE-BASED ACCESS CONTROL) SUMMARY
================================================================================

User Roles and Permissions:

┌─────────────┬──────────────────┬──────────────────┬─────────────────┐
│ Role │ Shop Management │ Inventory View │ Inventory Modify│
├─────────────┼──────────────────┼──────────────────┼─────────────────┤
│ CUSTOMER │ ✗ (403) │ ✗ (403) │ ✗ (403) │
│ STAFF │ ✗ (403) │ Own Shop Only │ Own Shop Only │
│ OWNER │ Own Shop Only │ Own Shop Only │ Own Shop Only │
│ ADMIN │ All Shops │ All Shops │ All Shops │
└─────────────┴──────────────────┴──────────────────┴─────────────────┘

CUSTOMER:

- Cannot create/modify/view shops
- Cannot access inventory

STAFF:

- Cannot create/modify shops
- Can VIEW inventory of their shop only
- Can MODIFY inventory of their shop only
- Use Case: Store staff managing daily stock

OWNER:

- Can create their own shop
- Can update/deactivate their own shop
- Can manage inventory of their shop only
- Use Case: Shop owner

ADMIN:

- Can manage all shops (create, view, update, deactivate)
- Can view/modify inventory of any shop
- Use Case: Platform administrator

================================================================================
DEPENDENCY EXAMPLES (For Backend Usage)
================================================================================

Example 1: Verify Shop Ownership
─────────────────────────────────

from app.shops.service import ShopService

shop = ShopService.get_shop(db, shop_id=1) # Raises 404 if not found

# Check if user owns the shop

if current_user.role == RoleEnum.ADMIN: # Admin can access any shop
pass
elif current_user.role == RoleEnum.OWNER and current_user.shop_id == shop.id: # Owner can access their own shop
pass
else:
raise HTTPException(status_code=403, detail="No access")

────────────────────────────────────────────────────────────────────────────────

Example 2: Update Inventory with Validation
────────────────────────────────────────────

from app.inventory.service import InventoryService
from app.inventory.schemas import InventoryUpdateStock

# Verify user has access

user = InventoryService.verify_shop_access(db, shop_id, user_id)

# Update stock with automatic validation

stock_data = InventoryUpdateStock(
product_id=5,
quantity_change=-10, # Sell 10 units
batch_no="BATCH2024001",
notes="Sale transaction"
)

inventory = InventoryService.update_stock(db, shop_id, stock_data)

# Automatically prevents negative stock, updates timestamp

────────────────────────────────────────────────────────────────────────────────

Example 3: Get Low Stock Alerts
───────────────────────────────

from app.inventory.service import InventoryService

alerts = InventoryService.get_low_stock_alerts(db, shop_id=1)

for alert in alerts:
print(f"URGENT: {alert.product_name} needs {alert.shortage} more units")

# Use for: Dashboard widgets, email notifications, SMS alerts

================================================================================
BUSINESS RULES & CONSTRAINTS
================================================================================

INVENTORY CONSTRAINTS:

- Cannot have negative stock (system prevents this)
- min_quantity should be >= 1 (recommended)
- selling_price should be > cost_price
- batch_no can be NULL (single batch)
- expiry_date is optional (for non-perishable items)

SHOP CONSTRAINTS:

- Email must be unique across all shops
- GST number (if provided) must be unique
- PAN number (if provided) must be unique
- Pincode must be 6 digits
- Phone must be 9-15 digits
- delivery_radius_km must be 1-100 km

MULTI-SHOP SUPPORT:

- Each user belongs to exactly ONE shop (shop_id in users table)
- Each product belongs to ONE shop
- Each inventory entry ties a product to a shop
- Staff and owners can only manage their own shop
- Admin can manage all shops
- Customer has read-only access (future: can be toggled)

OFFLINE-FIRST READY:

- Inventory model supports batch tracking (for sync conflicts)
- last_updated timestamps enable conflict resolution
- all_updated enables timestamp-based sync
- No external API dependencies
- Local SQLite can be synced to central database

FUTURE MARKETPLACE SUPPORT:

- Shop table prepared for multi-vendor marketplace
- inventory table uses shop_id for easy multi-shop queries
- user.shop_id enables shop isolation
- RBAC structure allows vendor verification
- ready for: Marketplace orders, commission tracking, rating systems

================================================================================
CURL EXAMPLES
================================================================================

1. Register User
   curl -X POST http://localhost:8000/api/v1/auth/register \\
   -H "Content-Type: application/json" \\
   -d '{
   "email": "owner@shop.com",
   "name": "Shop Owner",
   "phone": "9876543210",
   "password": "SecurePass123!"
   }'

2. Login
   curl -X POST http://localhost:8000/api/v1/auth/login \\
   -H "Content-Type: application/x-www-form-urlencoded" \\
   -d "email=owner@shop.com&password=SecurePass123!"

3. Create Shop (use token from login)
   curl -X POST http://localhost:8000/api/v1/shops \\
   -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
   -H "Content-Type: application/json" \\
   -d '{
   "name": "Fresh Produce",
   "address": "123 Main St",
   "city": "Mumbai",
   "state": "Maharashtra",
   "pincode": "400001",
   "phone": "9876543210",
   "email": "shop@example.com",
   "delivery_radius_km": 5
   }'

4. Get Shop Details
   curl -X GET http://localhost:8000/api/v1/shops/1 \\
   -H "Authorization: Bearer YOUR_TOKEN_HERE"

5. Add Inventory
   curl -X POST http://localhost:8000/api/v1/inventory \\
   -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
   -H "Content-Type: application/json" \\
   -d '{
   "product_id": 5,
   "quantity": 100,
   "min_quantity": 20,
   "cost_price": 45.50,
   "selling_price": 65.00,
   "batch_no": "BATCH001"
   }'

6. Update Stock
   curl -X PATCH http://localhost:8000/api/v1/inventory/update-stock \\
   -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
   -H "Content-Type: application/json" \\
   -d '{
   "product_id": 5,
   "quantity_change": 50,
   "batch_no": "BATCH001",
   "notes": "Received from supplier"
   }'

7. Get Shop Inventory
   curl -X GET "http://localhost:8000/api/v1/inventory/shop/1?skip=0&limit=20" \\
   -H "Authorization: Bearer YOUR_TOKEN_HERE"

8. Get Low Stock Alerts
   curl -X GET http://localhost:8000/api/v1/inventory/low-stock/1 \\
   -H "Authorization: Bearer YOUR_TOKEN_HERE"

================================================================================
TESTING CHECKLIST
================================================================================

Shop Management:
☐ Create shop with valid data
☐ Create shop as non-owner (should get 403)
☐ Create shop with duplicate email (should get 409)
☐ Get own shop details
☐ Get shop of different owner (should get 403 for non-admin)
☐ Get shop as admin (should succeed)
☐ List shops as non-admin (should get 403)
☐ List shops as admin (should succeed)
☐ Update own shop
☐ Update other's shop as non-admin (should get 403)
☐ Deactivate own shop
☐ Deactivate other's shop as non-admin (should get 403)

Inventory Management:
☐ Add product to inventory
☐ Add duplicate batch (should get 409)
☐ Add with selling_price < cost_price (should get 400)
☐ Update stock with valid change
☐ Update stock with negative result (should prevent and return 400)
☐ Get inventory of own shop
☐ Get inventory with pagination
☐ Get low stock alerts
☐ Verify summary statistics in inventory response

RBAC:
☐ Customer tries to access shop (should get 403)
☐ Customer tries to modify inventory (should get 403)
☐ Staff can view own shop inventory
☐ Staff cannot modify (verify permissions)
☐ Owner can access own shop
☐ Owner cannot access other shop
☐ Admin can access all shops

================================================================================
DATABASE SCHEMA SUMMARY
================================================================================

Inventory Table:
CREATE TABLE inventory (
id INTEGER PRIMARY KEY,
shop_id INTEGER NOT NULL FK(shops.id),
product_id INTEGER NOT NULL FK(products.id),
quantity INTEGER NOT NULL DEFAULT 0,
min_quantity INTEGER NOT NULL DEFAULT 10,
cost_price NUMERIC(10,2) NOT NULL,
selling_price NUMERIC(10,2) NOT NULL,
batch_no VARCHAR(100),
expiry_date DATETIME,
last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
UNIQUE (shop_id, product_id, batch_no),
INDEX idx_inventory_shop(shop_id),
INDEX idx_inventory_product(product_id),
INDEX idx_inventory_low_stock(shop_id, quantity),
INDEX idx_inventory_expiry(shop_id, expiry_date)
);

Used Tables (existing):

- shops: Store information
- users: User accounts with shop_id
- products: Product master (with shop_id)

================================================================================
FILE STRUCTURE
================================================================================

app/shops/
├── **init**.py (empty)
├── models.py (re-exports from shared.models)
├── schemas.py (Pydantic schemas)
├── service.py (Business logic)
└── router.py (FastAPI routes)

app/inventory/
├── **init**.py (empty)
├── models.py (re-exports from shared.models)
├── schemas.py (Pydantic schemas)
├── service.py (Business logic)
└── router.py (FastAPI routes)

shared/models.py (UPDATED: added Inventory model)
main_with_auth.py (UPDATED: added shop and inventory routers)

================================================================================
FUTURE ENHANCEMENTS
================================================================================

Planned Features:

1. Expiry date tracking and alerts for perishables
2. Batch-level stock movements
3. Supplier integration
4. Stock transfer between shops
5. Advanced analytics (ABC analysis, stock turnover)
6. Purchase order automation
7. Warehouse management integration
8. Multi-location inventory (main + branches)
9. Real-time stock sync for offline-first
10. Stock forecast predictions

================================================================================
"""
