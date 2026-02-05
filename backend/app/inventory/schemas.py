"""Pydantic schemas for inventory management"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


class InventoryBase(BaseModel):
    """Base inventory schema"""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., ge=0)
    min_quantity: int = Field(default=10, ge=1)
    cost_price: Decimal = Field(..., gt=0)
    selling_price: Decimal = Field(..., gt=0)
    batch_no: Optional[str] = Field(None, max_length=100)
    expiry_date: Optional[datetime] = None


class InventoryCreate(InventoryBase):
    """Schema for adding product to inventory"""
    pass


class InventoryUpdateStock(BaseModel):
    """Schema for updating stock quantity"""
    product_id: int = Field(..., gt=0)
    quantity_change: int = Field(...,
                                 description="Positive for inbound, negative for outbound")
    batch_no: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class InventoryResponse(InventoryBase):
    """Schema for inventory response"""
    id: int
    shop_id: int
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InventoryDetailResponse(InventoryResponse):
    """Extended inventory response with product details"""
    product_name: str = ""
    product_sku: str = ""
    stock_status: str = ""  # "in_stock", "low_stock", "out_of_stock"


class ShopInventoryResponse(BaseModel):
    """Shop inventory summary"""
    shop_id: int
    total_products: int
    in_stock: int
    low_stock: int
    out_of_stock: int
    total_inventory_value: Decimal = Decimal("0")


class LowStockAlert(BaseModel):
    """Low stock alert item"""
    product_id: int
    product_name: str
    product_sku: str
    current_quantity: int
    min_quantity: int
    shortage: int = Field(description="How many units below minimum")
    last_updated: datetime


class LowStockAlertResponse(BaseModel):
    """Low stock alerts list"""
    shop_id: int
    alert_count: int
    alerts: List[LowStockAlert]
