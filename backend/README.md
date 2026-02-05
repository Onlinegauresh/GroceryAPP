# SmartKirana AI Backend

Open-source grocery retail platform with **offline-first** architecture, **free AI**, and **Tally-like accounting**.

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 14+ (if not using Docker)

### Local Development

```bash
# 1. Clone repository
cd backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Setup environment
cp .env.example .env

# 5. Start Docker services (PostgreSQL, Redis)
docker-compose up -d postgres redis

# 6. Run migrations (when available)
alembic upgrade head

# 7. Seed initial data
python scripts/seed_data.py

# 8. Start FastAPI server
python main.py

# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/api/docs
```

### Docker Compose (All Services)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down
```

---

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login with password
- `POST /api/v1/auth/send-otp` - Send OTP
- `POST /api/v1/auth/verify-otp` - Verify OTP and login
- `GET /api/v1/auth/me` - Get current user

### Products

- `GET /api/v1/products` - List products
- `POST /api/v1/products` - Create product
- `GET /api/v1/products/{id}` - Get product
- `PUT /api/v1/products/{id}` - Update product
- `DELETE /api/v1/products/{id}` - Delete product
- `GET /api/v1/products/search/by-category` - Search by category
- `GET /api/v1/products/search/low-stock` - Get low stock items

### Orders

- `GET /api/v1/orders` - List orders
- `POST /api/v1/orders` - Create order (auto-deducts inventory)
- `GET /api/v1/orders/{id}` - Get order details
- `PUT /api/v1/orders/{id}/status` - Update order status
- `PUT /api/v1/orders/{id}/payment-status` - Update payment status

### Inventory

- `GET /api/v1/inventory/status` - Get inventory status
- `POST /api/v1/inventory/adjust` - Adjust stock manually
- `GET /api/v1/inventory/{product_id}/history` - Stock movement history
- `GET /api/v1/inventory/alerts/low-stock` - Low stock alerts

### Accounting

- `GET /api/v1/accounting/ledger` - Ledger entries
- `GET /api/v1/accounting/profit-loss` - P&L statement
- `GET /api/v1/accounting/sales-ledger` - Sales ledger
- `GET /api/v1/accounting/account-balance/{code}` - Account balance
- `GET /api/v1/accounting/monthly-summary` - Monthly summary
- `GET /api/v1/accounting/chart-of-accounts` - Chart of accounts

---

## Authentication

All endpoints (except `/register`, `/login`, `/send-otp`, `/verify-otp`) require a JWT token.

Pass token as query parameter:

```bash
curl "http://localhost:8000/api/v1/products?shop_id=1&token=YOUR_JWT_TOKEN"
```

Or as Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:8000/api/v1/products?shop_id=1"
```

---

## Example Workflow

### 1. Register Shop Owner

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "shop_id": 1,
    "name": "Rajesh Kumar",
    "phone": "9876543210",
    "email": "rajesh@kirana.local",
    "password": "secure123",
    "role": "owner"
  }'
```

**Response:**

```json
{
  "user_id": 1,
  "phone": "9876543210",
  "name": "Rajesh Kumar",
  "role": "owner",
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer"
}
```

### 2. Create Product

```bash
curl -X POST "http://localhost:8000/api/v1/products?shop_id=1&token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Basmati Rice 1kg",
    "sku": "RIC-001",
    "category": "Rice",
    "unit": "kg",
    "cost_price": 50,
    "mrp": 80,
    "selling_price": 75,
    "gst_rate": 5,
    "min_stock_level": 10,
    "reorder_quantity": 50
  }'
```

### 3. Create Order (Auto-Deducts Inventory)

```bash
curl -X POST "http://localhost:8000/api/v1/orders?shop_id=1&token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 2,
    "items": [
      {"product_id": 1, "quantity": 2}
    ],
    "payment_method": "cash"
  }'
