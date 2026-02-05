"""Inventory management API routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from decimal import Decimal
from shared.database import get_db
from shared.models import User, RoleEnum
from app.auth.security import get_current_user
from app.inventory.schemas import (
    InventoryCreate, InventoryUpdateStock, InventoryResponse,
    InventoryDetailResponse, ShopInventoryResponse, LowStockAlertResponse
)
from app.inventory.service import InventoryService
from app.inventory.models import Inventory
from shared.models import Product

router = APIRouter(prefix="/api/v1/inventory", tags=["inventory"])


def require_inventory_write_access(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to verify user can modify inventory"""
    if current_user.role not in [RoleEnum.OWNER, RoleEnum.STAFF, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only shop staff, owners, or admins can modify inventory"
        )
    return current_user


@router.post(
    "",
    response_model=InventoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add product to inventory",
    description="Add a product to a shop's inventory with pricing and stock levels."
)
def add_to_inventory(
    inventory_data: InventoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inventory_write_access)
):
    """
    Add a product to shop inventory.

    **Business Rules:**
    - Only OWNER, STAFF, or ADMIN can add inventory
    - Product must belong to the shop
    - Cannot add duplicate product + batch combinations
    - Selling price must be >= cost price
    - If no batch number, all items are in one batch

    **Use Cases:**
    - Initial stock entry when receiving products
    - Adding new batches of existing products
    - Different pricing per batch (e.g., discounted old stock)
    """
    shop_id = current_user.shop_id

    # Verify user has write access to their shop
    InventoryService.verify_shop_access(db, shop_id, current_user.id)

    inventory = InventoryService.add_to_inventory(db, shop_id, inventory_data)
    return inventory


@router.patch(
    "/update-stock",
    response_model=InventoryResponse,
    summary="Update product stock quantity",
    description="Increase or decrease stock for a product in inventory."
)
def update_stock(
    stock_data: InventoryUpdateStock,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_inventory_write_access)
):
    """
    Update stock quantity.

    **Parameters:**
    - `quantity_change`: Positive for inbound, negative for outbound
      - Example: 100 (add 100 units)
      - Example: -50 (reduce by 50 units)
    - `batch_no`: Optional batch identifier (null = use first available)

    **Business Rules:**
    - Cannot go below 0 (system prevents negative stock)
    - Updates last_updated timestamp automatically
    - No order processing here (orders handle stock reduction later)
    - Useful for: receipts, adjustments, damage reporting

    **Access:**
    - OWNER, STAFF, ADMIN of the shop
    """
    shop_id = current_user.shop_id

    # Verify access
    InventoryService.verify_shop_access(db, shop_id, current_user.id)

    inventory = InventoryService.update_stock(db, shop_id, stock_data)
    return inventory


@router.get(
    "/shop/{shop_id}",
    summary="Get shop inventory",
    description="Get all inventory items for a shop with statistics."
)
def get_shop_inventory(
    shop_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all inventory for a shop.

    **Access:**
    - Shop owner, staff can view their own shop inventory
    - Admin can view any shop inventory
    - Customer has no access

    **Returns:**
    - Inventory items list (paginated)
    - Summary statistics:
      - total_products: Count of products in inventory
      - in_stock: Products with quantity > 0
      - low_stock: Products at or below min_quantity
      - out_of_stock: Products with 0 quantity
      - total_inventory_value: Sum of (cost_price × quantity)
    """
    # Verify access
    InventoryService.verify_shop_access(db, shop_id, current_user.id)

    result = InventoryService.get_shop_inventory(db, shop_id, skip, limit)

    # Build response with product names
    items_with_details = []
    for inv in result["items"]:
        product = db.query(Product).filter(
            Product.id == inv.product_id).first()
        items_with_details.append({
            "id": inv.id,
            "shop_id": inv.shop_id,
            "product_id": inv.product_id,
            "product_name": product.name if product else "Unknown",
            "product_sku": product.sku if product else "Unknown",
            "quantity": inv.quantity,
            "min_quantity": inv.min_quantity,
            "cost_price": inv.cost_price,
            "selling_price": inv.selling_price,
            "batch_no": inv.batch_no,
            "expiry_date": inv.expiry_date,
            "stock_status": "out_of_stock" if inv.quantity == 0 else (
                "low_stock" if inv.quantity <= inv.min_quantity else "in_stock"
            ),
            "last_updated": inv.last_updated,
            "created_at": inv.created_at
        })

    return {
        "shop_id": shop_id,
        "data": items_with_details,
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"],
        "summary": result["summary"]
    }


@router.get(
    "/low-stock/{shop_id}",
    response_model=LowStockAlertResponse,
    summary="Get low stock alerts",
    description="Get all products below minimum stock level for a shop."
)
def get_low_stock_alerts(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get low stock alerts for a shop.

    **Business Rules:**
    - Shows products with quantity <= min_quantity
    - 'shortage' field = min_quantity - current_quantity
    - Sorted by severity (lowest stock first)
    - Used for reordering decisions

    **Access:**
    - Shop owner, staff can view their own shop alerts
    - Admin can view any shop alerts
    - Customer has no access

    **Use Cases:**
    - Daily inventory review
    - Automated reorder triggers
    - Dashboard alerts
    """
    # Verify access
    InventoryService.verify_shop_access(db, shop_id, current_user.id)

    alerts = InventoryService.get_low_stock_alerts(db, shop_id)

    return {
        "shop_id": shop_id,
        "alert_count": len(alerts),
        "alerts": alerts
    }
