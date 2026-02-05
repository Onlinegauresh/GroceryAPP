"""Pydantic schemas for shop management"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class ShopBase(BaseModel):
    """Base shop schema"""
    name: str = Field(..., min_length=1, max_length=255)
    address: str = Field(..., min_length=5)
    city: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    pincode: str = Field(..., pattern=r"^\d{6}$")
    phone: str = Field(..., pattern=r"^\+?1?\d{9,15}$")
    email: EmailStr
    delivery_radius_km: int = Field(default=5, ge=1, le=100)
    shop_category: Optional[str] = Field(default=None, max_length=50)
    gst_number: Optional[str] = Field(default=None, pattern=r"^[0-9A-Z]{15}$")
    pan_number: Optional[str] = Field(
        default=None, pattern=r"^[A-Z]{5}[0-9]{4}[A-Z]$")


class ShopCreate(ShopBase):
    """Schema for creating a shop"""
    pass


class ShopUpdate(BaseModel):
    """Schema for updating shop (partial)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address: Optional[str] = Field(None, min_length=5)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    state: Optional[str] = Field(None, min_length=1, max_length=100)
    pincode: Optional[str] = Field(None, pattern=r"^\d{6}$")
    phone: Optional[str] = Field(None, pattern=r"^\+?1?\d{9,15}$")
    delivery_radius_km: Optional[int] = Field(None, ge=1, le=100)
    shop_category: Optional[str] = Field(None, max_length=50)


class ShopResponse(ShopBase):
    """Schema for shop response"""
    id: int
    is_active: bool
    subscription_plan: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ShopDetailResponse(ShopResponse):
    """Extended shop response with stats"""
    product_count: int = 0
    active_products: int = 0
