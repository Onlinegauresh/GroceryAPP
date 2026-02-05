"""Utility to create a new shop from command line"""
import sys
from sqlalchemy.orm import Session
from shared.database import SessionLocal
from shared.models import Shop


def create_shop():
    """Create a new shop interactively"""

    print("="*50)
    print("Create New Shop")
    print("="*50)

    name = input("Shop Name: ").strip()
    email = input("Email: ").strip()
    phone = input("Phone (10 digits): ").strip()
    address = input("Address: ").strip()
    city = input("City: ").strip()
    state = input("State: ").strip()
    pincode = input("Pincode: ").strip()
    gst = input("GST Number (optional): ").strip() or None

    db = SessionLocal()

    try:
        # Check if email already exists
        existing = db.query(Shop).filter(Shop.email == email).first()
        if existing:
            print(f"✗ Email {email} already registered")
            return False

        # Create shop
        shop = Shop(
            name=name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            pincode=pincode,
            gst_number=gst,
            is_active=True
        )

        db.add(shop)
        db.commit()
        db.refresh(shop)

        print("\n" + "="*50)
        print("✓ Shop Created Successfully!")
        print("="*50)
        print(f"Shop ID: {shop.id}")
        print(f"Name: {shop.name}")
        print(f"Email: {shop.email}")
        print("\nNext: Create owner user for this shop")

        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        db.rollback()
        return False

    finally:
        db.close()


if __name__ == "__main__":
    success = create_shop()
    sys.exit(0 if success else 1)