```

**What happens:**

1. Stock of product 1 decreases by 2
2. StockMovement entry created (audit trail)
3. Ledger entry created (Debit: Cash, Credit: Sales)
4. Order returned with order_number: "ORD-20260204-0001"

### 4. View Profit & Loss

```bash
curl "http://localhost:8000/api/v1/accounting/profit-loss?shop_id=1&token=YOUR_TOKEN&period_days=30"
```

---

## Project Structure

```
backend/
├── shared/                  # Shared utilities
│   ├── config.py           # Settings
│   ├── database.py         # SQLAlchemy setup
│   ├── models.py           # ORM models (all tables)
│   ├── security.py         # JWT, hashing
│   └── exceptions.py       # Custom exceptions
│
├── auth_service/           # Authentication
│   └── routes.py          # Register, login, OTP
│
├── product_service/        # Product CRUD
│   └── routes.py          # Product endpoints
│
├── order_service/          # Order management
│   ├── routes.py          # Order endpoints
│   └── service.py         # Business logic (auto-inventory deduction)
│
├── inventory_service/      # Stock management
│   └── routes.py          # Inventory endpoints
│
├── accounting_service/     # Financial reports
│   └── routes.py          # Ledger, P&L, accounting
│
├── main.py                 # FastAPI app entry point
├── requirements.txt        # Dependencies
├── docker-compose.yml      # Local dev environment
├── Dockerfile             # Backend container
├── .env.example           # Environment template
└── README.md              # This file
```

---

## Key Features

### ✓ Authentication

- Register/login with phone + password
- OTP support (framework ready)
- JWT tokens
- Role-based access control (RBAC)

### ✓ Inventory Management

- Product CRUD with SKU uniqueness
- Stock tracking with movement history
- Low-stock alerts
- Auto-deduction on order

### ✓ Order Management

- Order creation with line items
- Automatic inventory deduction
- Tax calculation (GST)
- Payment tracking

### ✓ Accounting (Tally-like)

- Double-entry bookkeeping (ledger)
- Sales ledger
- Profit & Loss calculation
- Account balances
- Monthly summaries
- Chart of accounts

### ✓ Multi-Tenancy

- Data isolated by shop_id
- Multi-vendor ready

---

## Testing Endpoints with cURL

### Login

```bash
# First register, then login
SHOP_ID=1
PHONE="9876543210"
PASSWORD="secure123"

curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"shop_id\": $SHOP_ID, \"phone\": \"$PHONE\", \"password\": \"$PASSWORD\"}"
```

### List Products

```bash
TOKEN="your_token_here"
SHOP_ID=1

curl "http://localhost:8000/api/v1/products?shop_id=$SHOP_ID&token=$TOKEN&limit=10"
```

### View Low Stock Alerts

```bash
curl "http://localhost:8000/api/v1/inventory/alerts/low-stock?shop_id=1&token=$TOKEN"
```

---

## Development

### Code Style

```bash
# Format code
black .

# Lint
flake8 .

# Type check
mypy .
```

### Running Tests

```bash
pytest -v
pytest --cov=.  # With coverage
```

---

## Configuration

### Environment Variables

See `.env.example` for all options:

```
DATABASE_URL              PostgreSQL connection
REDIS_URL                 Redis connection
SECRET_KEY                JWT signing key
DEBUG                     Debug mode
OTP_EXPIRE_MINUTES        OTP validity
```

### Database

Default database is PostgreSQL. Connection:

```
postgresql://smartkirana:smartkirana123@localhost:5432/smartkirana
```

---

## Roadmap

### Phase 3 (Current)

✓ Authentication & JWT  
✓ Product CRUD  
✓ Order management  
✓ Inventory tracking  
✓ Basic accounting

### Phase 4 (Next)

- GST calculations & reports
- Khata (customer credit) system
- Invoice PDF generation
- Purchase order management

### Phase 5

- AI forecasting (demand prediction)
- Anomaly detection
- Smart reorder suggestions
- Price optimization

---

## License

Open source - Free for commercial use

---

## Support

For issues, create a GitHub issue or contact the team.

---

**Last Updated:** February 4, 2026  
**Version:** 1.0.0
