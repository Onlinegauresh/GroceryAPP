# SmartKirana AI - Accounting System Documentation

**Version:** 1.0.0  
**Status:** Production Ready  
**Last Updated:** 2024-01-15

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture & Design](#architecture--design)
3. [Database Schema](#database-schema)
4. [Automatic Accounting Logic](#automatic-accounting-logic)
5. [API Endpoints](#api-endpoints)
6. [RBAC & Security](#rbac--security)
7. [Report Specifications](#report-specifications)
8. [Integration with Orders](#integration-with-orders)
9. [Error Handling](#error-handling)
10. [Testing Scenarios](#testing-scenarios)

---

## System Overview

The SmartKirana AI Accounting System is a **Tally-like, double-entry bookkeeping engine** that automatically records all financial transactions from orders.

### Key Features

✅ **Automatic Entry Generation**

- Entries created automatically when orders are DELIVERED
- Entries reversed when orders are CANCELLED
- Prevention of duplicate entries via reference tracking

✅ **Complete Double-Entry Bookkeeping**

- Debit account and credit account for every transaction
- Sales recorded as Revenue
- Cash/Credit tracking in Assets
- Khata (credit) accounts for customers

✅ **Cash & Credit Support**

- Cash sales recorded immediately in Cash Book
- Credit sales tracked in Khata Accounts
- Credit limit enforcement per customer
- Balance tracking

✅ **GST Compliance**

- Tax amount tracking per order
- CGST, SGST, IGST breakdown
- Invoice number association
- Tax reporting ready

✅ **Financial Reporting**

- Daily sales reports
- Monthly Profit & Loss statements
- Cash book with opening/closing balances
- Customer credit statements (khata)

✅ **Multi-shop Support**

- Isolated accounting per shop
- Shop-level financial reporting
- Separate cash accounts per shop

---

## Architecture & Design

### Philosophy: Tally-Inspired Double-Entry Bookkeeping

Every transaction follows the fundamental accounting equation:

```
Debit Amount = Credit Amount
```

### Transaction Flow

```
Order Placed
    ↓
Order Delivered (status → DELIVERED)
    ↓
Automatic Accounting Service Triggered
    ↓
1. Create Ledger Entry (Sales)
2. Create GST Record (Tax tracking)
3. Record Cash/Khata (Payment method)
    ↓
Entries Visible in Reports
```

### Account Hierarchy

```
Assets
├── Cash (IN/OUT for cash sales)
├── Bank (IN/OUT for bank deposits)
└── Debtors (Balance from credit sales)

Revenue
└── Sales (Credit side of all sales)

Liabilities
├── CGST Payable
├── SGST Payable
└── IGST Payable
```

---

## Database Schema

### 1. LedgerEntry (ledger_entries)

Double-entry bookkeeping ledger for all financial transactions.

```sql
CREATE TABLE ledger_entries (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,           -- Which shop
    entry_date DATETIME NOT NULL,       -- When recorded
    entry_number VARCHAR(50),           -- Unique reference (ORD{ID}{DATE})
    description VARCHAR(500) NOT NULL,  -- Human-readable description

    -- Reference to source document
    reference_type VARCHAR(50),         -- 'order', 'purchase', 'manual', 'adjustment'
    reference_id INTEGER,               -- e.g., order_id

    -- Debit side
    debit_account VARCHAR(100) NOT NULL, -- Account name
    debit_amount DECIMAL(15,2) NOT NULL,

    -- Credit side
    credit_account VARCHAR(100) NOT NULL,
    credit_amount DECIMAL(15,2) NOT NULL,

    -- Metadata
    notes TEXT,
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT now()
);

-- Key Constraint
ALTER TABLE ledger_entries
ADD UNIQUE (shop_id, reference_type, reference_id);
```

**Example Entry for Order Sale:**

```
Debit:  Cash                    5000.00
Credit: Sales                   5000.00
Description: Sales from order #ORD20240115001
```

### 2. CashBook (cash_book)

Tracks all cash IN and OUT transactions.

```sql
CREATE TABLE cash_book (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    order_id INTEGER,           -- Link to order (if from order)
    amount DECIMAL(15,2) NOT NULL,
    entry_type VARCHAR(10),     -- 'IN' or 'OUT'
    description VARCHAR(500),
    reference_number VARCHAR(50),  -- Order number
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT now()
);
```

**Example Entries:**

```
IN:  Order #ORD20240115001, Amount 5000, Customer: John Doe
OUT: Cash withdrawal, Amount 1000, For supplies
```

### 3. BankBook (bank_book)

Tracks all bank transactions (for future payment gateway integration).

```sql
CREATE TABLE bank_book (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    order_id INTEGER,
    amount DECIMAL(15,2) NOT NULL,
    entry_type VARCHAR(10),     -- 'IN' or 'OUT'
    description VARCHAR(500),
    bank_account VARCHAR(100),
    cheque_number VARCHAR(50),
    reference_number VARCHAR(50),
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT now()
);
```

### 4. KhataAccount (khata_accounts)

Customer credit accounts (khata) for credit sales.

```sql
CREATE TABLE khata_accounts (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    customer_id INTEGER NOT NULL,  -- Which customer
    balance DECIMAL(15,2) DEFAULT 0,      -- Amount owed
    credit_limit DECIMAL(15,2) DEFAULT 10000,  -- Max credit
    total_credit_given DECIMAL(15,2) DEFAULT 0,
    total_credit_received DECIMAL(15,2) DEFAULT 0,
    last_transaction_date DATETIME,
    last_updated DATETIME DEFAULT now(),
    created_at DATETIME DEFAULT now()
);

-- Unique constraint: One khata per customer per shop
ALTER TABLE khata_accounts
ADD UNIQUE (shop_id, customer_id);
```

**Example:**

```
Customer: Rajesh Kumar (ID: 5)
Shop: Main Store (ID: 1)
Balance: 5000 (owes 5000)
Credit Limit: 10000
Available: 5000
```

### 5. GSTRecord (gst_records)

Tax tracking for GST compliance and reporting.

```sql
CREATE TABLE gst_records (
    id INTEGER PRIMARY KEY,
    shop_id INTEGER NOT NULL,
    order_id INTEGER NOT NULL,
    taxable_amount DECIMAL(15,2) NOT NULL,
    gst_rate DECIMAL(5,2) NOT NULL,
    gst_amount DECIMAL(15,2) NOT NULL,
    cgst_amount DECIMAL(15,2) DEFAULT 0,   -- Central GST (9%)
    sgst_amount DECIMAL(15,2) DEFAULT 0,   -- State GST (9%)
    igst_amount DECIMAL(15,2) DEFAULT 0,   -- Integrated GST (18%)
    invoice_number VARCHAR(50),            -- Order number
    created_by INTEGER NOT NULL,
    created_at DATETIME DEFAULT now()
);

-- One GST record per order
ALTER TABLE gst_records
ADD UNIQUE (order_id);
```

**Example:**

```
Order #ORD20240115001
Taxable Amount: 4545.45
GST Rate: 18%
CGST: 409.09 (9%)
SGST: 409.09 (9%)
Total GST: 818.18
Invoice Total: 5363.63
```

### 6. ChartOfAccounts (chart_of_accounts)

Master list of all accounts in the system.

```sql
CREATE TABLE chart_of_accounts (
    id INTEGER PRIMARY KEY,
    account_code VARCHAR(20) UNIQUE,
    account_name VARCHAR(100) NOT NULL,
    account_type VARCHAR(50),  -- 'asset', 'liability', 'equity', 'revenue', 'expense'
    description TEXT,
    created_at DATETIME DEFAULT now()
);
```

**Example Data:**

```
1001 | Cash          | asset   | Cash on hand
1002 | Bank          | asset   | Bank account
1003 | Debtors       | asset   | Credit sales
2001 | CGST Payable  | liability | Central GST
2002 | SGST Payable  | liability | State GST
4001 | Sales         | revenue | Sales revenue
```

---

## Automatic Accounting Logic

### PHASE C: When Order Status Changes to DELIVERED

The `AccountingService.process_order_delivery()` method is called automatically.

**Step 1: Check for Duplicates**

```python
# Prevent duplicate entries
existing = db.query(LedgerEntry).filter(
    LedgerEntry.reference_type == "order",
    LedgerEntry.reference_id == order.id
).first()
if existing:
    return False  # Already recorded
```

**Step 2: Create Sales Ledger Entry**

For Cash Sales:

```
Debit:  Cash              5000.00
Credit: Sales             5000.00
```

For Credit Sales:

```
Debit:  Debtors           5000.00
Credit: Sales             5000.00
```

**Step 3: Create GST Record**

```
Order: #ORD20240115001
Subtotal: 4545.45
Tax: 18% = 818.18
  CGST: 409.09
  SGST: 409.09
Total: 5363.63
```

**Step 4: Record Payment Method**

If Credit Sale:

```
Update KhataAccount:
  customer_balance += order_total
  last_transaction_date = now()
```

If Cash Sale:

```
Create CashBook Entry:
  Amount: 5000.00
  Type: IN
  Description: Cash received from customer
  Reference: Order number
```

### When Order Status Changes to CANCELLED

The `AccountingService.reverse_accounting_entries()` method is called.

**Reversal Logic:**

```
1. Find original ledger entry
2. Create reverse entry (opposite debit/credit)
3. Delete GST record
4. Reverse khata balance (credit sales)
5. Delete cash entry (cash sales)
```

Example Reversal:

```
Original:  Debit Cash 5000, Credit Sales 5000
Reversal:  Debit Sales 5000, Credit Cash 5000
```

---

## API Endpoints

### Endpoint 1: Daily Sales Report

**PHASE D - Endpoint 1**

```
GET /api/v1/accounting/daily-sales/{shop_id}?report_date=YYYY-MM-DD
```

**RBAC:**

- ADMIN: All shops
- OWNER: Own shop
- STAFF: Own shop (read-only)
- CUSTOMER: Forbidden

**Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/accounting/daily-sales/1?report_date=2024-01-15' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Response (200 OK):**

```json
{
  "shop_id": 1,
  "report_date": "2024-01-15",
  "total_orders": 5,
  "total_sales": 25000.00,
  "total_tax": 4500.00,
  "cash_sales": 15000.00,
  "credit_sales": 10000.00,
  "items": [
    {
      "order_id": 1,
      "order_number": "ORD20240115001",
      "customer_name": "John Doe",
      "subtotal": 4545.45,
      "tax_amount": 818.18,
      "total_amount": 5363.63,
      "payment_method": "Cash",
      "is_credit_sale": false,
      "created_at": "2024-01-15T10:30:00"
    },
    ...
  ]
}
```

**Error Responses:**

- 404: Shop not found
- 400: Invalid date format
- 403: Insufficient permissions

---

### Endpoint 2: Profit & Loss Report

**PHASE D - Endpoint 2**

```
GET /api/v1/accounting/profit-loss/{shop_id}?period=YYYY-MM
```

**RBAC:**

- ADMIN: All shops
- OWNER: Own shop
- STAFF: Own shop (read-only)
- CUSTOMER: Forbidden

**Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/accounting/profit-loss/1?period=2024-01' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Response (200 OK):**

```json
{
  "shop_id": 1,
  "report_period": "2024-01",
  "gross_sales": 100000.0,
  "discounts": 5000.0,
  "net_sales": 95000.0,
  "cost_of_goods_sold": 57000.0,
  "gross_profit": 38000.0,
  "gross_profit_margin": 40.0,
  "total_tax_collected": 18000.0,
  "total_tax_payable": 18000.0
}
```

**Calculation Logic:**

```
Gross Sales = Sum of all delivered order totals
Discounts = Sum of order discounts
Net Sales = Gross Sales - Discounts

COGS = Sum of (cost_price × quantity) for all items sold
Gross Profit = Net Sales - COGS
Profit Margin = (Gross Profit / Net Sales) × 100

Tax = Sum of tax_amount from all delivered orders
```

---

### Endpoint 3: Cash Book

**PHASE D - Endpoint 3**

```
GET /api/v1/accounting/cash-book/{shop_id}?from_date=YYYY-MM-DD&to_date=YYYY-MM-DD
```

**RBAC:**

- ADMIN: All shops
- OWNER: Own shop
- STAFF: Own shop (read-only)
- CUSTOMER: Forbidden

**Request:**

```bash
curl -X GET 'http://localhost:8000/api/v1/accounting/cash-book/1?from_date=2024-01-01&to_date=2024-01-31' \
  -H 'Authorization: Bearer YOUR_JWT_TOKEN'
```

**Response (200 OK):**

```json
{
  "shop_id": 1,
  "period": "2024-01-01 to 2024-01-31",
  "opening_balance": 5000.0,
  "cash_in": 75000.0,
  "cash_out": 25000.0,
  "closing_balance": 55000.0,
  "transactions": [
    {
      "id": 1,
      "shop_id": 1,
      "order_id": 1,
      "amount": 5000.0,
      "entry_type": "IN",
      "description": "Cash from order ORD20240115001",
      "reference_number": "ORD20240115001",
      "created_by": 2,
      "created_at": "2024-01-15T10:30:00"
    },
    {
      "id": 2,
      "shop_id": 1,
      "order_id": null,
      "amount": 2000.0,
      "entry_type": "OUT",
      "description": "Supplier payment",
      "reference_number": "CHK001",
      "created_by": 3,
      "created_at": "2024-01-15T15:00:00"
    }
  ]
}
```

**Calculation:**

```
Opening Balance = All previous IN - OUT before from_date
Cash In = Sum of all IN entries in period
Cash Out = Sum of all OUT entries in period
Closing Balance = Opening + Cash In - Cash Out
```

---

### Endpoint 4: Customer Khata Statement

**PHASE D - Endpoint 4**

```
GET /api/v1/accounting/khata/{customer_id}?shop_id=ID
```

**RBAC:**

- CUSTOMER: Own khata only (no shop_id needed)
- OWNER: Any customer in own shop
- ADMIN: Any customer in any shop
- STAFF: Any customer in own shop

**Request (as Customer):**

```bash
curl -X GET 'http://localhost:8000/api/v1/accounting/khata/10' \
  -H 'Authorization: Bearer CUSTOMER_JWT_TOKEN'
```

**Request (as OWNER/ADMIN):**

```bash
curl -X GET 'http://localhost:8000/api/v1/accounting/khata/10?shop_id=1' \
  -H 'Authorization: Bearer OWNER_JWT_TOKEN'
```

**Response (200 OK):**

```json
{
  "customer_id": 10,
  "customer_name": "Rajesh Kumar",
  "shop_id": 1,
  "balance": 5000.0,
  "credit_limit": 10000.0,
  "available_credit": 5000.0,
  "total_credit_given": 15000.0,
  "total_credit_received": 10000.0,
  "last_transaction_date": "2024-01-15T14:30:00"
}
```

**Interpretation:**

```
Balance: 5000.00 → Customer owes 5000
Credit Limit: 10000.00 → Max credit allowed
Available: 5000.00 → Can still get 5000 more credit
(= Credit Limit - Current Balance)

Total Given: 15000 → Shop gave 15000 on credit
Total Received: 10000 → Customer paid back 10000
```

---

## RBAC & Security

### PHASE E: Access Control

#### Endpoint Access Matrix

| Role     | Daily Sales | P&L      | Cash Book | Khata    |
| -------- | ----------- | -------- | --------- | -------- |
| CUSTOMER | ✗           | ✗        | ✗         | ✅\*     |
| STAFF    | ✅ (own)    | ✅ (own) | ✅ (own)  | ✅ (own) |
| OWNER    | ✅ (own)    | ✅ (own) | ✅ (own)  | ✅ (own) |
| ADMIN    | ✅ (all)    | ✅ (all) | ✅ (all)  | ✅ (all) |

`*` = Customer can only view own khata

### Permission Checking

**For Shop Reports (Daily Sales, P&L, Cash Book):**

```python
if role == ADMIN:
    # Can access any shop
    access = True
elif role in [OWNER, STAFF]:
    # Can only access own shop
    if user.shop_id == requested_shop_id:
        access = True
    else:
        raise 403 Forbidden
else:
    raise 403 Forbidden
```

**For Khata Statements:**

```python
if role == CUSTOMER:
    # Can only view own khata
    if user.id == requested_customer_id:
        access = True
elif role in [OWNER, STAFF]:
    # Need shop_id, can only access own shop
    if user.shop_id == requested_shop_id:
        access = True
elif role == ADMIN:
    # Can access any shop
    access = True
```

---

## Report Specifications

### Daily Sales Report

**Purpose:** View all sales for a specific day

**Data Included:**

- Order count
- Total sales amount (sum of order totals)
- Total tax collected
- Cash vs credit breakdown
- Item-level details for each order

**Use Cases:**

- EOD (End of Day) reconciliation
- Daily bank deposit verification
- Daily sales tracking
- Customer inquiry follow-up

**Frequency:** Daily

---

### Profit & Loss Report

**Purpose:** Understand shop profitability for a month

**Data Included:**

- Gross sales
- Discounts
- Net sales
- Cost of goods sold (COGS)
- Gross profit
- Profit margin
- Tax collected

**Formula:**

```
Net Sales = Gross Sales - Discounts
Gross Profit = Net Sales - COGS
Profit Margin % = (Gross Profit / Net Sales) × 100
```

**Example Interpretation:**

```
If Net Sales = 100,000
   COGS = 60,000
   Gross Profit = 40,000
   Margin = 40%

This means 60% cost, 40% profit (before other expenses)
```

**Use Cases:**

- Monthly performance review
- Quarterly business analysis
- Year-over-year comparison
- Identify cost optimization opportunities

**Frequency:** Monthly

---

### Cash Book

**Purpose:** Track physical cash movements

**Data Included:**

- Opening balance (cash on hand at period start)
- All cash IN transactions
- All cash OUT transactions
- Closing balance (cash on hand at period end)
- Transaction-level details

**Reconciliation:**

```
Closing Balance = Opening + Cash In - Cash Out
```

**Use Cases:**

- Cash reconciliation
- Identify cash shortfalls
- Verify daily deposits
- Track cash withdrawals
- Audit trail

**Frequency:** Daily or as needed

---

### Khata Statement

**Purpose:** View customer credit status

**Data Included:**

- Current balance (amount owed)
- Credit limit
- Available credit (limit - balance)
- Total credit given historically
- Total payments received
- Last transaction date

**Use Cases:**

- Customer credit queries
- Credit limit management
- Payment collection follow-up
- Customer verification
- Default risk assessment

**Frequency:** On-demand

---

## Integration with Orders

### Hook Points

#### 1. Order Delivery (PHASE F Integration)

**Trigger:** Order status changes from any → DELIVERED

**in app/orders/router.py:**

```python
@router.patch("/shops/{shop_id}/{order_id}/status")
def update_order_status(...):
    # Update order status
    success, message, order = OrderService.update_order_status(...)

    # NEW: Hook accounting when order is DELIVERED
    if order.order_status == OrderStatusEnum.DELIVERED:
        AccountingService.process_order_delivery(order, db, user)

    return order
```

**What Happens:**

1. Ledger entry created (Sales)
2. GST record created
3. Cash/Khata entry created based on payment method
4. All entries committed to database

---

#### 2. Order Cancellation (PHASE F Integration)

**Trigger:** Order status changes to CANCELLED

**in app/orders/router.py:**

```python
if order.order_status == OrderStatusEnum.CANCELLED:
    AccountingService.reverse_accounting_entries(order, db, user)
```

**What Happens:**

1. Reverse ledger entries created
2. GST record deleted
3. Khata balance reversed (credit sales)
4. Cash entry deleted (cash sales)

---

### Router Registration (PHASE F)

**in main_with_auth.py:**

```python
# Import accounting router
from app.accounting.router import router as accounting_router

# Register with app
app.include_router(accounting_router)
```

**Result:** All 4 endpoints become available at `/api/v1/accounting/*`

---

## Error Handling

### HTTP Status Codes

| Code | Scenario                 | Example                       |
| ---- | ------------------------ | ----------------------------- |
| 200  | Successful read          | Daily sales fetched           |
| 400  | Invalid parameters       | Bad date format               |
| 403  | Insufficient permissions | Customer accessing other shop |
| 404  | Resource not found       | Shop does not exist           |
| 500  | Server error             | Database error                |

### Error Response Format

```json
{
  "detail": "You can only access reports for your shop (ID: 1)"
}
```

### Common Errors

**1. Date Format Error**

```
Input: "15-01-2024"
Error: "Invalid date format: ... Expected YYYY-MM-DD"
```

**2. Permission Denied**

```
Request: STAFF accessing different shop
Error: 403 Forbidden - "You can only access reports for your shop"
```

**3. Shop Not Found**

```
Request: shop_id = 999 (doesn't exist)
Error: 404 Not Found - "Shop 999 not found"
```

---

## Testing Scenarios

### Scenario 1: Record Cash Sale and View Report

**Steps:**

1. Create an order with 5 items
2. Transition to DELIVERED
3. Call daily sales report for that date

**Expected:**

- Order appears in daily sales
- Total amount correct
- Marked as cash sale
- No khata entry created

**SQL Check:**

```sql
SELECT * FROM ledger_entries WHERE reference_id = ORDER_ID;
-- Should show: Debit Cash, Credit Sales

SELECT * FROM cash_book WHERE order_id = ORDER_ID;
-- Should show: 1 IN entry

SELECT * FROM khata_accounts WHERE customer_id = CUST_ID;
-- Should NOT exist or balance = 0
```

---

### Scenario 2: Record Credit Sale and Check Khata

**Steps:**

1. Create order with is_credit_sale = true
2. Transition to DELIVERED
3. Call khata statement for customer

**Expected:**

- Ledger shows: Debit Debtors, Credit Sales
- Khata balance updated to order total
- Available credit reduced
- Last transaction date updated

**SQL Check:**

```sql
SELECT * FROM khata_accounts WHERE customer_id = CUST_ID;
-- balance should equal order amount
-- available_credit = credit_limit - balance

SELECT * FROM ledger_entries WHERE reference_id = ORDER_ID;
-- debit_account = 'Debtors' (not 'Cash')
```

---

### Scenario 3: Cancel Credit Sale

**Steps:**

1. Record credit sale (see Scenario 2)
2. Change order status to CANCELLED
3. Check khata statement again

**Expected:**

- Ledger entry reversed
- GST record deleted
- Khata balance returned to 0
- Available credit restored

**SQL Check:**

```sql
-- Check reversal entry created
SELECT * FROM ledger_entries WHERE reference_type = 'order_reversal';

-- Check khata balance reset
SELECT balance FROM khata_accounts WHERE customer_id = CUST_ID;
-- Should be 0 or negative (payment)

-- Check GST deleted
SELECT * FROM gst_records WHERE order_id = ORDER_ID;
-- Should be empty
```

---

### Scenario 4: Multi-order Daily Report

**Steps:**

1. Create 3 orders (2 cash, 1 credit)
2. All to DELIVERED
3. Call daily sales report

**Expected:**

- Total: sum of all 3 order amounts
- Cash sales: sum of 2 cash orders
- Credit sales: 1 credit order
- All 3 orders listed with details
- Correct tax totals

**Verification:**

```
Total Sales = Order1 + Order2 + Order3
Cash Sales = Order1 + Order2
Credit Sales = Order3
Tax = Sum of all tax amounts
```

---

### Scenario 5: P&L Report Calculation

**Steps:**

1. Create 10 orders with total $100k
2. Total discounts $5k
3. COGS $60k (all delivered)
4. Call P&L report

**Expected:**

- Gross sales: $100k
- Discounts: $5k
- Net sales: $95k
- COGS: $60k
- Gross profit: $35k
- Margin: 36.84%

---

### Scenario 6: RBAC - Customer Khata Access

**Steps:**

1. Login as customer
2. Try to access: /khata/{own_id}
3. Try to access: /khata/{other_customer_id}
4. Try to access: /daily-sales/1

**Expected:**

- Own khata: ✅ 200 OK
- Other khata: ❌ 403 Forbidden
- Daily sales: ❌ 403 Forbidden

---

### Scenario 7: RBAC - Staff Report Access

**Steps:**

1. Login as STAFF for shop 1
2. Try: /daily-sales/1
3. Try: /daily-sales/2
4. Try: /profit-loss/1

**Expected:**

- Shop 1 reports: ✅ 200 OK
- Shop 2 reports: ❌ 403 Forbidden
- Same RBAC on all endpoints

---

## Implementation Notes

### Idempotency

The system prevents duplicate entries:

```python
# Check if entry already exists for this order
existing = db.query(LedgerEntry).filter(
    LedgerEntry.reference_type == "order",
    LedgerEntry.reference_id == order.id
).first()

if existing:
    return False  # Already recorded
```

This ensures:

- Safe retry on failures
- No duplicates from reprocessing
- Consistent state

---

### Decimal Precision

All amounts use `Decimal(15, 2)`:

```python
amount: Decimal = Field(..., max_digits=15, decimal_places=2)
```

This ensures:

- Accurate financial calculations
- No floating-point rounding errors
- Proper tax precision

---

### Transaction Safety

Order status change and accounting use same transaction:

```python
try:
    # Update order
    order.status = DELIVERED
    # Create accounting entries
    accounting_service.process(order)
    db.commit()  # All or nothing
except:
    db.rollback()  # Revert all changes
```

---

## Future Enhancements

1. **Payment Gateways**
   - UPI payments
   - Card payments
   - Digital wallets

2. **Bank Integration**
   - Automatic bank reconciliation
   - Bank book from API feeds

3. **Advanced Reporting**
   - Monthly balance sheet
   - Trial balance
   - Ledger drill-down
   - Tax schedules

4. **Audit Trail**
   - Who created which entry
   - Modification history
   - Approval workflows

5. **Multi-currency**
   - Exchange rate tracking
   - Multi-currency reporting

6. **Automation**
   - Recurring entries
   - Scheduled reports
   - Email alerts

---

## Troubleshooting

### Daily Sales Not Appearing

**Check:**

```sql
-- Verify order exists
SELECT * FROM orders WHERE id = ORDER_ID AND order_status = 'delivered';

-- Verify accounting entry created
SELECT * FROM ledger_entries WHERE reference_id = ORDER_ID;

-- Check GST record
SELECT * FROM gst_records WHERE order_id = ORDER_ID;
```

**Solution:**

- Ensure order status is exactly "delivered"
- Check server logs for errors
- Verify user role has access

---

### Khata Balance Incorrect

**Check:**

```sql
SELECT * FROM khata_accounts WHERE customer_id = CUST_ID;
SELECT * FROM orders
WHERE customer_id = CUST_ID
AND is_credit_sale = true
AND order_status = 'delivered';
```

**Verify:**

- All delivered orders summed
- Account created only after first sale
- No stale data

---

## Support & Contact

For issues:

1. Check logs: `/var/log/smartkirana/`
2. Review this documentation
3. Check test scenarios
4. Contact: support@smartkirana.local

---

**Document Version:** 1.0.0  
**Last Updated:** 2024-01-15  
**Status:** Production Ready ✅
