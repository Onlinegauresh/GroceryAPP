# """

# QUICK START GUIDE - Shop & Inventory Management

Get started with Shop and Inventory APIs in 5 minutes!

================================================================================
STEP 1: Start the Server (if not running)
================================================================================

Terminal:
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
.\venv\Scripts\python.exe -m uvicorn main_with_auth:app --host 0.0.0.0 --port 8000

Or using uvicorn directly:
.\venv\Scripts\uvicorn.exe main_with_auth:app --host 0.0.0.0 --port 8000

Check if running:

- Open http://localhost:8000/api/docs in your browser
- You should see Swagger UI with all endpoints

================================================================================
STEP 2: Register & Login (Get JWT Token)
================================================================================

Swagger UI approach (easiest):

1. Go to http://localhost:8000/api/docs
2. Expand "auth" section
3. Click "POST /api/v1/auth/register"
4. Click "Try it out"
5. Fill in the form:
   - email: shopowner@example.com
   - name: Test Shop Owner
   - phone: 9876543210
   - password: SecurePass123!
6. Click "Execute"
7. Copy the "id" from response (you'll need this)

Then Login:

1. Click "POST /api/v1/auth/login"
2. Click "Try it out"
3. Fill in form:
   - email: shopowner@example.com
   - password: SecurePass123!
4. Click "Execute"
5. Copy the "access_token" from response
6. Click the green "Authorize" button at top
7. Paste: Bearer {access_token}
8. Click "Authorize"

Now all endpoints will work with your authentication!

================================================================================
STEP 3: Create a Shop
================================================================================

Swagger UI:

1. Expand "shops" section
2. Click "POST /api/v1/shops"
3. Click "Try it out"
4. Fill in example:
   {
   "name": "Fresh Produce Market",
   "address": "123 Market Street, Ground Floor",
   "city": "Mumbai",
   "state": "Maharashtra",
   "pincode": "400001",
   "phone": "9876543210",
   "email": "freshproduce@example.com",
   "delivery_radius_km": 5,
   "shop_category": "Grocery"
   }
5. Click "Execute"
6. Copy the "id" from response (e.g., id: 1)

================================================================================
STEP 4: Get Shop Details
================================================================================

Swagger UI:

1. Click "GET /api/v1/shops/{shop_id}"
2. Click "Try it out"
3. Enter the shop_id from previous step (e.g., 1)
4. Click "Execute"
5. You should see detailed shop info with product count

================================================================================
STEP 5: Create a Product (if needed)
================================================================================

Note: Products must exist before adding to inventory.
Check existing products first:

1. Click "GET /api/v1/products"
2. Click "Execute"
3. Note down a product_id

If you need to create a product:

1. Click "POST /api/v1/products"
2. Fill in product details
3. Note the product_id from response

================================================================================
STEP 6: Add Products to Inventory
================================================================================

Swagger UI:

1. Click "POST /api/v1/inventory"
2. Click "Try it out"
3. Fill in example:
   {
   "product_id": 1,
   "quantity": 100,
   "min_quantity": 20,
   "cost_price": 45.50,
   "selling_price": 65.00,
   "batch_no": "BATCH2024001",
   "expiry_date": "2026-08-05T00:00:00Z"
   }
4. Click "Execute"
5. You should get 201 Created response

================================================================================
STEP 7: Update Stock Quantity
================================================================================

Swagger UI:

1. Click "PATCH /api/v1/inventory/update-stock"
2. Click "Try it out"
3. Fill in example:
   {
   "product_id": 1,
   "quantity_change": 50,
   "batch_no": "BATCH2024001",
   "notes": "Received from supplier"
   }
4. Click "Execute"
5. Quantity should increase by 50

Try reducing stock:
{
"product_id": 1,
"quantity_change": -10,
"batch_no": "BATCH2024001",
"notes": "Sale transaction"
}

================================================================================
STEP 8: View Shop Inventory
================================================================================

Swagger UI:

1. Click "GET /api/v1/inventory/shop/{shop_id}"
2. Click "Try it out"
3. Enter your shop_id (e.g., 1)
4. Click "Execute"
5. See all products, quantities, and inventory summary

Example Response shows:

- Total products in inventory
- Stock status (in_stock, low_stock, out_of_stock)
- Summary: in_stock count, low_stock count, total value
- Pagination: total, skip, limit

================================================================================
STEP 9: Get Low Stock Alerts
================================================================================

Swagger UI:

1. Click "GET /api/v1/inventory/low-stock/{shop_id}"
2. Click "Try it out"
3. Enter your shop_id
4. Click "Execute"
5. See products below min_quantity with shortage amounts

This is useful for:

- Generating purchase orders
- Dashboard alerts
- Email notifications

================================================================================
TROUBLESHOOTING
================================================================================

ERROR: 403 Forbidden
Fix: Make sure you have Bearer token in Authorize header

- Click green "Authorize" button at top
- Paste: Bearer {your_token}
- Click "Authorize"

ERROR: User doesn't have OWNER role
Fix: You need to update user role in database

- Currently all new users get CUSTOMER role
- To test as OWNER/ADMIN, ask admin to change your role
- Or modify user role in database directly

ERROR: Cannot reduce stock below 0
Fix: Quantity change is too negative

- Current stock is 10, trying to reduce by 20
- Use positive number to add stock, negative to remove
- Maximum removal = current quantity

ERROR: Inventory already exists
Fix: Batch combination already added

- Each shop can have multiple batches of same product
- Use different batch_no or remove duplicate

ERROR: Product not found in this shop
Fix: Product belongs to different shop

- Products are shop-specific
- Create product in the correct shop first

================================================================================
COMMON WORKFLOWS
================================================================================

WORKFLOW 1: Setting up a new shop

1. Register as owner
2. Create shop
3. Add first products to inventory
4. Set min_quantity for each product
5. Done! Inventory is ready

WORKFLOW 2: Receiving new stock

1. POST /api/v1/inventory (add new batch) OR
2. PATCH /api/v1/inventory/update-stock (increase existing)
3. Quantity increases
4. last_updated timestamp updates automatically

WORKFLOW 3: Low stock alerts

1. Set proper min_quantity when adding inventory
2. Regularly check GET /api/v1/inventory/low-stock/{shop_id}
3. Alert shows shortage amount
4. Generate purchase order
5. Update stock when received

WORKFLOW 4: Inventory counting/audit

1. Get current inventory: GET /api/v1/inventory/shop/{shop_id}
2. Compare with physical count
3. For discrepancies use PATCH /api/v1/inventory/update-stock
4. Add notes explaining the adjustment

================================================================================
SAMPLE DATA FOR TESTING
================================================================================

User Registration:
{
"email": "owner@grocery.com",
"name": "Grocery Store Owner",
"phone": "9876543210",
"password": "SecurePass123!"
}

Shop Creation:
{
"name": "Daily Needs Market",
"address": "456 Shopping Plaza, 2nd Floor",
"city": "Bangalore",
"state": "Karnataka",
"pincode": "560001",
"phone": "9876543211",
"email": "dailyneeds@example.com",
"delivery_radius_km": 8,
"shop_category": "Super Market",
"gst_number": "29AABCH9876G1Z0"
}

Inventory Addition:
{
"product_id": 1,
"quantity": 200,
"min_quantity": 25,
"cost_price": 30.00,
"selling_price": 45.00,
"batch_no": "BATCH001",
"expiry_date": "2026-12-31T00:00:00Z"
}

Stock Update - Receive:
{
"product_id": 1,
"quantity_change": 100,
"batch_no": "BATCH001",
"notes": "Received from supplier Rajesh & Co"
}

Stock Update - Sell:
{
"product_id": 1,
"quantity_change": -5,
"batch_no": "BATCH001",
"notes": "Sale to customer"
}

================================================================================
PAGINATION
================================================================================

List endpoints support pagination:

- skip: Number of items to skip (default: 0)
- limit: Number of items to return (default: 20, max: 100)

Example:
GET /api/v1/inventory/shop/1?skip=0&limit=50

To get next page:
GET /api/v1/inventory/shop/1?skip=50&limit=50

Total items returned in "total" field.

================================================================================
ROLE GUIDE
================================================================================

CUSTOMER Role:
✗ Cannot create shops
✗ Cannot access inventory
✓ Can view products (future)
Use Case: End customers

STAFF Role:
✓ Can view inventory of their shop
✓ Can update stock of their shop
✗ Cannot create/modify shops
✗ Cannot access other shops
Use Case: Store assistants, warehouse staff

OWNER Role:
✓ Can create their own shop
✓ Can modify their own shop
✓ Can access inventory of their shop
✗ Cannot access other shops
Use Case: Shop owner/manager

ADMIN Role:
✓ Can manage all shops
✓ Can access all inventories
✓ Can list all shops
✓ Can deactivate shops
Use Case: Platform administrator

================================================================================
TESTING CHECKLIST
================================================================================

✓ Server running on port 8000
✓ Can access Swagger UI
✓ Can register new user
✓ Can login and get token
✓ Can create shop
✓ Can view shop details
✓ Can add inventory
✓ Can update stock (increase)
✓ Can update stock (decrease)
✓ Can view shop inventory
✓ Can get low stock alerts
✓ Cannot access other shop (403)
✓ Stock cannot go negative

================================================================================
NEXT STEPS
================================================================================

1. Read SHOP_INVENTORY_API_DOCUMENTATION.md for complete API reference
2. Test all endpoints in Swagger UI
3. Try different user roles
4. Test error cases
5. Set up automated low stock alerts
6. Integrate with order management
7. Add analytics dashboard

================================================================================
HELPFUL RESOURCES
================================================================================

Swagger UI (Interactive Testing):
http://localhost:8000/api/docs

ReDoc (Read-only Documentation):
http://localhost:8000/api/redoc

API Specification (OpenAPI JSON):
http://localhost:8000/api/openapi.json

Complete Documentation:
/backend/SHOP_INVENTORY_API_DOCUMENTATION.md

Completion Summary:
/backend/SHOP_INVENTORY_COMPLETION_SUMMARY.md

================================================================================
"""
