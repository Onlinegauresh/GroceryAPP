"""Accounting API routes - FastAPI endpoints for accounting reports"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import Optional

from shared.database import get_db
from app.auth.security import get_current_user
from shared.models import User, RoleEnum
from app.accounting.service import AccountingService
from app.accounting.schemas import (
    DailySalesReport, ProfitLossReport, CashBookSummary, KhataStatement
)

router = APIRouter(prefix="/api/v1/accounting", tags=["Accounting"])


# ===== RBAC DEPENDENCIES =====

def require_accounting_read_access(current_user: User = Depends(get_current_user)):
    """
    Require read access to accounting reports.

    RBAC Rules (PHASE E):
    - OWNER/ADMIN: Full access to shop reports
    - STAFF: Read-only access to shop reports
    - CUSTOMER: Can only view own khata
    """
    if current_user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN, RoleEnum.STAFF]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions for accounting reports"
        )
    return current_user


def require_accounting_full_access(current_user: User = Depends(get_current_user)):
    """Require full access (owner/admin only)"""
    if current_user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can access accounting data"
        )
    return current_user


# ===== ENDPOINT 1: DAILY SALES REPORT =====

@router.get(
    "/daily-sales/{shop_id}",
    response_model=DailySalesReport,
    summary="Daily Sales Report",
    description="""
    Get daily sales report for a shop.
    
    PHASE D - Endpoint 1
    
    RBAC:
    - OWNER/ADMIN: Full access
    - STAFF: Own shop only
    - CUSTOMER: Forbidden
    
    Returns:
    - Total sales, tax, and transaction count
    - Breakdown by cash vs credit
    - Item-level sales details
    """
)
async def get_daily_sales_report(
    shop_id: int,
    report_date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$",
                             description="YYYY-MM-DD format"),
    current_user: User = Depends(require_accounting_read_access),
    db: Session = Depends(get_db)
):
    """
    Get daily sales report.

    **RBAC Rules:**
    - ADMIN: Access any shop
    - OWNER: Access own shop only
    - STAFF: Read-only access to own shop
    - CUSTOMER: Forbidden

    **Parameters:**
    - shop_id: Target shop ID
    - report_date: Date in YYYY-MM-DD format

    **Returns:**
    Daily sales with all transactions and tax details
    """

    # RBAC: Verify access
    if current_user.role == RoleEnum.ADMIN:
        pass  # Admin can access any shop
    elif current_user.role in [RoleEnum.OWNER, RoleEnum.STAFF]:
        if current_user.shop_id != shop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You can only access reports for your shop (ID: {current_user.shop_id})"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Validate shop exists
    from shared.models import Shop
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shop {shop_id} not found"
        )

    # Generate report
    try:
        report = AccountingService.get_daily_sales_report(
            shop_id, report_date, db)
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format: {str(e)}"
        )


# ===== ENDPOINT 2: PROFIT & LOSS REPORT =====

@router.get(
    "/profit-loss/{shop_id}",
    response_model=ProfitLossReport,
    summary="Profit & Loss Statement",
    description="""
    Get Profit & Loss statement for a shop.
    
    PHASE D - Endpoint 2
    
    RBAC:
    - OWNER/ADMIN: Full access
    - STAFF: Own shop only
    - CUSTOMER: Forbidden
    
    Shows:
    - Gross sales vs net sales
    - Cost of goods sold
    - Gross profit and margin
    - Tax collected vs payable
    """
)
async def get_profit_loss_report(
    shop_id: int,
    period: str = Query(..., regex=r"^\d{4}-\d{2}$",
                        description="YYYY-MM format (e.g., 2024-01)"),
    current_user: User = Depends(require_accounting_read_access),
    db: Session = Depends(get_db)
):
    """
    Get Profit & Loss statement.

    **RBAC Rules:**
    - ADMIN: Access any shop
    - OWNER: Access own shop only
    - STAFF: Read-only for own shop
    - CUSTOMER: Forbidden

    **Parameters:**
    - shop_id: Target shop ID
    - period: Month in YYYY-MM format (e.g., "2024-01")

    **Returns:**
    P&L statement with revenue, COGS, and profit details
    """

    # RBAC: Verify access
    if current_user.role == RoleEnum.ADMIN:
        pass
    elif current_user.role in [RoleEnum.OWNER, RoleEnum.STAFF]:
        if current_user.shop_id != shop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You can only access reports for your shop (ID: {current_user.shop_id})"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Validate shop exists
    from shared.models import Shop
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shop {shop_id} not found"
        )

    # Generate report
    try:
        report = AccountingService.get_profit_loss_report(shop_id, period, db)
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid period format: {str(e)}"
        )


# ===== ENDPOINT 3: CASH BOOK =====

@router.get(
    "/cash-book/{shop_id}",
    response_model=CashBookSummary,
    summary="Cash Book",
    description="""
    Get cash book for a date range.
    
    PHASE D - Endpoint 3
    
    RBAC:
    - OWNER/ADMIN: Full access
    - STAFF: Own shop only
    - CUSTOMER: Forbidden
    
    Shows:
    - Opening balance
    - All cash IN and OUT transactions
    - Closing balance
    """
)
async def get_cash_book(
    shop_id: int,
    from_date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$",
                           description="YYYY-MM-DD format"),
    to_date: str = Query(..., regex=r"^\d{4}-\d{2}-\d{2}$",
                         description="YYYY-MM-DD format"),
    current_user: User = Depends(require_accounting_read_access),
    db: Session = Depends(get_db)
):
    """
    Get cash book for a date range.

    **RBAC Rules:**
    - ADMIN: Access any shop
    - OWNER: Access own shop only
    - STAFF: Read-only for own shop
    - CUSTOMER: Forbidden

    **Parameters:**
    - shop_id: Target shop ID
    - from_date: Start date in YYYY-MM-DD format
    - to_date: End date in YYYY-MM-DD format

    **Returns:**
    Cash book with opening balance, transactions, and closing balance
    """

    # RBAC: Verify access
    if current_user.role == RoleEnum.ADMIN:
        pass
    elif current_user.role in [RoleEnum.OWNER, RoleEnum.STAFF]:
        if current_user.shop_id != shop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You can only access reports for your shop (ID: {current_user.shop_id})"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Validate shop exists
    from shared.models import Shop
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shop {shop_id} not found"
        )

    # Validate dates
    try:
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        if from_dt > to_dt:
            raise ValueError("from_date must be before to_date")
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid date format or range: {str(e)}"
        )

    # Generate report
    cash_book = AccountingService.get_cash_book(
        shop_id, from_date, to_date, db)
    return cash_book


# ===== ENDPOINT 4: CUSTOMER KHATA =====

@router.get(
    "/khata/{customer_id}",
    response_model=KhataStatement,
    summary="Customer Khata Statement",
    description="""
    Get customer khata (credit account) statement.
    
    PHASE D - Endpoint 4
    
    RBAC:
    - CUSTOMER: View only own khata
    - OWNER/ADMIN: View any customer's khata for their shop
    - STAFF: View any customer's khata for own shop
    
    Shows:
    - Current balance
    - Credit limit and available credit
    - Total credit given/received
    - Last transaction date
    """
)
async def get_khata_statement(
    customer_id: int,
    shop_id: Optional[int] = Query(
        None, description="Shop ID (required for non-customers)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get customer khata statement.

    **RBAC Rules:**
    - CUSTOMER: View only own khata (use own ID, shop_id optional)
    - OWNER: View any customer's khata for own shop
    - ADMIN: View any customer's khata for any shop
    - STAFF: View any customer's khata for own shop

    **Parameters:**
    - customer_id: Target customer ID
    - shop_id: Shop ID (required if not a customer viewing own khata)

    **Returns:**
    Khata statement with balance, credit limit, and transaction history
    """

    from shared.models import Shop

    # RBAC Logic
    if current_user.role == RoleEnum.CUSTOMER:
        # Customers can only view their own khata
        if current_user.id != customer_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Customers can only view their own khata"
            )
        shop_id = current_user.shop_id

    elif current_user.role in [RoleEnum.OWNER, RoleEnum.STAFF]:
        # Need shop_id for staff/owner
        if not shop_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="shop_id is required for staff/owner"
            )
        # Can only access own shop
        if current_user.shop_id != shop_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You can only access khata for your shop (ID: {current_user.shop_id})"
            )

    elif current_user.role == RoleEnum.ADMIN:
        # Admin needs shop_id
        if not shop_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="shop_id is required"
            )

    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions"
        )

    # Validate shop exists
    shop = db.query(Shop).filter(Shop.id == shop_id).first()
    if not shop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shop {shop_id} not found"
        )

    # Validate customer exists
    customer = db.query(User).filter(User.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer {customer_id} not found"
        )

    # Generate statement
    statement = AccountingService.get_khata_statement(shop_id, customer_id, db)
    return statement


# ===== HEALTH CHECK =====

@router.get(
    "/health",
    summary="Accounting Module Health Check",
    tags=["Health"]
)
async def accounting_health():
    """Health check endpoint for accounting module"""
    return {
        "status": "healthy",
        "module": "accounting",
        "version": "1.0.0",
        "description": "Automatic accounting system with ledger, cash book, and GST tracking"
    }
