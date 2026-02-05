# Orders Quick Start - 5 Minute Guide

## Get Started with Order Management in 5 Minutes

This guide walks you through creating and managing orders in SmartKirana AI.

---

## Prerequisites

✅ Server running on http://localhost:8000  
✅ Swagger UI accessible at http://localhost:8000/api/docs  
✅ Authentication working (can login)

---

## Step 1: Open Swagger UI

Go to: **http://localhost:8000/api/docs**

You'll see all available endpoints grouped by tag.

---

## Step 2: Register Users (If Not Done)

### Register as Customer

```
1. Find "auth" section
2. Click "POST /api/v1/auth/register"
3. Click "Try it out"
4. Enter:
   {
     "phone": "9876543210",
     "email": "customer@test.com",
     "name": "John Customer",
     "password": "Test123!",
     "shop_id": 1,
     "role": "customer"
   }
5. Click "Execute"
6. Copy the "access_token" from response
```

### Register as Staff

```
1. Same as above but:
   {
     "phone": "9876543211",
     "email": "staff@test.com",
     "name": "Jane Staff",
     "password": "Test123!",
     "shop_id": 1,
     "role": "staff"
   }
2. Copy the access_token
```

---

## Step 3: Authorize in Swagger UI

```
1. Click "Authorize" button (top right)
2. Enter: Bearer YOUR_TOKEN_HERE
3. Click "Authorize"
4. Click "Close"

Now all requests will include your token automatically!
```

---

## Step 4: Create Your First Order

```
1. Go to "Orders" section
2. Click "POST /api/v1/orders/shops/{shop_id}"
3. Click "Try it out"
4. Set shop_id = 1
5. Enter this JSON:

{
  "customer_name": "John Doe",
  "customer_phone": "9876543210",
  "shipping_address": "123 Main Street, City, State 12345",
  "items": [
    {
      "product_id": 1,
      "quantity": 2,
      "unit_price": "99.99"
    },
    {
      "product_id": 2,
      "quantity": 1,
      "unit_price": "49.99"
    }
  ],
  "notes": "Please deliver in morning",
  "is_credit_sale": false
}

6. Click "Execute"
7. You should get response 201 Created with order details
```

**What Happened:**

- ✅ Order created with status = "placed"
- ✅ Inventory automatically deducted
- ✅ Totals calculated (subtotal, tax, total)
- ✅ Order items created

---

## Step 5: View Your Order

```
1. From Step 4 response, note the order "id" (e.g., id: 1)
2. Click "GET /api/v1/orders/shops/{shop_id}/{order_id}"
3. Click "Try it out"
4. Set:
   - shop_id = 1
   - order_id = 1 (from response above)
5. Click "Execute"
6. See full order details with items
```

---

## Step 6: Update Order Status (as Staff)

```
1. Make sure you're logged in as STAFF user
2. Click "PATCH /api/v1/orders/shops/{shop_id}/{order_id}/status"
3. Click "Try it out"
4. Set:
   - shop_id = 1
   - order_id = 1
5. Enter JSON:

{
  "new_status": "accepted",
  "notes": "Order confirmed by shop"
}

6. Click "Execute"
7. Order status changes to "accepted"
```

**Try the complete flow:**

```
Step 1: "placed" → "accepted"
  {
    "new_status": "accepted",
    "notes": "Order confirmed"
  }

Step 2: "accepted" → "packed"
  {
    "new_status": "packed",
    "notes": "Items packed and ready"
  }

Step 3: "packed" → "out_for_delivery"
  {
    "new_status": "out_for_delivery",
    "notes": "Handed to delivery partner"
  }

Step 4: "out_for_delivery" → "delivered"
  {
    "new_status": "delivered"
  }
```

---

## Step 7: List All Orders (as Staff)

```
1. Click "GET /api/v1/orders/shops/{shop_id}"
2. Click "Try it out"
3. Set:
   - shop_id = 1
   - skip = 0
   - limit = 20
   - status = (leave empty or select "placed", "accepted", etc.)
4. Click "Execute"
5. See all orders for the shop with pagination
```

---

## Step 8: View Order Dashboard (as Staff)

```
1. Click "GET /api/v1/orders/shops/{shop_id}/dashboard"
2. Click "Try it out"
3. Set shop_id = 1
4. Click "Execute"
5. See statistics:
   - Total orders
   - Orders by status (placed, accepted, packed, etc.)
   - Total revenue
   - Average order value
   - Recent orders
```

---

## Step 9: View Your Orders (as Customer)

