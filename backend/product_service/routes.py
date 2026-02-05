"""Product management routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime

from shared.database import get_db
from shared.models import Product, User, RoleEnum
from shared.security import verify_token
from shared.exceptions import UnauthorizedException, NotFoundException, ConflictException

router = APIRouter(prefix="/api/v1/products", tags=["products"])


# ===== SCHEMAS =====
class ProductCreate(BaseModel):
    """Create product request"""
    name: str
    sku: str
    category: str
    subcategory: Optional[str] = None
    unit: str
    cost_price: Decimal
    mrp: Decimal
    selling_price: Decimal
    gst_rate: Decimal = 0
    hsn_code: Optional[str] = None
    min_stock_level: int = 10
    reorder_quantity: int = 0
    is_perishable: bool = False


class ProductUpdate(BaseModel):
    """Update product request"""
    name: Optional[str] = None
    selling_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    is_active: Optional[bool] = None
    min_stock_level: Optional[int] = None
    mrp: Optional[Decimal] = None


class ProductResponse(BaseModel):
    """Product response"""
    id: int
    name: str
    sku: str
    category: str
    subcategory: Optional[str]
    selling_price: Decimal
    mrp: Decimal
    cost_price: Decimal
    current_stock: int
    is_active: bool
    gst_rate: Decimal
    unit: str

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


def check_owner_access(token: str, db: Session, shop_id: int):
    """Check if user is shop owner"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    if user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise UnauthorizedException("Only shop owner can perform this action")

    return user, token_data


# ===== ENDPOINTS =====

@router.get("", response_model=List[ProductResponse])
def list_products(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100)
):
    """
    List products for a shop.

    Filters:
    - **category**: Filter by product category
    - **is_active**: Show active/inactive products
    """
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    query = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.deleted_at == None
    )

    if category:
        query = query.filter(Product.category == category)

    if is_active is not None:
        query = query.filter(Product.is_active == is_active)

    # Pagination
    offset = (page - 1) * limit
    products = query.order_by(Product.name).offset(offset).limit(limit).all()

    return products


@router.post("", response_model=ProductResponse, status_code=201)
def create_product(
    shop_id: int,
    request: ProductCreate,
    token: str,
    db: Session = Depends(get_db)
):
    """
    Create new product (owner only).

    Product must include:
    - Valid SKU (unique within shop)
    - Cost price ≤ Selling price
    - Valid GST rate (0, 5, 12, 18, 28)
    """
    user, token_data = check_owner_access(token, db, shop_id)

    # Check SKU uniqueness
    existing = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.sku == request.sku,
        Product.deleted_at == None
    ).first()

    if existing:
        raise ConflictException(
            f"SKU '{request.sku}' already exists in this shop")

    # Validate prices
    if request.cost_price > request.selling_price:
        raise HTTPException(
            status_code=400, detail="Cost price cannot exceed selling price")

    # Validate GST
    valid_gst = [Decimal(x) for x in [0, 5, 12, 18, 28]]
    if request.gst_rate not in valid_gst:
        raise HTTPException(
            status_code=400, detail="Invalid GST rate. Must be 0, 5, 12, 18, or 28")

    # Create product
    product = Product(
        shop_id=shop_id,
        name=request.name,
        sku=request.sku,
        category=request.category,
        subcategory=request.subcategory,
        unit=request.unit,
        cost_price=request.cost_price,
        mrp=request.mrp,
        selling_price=request.selling_price,
        gst_rate=request.gst_rate,
        hsn_code=request.hsn_code,
        min_stock_level=request.min_stock_level,
        reorder_quantity=request.reorder_quantity,
        is_perishable=request.is_perishable
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    return product


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    shop_id: int,
    product_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get product details"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id,
        Product.deleted_at == None
    ).first()

    if not product:
        raise NotFoundException("Product not found")

    return product


@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    shop_id: int,
    product_id: int,
    request: ProductUpdate,
    token: str,
    db: Session = Depends(get_db)
):
    """Update product (owner only)"""
    user, token_data = check_owner_access(token, db, shop_id)

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id,
        Product.deleted_at == None
    ).first()

    if not product:
        raise NotFoundException("Product not found")

    # Update fields
    if request.name:
        product.name = request.name
    if request.selling_price:
        product.selling_price = request.selling_price
    if request.cost_price:
        product.cost_price = request.cost_price
    if request.mrp:
        product.mrp = request.mrp
    if request.is_active is not None:
        product.is_active = request.is_active
    if request.min_stock_level:
        product.min_stock_level = request.min_stock_level

    product.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(product)

    return product


@router.delete("/{product_id}")
def delete_product(
    shop_id: int,
    product_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Soft delete product (owner only)"""
    user, token_data = check_owner_access(token, db, shop_id)

    product = db.query(Product).filter(
        Product.id == product_id,
        Product.shop_id == shop_id,
        Product.deleted_at == None
    ).first()

    if not product:
        raise NotFoundException("Product not found")

    # Soft delete
    product.deleted_at = datetime.utcnow()
    db.commit()

    return {"message": "Product deleted successfully", "product_id": product_id}


@router.get("/search/by-category", response_model=List[ProductResponse])
def search_by_category(
    shop_id: int,
    category: str,
    token: str,
    db: Session = Depends(get_db),
    limit: int = Query(50, le=100)
):
    """Search products by category"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    products = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.category == category,
        Product.deleted_at == None,
        Product.is_active == True
    ).limit(limit).all()

    return products


@router.get("/search/low-stock", response_model=List[ProductResponse])
def get_low_stock_products(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db)
):
    """Get products with stock below minimum level"""
    user, token_data = check_auth(token, db)

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    products = db.query(Product).filter(
        Product.shop_id == shop_id,
        Product.current_stock < Product.min_stock_level,
        Product.deleted_at == None,
        Product.is_active == True
    ).order_by(Product.current_stock).all()

    return products
