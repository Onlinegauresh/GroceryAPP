"""Shop management service logic"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from shared.models import Shop, User, Product, RoleEnum
from app.shops.schemas import ShopCreate, ShopUpdate
from fastapi import HTTPException, status
from datetime import datetime


class ShopService:
    """Service for shop management operations"""

    @staticmethod
    def create_shop(db: Session, shop_data: ShopCreate, owner_id: int) -> Shop:
        """Create a new shop (owner_id is the logged-in user)"""
        # Check if user exists and is OWNER or ADMIN
        owner = db.query(User).filter(User.id == owner_id).first()
        if not owner:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify user is OWNER or ADMIN
        if owner.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only shop owners or admins can create shops"
            )

        # Check for duplicate email
        existing = db.query(Shop).filter(Shop.email == shop_data.email).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Shop with this email already exists"
            )

        # Create shop
        new_shop = Shop(
            name=shop_data.name,
            email=shop_data.email,
            phone=shop_data.phone,
            address=shop_data.address,
            city=shop_data.city,
            state=shop_data.state,
            pincode=shop_data.pincode,
            shop_category=shop_data.shop_category,
            gst_number=shop_data.gst_number,
            pan_number=shop_data.pan_number,
            is_active=True,
            subscription_plan="free",
            onboarded_at=datetime.utcnow()
        )

        db.add(new_shop)
        db.commit()
        db.refresh(new_shop)

        return new_shop

    @staticmethod
    def get_shop(db: Session, shop_id: int) -> Shop:
        """Get shop by ID"""
        shop = db.query(Shop).filter(and_(
            Shop.id == shop_id,
            Shop.deleted_at == None
        )).first()

        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )

        return shop

    @staticmethod
    def list_shops(db: Session, skip: int = 0, limit: int = 20):
        """List all active shops (admin only - verified in router)"""
        shops = db.query(Shop).filter(
            Shop.deleted_at == None
        ).offset(skip).limit(limit).all()

        total = db.query(Shop).filter(Shop.deleted_at == None).count()

        return {"shops": shops, "total": total, "skip": skip, "limit": limit}

    @staticmethod
    def update_shop(db: Session, shop_id: int, shop_data: ShopUpdate, user_id: int) -> Shop:
        """Update shop (owner can update their own shop, admin can update any)"""
        shop = ShopService.get_shop(db, shop_id)

        # Verify ownership (unless user is admin)
        user = db.query(User).filter(User.id == user_id).first()
        is_admin = user.role == RoleEnum.ADMIN if user else False

        shop_owner = db.query(User).filter(
            and_(User.shop_id == shop_id, User.role == RoleEnum.OWNER)
        ).first()

        if not is_admin and (not shop_owner or shop_owner.id != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own shop"
            )

        # Update fields
        update_data = shop_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(shop, field, value)

        shop.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(shop)

        return shop

    @staticmethod
    def deactivate_shop(db: Session, shop_id: int, user_id: int) -> Shop:
        """Deactivate a shop (owner or admin only)"""
        shop = ShopService.get_shop(db, shop_id)

        # Verify ownership
        user = db.query(User).filter(User.id == user_id).first()
        is_admin = user.role == RoleEnum.ADMIN if user else False

        shop_owner = db.query(User).filter(
            and_(User.shop_id == shop_id, User.role == RoleEnum.OWNER)
        ).first()

        if not is_admin and (not shop_owner or shop_owner.id != user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only deactivate your own shop"
            )

        shop.is_active = False
        shop.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(shop)

        return shop

    @staticmethod
    def get_shop_inventory_count(db: Session, shop_id: int) -> dict:
        """Get shop inventory statistics"""
        total_products = db.query(Product).filter(
            and_(Product.shop_id == shop_id, Product.is_active == True)
        ).count()

        low_stock = db.query(Product).filter(
            and_(
                Product.shop_id == shop_id,
                Product.is_active == True,
                Product.current_stock <= Product.min_stock_level
            )
        ).count()

        return {
            "total_products": total_products,
            "low_stock_count": low_stock
        }
