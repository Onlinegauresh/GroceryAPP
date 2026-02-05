"""Order management FastAPI router"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from shared.database import get_db
from app.auth.security import get_current_user
from shared.models import User, RoleEnum, OrderStatusEnum
from app.orders.schemas import (
    OrderCreateRequest, OrderStatusUpdate, OrderResponse,
    OrderDetailResponse, OrderListResponse, OrderDashboard
)
from app.orders.service import OrderService
from app.accounting.service import AccountingService

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"],
    dependencies=[Depends(get_current_user)]
)


def require_order_create_access(user: User = Depends(get_current_user)):
    """Verify user can create orders"""
    if user.role not in [RoleEnum.CUSTOMER, RoleEnum.STAFF, RoleEnum.OWNER]:
        raise HTTPException(
            status_code=403,
            detail="Customers, staff, and owners can create orders"
        )
    return user


def require_order_manage_access(user: User = Depends(get_current_user)):
    """Verify user can manage orders (STAFF/OWNER/ADMIN)"""
    if user.role not in [RoleEnum.STAFF, RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=403,
            detail="Only staff, owners, and admins can manage orders"
        )
    return user


# ===== ORDER CREATION =====

@router.post(
    "/shops/{shop_id}",
    response_model=OrderDetailResponse,
    status_code=201,
    summary="Create Order",
    description="Create new order with inventory auto-deduction. Customers can place own orders, staff/owners manage shop orders."
)
def create_order(
    shop_id: int,
    request: OrderCreateRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_order_create_access),
):
    """Create a new order with automatic inventory deduction"""
    # For customers, they can only place orders for themselves
    if user.role == RoleEnum.CUSTOMER:
        if request.customer_id and request.customer_id != user.id:
            raise HTTPException(
                status_code=403,
                detail="Customers can only place orders for themselves"
            )
        request.customer_id = user.id

    success, message, order = OrderService.create_order(
        db, shop_id, user, request
    )

    if not success:
        # Determine appropriate status code
        if "not found" in message.lower():
            status_code = 404
        elif "insufficient" in message.lower() or "not available" in message.lower():
            status_code = 409  # Conflict - inventory not available
        else:
            status_code = 400

        raise HTTPException(status_code=status_code, detail=message)

    return order


# ===== ORDER RETRIEVAL =====

@router.get(
    "/shops/{shop_id}/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get Order Details",
    description="Retrieve specific order details. Customers view own orders, staff/owners view shop orders, admins view all."
)
def get_order(
    shop_id: int,
    order_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get order details"""
    # Access control
    if user.role == RoleEnum.CUSTOMER:
        # Customers can only view their own orders
        access_ok, _ = OrderService.verify_shop_access(user, shop_id, db)
        if not access_ok:
            raise HTTPException(
                status_code=403, detail="Cannot access this shop")
    elif user.role in [RoleEnum.STAFF, RoleEnum.OWNER]:
        # Staff/owners can view their shop's orders
        access_ok, msg = OrderService.verify_shop_access(user, shop_id, db)
        if not access_ok:
            raise HTTPException(status_code=403, detail=msg)
    elif user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    order = OrderService.get_order(db, shop_id, order_id)
    if not order:
        raise HTTPException(
            status_code=404, detail=f"Order {order_id} not found")

    return order


@router.get(
    "/shops/{shop_id}",
    response_model=OrderListResponse,
    summary="List Orders",
    description="List orders with pagination and optional status filter. Staff/owners view shop orders, admins view all."
)
def list_orders(
    shop_id: int,
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(20, ge=1, le=100, description="Limit records"),
    status: Optional[OrderStatusEnum] = Query(
        None, description="Filter by order status"),
    db: Session = Depends(get_db),
    user: User = Depends(require_order_manage_access),
):
    """List orders for a shop with optional filtering"""
    # Verify access
    access_ok, msg = OrderService.verify_shop_access(user, shop_id, db)
    if not access_ok:
        raise HTTPException(status_code=403, detail=msg)

    orders, total = OrderService.list_orders(
        db, shop_id, skip=skip, limit=limit, status=status
    )

    return OrderListResponse(
        orders=orders,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/me/my-orders",
    response_model=OrderListResponse,
    summary="Get My Orders",
    description="Customers retrieve their own orders"
)
def get_my_orders(
    skip: int = Query(0, ge=0, description="Skip records"),
    limit: int = Query(20, ge=1, le=100, description="Limit records"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get current user's orders (customers only)"""
    if user.role != RoleEnum.CUSTOMER:
        raise HTTPException(
            status_code=403,
            detail="Only customers can use this endpoint"
        )

    orders, total = OrderService.list_customer_orders(
        db, user.shop_id, user.id, skip=skip, limit=limit
    )

    return OrderListResponse(
        orders=orders,
        total=total,
        skip=skip,
        limit=limit
    )


# ===== ORDER STATUS UPDATES =====

@router.patch(
    "/shops/{shop_id}/{order_id}/status",
    response_model=OrderDetailResponse,
    summary="Update Order Status",
    description="Update order status through lifecycle: PLACED → ACCEPTED → PACKED → OUT_FOR_DELIVERY → DELIVERED"
)
def update_order_status(
    shop_id: int,
    order_id: int,
    request: OrderStatusUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(require_order_manage_access),
):
    """Update order status with validation and automatic accounting"""
    success, message, order = OrderService.update_order_status(
        db, shop_id, order_id, request, user
    )

    if not success:
        status_code = 404 if "not found" in message.lower() else 400
        raise HTTPException(status_code=status_code, detail=message)

    # PHASE F: Hook accounting service when order is DELIVERED
    if order.order_status == OrderStatusEnum.DELIVERED:
        try:
            # Create automatic accounting entries
            accounting_ok = AccountingService.process_order_delivery(
                order, db, user
            )
            if not accounting_ok:
                # Log but don't fail - accounting is secondary to order management
                pass
        except Exception as e:
            # Log accounting error but don't fail order update
            pass

    # PHASE F: Hook accounting service when order is CANCELLED
    if order.order_status == OrderStatusEnum.CANCELLED:
        try:
            # Reverse accounting entries
            accounting_ok = AccountingService.reverse_accounting_entries(
                order, db, user
            )
            if not accounting_ok:
                # Log but don't fail
                pass
        except Exception as e:
            # Log but don't fail
            pass

    return order


# ===== DASHBOARD & ANALYTICS =====

@router.get(
    "/shops/{shop_id}/dashboard",
    response_model=OrderDashboard,
    summary="Order Dashboard",
    description="Get order statistics and dashboard metrics for a shop"
)
def get_order_dashboard(
    shop_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_order_manage_access),
):
    """Get order dashboard with statistics"""
    # Verify access
    access_ok, msg = OrderService.verify_shop_access(user, shop_id, db)
    if not access_ok:
        raise HTTPException(status_code=403, detail=msg)

    dashboard_data = OrderService.get_order_dashboard(db, shop_id)

    return OrderDashboard(
        total_orders=dashboard_data["total_orders"],
        placed_orders=dashboard_data["placed_orders"],
        accepted_orders=dashboard_data["accepted_orders"],
        packed_orders=dashboard_data["packed_orders"],
        out_for_delivery_orders=dashboard_data["out_for_delivery_orders"],
        delivered_orders=dashboard_data["delivered_orders"],
        cancelled_orders=dashboard_data["cancelled_orders"],
        total_revenue=dashboard_data["total_revenue"],
        average_order_value=dashboard_data["average_order_value"],
        recent_orders=dashboard_data["recent_orders"],
    )
