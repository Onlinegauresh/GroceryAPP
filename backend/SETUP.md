# SmartKirana Backend - Quick Setup Guide

## What's Included

This is a **production-ready FastAPI backend** for the SmartKirana grocery application with:

✓ **PostgreSQL database** with 24 tables  
✓ **Double-entry accounting** (ledger, P&L, cash book)  
✓ **Multi-tenancy** (single database, multiple shops)  
✓ **Role-based access control** (customer, staff, owner, admin)  
✓ **Auto-inventory deduction** on orders  
✓ **Full audit trail** (stock movements, ledger entries)  
✓ **Offline-first ready** (structured for mobile sync)

---

## 1. INSTALLATION (Windows/Mac/Linux)

### Option A: Docker Compose (Recommended)

```bash
# Navigate to backend folder
cd backend

# Copy environment template
copy .env.example .env   # Windows
# or
cp .env.example .env     # Mac/Linux

# Start all services (PostgreSQL, Redis, FastAPI)
docker-compose up -d

# Watch logs
docker-compose logs -f backend

# Access API at http://localhost:8000
```

### Option B: Local Development

```bash
# 1. Create virtual environment
python -m venv venv
source venv/bin/activate   # Mac/Linux
# or
venv\Scripts\activate      # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and update .env
copy .env.example .env     # Windows
cp .env.example .env       # Mac/Linux

# 4. Start PostgreSQL and Redis (via Docker or local install)
docker-compose up -d postgres redis

# 5. Create database tables
python -c "from shared.database import Base, engine; Base.metadata.create_all(bind=engine)"

# 6. Seed demo data
python scripts/seed_data.py

# 7. Start FastAPI
python main.py

# Access API at http://localhost:8000
```

---

## 2. VERIFY INSTALLATION

```bash
# Check API is running
curl http://localhost:8000/

# Check health
curl http://localhost:8000/health

# View Swagger docs
# Open browser: http://localhost:8000/api/docs

# View ReDoc
# Open browser: http://localhost:8000/api/redoc
```

---

## 3. FIRST API CALL

### Register Shop Owner

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": 1,
    "name": "Your Name",
    "phone": "9876543210",
    "email": "you@kirana.local",
    "password": "demo123",
    "role": "owner"
  }'
```

**Response:**

```json
{
  "user_id": 1,
  "phone": "9876543210",
  "name": "Your Name",
  "role": "owner",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

**Save the `access_token` for next requests!**

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": 1,
    "phone": "9876543210",
    "password": "demo123"
  }'
```

---

## 4. KEY ENDPOINTS

All endpoints require `?token=YOUR_TOKEN` or header `Authorization: Bearer TOKEN`

### Products

```bash
# Create product
curl -X POST "http://localhost:8000/api/v1/products?shop_id=1&token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Rice 1kg", "sku": "RIC-001", "category": "Grains", "unit": "kg", "cost_price": 50, "mrp": 80, "selling_price": 75, "gst_rate": 5}'

# List products
curl "http://localhost:8000/api/v1/products?shop_id=1&token=YOUR_TOKEN"

# Get low stock
curl "http://localhost:8000/api/v1/products/search/low-stock?shop_id=1&token=YOUR_TOKEN"
```

### Orders

```bash
# Create order (auto-deducts inventory!)
curl -X POST "http://localhost:8000/api/v1/orders?shop_id=1&token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 2,
    "items": [{"product_id": 1, "quantity": 2}],
    "payment_method": "cash"
  }'

# List orders
curl "http://localhost:8000/api/v1/orders?shop_id=1&token=YOUR_TOKEN"
```

### Inventory

```bash
# Check inventory status
curl "http://localhost:8000/api/v1/inventory/status?shop_id=1&token=YOUR_TOKEN"

# Adjust stock
curl -X POST "http://localhost:8000/api/v1/inventory/adjust?shop_id=1&token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"product_id": 1, "quantity_change": -5, "adjustment_reason": "damage", "notes": "Broken bags"}'

# View stock history
curl "http://localhost:8000/api/v1/inventory/1/history?shop_id=1&token=YOUR_TOKEN"
```

### Accounting

```bash
# Profit & Loss
curl "http://localhost:8000/api/v1/accounting/profit-loss?shop_id=1&token=YOUR_TOKEN&period_days=30"

# Sales ledger
curl "http://localhost:8000/api/v1/accounting/sales-ledger?shop_id=1&token=YOUR_TOKEN"

# Account balance
curl "http://localhost:8000/api/v1/accounting/account-balance/1001?shop_id=1&token=YOUR_TOKEN"

