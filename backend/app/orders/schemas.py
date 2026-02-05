"""Pydantic schemas for order operations"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum


class OrderStatusEnum(str, Enum):
    """Order status values"""
    PLACED = "placed"
    ACCEPTED = "accepted"
    PACKED = "packed"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


# ===== ORDER ITEM SCHEMAS =====

class OrderItemBase(BaseModel):
    """Base order item data"""
    product_id: int = Field(..., gt=0, description="Product ID")
    quantity: int = Field(..., gt=0, description="Quantity (must be positive)")
    unit_price: Decimal = Field(..., gt=0, description="Price per unit")


class OrderItemCreate(OrderItemBase):
    """Create order item request"""
    pass


class OrderItemResponse(OrderItemBase):
    """Order item response with calculated fields"""
    id: int
    order_id: int
    shop_id: int
    product_name: str
    gst_rate: Optional[Decimal] = None
    gst_amount: Optional[Decimal] = None
    discount_on_item: Decimal = Decimal("0.00")
    line_total: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


# ===== ORDER SCHEMAS =====

class OrderBase(BaseModel):
    """Base order data"""
    customer_id: Optional[int] = Field(
        None, description="Customer ID (if applicable)")
    customer_name: str = Field(..., min_length=1, max_length=255)
    customer_phone: str = Field(..., pattern=r"^\d{9,15}$")
    shipping_address: str = Field(..., min_length=1)


class OrderCreateRequest(OrderBase):
    """Create order request"""
    items: List[OrderItemCreate] = Field(..., min_items=1,
                                         description="At least one item required")
    notes: Optional[str] = None
    is_credit_sale: bool = Field(
        False, description="Whether this is a credit sale")
    credit_duration_days: Optional[int] = Field(None, ge=1, le=365)

    @field_validator("items")
    @classmethod
    def validate_items_not_empty(cls, v):
        """Ensure at least one item in order"""
        if not v:
            raise ValueError("Order must have at least one item")
        return v


class OrderStatusUpdate(BaseModel):
    """Update order status request"""
    new_status: OrderStatusEnum = Field(..., description="New order status")
    notes: Optional[str] = None


class OrderResponse(OrderBase):
    """Order response with full details"""
    id: int
    shop_id: int
    order_number: str
    order_date: datetime

    subtotal: Decimal
    discount_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal

    order_status: OrderStatusEnum
    payment_status: str = "pending"
    payment_method: Optional[str] = None
    payment_date: Optional[datetime] = None

    items: List[OrderItemResponse] = []

    is_credit_sale: bool = False
    credit_duration_days: Optional[int] = None

    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderDetailResponse(OrderResponse):
    """Detailed order response for single order retrieval"""
    item_count: int = 0

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    """List orders response with pagination"""
    orders: List[OrderResponse]
    total: int
    skip: int
    limit: int


class OrderSummary(BaseModel):
    """Order summary for dashboard"""
    id: int
    order_number: str
    order_date: datetime
    customer_name: str
    order_status: OrderStatusEnum
    total_amount: Decimal
    item_count: int


class OrderDashboard(BaseModel):
    """Order dashboard statistics"""
    total_orders: int
    placed_orders: int
    accepted_orders: int
    packed_orders: int
    out_for_delivery_orders: int
    delivered_orders: int
    cancelled_orders: int
    total_revenue: Decimal
    average_order_value: Decimal
    recent_orders: List[OrderSummary]
