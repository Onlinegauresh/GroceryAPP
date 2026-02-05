"""Inventory management routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from shared.database import get_db
from shared.models import Product, StockMovement, User, RoleEnum
from shared.security import verify_token
from shared.exceptions import UnauthorizedException, NotFoundException, ValidationException

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


# ===== SCHEMAS =====
class StockAdjustmentRequest(BaseModel):
    """Stock adjustment request"""
    product_id: int
    quantity_change: int  # Positive for inbound, negative for adjustment/damage
    adjustment_reason: str  # 'adjustment', 'damage', 'loss', 'return', 'correction'
    notes: Optional[str] = None


class StockAdjustmentResponse(BaseModel):
    """Stock adjustment response"""
    product_id: int
    product_name: str
    previous_stock: int
    quantity_change: int
    new_stock: int
    reason: str
    timestamp: datetime

    class Config:
        from_attributes = True


class StockMovementResponse(BaseModel):
    """Stock movement history response"""
    id: int
    product_id: int
    movement_type: str
    quantity: int
    reference_type: Optional[str]
    reference_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryStatusResponse(BaseModel):
    """Inventory status response"""
    product_id: int
    product_name: str
    sku: str
    current_stock: int
    min_stock_level: int
    max_stock_level: Optional[int]
    reorder_quantity: int
    status: str  # 'normal', 'low', 'critical', 'overstocked'


# ===== HELPER FUNCTIONS =====
def check_auth(token: str, db: Session):
    """Verify token and return user"""
    try:
        token_data = verify_token(token)
    except Exception as e:
        raise UnauthorizedException(str(e))

    user = db.query(User).filter(
        User.id == token_data.user_id,
        User.deleted_at == None
    ).first()

    if not user:
        raise UnauthorizedException("User not found")

    return user, token_data


def check_inventory_access(token: str, db: Session, shop_id: int):
    """Check inventory access (staff/owner)"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    if user.role not in [RoleEnum.STAFF, RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise UnauthorizedException(
            "Insufficient permissions for inventory management")

    return user, token_data


# ===== ENDPOINTS =====

@router.get("/status", response_model=list)
def get_inventory_status(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    include_inactive: bool = Query(False)
):
    """
    Get inventory status for all products.

    Status codes:
    - **normal**: Stock above minimum
    - **low**: Stock below minimum, above 0
    - **critical**: Stock at 0
    - **overstocked**: Stock above maximum (if set)
    """
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    query = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.deleted_at == None
    )

    if not include_inactive:
        query = query.filter(Product.is_active == True)

    products = query.all()

    results = []
    for product in products:
        # Determine status
        if product.current_stock == 0:
            status = "critical"
        elif product.current_stock < product.min_stock_level:
            status = "low"
        elif product.max_stock_level and product.current_stock > product.max_stock_level:
            status = "overstocked"
        else:
            status = "normal"

        results.append({
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "current_stock": product.current_stock,
            "min_stock_level": product.min_stock_level,
            "max_stock_level": product.max_stock_level,
            "reorder_quantity": product.reorder_quantity,
            "status": status
        })

    return results


@router.post("/adjust", response_model=StockAdjustmentResponse)
def adjust_stock(
    shop_id: int,
    request: StockAdjustmentRequest,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Manually adjust product stock.

    Reasons:
    - **adjustment**: Manual correction
    - **damage**: Product damaged
    - **loss**: Theft or loss
    - **return**: Customer return
    - **correction**: Data correction
    """
    user, token_data = check_inventory_access(token, db, shop_id)

    # Get product
    product = db.query(Product).filter(
        Product.id == request.product_id,
        Product.shop_id == shop_id,
        Product.deleted_at == None
    ).first()

    if not product:
        raise NotFoundException("Product not found")

    # Validate new stock won't be negative
    new_stock = product.current_stock + request.quantity_change
    if new_stock < 0:
        raise ValidationException(
            f"Adjustment would result in negative stock. "
            f"Current: {product.current_stock}, Change: {request.quantity_change}"
        )

    previous_stock = product.current_stock

    # Update stock
    product.current_stock = new_stock
    product.updated_at = datetime.utcnow()

    # Log movement
    movement = StockMovement(
        shop_id=shop_id,
        product_id=product.id,
        movement_type="adjustment",
        quantity=request.quantity_change,
        reference_type="manual",
        notes=f"{request.adjustment_reason}: {request.notes or ''}",
        moved_by=token_data.user_id
    )

    db.add(movement)
    db.commit()
    db.refresh(product)

    return {
        "product_id": product.id,
        "product_name": product.name,
        "previous_stock": previous_stock,
        "quantity_change": request.quantity_change,
        "new_stock": new_stock,
        "reason": request.adjustment_reason,
        "timestamp": datetime.utcnow()
    }


@router.get("/{product_id}/history", response_model=list)
def get_stock_history(
    shop_id: int,
    product_id: int,
    token: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, le=500)
):
    """Get stock movement history for a product"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    # Verify product exists in shop
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id
    ).first()

    if not product:
        raise NotFoundException("Product not found")

    # Get movements
    movements = db.query(StockMovement).filter(
        StockMovement.product_id == product_id,
        StockMovement.shop_id == shop_id
    ).order_by(StockMovement.created_at.desc()).limit(limit).all()

    return [
        {
            "id": m.id,
            "product_id": m.product_id,
            "movement_type": m.movement_type,
            "quantity": m.quantity,
            "reference_type": m.reference_type,
            "reference_id": m.reference_id,
            "notes": m.notes,
            "moved_by_user_id": m.moved_by,
            "created_at": m.created_at
        }
        for m in movements
    ]


@router.get("/alerts/low-stock", response_model=list)
def get_low_stock_alerts(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get all products with low stock that need reordering"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    # Products below minimum level
    low_stock = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.current_stock < Product.min_stock_level,
        Product.is_active == True,
        Product.deleted_at == None
    ).order_by(Product.current_stock).all()

    results = []
    for product in low_stock:
        results.append({
            "product_id": product.id,
            "product_name": product.name,
            "sku": product.sku,
            "current_stock": product.current_stock,
            "min_stock_level": product.min_stock_level,
            "reorder_quantity": product.reorder_quantity or 0,
            "suggested_order_qty": (product.min_stock_level * 2) - product.current_stock,
            "urgency": "critical" if product.current_stock == 0 else "high"
        })

    return results