# Monthly summary
curl "http://localhost:8000/api/v1/accounting/monthly-summary?shop_id=1&token=YOUR_TOKEN&year=2026&month=2"
```

---

## 5. DEMO DATA

If you ran `python scripts/seed_data.py`, here's available test data:

**Shop ID:** 1  
**Owner:** Phone: 9876543210, Email: owner@kirana.local  
**Staff:** Phone: 9876543211, Email: staff@kirana.local  
**Customer1:** Phone: 9876543212, Email: customer1@kirana.local  
**Customer2:** Phone: 9876543213, Email: customer2@kirana.local

**Password:** demo123

**Demo Products:**

- RIC-001: Basmati Rice 1kg
- TEA-001: Tata Tea 500g
- MIL-001: Milk 1L
- OIL-001: Sunflower Oil 1L
- SAL-001: Iodized Salt 1kg
- SUG-001: Sugar 1kg

---

## 6. DIRECTORY STRUCTURE

```
backend/
├── auth_service/          # Authentication (register, login, OTP)
├── product_service/       # Product CRUD
├── order_service/         # Orders (auto-inventory deduction)
├── inventory_service/     # Stock tracking & alerts
├── accounting_service/    # Financial reports & ledger
├── shared/                # Database, models, security, config
├── scripts/               # Seed data, CLI tools
├── tests/                 # Unit & integration tests
├── main.py               # FastAPI entry point
├── requirements.txt      # Python dependencies
├── docker-compose.yml    # Local development environment
├── Dockerfile           # Container image
├── .env.example         # Environment template
└── README.md            # Full documentation
```

---

## 7. IMPORTANT CONCEPTS

### Multi-Tenancy

Every table has `shop_id`. Users can only access their own shop's data:

```python
# Good ✓
Order.filter(Order.shop_id == user.shop_id)

# Bad ✗ (exposes other shop data)
Order.filter(Order.id == order_id)
```

### Auto-Inventory Deduction

When you create an order, inventory is **automatically** reduced:

```
1. Order created
2. Stock updated (Product.current_stock -= quantity)
3. StockMovement logged (audit trail)
4. Ledger entry created (Debit: Cash, Credit: Sales)
```

### Double-Entry Bookkeeping

Every transaction creates TWO ledger entries (must balance):

```
Order Sale:
  Debit: 1001 (Cash) - 100 rupees
  Credit: 4001 (Sales Revenue) - 100 rupees
```

### Role-Based Access

```
Customer:  Can browse products, create orders, view own orders
Staff:     Can process orders, adjust inventory, view reports
Owner:     Full access (create products, view ledger, financial reports)
Admin:     System-wide access (future: multi-shop management)
```

---

## 8. TESTING

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=.

# Run specific test
pytest tests/test_auth.py::test_register_user -v
```

---

## 9. DEVELOPMENT WORKFLOW

### Code Style

```bash
# Format code
black .

# Lint code
flake8 .

# Type checking
mypy .
```

### Database Migrations (When Needed)

```bash
# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## 10. TROUBLESHOOTING

### "Connection refused" on localhost:5432

- PostgreSQL not running. Start it:
  ```bash
  docker-compose up -d postgres
  ```

### "ModuleNotFoundError: No module named 'shared'"

- Add backend folder to PYTHONPATH:
  ```bash
  export PYTHONPATH="${PYTHONPATH}:$(pwd)"
  python main.py
  ```

### Token validation fails

- Check token format: `eyJ0eXAiOiJKV1QiLCJhbGc...`
- Token expires after 24 hours
- Use `/api/v1/auth/me?token=YOUR_TOKEN` to verify token

### Inventory goes negative

- There's validation to prevent negative stock
- Check `current_stock` before creating orders
- Use inventory adjustment for corrections

---

## 11. PRODUCTION CHECKLIST

Before deploying to production:

- [ ] Change `SECRET_KEY` in .env
- [ ] Set `DEBUG=false`
- [ ] Configure PostgreSQL with strong password
- [ ] Set up automated backups
- [ ] Configure CORS properly (not allow "\*")
- [ ] Use HTTPS/TLS
- [ ] Setup logging aggregation
- [ ] Monitor database connections
- [ ] Rate limit API endpoints
- [ ] Configure reverse proxy (Nginx/HAProxy)

---

## 12. NEXT STEPS

1. **Run demo:**

   ```bash
   docker-compose up -d
   python scripts/seed_data.py
   python main.py
   ```

2. **Test API:**
   - Open http://localhost:8000/api/docs
   - Try register, create product, create order

3. **Explore code:**
   - Auth: `auth_service/routes.py`
   - Products: `product_service/routes.py`
   - Orders: `order_service/routes.py` + `order_service/service.py`
   - Accounting: `accounting_service/routes.py`

4. **Read documentation:**
   - [PHASE_1_PRODUCT_SYSTEM_DESIGN.md](../PHASE_1_PRODUCT_SYSTEM_DESIGN.md) - Product vision
   - [PHASE_2_DATABASE_DESIGN.md](../PHASE_2_DATABASE_DESIGN.md) - Database schema
   - [PHASE_3_BACKEND_IMPLEMENTATION.md](../PHASE_3_BACKEND_IMPLEMENTATION.md) - API design
   - [README.md](./README.md) - Full API documentation

---

## Support

For issues:

1. Check [README.md](./README.md) for API details
2. Look at test files for examples
3. View logs: `docker-compose logs -f backend`
4. Check database directly:
   ```bash
   docker exec -it smartkirana_db psql -U smartkirana -d smartkirana
   ```

---

**Last Updated:** February 4, 2026  
**FastAPI Version:** 0.104.1  
**Python:** 3.11+  
**Status:** Production Ready
