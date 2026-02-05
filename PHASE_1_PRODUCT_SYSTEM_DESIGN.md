# SmartKirana AI - PHASE 1: PRODUCT & SYSTEM DESIGN

**Last Updated:** February 4, 2026  
**Status:** Complete  
**Version:** 1.0

---

## 1. PRODUCT VISION & MISSION

### What is SmartKirana AI?

A **complete retail platform** for Indian grocery stores (kirana shops) that combines:

- **Customer-facing mobile/web app** – Amazon/Flipkart-like experience
- **Merchant dashboard** – Tally-like accounting + inventory + AI insights
- **Offline-first architecture** – works in low-connectivity areas
- **Free/open-source AI** – demand forecasting, smart ordering, fraud detection
- **Scalable design** – single shop today, multi-vendor marketplace tomorrow

### Core Philosophy

1. **Store-centric, not vendor-centric** – prioritize shop owner profitability
2. **Offline-first** – sync when online, work always
3. **Open-source only** – no vendor lock-in, full control
4. **Indian market fit** – GST compliance, cash handling, khata (credit), bulk selling
5. **Simplicity > Features** – 80/20 principle: deliver core value, iterate

### Market Problem

- Indian kirana stores lose ₹10-30% margin due to:
  - Manual inventory mismanagement
  - Lack of demand forecasting
  - No customer relationship management
  - Cash/ledger errors
  - No competitive advantage vs. modern retail

### Solution

- **Customers**: Convenient ordering, subscription models, personalized offers
- **Shop Owners**: Real-time analytics, auto inventory alerts, smart pricing, khata management
- **Platform**: Data-driven supply chain, vendor marketplace, financing (future)

---

## 2. USER ROLES & PERSONAS

### 2.1 Customer (Retail Buyer)

**Profile:** Individual consumer, family grocery buyer  
**Primary Goals:**

- Browse products easily
- Compare prices
- Quick checkout
- Loyalty/subscription options
- Voice ordering support (future)
- Reorder history

**Permissions:**

- View products, prices, stock
- Create orders
- Pay (cash/digital)
- View order history
- Manage profile
- View recommendations

**Devices:** Mobile app (Flutter) + SMS/WhatsApp

---

### 2.2 Shop Staff (Sales/Inventory)

**Profile:** Shop employee managing sales and stock  
**Primary Goals:**

- Process customer orders
- Update inventory (quick stock take)
- Check low-stock alerts
- Print/email invoices

**Permissions:**

- View products & stock
- Create/process orders
- Update inventory
- View daily sales
- Generate invoices (read-only reports)

**Devices:** Mobile app (Flutter) + Web (tablet-friendly)

---

### 2.3 Shop Owner / Manager

**Profile:** Small-to-medium grocery shop owner  
**Primary Goals:**

- Monitor sales & profitability
- Manage inventory & suppliers
- Track customer credit (khata)
- Understand best-sellers
- Make pricing decisions
- Compliance (GST, tax)

**Permissions:**

- All staff permissions
- Create/edit products & prices
- Set reorder points
- Manage suppliers
- View all accounting ledgers
- Manage discounts/offers
- Generate financial reports
- View AI insights

**Devices:** Web dashboard (React) + Mobile app

---

### 2.4 System Admin (Future: Multi-Shop)

**Profile:** Superuser managing multiple shops  
**Primary Goals:**

- Monitor all shops
- Manage vendors
- Process payouts
- Generate platform reports

**Permissions:**

- Full access to all shops
- Vendor management
- Financial reconciliation
- System configuration

**Devices:** Web dashboard (React)

---

## 3. CORE MODULES & FEATURES

### Module 1: User Management & Authentication

**Features:**

- Phone + Email registration (OTP)
- Role-based access control (RBAC)
- Session management
- Password reset
- User profile management
- Multi-device support

**Why:** Security, compliance, role isolation

---

### Module 2: Product Catalog & Search

**Features:**

