"""Order management routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from shared.database import get_db
from shared.models import Order, OrderItem, User, RoleEnum
from shared.security import verify_token
from shared.exceptions import UnauthorizedException, NotFoundException, ValidationException
from order_service.service import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


# ===== SCHEMAS =====
class OrderItemRequest(BaseModel):
    """Order item in creation request"""
    product_id: int
    quantity: int


class CreateOrderRequest(BaseModel):
    """Create order request"""
    customer_id: Optional[int] = None  # None for walk-in customers
    items: List[OrderItemRequest]
    payment_method: str = "cash"  # 'cash', 'upi', 'card', 'bank_transfer', 'credit'
    is_credit_sale: bool = False
    credit_duration_days: Optional[int] = None
    notes: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Order item response"""
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    gst_rate: Decimal
    gst_amount: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    """Order response"""
    id: int
    order_number: str
    order_date: datetime
    subtotal: Decimal
    discount_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_method: str
    payment_status: str
    order_status: str
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """Order list response (without items)"""
    id: int
    order_number: str
    order_date: datetime
    total_amount: Decimal
    payment_status: str
    order_status: str

    class Config:
        from_attributes = True


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


# ===== ENDPOINTS =====

@router.post("", response_model=OrderResponse, status_code=201)
def create_order(
    shop_id: int,
    request: CreateOrderRequest,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Create new order with automatic inventory deduction.

    Process:
    1. Validate stock availability
    2. Calculate totals (with GST)
    3. Create order and items
    4. Deduct inventory automatically
    5. Create accounting ledger entries
    """
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot create orders for other shops")

    try:
        # Use OrderService to handle complex business logic
        order = OrderService.create_order(
            shop_id=shop_id,
            customer_id=request.customer_id,
            items=[{"product_id": item.product_id, "quantity": item.quantity}
                   for item in request.items],
            payment_method=request.payment_method,
            created_by=token_data.user_id,
            is_credit_sale=request.is_credit_sale,
            credit_duration_days=request.credit_duration_days,
            db=db
        )

        # Fetch items for response
        order_items = db.query(OrderItem).filter(
            OrderItem.order_id == order.id).all()

        return OrderResponse(
            id=order.id,
            order_number=order.order_number,
            order_date=order.order_date,
            subtotal=order.subtotal,
            discount_amount=order.discount_amount,
            tax_amount=order.tax_amount,
            total_amount=order.total_amount,
            payment_method=order.payment_method,
            payment_status=order.payment_status.value,
            order_status=order.order_status.value,
            items=order_items
        )

    except ValidationException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Order creation failed: {str(e)}")


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    shop_id: int,
    order_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get order details with items"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.shop_id == shop_id
    ).first()

    if not order:
        raise NotFoundException("Order not found")

    items = db.query(OrderItem).filter(OrderItem.order_id == order_id).all()

    return OrderResponse(
        id=order.id,
        order_number=order.order_number,
        order_date=order.order_date,
        subtotal=order.subtotal,
        discount_amount=order.discount_amount,
        tax_amount=order.tax_amount,
        total_amount=order.total_amount,
        payment_method=order.payment_method,
        payment_status=order.payment_status.value,
        order_status=order.order_status.value,
        items=items
    )


@router.get("", response_model=List[OrderListResponse])
def list_orders(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    status: Optional[str] = Query(None),
    payment_status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List orders for a shop.

    Filters:
    - **status**: Order status (pending, confirmed, packed, completed, cancelled)
    - **payment_status**: Payment status (pending, completed, failed, refunded)
    """
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    query = db.query(Order).filter(Order.shop_id == shop_id)

    if status:
        query = query.filter(Order.order_status == status)

    if payment_status:
        query = query.filter(Order.payment_status == payment_status)

    # Pagination
    offset = (page - 1) * limit
    orders = query.order_by(Order.order_date.desc()).offset(
        offset).limit(limit).all()

    return orders


@router.put("/{order_id}/status")
def update_order_status(
    shop_id: int,
    order_id: int,
    new_status: str,
    token: str,
    db: Session = Depends(get_db)
):
    """Update order status (staff/owner only)"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    if user.role not in [RoleEnum.STAFF, RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise UnauthorizedException("Insufficient permissions")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.shop_id == shop_id
    ).first()

    if not order:
        raise NotFoundException("Order not found")

    # Validate status
    valid_statuses = ["pending", "confirmed",
                      "packed", "completed", "cancelled"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    order.order_status = new_status
    order.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Order status updated",
        "order_id": order_id,
        "new_status": new_status
    }


@router.put("/{order_id}/payment-status")
def update_payment_status(
    shop_id: int,
    order_id: int,
    new_status: str,
    token: str,
    db: Session = Depends(get_db)
):
    """Update payment status (owner only)"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    if user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise UnauthorizedException(
            "Only shop owner can update payment status")

    order = db.query(Order).filter(
        Order.id == order_id,
        Order.shop_id == shop_id
    ).first()

    if not order:
        raise NotFoundException("Order not found")

    # Validate status
    valid_statuses = ["pending", "completed", "failed", "refunded"]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}")

    order.payment_status = new_status
    if new_status == "completed":
        order.payment_date = datetime.utcnow()

    order.updated_at = datetime.utcnow()
    db.commit()

    return {
        "message": "Payment status updated",
        "order_id": order_id,
        "new_status": new_status
    }
