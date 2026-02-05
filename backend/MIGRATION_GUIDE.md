# Database Migration Guide - Adding Users Table & RBAC

## Option 1: Auto-Creation (Development)

The app automatically creates tables on startup from SQLAlchemy models.

```bash
cd backend
python -c "
from shared.database import engine, Base
from app.auth.models import User
from product_service.models import Product

# Create all tables
Base.metadata.create_all(bind=engine)
print('✅ Tables created successfully')
"
```

---

## Option 2: Manual SQL (Production)

### SQLite

```sql
-- Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'customer' NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Update Products Table
ALTER TABLE products ADD COLUMN created_by INTEGER DEFAULT 1;
```

### PostgreSQL

```sql
-- Create Enum Type for Roles
CREATE TYPE user_role AS ENUM ('customer', 'staff', 'shop_owner', 'admin');

-- Create Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role user_role DEFAULT 'customer',
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create Indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active);

-- Update Products Table
ALTER TABLE products ADD COLUMN IF NOT EXISTS created_by UUID;
ALTER TABLE products ADD CONSTRAINT fk_products_user_id
  FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE CASCADE;
```

---

## Option 3: Using Alembic (Recommended for Production)

```bash
# Initialize Alembic (if not done)
cd backend
alembic init migrations

# Create a migration
alembic revision --autogenerate -m "Add users table and RBAC"

# Apply migration
alembic upgrade head

# Verify
alembic current
```

### Sample Migration File

Create: `migrations/versions/001_add_users_table.py`

```python
"""Add users table and RBAC

Revision ID: 001
Revises:
Create Date: 2024-02-05 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum
    op.execute("CREATE TYPE user_role AS ENUM ('customer', 'staff', 'shop_owner', 'admin')")

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('phone', sa.String(20), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', postgresql.ENUM(name='user_role'), nullable=False, server_default='customer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_phone', 'users', ['phone'])
    op.create_index('idx_users_role', 'users', ['role'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])

    # Add created_by to products
    op.add_column('products', sa.Column('created_by', postgresql.UUID(as_uuid=True)))
    op.create_foreign_key('fk_products_user_id', 'products', 'users', ['created_by'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_products_user_id', 'products', type_='foreignkey')
    op.drop_column('products', 'created_by')
    op.drop_index('idx_users_is_active', table_name='users')
    op.drop_index('idx_users_role', table_name='users')
    op.drop_index('idx_users_phone', table_name='users')
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')
    op.execute('DROP TYPE user_role')
```

---

## Verify Installation

### Check Users Table (SQLite)

```bash
sqlite3 smartkirana.db ".schema users"
```

**Expected Output:**

```sql
CREATE TABLE users (
    id VARCHAR(36) NOT NULL,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active BOOLEAN NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (email),
    UNIQUE (phone)
);
```

### Check Users Table (PostgreSQL)

```bash
psql -U smartkirana -d smartkirana -c "\d users"
```

---

## Seed Demo Users

```python
# seed_auth_users.py
from sqlalchemy.orm import Session
from shared.database import SessionLocal, engine, Base
from app.auth.models import User, RoleEnum
from app.auth.security import hash_password
from uuid import uuid4

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Demo users
demo_users = [
    {
        "name": "Admin User",
        "email": "admin@smartkirana.com",
        "phone": "9000000001",
        "password": "admin@123",
        "role": RoleEnum.ADMIN
    },
    {
        "name": "Shop Owner",
        "email": "owner@smartkirana.com",
        "phone": "9000000002",
        "password": "owner@123",
        "role": RoleEnum.SHOP_OWNER
    },
    {
        "name": "Staff Member",
        "email": "staff@smartkirana.com",
        "phone": "9000000003",
        "password": "staff@123",
        "role": RoleEnum.STAFF
    },
    {
        "name": "Customer",
        "email": "customer@smartkirana.com",
        "phone": "9000000004",
        "password": "customer@123",
        "role": RoleEnum.CUSTOMER
    }
]

for user_data in demo_users:
    # Check if user exists
    existing = db.query(User).filter(User.email == user_data["email"]).first()
    if existing:
        print(f"⏭️  User {user_data['email']} already exists")
        continue

    # Create user
    user = User(
        id=str(uuid4()),
        name=user_data["name"],
        email=user_data["email"],
        phone=user_data["phone"],
        password_hash=hash_password(user_data["password"]),
        role=user_data["role"],
        is_active=True
    )
    db.add(user)
    print(f"✅ Created user: {user_data['email']} ({user_data['role'].value})")

db.commit()
db.close()
print("\n✅ Auth users seeded successfully!")
```

**Run:**

```bash
python seed_auth_users.py
```

---

## Check After Migration

```bash
# Start server
python main_with_auth.py

# In another terminal, test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "phone": "9876543210",
    "password": "password123",
    "role": "customer"
  }'

# Should return 201 Created
```

---

## Rollback Migration (if needed)

### SQLite (No rollback needed, delete db)

```bash
rm smartkirana.db
python main_with_auth.py  # Recreates tables
```

### PostgreSQL (Using Alembic)

```bash
# Rollback one revision
alembic downgrade -1

# Rollback to specific revision
alembic downgrade 001
```

---

## Summary

✅ Users table created
✅ RBAC enum for roles
✅ Indexes for performance
✅ Products linked to creator
✅ Demo users seeded
✅ Ready for authentication

---

**Migration Complete! 🎉**