- Product CRUD (shop owner only)
- Categories & subcategories
- SKU management
- Pricing (MRP, cost, discount)
- Product images
- GST classification
- Full-text search
- Filters (price, category, freshness)

**Why:** Core UX, enables orders

---

### Module 3: Inventory Management

**Features:**

- Stock tracking (real-time)
- Stock adjustments (damage, theft)
- Reorder points & alerts
- Expiry date tracking (for perishables)
- Stock history (for audits)
- Barcode scanning (future)
- Low-stock alerts (rule-based)

**Why:** Prevent stockouts, reduce waste, enable forecasting

---

### Module 4: Order Management

**Features:**

- Shopping cart
- Order creation (web, mobile, phone)
- Order history
- Invoice generation (PDF)
- Payment tracking
- Delivery status (if applicable)
- Order cancellation/returns
- Bulk orders support

**Why:** Core transaction handling, compliance

---

### Module 5: Payment & Billing

**Features:**

- Multiple payment modes (cash, UPI, card, bank transfer)
- Digital receipt generation
- Invoice PDF download
- Payment reconciliation
- Cash register management (for staff)
- Refund tracking

**Why:** Liquidity, tax compliance, customer proof

---

### Module 6: Accounting (Tally-like)

**Features:**

- **Sales Ledger** – daily/monthly sales, returns, discounts
- **Purchase Ledger** – supplier invoices, payments, returns
- **Cash Book** – cash in/out, bank reconciliation
- **Profit & Loss** – revenue - COGS - expenses
- **Balance Sheet** – assets, liabilities, equity
- **Customer Credit (Khata)** – track customer credit, dues, payments
- **GST Ledger** – CGST, SGST, IGST, GST returns
- **Bank Reconciliation** – match bank statements
- **Tax Reports** – quarterly/annual

**Why:** Legal compliance, profitability tracking, financial health

---

### Module 7: AI & Analytics Engine

**Features:**

- **Demand Forecasting** – predict next month's sales
- **Smart Reorder** – auto-suggest reorder quantities
- **Price Optimization** – rule-based pricing recommendations
- **Anomaly Detection** – detect theft, fraud, data entry errors
- **Customer Insights** – top buyers, repeat products
- **Trend Analysis** – seasonal patterns, category performance
- **Churn Prediction** – identify at-risk customers

**Why:** Competitive advantage, margin improvement, risk reduction

---

### Module 8: Reporting & Dashboards

**Features:**

- Sales dashboard (daily, weekly, monthly, yearly)
- Top products, top customers
- Cash flow analysis
- Profitability by category
- Supplier performance
- Customer credit aging
- Inventory valuation
- Custom reports

**Why:** Decision-making, performance tracking

---

### Module 9: Notifications & Alerts

**Features:**

- Low-stock alerts (SMS/in-app)
- Order alerts (new, completed)
- Payment reminders (khata)
- System alerts (errors, backups)
- Promotional notifications
- Offer recommendations

**Why:** Real-time awareness, engagement

---

### Module 10: Offline-First Sync

**Features:**

- Local SQLite cache (mobile)
- Intelligent sync strategy
- Conflict resolution
- Fallback when online
- Background sync

**Why:** Works anywhere, seamless UX

---

## 4. SYSTEM ARCHITECTURE

