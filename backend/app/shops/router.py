"""Shop management API routes"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.models import User, RoleEnum
from app.auth.security import get_current_user
from app.shops.schemas import ShopCreate, ShopUpdate, ShopResponse, ShopDetailResponse
from app.shops.service import ShopService

router = APIRouter(prefix="/api/v1/shops", tags=["shops"])


def require_shop_owner_or_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to verify user is shop owner or admin"""
    if current_user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only shop owners or admins can access this resource"
        )
    return current_user


@router.post(
    "",
    response_model=ShopResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new shop",
    description="Create a new shop. Only SHOP_OWNER and ADMIN roles can create shops."
)
def create_shop(
    shop_data: ShopCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner_or_admin)
):
    """
    Create a new shop.

    **Business Rules:**
    - Only SHOP_OWNER or ADMIN can create shops
    - Email and GST number must be unique
    - Current user becomes the shop owner
    """
    shop = ShopService.create_shop(db, shop_data, current_user.id)
    return shop


@router.get(
    "/{shop_id}",
    response_model=ShopDetailResponse,
    summary="Get shop details",
    description="Get details of a specific shop with inventory statistics."
)
def get_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get shop details.

    **Access:**
    - Shop owner can view their own shop
    - STAFF can view shops they work for
    - ADMIN can view any shop
    - CUSTOMER cannot access
    """
    shop = ShopService.get_shop(db, shop_id)

    # Permission check
    is_admin = current_user.role == RoleEnum.ADMIN
    is_owner = current_user.role == RoleEnum.OWNER and current_user.shop_id == shop_id
    is_staff = current_user.role == RoleEnum.STAFF and current_user.shop_id == shop_id

    if not (is_admin or is_owner or is_staff):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this shop"
        )

    # Get inventory stats
    stats = ShopService.get_shop_inventory_count(db, shop_id)

    response = ShopDetailResponse.from_attributes(**shop.__dict__)
    response.product_count = stats["total_products"]
    response.active_products = stats["total_products"] - \
        stats["low_stock_count"]

    return response


@router.get(
    "",
    summary="List all shops",
    description="List all active shops. Only ADMIN can use this endpoint."
)
def list_shops(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all shops.

    **Access:**
    - Only ADMIN can list all shops
    """
    if current_user.role != RoleEnum.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can list all shops"
        )

    result = ShopService.list_shops(db, skip, limit)
    return {
        "data": [ShopResponse.from_attributes(**shop.__dict__) for shop in result["shops"]],
        "total": result["total"],
        "skip": result["skip"],
        "limit": result["limit"]
    }


@router.put(
    "/{shop_id}",
    response_model=ShopResponse,
    summary="Update shop",
    description="Update shop details. Owner can update their own shop, admin can update any."
)
def update_shop(
    shop_id: int,
    shop_data: ShopUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner_or_admin)
):
    """
    Update shop details.

    **Business Rules:**
    - Shop owner can only update their own shop
    - ADMIN can update any shop
    - Fields with null values are not updated
    """
    shop = ShopService.update_shop(db, shop_id, shop_data, current_user.id)
    return shop


@router.patch(
    "/{shop_id}/deactivate",
    response_model=ShopResponse,
    summary="Deactivate shop",
    description="Deactivate a shop. Owner can deactivate their own shop, admin can deactivate any."
)
def deactivate_shop(
    shop_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_shop_owner_or_admin)
):
    """
    Deactivate a shop.

    **Business Rules:**
    - Shop owner can only deactivate their own shop
    - ADMIN can deactivate any shop
    - Deactivated shops cannot be reactivated via API (use database directly)
    """
    shop = ShopService.deactivate_shop(db, shop_id, current_user.id)
    return shop
