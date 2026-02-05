# Orders & Order Lifecycle - Implementation Guide

## ✅ STEP 3 Complete: Orders & Order Lifecycle

This document covers the complete Orders & Order Lifecycle implementation for SmartKirana AI.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Database Schema](#database-schema)
4. [API Endpoints](#api-endpoints)
5. [Order Lifecycle](#order-lifecycle)
6. [Role-Based Access Control](#role-based-access-control)
7. [Inventory Integration](#inventory-integration)
8. [API Examples](#api-examples)
9. [Error Handling](#error-handling)
10. [Testing Checklist](#testing-checklist)

---

## Overview

### What's New (STEP 3)

The Orders & Order Lifecycle module provides:

✅ **Order Creation** - Place orders with automatic inventory deduction  
✅ **Order Items** - Track products, quantities, and pricing per order  
✅ **Order Lifecycle** - Complete status flow: PLACED → ACCEPTED → PACKED → OUT_FOR_DELIVERY → DELIVERED  
✅ **Inventory Management** - Automatic stock reduction on order placement  
✅ **Negative Stock Prevention** - Prevents orders if inventory insufficient  
✅ **Order Retrieval** - List orders with pagination and filtering  
✅ **Order Status Updates** - Transition orders through lifecycle  
✅ **Dashboard & Analytics** - Order statistics and metrics  
✅ **RBAC Integration** - Role-based access control with 4 roles  
✅ **Production-Ready** - Complete error handling and validation

### Key Features

- **Multi-Shop Support** - Orders isolated per shop
- **Inventory Deduction** - Real-time stock reduction
- **Credit Sales** - Support for credit/post-paid sales
- **Tax Calculation** - Automatic GST/tax computation
- **Status Transitions** - Validated workflow with business rules
- **Order Cancellation** - Restore inventory when cancelling
- **Dashboard** - Real-time order metrics and analytics

---

## Architecture

### Module Structure

```
app/orders/
├── __init__.py          (Module marker)
├── models.py            (Import wrapper for Order, OrderItem)
├── schemas.py           (Pydantic validation schemas)
├── service.py           (Business logic & database operations)
└── router.py            (FastAPI endpoints with RBAC)
```

### Database Tables

```
orders
├── id (PK)
├── shop_id (FK) ─────────┐
├── customer_id (FK)      │
├── order_number          │
├── order_date            │
├── subtotal              │
├── tax_amount            │
├── total_amount          │
├── order_status          │
├── payment_status        │
├── created_by (FK)       │
└── ... (other fields)    │
                          │
order_items              │
├── id (PK)              │
├── order_id (FK) ─────┐ │
├── product_id (FK)    │ │
├── shop_id (FK) ──────┤─┘
├── quantity           │
├── unit_price         │
├── line_total         │
└── ... (pricing)      │
                       │
Relationships:        │
└─ Order → OrderItem ─┘
  (CASCADE delete)
```

### Data Flow

```
Customer/Staff
     │
     ▼
[POST /api/v1/orders/shops/{shop_id}]
     │
     ├─ Verify User Access (RBAC)
     │
     ├─ Validate Inventory Available
     │
     ├─ Calculate Totals (Subtotal, Tax, Total)
     │
     ├─ DEDUCT INVENTORY (Atomic operation)
     │
     ├─ Create Order
     │
     ├─ Create OrderItems
     │
     └─ Return Order (201 Created)
            │
            ▼
      [Order PLACED]
            │
            ├─ [PATCH] Update Status → ACCEPTED
            ├─ [PATCH] Update Status → PACKED
            ├─ [PATCH] Update Status → OUT_FOR_DELIVERY
            ├─ [PATCH] Update Status → DELIVERED
            │
            └─ [GET] View Order Details & Items
```

---

## Database Schema

### Order Table

```sql
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL (FK shops.id),
    customer_id INTEGER (FK users.id),
    order_number VARCHAR(50) NOT NULL UNIQUE,
    order_date DATETIME DEFAULT NOW,

    subtotal DECIMAL(15,2),
    discount_amount DECIMAL(15,2) DEFAULT 0,
    tax_amount DECIMAL(15,2) DEFAULT 0,
    total_amount DECIMAL(15,2),

    payment_method VARCHAR(50),
    payment_status ENUM('pending','completed','failed','refunded'),
    payment_date DATETIME,

    order_status ENUM('placed','accepted','packed','out_for_delivery','delivered','cancelled'),
    delivery_date DATETIME,

    customer_name VARCHAR(255),
    customer_phone VARCHAR(20),
    shipping_address TEXT,

    is_credit_sale BOOLEAN DEFAULT 0,
    credit_duration_days INTEGER,

    created_by INTEGER NOT NULL (FK users.id),
    notes TEXT,

    created_at DATETIME,
    updated_at DATETIME,

    UNIQUE (shop_id, order_number),
    INDEX idx_orders_customer (shop_id, customer_id),
    INDEX idx_orders_date (shop_id, order_date),
    INDEX idx_orders_status (shop_id, order_status)
);
```

### OrderItem Table

```sql
CREATE TABLE order_items (
    id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL (FK orders.id ON DELETE CASCADE),
    product_id INTEGER NOT NULL (FK products.id),
    shop_id INTEGER NOT NULL (FK shops.id),

    product_name VARCHAR(255),
    quantity INTEGER,
    unit_price DECIMAL(10,2),

    gst_rate DECIMAL(5,2),
    gst_amount DECIMAL(10,2),
    discount_on_item DECIMAL(10,2) DEFAULT 0,
    line_total DECIMAL(15,2),

    created_at DATETIME,

    INDEX idx_order_items_order (order_id),
    INDEX idx_order_items_product (shop_id, product_id)
);
```

### Order Status Enum

```python
PLACED              # Order just created
ACCEPTED            # Shop accepted the order
PACKED              # Order packed/ready
OUT_FOR_DELIVERY    # Order sent for delivery
DELIVERED           # Order delivered to customer
CANCELLED           # Order cancelled
```

---

## API Endpoints

### 1. Create Order (POST)

**Endpoint:** `POST /api/v1/orders/shops/{shop_id}`

**Authentication:** Required (Bearer JWT)

**Authorization:**

- CUSTOMER: Can place orders for themselves
- STAFF/OWNER: Can place orders for their shop
- ADMIN: Can place orders for any shop

**Request Body:**

```json
{
  "customer_id": 123,
  "customer_name": "John Doe",
  "customer_phone": "9876543210",
  "shipping_address": "123 Main St, City, State 12345",
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
  "notes": "Deliver in morning",
  "is_credit_sale": false,
  "credit_duration_days": null
}
```

**Success Response (201 Created):**

```json
{
  "id": 1,
  "shop_id": 1,
  "order_number": "ORD20260205121500011234",
  "order_date": "2026-02-05T12:15:00",
  "customer_id": 123,
  "customer_name": "John Doe",
  "customer_phone": "9876543210",
  "shipping_address": "123 Main St, City, State 12345",
  "subtotal": "249.97",
  "discount_amount": "0.00",
  "tax_amount": "44.99",
  "total_amount": "294.96",
  "order_status": "placed",
  "payment_status": "pending",
  "payment_method": null,
  "payment_date": null,
  "items": [
    {
      "id": 1,
      "order_id": 1,
      "product_id": 1,
      "shop_id": 1,
      "product_name": "Milk 1L",
      "quantity": 2,
      "unit_price": "99.99",
      "gst_rate": "5.00",
      "gst_amount": "9.99",
      "discount_on_item": "0.00",
      "line_total": "199.98",
      "created_at": "2026-02-05T12:15:00"
    }
  ],
  "created_at": "2026-02-05T12:15:00",
  "updated_at": "2026-02-05T12:15:00"
}
```

**Error Responses:**

```json
// 400 Bad Request - Validation error
{
  "detail": "Order must have at least one item"
}

// 403 Forbidden - No access to shop
{
  "detail": "User does not belong to shop 1"
}

// 404 Not Found - Shop not found
{
  "detail": "Shop 999 not found"
}

// 409 Conflict - Insufficient inventory
{
  "detail": "Insufficient stock for Milk 1L. Available: 5, Requested: 10"
}
```

---

### 2. Get Order Details (GET)

**Endpoint:** `GET /api/v1/orders/shops/{shop_id}/{order_id}`

**Authentication:** Required

**Authorization:**

- CUSTOMER: View own orders only
- STAFF/OWNER: View shop orders
- ADMIN: View all orders

**Response (200 OK):**

```json
{
  "id": 1,
  "shop_id": 1,
  "order_number": "ORD20260205121500011234",
  "customer_name": "John Doe",
  "order_status": "placed",
  "total_amount": "294.96",
  "items": [
    {
      "id": 1,
      "product_id": 1,
      "product_name": "Milk 1L",
      "quantity": 2,
      "unit_price": "99.99",
      "line_total": "199.98"
    }
  ],
  "created_at": "2026-02-05T12:15:00"
}
```

---

### 3. List Orders (GET)

**Endpoint:** `GET /api/v1/orders/shops/{shop_id}`

**Query Parameters:**

- `skip` (int, default=0) - Skip records for pagination
- `limit` (int, default=20, max=100) - Limit records
- `status` (enum, optional) - Filter by order status

**Authentication:** Required

**Authorization:** STAFF/OWNER/ADMIN only

**Example:**

```
GET /api/v1/orders/shops/1?skip=0&limit=20&status=placed
```

**Response (200 OK):**

```json
{
  "orders": [
    {
      "id": 1,
      "order_number": "ORD20260205121500011234",
      "customer_name": "John Doe",
      "order_status": "placed",
      "total_amount": "294.96"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 20
}
```

---

### 4. Get My Orders (GET)

**Endpoint:** `GET /api/v1/orders/me/my-orders`

**Authentication:** Required

**Authorization:** CUSTOMER only

**Query Parameters:**

- `skip` (int, default=0)
- `limit` (int, default=20, max=100)

**Response (200 OK):**

```json
{
  "orders": [
    {
      "id": 1,
      "order_number": "ORD20260205121500011234",
      "order_date": "2026-02-05T12:15:00",
      "order_status": "placed",
      "total_amount": "294.96"
    }
  ],
  "total": 5,
  "skip": 0,
  "limit": 20
}
```

---

### 5. Update Order Status (PATCH)

**Endpoint:** `PATCH /api/v1/orders/shops/{shop_id}/{order_id}/status`

**Authentication:** Required

**Authorization:** STAFF/OWNER/ADMIN only

**Request Body:**

```json
{
  "new_status": "accepted",
  "notes": "Order confirmed by shop"
}
```

**Response (200 OK):**

```json
{
  "id": 1,
  "order_number": "ORD20260205121500011234",
  "order_status": "accepted",
  "updated_at": "2026-02-05T12:16:00"
}
```

**Valid Transitions:**

```
PLACED ─→ ACCEPTED | CANCELLED
ACCEPTED ─→ PACKED | CANCELLED
PACKED ─→ OUT_FOR_DELIVERY | CANCELLED
OUT_FOR_DELIVERY ─→ DELIVERED | CANCELLED
DELIVERED ─→ (Final state)
CANCELLED ─→ (Final state)
```

---

### 6. Order Dashboard (GET)

**Endpoint:** `GET /api/v1/orders/shops/{shop_id}/dashboard`

**Authentication:** Required

**Authorization:** STAFF/OWNER/ADMIN only

**Response (200 OK):**

```json
{
  "total_orders": 42,
  "placed_orders": 3,
  "accepted_orders": 5,
  "packed_orders": 2,
  "out_for_delivery_orders": 1,
  "delivered_orders": 31,
  "cancelled_orders": 0,
  "total_revenue": "15234.50",
  "average_order_value": "362.73",
  "recent_orders": [
    {
      "id": 42,
      "order_number": "ORD20260205123000011242",
      "order_date": "2026-02-05T12:30:00",
      "customer_name": "Jane Smith",
      "order_status": "placed",
      "total_amount": "599.99",
      "item_count": 3
    }
  ]
}
```

---

## Order Lifecycle

### Visual Flow

```
┌─────────────┐
│   PLACED    │  Order created, inventory deducted
└──────┬──────┘
       │
       │ Shop accepts order
       ▼
┌─────────────┐
│  ACCEPTED   │  Payment confirmed
└──────┬──────┘
       │
       │ Items packed & ready
       ▼
┌─────────────┐
│   PACKED    │  Ready for shipment
└──────┬──────┘
       │
       │ Handed to delivery partner
       ▼
┌──────────────────────┐
│  OUT_FOR_DELIVERY    │  In transit
└──────┬───────────────┘
       │
       │ Delivered to customer
       ▼
┌─────────────┐
│  DELIVERED  │  Order complete
└─────────────┘

Alternative: Cancel at any point
       │
       ├─→ CANCELLED  (Inventory restored)
```

### Status Meanings

| Status           | Meaning              | Inventory Impact | Next Steps       |
| ---------------- | -------------------- | ---------------- | ---------------- |
| PLACED           | Order created        | ✅ Deducted      | Await acceptance |
| ACCEPTED         | Shop confirmed       | No change        | Pack items       |
| PACKED           | Items packed         | No change        | Hand to delivery |
| OUT_FOR_DELIVERY | In transit           | No change        | Await delivery   |
| DELIVERED        | Received by customer | No change        | Complete         |
| CANCELLED        | Order cancelled      | ✅ Restored      | Final            |

---

## Role-Based Access Control

### RBAC Matrix

```
┌──────────────┬─────────┬──────────┬──────────────┬───────┐
│ Operation    │Customer │ Staff    │ Owner        │ Admin │
├──────────────┼─────────┼──────────┼──────────────┼───────┤
│ Create Order │ ✅Own   │ ✅ Shop  │ ✅ Shop      │ ✅All │
│ View Order   │ ✅Own   │ ✅ Shop  │ ✅ Shop      │ ✅All │
│ List Orders  │ ❌      │ ✅ Shop  │ ✅ Shop      │ ✅All │
│ Update Status│ ❌      │ ✅ Shop  │ ✅ Shop      │ ✅All │
│ Dashboard    │ ❌      │ ✅ Shop  │ ✅ Shop      │ ✅All │
└──────────────┴─────────┴──────────┴──────────────┴───────┘
```

### Role Permissions

**CUSTOMER** (Role: "customer")

- ✅ Place own orders
- ✅ View own orders via `/api/v1/orders/me/my-orders`
- ❌ Cannot manage orders
- ❌ Cannot view other customer orders

**STAFF** (Role: "staff")

- ✅ Place orders for own shop
- ✅ View all shop orders
- ✅ Update order status
- ✅ View shop dashboard
- ❌ Cannot access other shops

**OWNER** (Role: "owner")

- ✅ Place orders for own shop
- ✅ View all shop orders
- ✅ Update order status
- ✅ View shop dashboard
- ❌ Cannot access other shops

**ADMIN** (Role: "admin")

- ✅ Place orders for any shop
- ✅ View all orders (any shop)
- ✅ Update any order status
- ✅ View all dashboards
- ✅ Full system access

---

## Inventory Integration

### Automatic Inventory Deduction

When an order is created:

1. **Validate Availability** - Check each product has sufficient stock
2. **Prevent Conflicts** - Return 409 Conflict if any product unavailable
3. **Atomic Deduction** - Deduct all items or none (no partial orders)
4. **Track Movement** - Update `last_updated` timestamp

```python
# Validation
Order has: 2x Milk (stock: 10)
           1x Bread (stock: 0)

Result: ❌ FAIL - Bread out of stock
No inventory deducted

---

Order has: 2x Milk (stock: 10)
           1x Bread (stock: 5)

Result: ✅ SUCCESS
Milk: 10 → 8
Bread: 5 → 4
```

### Inventory Restoration

When an order is cancelled:

1. **Restore Stock** - Add back deducted quantities
2. **Update Timestamp** - Mark inventory as updated
3. **Maintain Audit Trail** - Keep in stock_movements table

```python
Before: Milk (stock: 8)
Cancel Order: -2x Milk

After: Milk (stock: 10)
```

### Prevention of Negative Stock

```python
# Service layer validation
def deduct_inventory(shop_id, items):
    for product_id, quantity in items:
        inventory = db.query(Inventory).get(product_id)

        if inventory.quantity < quantity:  # ← Prevents negative stock
            raise ValueError("Insufficient stock")

        inventory.quantity -= quantity
```

---

## API Examples

### Example 1: Create Order as Customer

```bash
# 1. Register and login as customer
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "phone": "9876543210",
    "email": "customer@example.com",
    "name": "John Doe",
    "password": "secure_password",
    "shop_id": 1,
    "role": "customer"
  }'

# Response includes: access_token

# 2. Place order as customer
curl -X POST http://localhost:8000/api/v1/orders/shops/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_name": "John Doe",
    "customer_phone": "9876543210",
    "shipping_address": "123 Main St, City",
    "items": [
      {
        "product_id": 1,
        "quantity": 2,
        "unit_price": "99.99"
      }
    ]
  }'

# Response: Order created with status PLACED
```

### Example 2: Update Order Status as Staff

```bash
# Update order to ACCEPTED
curl -X PATCH http://localhost:8000/api/v1/orders/shops/1/1/status \
  -H "Authorization: Bearer STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "accepted",
    "notes": "Order confirmed, ready to pack"
  }'

# Update order to PACKED
curl -X PATCH http://localhost:8000/api/v1/orders/shops/1/1/status \
  -H "Authorization: Bearer STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "packed",
    "notes": "Items packed and labeled"
  }'

# Update order to OUT_FOR_DELIVERY
curl -X PATCH http://localhost:8000/api/v1/orders/shops/1/1/status \
  -H "Authorization: Bearer STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "out_for_delivery",
    "notes": "Handed to delivery partner"
  }'

# Update order to DELIVERED
curl -X PATCH http://localhost:8000/api/v1/orders/shops/1/1/status \
  -H "Authorization: Bearer STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "delivered"
  }'
```

### Example 3: Cancel Order with Inventory Restoration

```bash
# Cancel order (restores inventory automatically)
curl -X PATCH http://localhost:8000/api/v1/orders/shops/1/1/status \
  -H "Authorization: Bearer STAFF_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_status": "cancelled",
    "notes": "Customer requested cancellation"
  }'

# Result: Order cancelled, inventory restored
```

### Example 4: View Dashboard Statistics

```bash
curl -X GET http://localhost:8000/api/v1/orders/shops/1/dashboard \
  -H "Authorization: Bearer STAFF_TOKEN"

# Response:
{
  "total_orders": 42,
  "placed_orders": 3,
  "accepted_orders": 5,
  "packed_orders": 2,
  "out_for_delivery_orders": 1,
  "delivered_orders": 31,
  "cancelled_orders": 0,
  "total_revenue": "15234.50",
  "average_order_value": "362.73",
  "recent_orders": [...]
}
```

---

## Error Handling

### HTTP Status Codes

| Code | Meaning     | Example                    |
| ---- | ----------- | -------------------------- |
| 201  | Created     | Order successfully created |
| 200  | OK          | Order retrieved/updated    |
| 400  | Bad Request | Invalid request body       |
| 403  | Forbidden   | Unauthorized access        |
| 404  | Not Found   | Order/Shop not found       |
| 409  | Conflict    | Insufficient inventory     |

### Common Error Scenarios

```json
// Missing inventory
{
  "detail": "Insufficient stock for Milk 1L. Available: 5, Requested: 10"
}

// Product not found
{
  "detail": "Product 999 not found"
}

// Invalid status transition
{
  "detail": "Cannot transition from placed to delivered"
}

// Unauthorized access
{
  "detail": "User does not belong to shop 1"
}

// No items in order
{
  "detail": "Order must have at least one item"
}
```

---

## Testing Checklist

### Prerequisites

- [ ] Server running on http://localhost:8000
- [ ] Database initialized with tables
- [ ] Swagger UI accessible at /api/docs

### Manual Testing via Swagger UI

#### Phase 1: Authentication

- [ ] Register as CUSTOMER
- [ ] Register as STAFF
- [ ] Login and get JWT token
- [ ] Use token in Authorization header

#### Phase 2: Create Orders

- [ ] Customer places own order (201 Created)
- [ ] Staff places shop order (201 Created)
- [ ] Create order with multiple items
- [ ] Create order with insufficient inventory (409 Conflict)
- [ ] Create order with invalid product (404 Not Found)
- [ ] Verify inventory deducted after order

#### Phase 3: Retrieve Orders

- [ ] Customer views own orders
- [ ] Staff views shop orders
- [ ] Admin views all orders
- [ ] List orders with pagination (skip, limit)
- [ ] Filter orders by status
- [ ] Single order details

#### Phase 4: Status Updates

- [ ] Update PLACED → ACCEPTED
- [ ] Update ACCEPTED → PACKED
- [ ] Update PACKED → OUT_FOR_DELIVERY
- [ ] Update OUT_FOR_DELIVERY → DELIVERED
- [ ] Cancel order from PLACED
- [ ] Cancel order from PACKED
- [ ] Verify inventory restored on cancel

#### Phase 5: Dashboard & Analytics

- [ ] View order dashboard stats
- [ ] Verify order counts by status
- [ ] Check total revenue calculation
- [ ] Check average order value
- [ ] View recent orders

#### Phase 6: RBAC & Permissions

- [ ] Customer cannot update order status (403)
- [ ] Staff cannot access other shop (403)
- [ ] Admin can access any shop (200)
- [ ] Invalid user cannot create order (403)

#### Phase 7: Edge Cases

- [ ] Create order with 0 items (400)
- [ ] Create order with invalid phone format (400)
- [ ] Negative quantity in order (400)
- [ ] Very large order (test precision)
- [ ] Create order with expired token (401)

### Curl Testing

```bash
# Test create order
curl -X POST http://localhost:8000/api/v1/orders/shops/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Test list orders
curl -X GET "http://localhost:8000/api/v1/orders/shops/1?skip=0&limit=20" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test status update
curl -X PATCH http://localhost:8000/api/v1/orders/shops/1/1/status \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{...}'

# Test dashboard
curl -X GET http://localhost:8000/api/v1/orders/shops/1/dashboard \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Summary

**STEP 3 - Orders & Order Lifecycle** delivers:

✅ 6 production-ready API endpoints  
✅ Complete order status lifecycle  
✅ Automatic inventory deduction & restoration  
✅ Negative stock prevention  
✅ Full RBAC with 4 roles  
✅ Order dashboard with analytics  
✅ Comprehensive error handling  
✅ Tax/GST calculation  
✅ Credit sale support  
✅ Complete testing checklist

**Next Steps:**

- Test all endpoints via Swagger UI
- Integrate with payment gateway
- Implement order notifications
- Add order history/audit trail