### 4.1 High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                              │
├────────────────────────────────────────┬────────────────────────────┤
│  MOBILE (Flutter)                      │  WEB (React)               │
│  - Customer App                        │  - Admin Dashboard         │
│  - Manager Lite App                    │  - Manager Dashboard       │
│  - Offline-first (SQLite)              │  - Reports                 │
└────────────────────────────────────────┴────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                          API GATEWAY                                │
│                    (Load Balancer, Auth, Rate Limit)               │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                       MICROSERVICES LAYER (FastAPI)                         │
├──────────────────┬─────────────────┬──────────────────┬─────────────────────┤
│ AUTH SERVICE     │ PRODUCT SERVICE │ ORDER SERVICE    │ INVENTORY SERVICE   │
│ - Register       │ - CRUD products │ - Create order   │ - Stock tracking    │
│ - Login/OTP      │ - Search        │ - Order history  │ - Adjustments       │
│ - Token mgmt     │ - Categories    │ - Invoices       │ - Forecasting data  │
│ - RBAC           │ - Pricing       │ - Payment        │ - Alerts            │
└──────────────────┴─────────────────┴──────────────────┴─────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                    DOMAIN SERVICES (FastAPI + Python)                       │
├──────────────────┬─────────────────┬──────────────────┬─────────────────────┤
│ ACCOUNTING SVC   │ AI ENGINE        │ NOTIFICATION SVC │ REPORTING SVC       │
│ - Sales ledger   │ - Forecasting    │ - SMS/Email      │ - Dashboard queries │
│ - Purchases      │ - Anomalies      │ - Alerts         │ - Report generation │
│ - Cash/Bank      │ - Reorder logic  │ - Offers         │ - Export (PDF/XLS)  │
│ - GST/Khata      │ - Pricing rules  │ - Push notifs    │ - Custom reports    │
└──────────────────┴─────────────────┴──────────────────┴─────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────────────────┐
│                         DATA LAYER                                          │
├──────────────────┬─────────────────┬──────────────────┬─────────────────────┤
│ PostgreSQL DB    │ Redis Cache      │ Message Queue    │ Object Storage      │
│ (Primary store)  │ (Session, cache) │ (Async tasks)    │ (Invoices, images)  │
│                  │                  │                  │                     │
│ - Users          │ - Sessions       │ - Email tasks    │ - PDF invoices      │
│ - Products       │ - Product cache  │ - SMS tasks      │ - Product images    │
│ - Orders         │ - Dashboard data │ - Notifications  │ - Reports (XLS)     │
│ - Ledgers        │ - Rate limit     │ - Forecasts      │                     │
│ - Inventory      │ - Locks          │ - Data sync      │                     │
└──────────────────┴─────────────────┴──────────────────┴─────────────────────┘
```

### 4.2 Service Boundaries & Ownership

| Service                  | Purpose                                    | Tech                                 | Owner             |
| ------------------------ | ------------------------------------------ | ------------------------------------ | ----------------- |
| **Auth Service**         | User registration, login, token generation | FastAPI + JWT                        | Backend Team      |
| **Product Service**      | Product catalog, search, pricing           | FastAPI + PostgreSQL                 | Backend Team      |
| **Order Service**        | Order CRUD, invoicing, payment tracking    | FastAPI + PostgreSQL                 | Backend Team      |
| **Inventory Service**    | Stock tracking, adjustments, alerts        | FastAPI + PostgreSQL                 | Backend Team      |
| **Accounting Service**   | Ledgers, P&L, GST, khata management        | FastAPI + PostgreSQL + Python (calc) | Finance/Backend   |
| **AI Engine**            | Forecasting, reorder, anomalies, pricing   | Python (scikit-learn, ARIMA)         | ML/Backend        |
| **Notification Service** | SMS, Email, Push alerts                    | FastAPI + Celery                     | Backend Team      |
| **Reporting Service**    | Dashboard data, PDF reports, analytics     | FastAPI + PostgreSQL                 | Analytics/Backend |

---

## 5. DATA FLOW DIAGRAMS

### 5.1 Customer Order Flow

```
Customer App
    ↓
[Browse Products] → Product Service (cached locally)
    ↓
[Add to Cart] → Local SQLite storage
    ↓
[Checkout] → Order Service
    ↓
[Payment] → Payment processor (online) / Local cash flag
    ↓
[Invoice Generated] → Accounting Service
    ↓
[Stock Deducted] → Inventory Service
    ↓
[Order Confirmation] → Customer (SMS/Email)
    ↓
[Sync to Cloud] → When online (conflict resolution)
```

### 5.2 Manager Accounting Flow

```
Shop Owner Dashboard
    ↓
