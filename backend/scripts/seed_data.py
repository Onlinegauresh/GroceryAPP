"""Bootstrap script to seed initial data"""
from decimal import Decimal
from datetime import datetime
from shared.security import hash_password
from shared.models import Base, Shop, User, RoleEnum, Product, ChartOfAccounts
from shared.database import SessionLocal, engine
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path so we can import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def seed_data():
    """Create initial demo data"""

    # Create tables
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # ===== SEED CHART OF ACCOUNTS =====
        print("Creating chart of accounts...")

        accounts = [
            # Assets
            ("1001", "Cash", "asset", "Cash in hand and bank"),
            ("1002", "Bank Account", "asset", "Bank deposits"),
            ("1003", "Inventory", "asset", "Stock of goods"),
            ("1004", "Accounts Receivable", "asset", "Customer credit dues"),

            # Liabilities
            ("2001", "Accounts Payable", "liability", "Supplier credit dues"),
            ("2002", "Loan Payable", "liability", "Bank/personal loans"),
            ("2003", "GST Payable", "liability", "GST collected from sales"),

            # Equity
            ("3001", "Capital", "equity", "Owner's capital"),

            # Revenue
            ("4001", "Sales Revenue", "revenue", "Income from sales"),
            ("4002", "Sales Return", "revenue", "Customer returns"),

            # Expenses
            ("5001", "Cost of Goods Sold", "expense", "Product cost"),
            ("5002", "Salary & Wages", "expense", "Staff salaries"),
            ("5003", "Rent", "expense", "Store rent"),
            ("5004", "Utilities", "expense", "Electricity, water"),
            ("5005", "Administrative", "expense", "Office expenses"),
        ]

        for code, name, type_, desc in accounts:
            existing = db.query(ChartOfAccounts).filter(
                ChartOfAccounts.account_code == code).first()
            if not existing:
                account = ChartOfAccounts(
                    account_code=code,
                    account_name=name,
                    account_type=type_,
                    description=desc
                )
                db.add(account)

        db.commit()
        print("✓ Chart of accounts created")

        # ===== SEED SHOP =====
        print("\nCreating demo shop...")

        shop = db.query(Shop).filter(
            Shop.email == "demo@smartkirana.local").first()
        if not shop:
            shop = Shop(
                name="Demo Kirana Store",
                email="demo@smartkirana.local",
                phone="9999999999",
                address="123 Market Street",
                city="Delhi",
                state="Delhi",
                pincode="110001",
                gst_number="27AAFCU5055K1ZO",
                subscription_plan="free",
                is_active=True
            )
            db.add(shop)
            db.commit()
            db.refresh(shop)

        shop_id = shop.id
        print(f"✓ Demo shop created (ID: {shop_id})")

        # ===== SEED USERS =====
        print("\nCreating demo users...")

        users_data = [
            ("9876543210", "owner@kirana.local", "Rajesh Kumar", RoleEnum.OWNER),
            ("9876543211", "staff@kirana.local", "Priya Singh", RoleEnum.STAFF),
            ("9876543212", "customer1@kirana.local",
             "Amit Patel", RoleEnum.CUSTOMER),
            ("9876543213", "customer2@kirana.local",
             "Sneha Sharma", RoleEnum.CUSTOMER),
        ]

        for phone, email, name, role in users_data:
            existing = db.query(User).filter(
                User.shop_id == shop_id,
                User.phone == phone
            ).first()

            if not existing:
                user = User(
                    shop_id=shop_id,
                    phone=phone,
                    email=email,
                    name=name,
                    role=role,
                    password_hash=hash_password("demo123"),
                    is_active=True
                )
                db.add(user)

        db.commit()
        print("✓ Demo users created")

        # ===== SEED PRODUCTS =====
        print("\nCreating demo products...")

        products_data = [
            ("RIC-001", "Basmati Rice 1kg", "Rice", "Dairy & Grains",
             "kg", Decimal(50), Decimal(80), Decimal(75), 5),
            ("TEA-001", "Tata Tea 500g", "Tea/Coffee", "Beverages",
             "g", Decimal(200), Decimal(350), Decimal(330), 18),
            ("MIL-001", "Milk 1L", "Dairy", "Dairy & Grains",
             "litre", Decimal(35), Decimal(45), Decimal(42), 0),
            ("OIL-001", "Sunflower Oil 1L", "Oil", "Cooking Items",
             "litre", Decimal(100), Decimal(150), Decimal(140), 5),
            ("SAL-001", "Iodized Salt 1kg", "Salt", "Cooking Items",
             "kg", Decimal(15), Decimal(25), Decimal(22), 0),
            ("SUG-001", "Sugar 1kg", "Sugar", "Dairy & Grains",
             "kg", Decimal(35), Decimal(50), Decimal(48), 5),
        ]

        for sku, name, category, subcategory, unit, cost, mrp, selling, gst in products_data:
            existing = db.query(Product).filter(
                Product.shop_id == shop_id,
                Product.sku == sku
            ).first()

            if not existing:
                product = Product(
                    shop_id=shop_id,
                    name=name,
                    sku=sku,
                    category=category,
                    subcategory=subcategory,
                    unit=unit,
                    cost_price=cost,
                    mrp=mrp,
                    selling_price=selling,
                    gst_rate=gst,
                    current_stock=100,
                    min_stock_level=10,
                    reorder_quantity=50,
                    is_active=True
                )
                db.add(product)

        db.commit()
        print("✓ Demo products created")

        print("\n" + "="*50)
        print("✓ Bootstrap complete!")
        print("="*50)
        print("\nDemo Credentials:")
        print("  Shop ID: 1")
        print("  Owner Phone: 9876543210")
        print("  Staff Phone: 9876543211")
        print("  Password: demo123")
        print("\nStart API: python main.py")
        print("API Docs: http://localhost:8000/api/docs")

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False

    finally:
        db.close()

    return True


if __name__ == "__main__":
    success = seed_data()
    sys.exit(0 if success else 1)
