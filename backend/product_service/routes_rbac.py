"""Product management routes with RBAC"""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal

from shared.database import get_db
from app.auth.security import get_current_user, require_role
from shared.models import User, Product

router = APIRouter(
    prefix="/api/v1/products",
    tags=["products"]
)


# ===== SCHEMAS =====
class ProductCreate(BaseModel):
    """Schema for creating a product"""
    name: str = Field(..., min_length=1, max_length=255)
    sku: str = Field(..., min_length=1, max_length=100)
    category: str = Field(..., min_length=1, max_length=100)
    subcategory: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    unit: str = Field(..., min_length=1, max_length=50)
    cost_price: Decimal = Field(..., gt=0, decimal_places=2)
    selling_price: Decimal = Field(..., gt=0, decimal_places=2)
    mrp: Decimal = Field(..., gt=0, decimal_places=2)
    gst_rate: Decimal = Field(default=0, ge=0, le=100, decimal_places=2)
    hsn_code: Optional[str] = Field(None, max_length=20)
    current_stock: int = Field(default=0, ge=0)
    min_stock_level: int = Field(default=10, ge=0)
    reorder_quantity: int = Field(default=0, ge=0)
    is_perishable: bool = Field(default=False)


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    selling_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    cost_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    mrp: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    gst_rate: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    min_stock_level: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: int
    name: str
    sku: str
    category: str
    subcategory: Optional[str]
    description: Optional[str]
    unit: str
    cost_price: Decimal
    selling_price: Decimal
    mrp: Decimal
    gst_rate: Decimal
    current_stock: int
    min_stock_level: int
    is_perishable: bool
    is_active: bool
    created_by: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


# ===== ENDPOINTS =====

@router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List all products",
    description="Get all active products. Accessible to all authenticated users."
)
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> List[Product]:
    """
    List all products with pagination.

    **Query Parameters:**
    - skip: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 10, max: 100)
    - category: Filter by category (optional)
    """
    query = db.query(Product).filter(Product.is_active == True)

    if category:
        query = query.filter(Product.category == category)

    products = query.offset(skip).limit(limit).all()
    return products


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
    description="Get a specific product by ID. Accessible to all authenticated users."
)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
) -> Product:
    """
    Get a specific product by ID.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    return product


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product",
    description="Create a new product. Only OWNER and ADMIN roles can create products."
)
def create_product(
    product_create: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("owner", "admin"))
) -> Product:
    """
    Create a new product.

    **Required Role:** SHOP_OWNER or ADMIN

    **Request Body:**
    - name: Product name
    - sku: Unique SKU
    - category: Product category
    - selling_price: Selling price
    - cost_price: Cost price
    - mrp: Maximum retail price
    - unit: Unit of measure (e.g., kg, liter, piece)
    - gst_rate: GST rate (0-100)
    """
    # Check if SKU already exists
    existing = db.query(Product).filter(
        Product.sku == product_create.sku).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Product with this SKU already exists"
        )

    # Create product
    db_product = Product(
        **product_create.dict(),
        created_by=current_user.id
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)

    return db_product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a product",
    description="Update an existing product. Only OWNER and ADMIN roles can update products."
)
def update_product(
    product_id: int,
    product_update: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("owner", "admin"))
) -> Product:
    """
    Update an existing product.

    **Required Role:** SHOP_OWNER or ADMIN
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    # Update only provided fields
    update_data = product_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)

    return product


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
    description="Soft-delete a product (mark as inactive). Only OWNER and ADMIN roles can delete products."
)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("owner", "admin"))
) -> None:
    """
    Soft-delete a product by marking it as inactive.

    **Required Role:** SHOP_OWNER or ADMIN
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )

    product.is_active = False
    db.commit()


@router.get(
    "/category/{category}/low-stock",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="Get low stock products",
    description="Get products below minimum stock level in a category. Accessible to STAFF and ADMIN only."
)
def get_low_stock_products(
    category: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("staff", "shop_owner", "admin"))
) -> List[Product]:
    """
    Get products with stock below minimum level in a specific category.

    **Required Role:** STAFF, SHOP_OWNER, or ADMIN
    """
    products = db.query(Product).filter(
        Product.category == category,
        Product.current_stock < Product.min_stock_level,
        Product.is_active == True
    ).all()

    return products