```
1. Make sure you're logged in as CUSTOMER user
2. Click "GET /api/v1/orders/me/my-orders"
3. Click "Try it out"
4. Set:
   - skip = 0
   - limit = 20
5. Click "Execute"
6. See only your orders
```

---

## Step 10: Cancel an Order

```
1. Click "PATCH /api/v1/orders/shops/{shop_id}/{order_id}/status"
2. Click "Try it out"
3. Set:
   - shop_id = 1
   - order_id = 1
4. Enter JSON:

{
  "new_status": "cancelled",
  "notes": "Customer requested cancellation"
}

5. Click "Execute"
6. Order cancelled and inventory restored automatically
```

---

## Common Scenarios

### Scenario 1: Place Order with Insufficient Inventory

```
Try to create order with:
  product_id: 1
  quantity: 10000  (more than available)

Expected: 409 Conflict
Message: "Insufficient stock for Product Name"
```

### Scenario 2: Customer Tries to Manage Orders

```
As CUSTOMER, try to:
  PATCH /api/v1/orders/shops/1/1/status

Expected: 403 Forbidden
Message: "Only staff, owners, and admins can manage orders"
```

### Scenario 3: Invalid Status Transition

```
Try to go directly from PLACED to DELIVERED:
  "new_status": "delivered"

Expected: 400 Bad Request
Message: "Cannot transition from placed to delivered"
```

### Scenario 4: Create Order Missing Items

```
Try to create order with:
  "items": []

Expected: 400 Bad Request
Message: "Order must have at least one item"
```

---

## Order Status Flow Reference

```
PLACED
  ↓
ACCEPTED
  ↓
PACKED
  ↓
OUT_FOR_DELIVERY
  ↓
DELIVERED

Alternative: Cancel at any point
  ↓
CANCELLED (Inventory restored)
```

---

## Inventory Auto-Deduction

When you create an order, inventory is automatically deducted:

**Before Order:**

```
Product 1 (Milk): 10 units
Product 2 (Bread): 5 units
```

**Create Order:**

```
- Milk: 2 units
- Bread: 1 unit
```

**After Order Created:**

```
Product 1 (Milk): 8 units ✅ Deducted
Product 2 (Bread): 4 units ✅ Deducted
```

**If You Cancel:**

```
Product 1 (Milk): 10 units ✅ Restored
Product 2 (Bread): 5 units ✅ Restored
```

---

## Quick Reference: Endpoints

| Method | Endpoint                                           | Purpose                  |
| ------ | -------------------------------------------------- | ------------------------ |
| POST   | `/api/v1/orders/shops/{shop_id}`                   | Create order             |
| GET    | `/api/v1/orders/shops/{shop_id}`                   | List shop orders         |
| GET    | `/api/v1/orders/shops/{shop_id}/{order_id}`        | Get order details        |
| GET    | `/api/v1/orders/me/my-orders`                      | Get my orders (customer) |
| PATCH  | `/api/v1/orders/shops/{shop_id}/{order_id}/status` | Update status            |
| GET    | `/api/v1/orders/shops/{shop_id}/dashboard`         | View dashboard           |

---

## Roles & Permissions

| Role     | Can Create | Can View | Can Manage |
| -------- | ---------- | -------- | ---------- |
| CUSTOMER | ✅ Own     | ✅ Own   | ❌         |
| STAFF    | ✅ Shop    | ✅ Shop  | ✅         |
| OWNER    | ✅ Shop    | ✅ Shop  | ✅         |
| ADMIN    | ✅ All     | ✅ All   | ✅         |

---

## Troubleshooting

**"Insufficient stock" error:**

- Check available inventory via GET /api/v1/inventory/shop/{shop_id}
- Reduce order quantity
- Cancel other pending orders

**"User does not belong to shop" error:**

- Staff/owners can only manage their own shop
- Use correct shop_id
- Admin can access any shop

**"Cannot transition from X to Y" error:**

- Order status has fixed transitions
- Follow the lifecycle: PLACED → ACCEPTED → PACKED → OUT_FOR_DELIVERY → DELIVERED
- Can cancel from any status

**401 Unauthorized:**

- Token expired or invalid
- Re-login and get new token
- Use "Authorize" button to add token

---

## Next Steps

✅ Created your first order  
✅ Updated order status  
✅ Viewed orders  
✅ Understood auto-deduction

**What to do next:**

1. Read ORDERS_LIFECYCLE_DOCUMENTATION.md for detailed API reference
2. Test with different products and quantities
3. Create multiple orders and filter by status
4. Integrate with payment gateway (future)
5. Add order notifications (future)

---

Happy ordering! 🎉
