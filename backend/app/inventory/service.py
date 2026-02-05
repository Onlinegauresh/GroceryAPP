"""Inventory management service logic"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from app.inventory.models import Inventory
from app.inventory.schemas import InventoryCreate, InventoryUpdateStock, LowStockAlert
from shared.models import Shop, Product, User, RoleEnum
from fastapi import HTTPException, status
from datetime import datetime
from decimal import Decimal


class InventoryService:
    """Service for inventory operations"""

    @staticmethod
    def add_to_inventory(db: Session, shop_id: int, inventory_data: InventoryCreate) -> Inventory:
        """Add a product to shop inventory"""
        # Verify shop exists
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )

        # Verify product exists and belongs to shop
        product = db.query(Product).filter(
            and_(Product.id == inventory_data.product_id,
                 Product.shop_id == shop_id)
        ).first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found in this shop"
            )

        # Check if inventory already exists for this product + batch
        existing = db.query(Inventory).filter(
            and_(
                Inventory.shop_id == shop_id,
                Inventory.product_id == inventory_data.product_id,
                Inventory.batch_no == inventory_data.batch_no
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Inventory already exists for this product and batch"
            )

        # Validate prices
        if inventory_data.selling_price < inventory_data.cost_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Selling price cannot be less than cost price"
            )

        # Create inventory entry
        new_inventory = Inventory(
            shop_id=shop_id,
            product_id=inventory_data.product_id,
            quantity=inventory_data.quantity,
            min_quantity=inventory_data.min_quantity,
            cost_price=inventory_data.cost_price,
            selling_price=inventory_data.selling_price,
            batch_no=inventory_data.batch_no,
            expiry_date=inventory_data.expiry_date
        )

        db.add(new_inventory)
        db.commit()
        db.refresh(new_inventory)

        return new_inventory

    @staticmethod
    def update_stock(db: Session, shop_id: int, stock_data: InventoryUpdateStock) -> Inventory:
        """Update stock quantity for a product"""
        # Verify shop exists
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )

        # Find inventory entry (if batch_no is None, get first available)
        inventory = db.query(Inventory).filter(
            and_(
                Inventory.shop_id == shop_id,
                Inventory.product_id == stock_data.product_id,
                or_(
                    Inventory.batch_no == stock_data.batch_no,
                    (Inventory.batch_no ==
                     None if stock_data.batch_no is None else False)
                )
            )
        ).first()

        if not inventory:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Inventory not found for this product"
            )

        # Calculate new quantity
        new_quantity = inventory.quantity + stock_data.quantity_change

        # Prevent negative stock
        if new_quantity < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot reduce stock below 0. Current: {inventory.quantity}, Change: {stock_data.quantity_change}"
            )

        # Update quantity and timestamp
        inventory.quantity = new_quantity
        inventory.last_updated = datetime.utcnow()

        db.commit()
        db.refresh(inventory)

        return inventory

    @staticmethod
    def get_shop_inventory(db: Session, shop_id: int, skip: int = 0, limit: int = 20):
        """Get all inventory items for a shop"""
        # Verify shop exists
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )

        # Get inventory items
        items = db.query(Inventory).filter(
            Inventory.shop_id == shop_id
        ).offset(skip).limit(limit).all()

        total = db.query(Inventory).filter(
            Inventory.shop_id == shop_id).count()

        # Calculate statistics
        total_items = len(items)
        in_stock = sum(1 for inv in items if inv.quantity > 0)
        low_stock = sum(1 for inv in items if 0 <
                        inv.quantity <= inv.min_quantity)
        out_of_stock = sum(1 for inv in items if inv.quantity == 0)

        # Calculate total inventory value
        total_value = sum(
            (inv.cost_price * inv.quantity) for inv in items
        )

        return {
            "items": items,
            "total": total,
            "skip": skip,
            "limit": limit,
            "summary": {
                "total_products": total_items,
                "in_stock": in_stock,
                "low_stock": low_stock,
                "out_of_stock": out_of_stock,
                "total_inventory_value": total_value
            }
        }

    @staticmethod
    def get_low_stock_alerts(db: Session, shop_id: int) -> list:
        """Get all products below minimum stock level"""
        # Verify shop exists
        shop = db.query(Shop).filter(Shop.id == shop_id).first()
        if not shop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Shop not found"
            )

        # Get low stock items
        low_stock_items = db.query(Inventory).filter(
            and_(
                Inventory.shop_id == shop_id,
                Inventory.quantity <= Inventory.min_quantity
            )
        ).order_by(Inventory.quantity.asc()).all()

        # Build alert list
        alerts = []
        for item in low_stock_items:
            product = db.query(Product).filter(
                Product.id == item.product_id).first()
            if product:
                alert = LowStockAlert(
                    product_id=item.product_id,
                    product_name=product.name,
                    product_sku=product.sku,
                    current_quantity=item.quantity,
                    min_quantity=item.min_quantity,
                    shortage=item.min_quantity - item.quantity,
                    last_updated=item.last_updated
                )
                alerts.append(alert)

        return alerts

    @staticmethod
    def verify_shop_access(db: Session, shop_id: int, user_id: int, required_role=None):
        """Verify user has access to shop inventory"""
        # Get user
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Admin has access to all shops
        if user.role == RoleEnum.ADMIN:
            return user

        # Non-admin users can only access their own shop
        if user.shop_id != shop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this shop's inventory"
            )

        # Check specific role if required
        if required_role:
            if user.role != required_role:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"This operation requires {required_role} role"
                )

        return user
