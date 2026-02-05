"""Test customer registration"""
from shared.auth_utils import hash_password
from shared.models import User, Shop, RoleEnum
from shared.database import SessionLocal, engine, Base
from sqlalchemy.orm import Session
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='ignore')


# Create tables
Base.metadata.create_all(bind=engine)

# Get session
db = SessionLocal()

try:
    # Check if shop exists
    shop = db.query(Shop).filter(Shop.id == 1).first()
    if not shop:
        print("[ERROR] Shop 1 does not exist")
        print("[INFO] Creating default shop...")
        default_shop = Shop(
            id=1,
            name="SmartKirana",
            email="admin@smartkirana.local",
            phone="1000000000",
            address="123 Main Street",
            city="City",
            state="State",
            pincode="000000",
            country="India",
            is_active=True
        )
        db.add(default_shop)
        db.commit()
        shop = default_shop
        print(f"[OK] Shop created: {shop.name}")
    else:
        print(f"[OK] Shop exists: {shop.name} (ID={shop.id})")

    # Try to create a test customer
    print("[INFO] Testing customer registration...")
    test_phone = "9876543210"

    # Check if customer already exists
    existing = db.query(User).filter(User.phone == test_phone).first()
    if existing:
        print(f"[WARN] Customer already exists: {existing.phone}")
        db.delete(existing)
        db.commit()
        print(f"[OK] Deleted existing customer")

    # Create new customer
    new_user = User(
        shop_id=1,
        phone=test_phone,
        email="test@example.com",
        name="Test Customer",
        role=RoleEnum.CUSTOMER,
        password_hash=hash_password("password123")
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    print(f"[OK] Customer created successfully!")
    print(f"  ID: {new_user.id}")
    print(f"  Name: {new_user.name}")
    print(f"  Phone: {new_user.phone}")
    print(f"  Role: {new_user.role}")
    print(f"  Shop ID: {new_user.shop_id}")

    # Verify customer exists
    verify = db.query(User).filter(User.phone == test_phone).first()
    if verify:
        print(f"[OK] Verification: Customer found in database")
    else:
        print(f"[ERROR] Verification failed: Customer not found in database")

except Exception as e:
    print(f"[ERROR] {str(e)}")
    import traceback
    traceback.print_exc()

finally:
    db.close()
    print("[OK] Test completed")