[View Dashboard] → Reporting Service (cached, 5-min refresh)
    ↓
[Daily Ledger] → Accounting Service queries
    ↓
[Reconciliation] → P&L calculation (real-time from orders + invoices)
    ↓
[GST Report] → Ledger filtering by GST code
    ↓
[Khata Management] → Customer credit tracking
    ↓
[Export Report] → PDF/Excel generation
```

### 5.3 AI Forecasting Flow

```
Order → Inventory Service
    ↓
[Store in forecast data table]
    ↓
[Daily batch job @ midnight]
    ↓
[AI Engine: ARIMA/Linear Regression on last 90 days]
    ↓
[Generate reorder suggestions]
    ↓
[Alert if stock < (forecast + 2-day buffer)]
    ↓
[Store predictions in cache]
    ↓
[Manager dashboard shows smart reorder]
```

---

## 6. KEY DESIGN DECISIONS & RATIONALE

### Decision 1: FastAPI over Django

**Why:**

- Lightweight, async-first (better for microservices)
- Automatic Swagger documentation
- Better performance for I/O-bound operations
- Simpler to split into microservices
- Excellent for ML model serving

**Trade-off:** Smaller ecosystem (mitigated by FastAPI's simplicity)

---

### Decision 2: PostgreSQL (not NoSQL)

**Why:**

- Accounting data requires ACID transactions
- Complex relationships (orders → items → ledger entries)
- Easier to audit and reconcile
- Indian tax laws require data integrity
- Join-heavy queries for reporting

**Trade-off:** Vertical scaling limits (acceptable for 1-100 shops)

---

### Decision 3: Redis for Cache, NOT primary store

**Why:**

- Session management (fast, volatile)
- Product cache (stale OK, refreshes hourly)
- Dashboard cache (5-min lag acceptable)
- Rate limiting
- Distributed locks (for concurrent orders)

**Trade-off:** Must have fallback to PostgreSQL on cache miss

---

### Decision 4: Offline-First Mobile Architecture

**Why:**

- Many areas have patchy internet
- Better perceived performance
- Reduces server load
- Works during outages

**Implementation:**

- SQLite local database
- Sync on interval (every 5 min when online)
- Conflict resolution: Last-write-wins for products, client-wins for orders
- Queue management: Store failed requests, retry on online

---

### Decision 5: Open-Source AI Only (No OpenAI/Gemini)

**Why:**

- No vendor lock-in
- Full control over data (crucial for Indian users)
- No recurring API costs
- Works offline
- Can be fine-tuned on shop-specific data

**Implementation:**

- Demand forecasting: ARIMA (statsmodels) or Linear Regression (scikit-learn)
- Anomaly detection: Isolation Forest (scikit-learn)
- Price optimization: Rule-based (no ML needed)
- Recommendations: Collaborative filtering (scikit-learn)

---

### Decision 6: Multi-Shop Architecture from Day 1

**Why:**

- Easier to scale than refactoring
- Each shop is a tenant with isolated data
- Shop ID in every query (by design)
- Supports future marketplace

**Trade-off:** Slight complexity today (worth it)

---

### Decision 7: Role-Based Access Control (RBAC)

**Why:**

- Shop owner ≠ staff ≠ customer
- Legal liability: staff cannot change prices arbitrarily
- Auditing: track who made what change
- Future-proof: easy to add admin role

**Implementation:**

- JWT token includes role + shop_id
- Middleware checks permissions
- Row-level security in PostgreSQL (future)

---

## 7. TECHNICAL CONSTRAINTS & ASSUMPTIONS

### Constraints

1. **No paid APIs** – Stripe? Use Razorpay free tier or cash-first
2. **No OpenAI/Gemini** – Use local models or scikit-learn
3. **Single region initially** – Can scale to multi-region later
4. **Single PostgreSQL instance** – No sharding (yet)
5. **Offline sync conflict resolution** – Simple approach, not Google Firestore-level

### Assumptions

1. **Internet:** 50% of time available (async sync works)
2. **Users:** 100-500 customers per shop, 1-5 staff
3. **Data volume:** < 1GB per shop in year 1
4. **Response time:** < 2s for most APIs (acceptable for retail)
5. **Availability:** 99% during business hours, 95% overall
6. **Load:** < 100 concurrent users per shop initially

---

## 8. SECURITY & COMPLIANCE

### Authentication

- OTP-based (no password complexity burden)
- JWT tokens (expiry: 24h access, 30d refresh)
- Multi-device support (tokens per device)

### Authorization

- JWT includes `role`, `shop_id`, `user_id`
- Middleware validates on every request
- Shop ID enforced in queries (no cross-shop access)

### Data Privacy

- Passwords hashed (bcrypt)
- PII encrypted at rest (addresses, phone numbers)
- Audit logs for sensitive changes (prices, ledger entries)
- GDPR-ready (delete customer data)

### Tax Compliance

- GST classification on every product
- Ledger entries immutable (append-only)
- Invoice auto-generation (no manual entry)
- Khata tracking for credit control

---

## 9. FUTURE ROADMAP (Not in MVP)

### Phase 2 (Q2 2026)

- Multi-vendor marketplace
- Supplier integration (auto purchase orders)
- Payment gateway integration (Razorpay)
- Advanced forecasting (neural networks)

### Phase 3 (Q3 2026)

- Barcode scanning
- Voice ordering (Whisper.cpp)
- Customer loyalty program
- Franchise model

### Phase 4 (Q4 2026)

- Multi-region deployment
- Supplier financing
- Marketplace commissions
- Mobile payment (AEPS)

---

## 10. FOLDER STRUCTURE (Preview for Phase 2)

```
GroceryAPP/
├── backend/
│   ├── auth_service/
│   ├── product_service/
│   ├── order_service/
│   ├── inventory_service/
│   ├── accounting_service/
│   ├── ai_engine/
│   ├── notification_service/
│   ├── reporting_service/
│   ├── shared/
│   │   ├── models.py (SQLAlchemy)
│   │   ├── config.py
│   │   ├── database.py
│   ├── docker-compose.yml
│   └── requirements.txt
├── mobile/
│   ├── flutter/
│   │   ├── lib/
│   │   │   ├── screens/
│   │   │   ├── widgets/
│   │   │   ├── services/
│   │   │   ├── models/
│   │   │   └── db/
├── web/
│   ├── react/
│   │   ├── src/
│   │   │   ├── pages/
│   │   │   ├── components/
│   │   │   ├── services/
│   │   │   └── store/
├── docs/
│   ├── API.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   └── AI_LOGIC.md
├── scripts/
│   ├── setup.sh
│   ├── migrate.sh
│   └── deploy.sh
└── README.md
```

---

## 11. SUCCESS METRICS (MVP)

| Metric                  | Target                 | Why              |
| ----------------------- | ---------------------- | ---------------- |
| **API Response Time**   | < 500ms (p95)          | User retention   |
| **Uptime**              | 99% during 6am-9pm     | Business hours   |
| **Sync Success Rate**   | > 99%                  | Data consistency |
| **App Size**            | < 50MB                 | Mobile adoption  |
| **Search Latency**      | < 100ms                | UX perception    |
| **Accounting Accuracy** | 100% match with manual | Compliance       |
| **Forecast MAPE**       | < 25%                  | Business utility |

---

## PHASE 1 COMPLETE ✓

**Deliverables:**
✓ Product vision & market fit  
✓ User roles & personas (4 roles)  
✓ 10 core modules defined  
✓ System architecture (8 microservices)  
✓ Data flow diagrams  
✓ Design decisions rationale  
✓ Security & compliance approach

**Next Phase:** PHASE 2 – DATABASE DESIGN (PostgreSQL schema)

---

**Approval:** Ready for DB design  
**Review Date:** Feb 4, 2026
