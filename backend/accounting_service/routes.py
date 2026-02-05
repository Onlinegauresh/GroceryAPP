"""Accounting and financial reporting routes"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from decimal import Decimal

from shared.database import get_db
from shared.models import LedgerEntry, Order, OrderItem, User, RoleEnum, ChartOfAccounts
from shared.security import verify_token
from shared.exceptions import UnauthorizedException, NotFoundException, ValidationException

router = APIRouter(prefix="/api/v1/accounting", tags=["accounting"])


# ===== SCHEMAS =====
class LedgerEntryResponse(BaseModel):
    """Ledger entry response"""
    id: int
    entry_date: datetime
    description: str
    debit_account: str
    debit_amount: Decimal
    credit_account: str
    credit_amount: Decimal
    reference_type: Optional[str]
    reference_id: Optional[int]

    class Config:
        from_attributes = True


class ProfitLossResponse(BaseModel):
    """P&L statement response"""
    period_start: datetime
    period_end: datetime

    total_revenue: Decimal
    total_cogs: Decimal  # Cost of goods sold
    gross_profit: Decimal

    total_expenses: Decimal
    net_profit: Decimal

    profit_margin: Decimal  # As percentage


class SalesLedgerResponse(BaseModel):
    """Sales ledger response"""
    date: datetime
    order_number: str
    customer_id: Optional[int]
    total_amount: Decimal
    tax_amount: Decimal


class BalanceSheetResponse(BaseModel):
    """Balance sheet response"""
    date: datetime

    # Assets
    cash: Decimal
    accounts_receivable: Decimal
    inventory: Decimal
    fixed_assets: Decimal
    total_assets: Decimal

    # Liabilities
    accounts_payable: Decimal
    loans_payable: Decimal
    total_liabilities: Decimal

    # Equity
    capital: Decimal
    retained_earnings: Decimal
    total_equity: Decimal


# ===== HELPER FUNCTIONS =====
def check_owner_access(token: str, db: Session, shop_id: int):
    """Check if user is shop owner/admin"""
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

    if token_data.shop_id != shop_id:
        raise UnauthorizedException("Cannot access other shops")

    if user.role not in [RoleEnum.OWNER, RoleEnum.ADMIN]:
        raise UnauthorizedException(
            "Only shop owner can access financial reports")

    return user, token_data


# ===== ENDPOINTS =====

@router.get("/ledger", response_model=list)
def get_ledger(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    account: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000)
):
    """
    Get ledger entries for a date range.

    Optionally filter by account code.
    """
    user, token_data = check_owner_access(token, db, shop_id)

    query = db.query(LedgerEntry).filter(LedgerEntry.shop_id == shop_id)

    if account:
        query = query.filter(
            (LedgerEntry.debit_account == account) |
            (LedgerEntry.credit_account == account)
        )

    if start_date:
        query = query.filter(LedgerEntry.entry_date >= start_date)

    if end_date:
        query = query.filter(LedgerEntry.entry_date <= end_date)

    entries = query.order_by(LedgerEntry.entry_date.desc()).limit(limit).all()

    return [
        {
            "id": e.id,
            "entry_date": e.entry_date,
            "description": e.description,
            "debit_account": e.debit_account,
            "debit_amount": e.debit_amount,
            "credit_account": e.credit_account,
            "credit_amount": e.credit_amount,
            "reference_type": e.reference_type,
            "reference_id": e.reference_id
        }
        for e in entries
    ]


@router.get("/profit-loss")
def get_profit_loss(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    period_days: int = Query(30, ge=1, le=365)
):
    """
    Generate Profit & Loss statement for last N days.

    Calculation:
    - Revenue = SUM(sales ledger debit amounts for account 4001)
    - COGS = SUM(expenses for account 5001)
    - Gross Profit = Revenue - COGS
    - Total Expenses = SUM(all other expenses)
    - Net Profit = Gross Profit - Total Expenses
    """
    user, token_data = check_owner_access(token, db, shop_id)

    period_start = datetime.utcnow() - timedelta(days=period_days)
    period_end = datetime.utcnow()

    # Get all orders in period (sales)
    orders = db.query(Order).filter(
        Order.shop_id == shop_id,
        Order.order_date >= period_start,
        Order.order_date <= period_end
    ).all()

    total_revenue = sum(order.total_amount for order in orders)

    # TODO: Calculate COGS from purchase orders
    # For now, estimate based on product cost
    total_cogs = Decimal(0)
    for order in orders:
        for item in order.items:
            cost = item.quantity * Decimal(item.product_id)  # Placeholder
            total_cogs += cost

    gross_profit = total_revenue - total_cogs

    # Get expenses from ledger
    expenses = db.query(func.sum(LedgerEntry.debit_amount)).filter(
        LedgerEntry.shop_id == shop_id,
        LedgerEntry.entry_date >= period_start,
        LedgerEntry.entry_date <= period_end,
        LedgerEntry.debit_account.in_(
            ["5001", "5002", "5003", "5004", "5005"])  # Expense accounts
    ).scalar() or Decimal(0)

    net_profit = gross_profit - expenses
    profit_margin = (net_profit / total_revenue *
                     100) if total_revenue > 0 else Decimal(0)

    return {
        "period_start": period_start,
        "period_end": period_end,
        "period_days": period_days,
        "total_revenue": total_revenue,
        "total_cogs": total_cogs,
        "gross_profit": gross_profit,
        "total_expenses": expenses,
        "net_profit": net_profit,
        "profit_margin_percent": profit_margin,
        "order_count": len(orders)
    }


@router.get("/sales-ledger")
def get_sales_ledger(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=1000)
):
    """
    Get sales ledger (all customer sales).

    Shows: Order number, date, customer, amount, tax
    """
    user, token_data = check_owner_access(token, db, shop_id)

    query = db.query(Order).filter(Order.shop_id == shop_id)

    if start_date:
        query = query.filter(Order.order_date >= start_date)

    if end_date:
        query = query.filter(Order.order_date <= end_date)

    orders = query.order_by(Order.order_date.desc()).limit(limit).all()

    return [
        {
            "date": order.order_date,
            "order_number": order.order_number,
            "customer_id": order.customer_id,
            "subtotal": order.subtotal,
            "tax_amount": order.tax_amount,
            "total_amount": order.total_amount,
            "payment_status": order.payment_status.value
        }
        for order in orders
    ]


@router.get("/account-balance/{account_code}")
def get_account_balance(
    shop_id: int,
    account_code: str,
    token: str,
    db: Session = Depends(get_db),
    as_of_date: Optional[datetime] = Query(None)
):
    """
    Get balance of specific account as of a date.

    Balance = SUM(debit) - SUM(credit)
    """
    user, token_data = check_owner_access(token, db, shop_id)

    if not as_of_date:
        as_of_date = datetime.utcnow()

    # Sum debits for this account
    debits = db.query(func.sum(LedgerEntry.debit_amount)).filter(
        LedgerEntry.shop_id == shop_id,
        LedgerEntry.debit_account == account_code,
        LedgerEntry.entry_date <= as_of_date
    ).scalar() or Decimal(0)

    # Sum credits for this account
    credits = db.query(func.sum(LedgerEntry.credit_amount)).filter(
        LedgerEntry.shop_id == shop_id,
        LedgerEntry.credit_account == account_code,
        LedgerEntry.entry_date <= as_of_date
    ).scalar() or Decimal(0)

    balance = debits - credits

    # Get account info
    account = db.query(ChartOfAccounts).filter(
        ChartOfAccounts.account_code == account_code
    ).first()

    return {
        "account_code": account_code,
        "account_name": account.account_name if account else "Unknown",
        "account_type": account.account_type if account else None,
        "debit_total": debits,
        "credit_total": credits,
        "balance": balance,
        "as_of_date": as_of_date
    }


@router.get("/monthly-summary")
def get_monthly_summary(
    shop_id: int,
    token: str,
    db: Session = Depends(get_db),
    year: int = Query(2026),
    month: int = Query(2, ge=1, le=12)
):
    """
    Get monthly financial summary.

    Shows: Revenue, expenses, profit, transaction count
    """
    user, token_data = check_owner_access(token, db, shop_id)

    # Date range for month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    # Get orders
    orders = db.query(Order).filter(
        Order.shop_id == shop_id,
        Order.order_date >= start_date,
        Order.order_date < end_date
    ).all()

    total_revenue = sum(order.total_amount for order in orders)
    total_tax = sum(order.tax_amount for order in orders)
    order_count = len(orders)

    # Get unique customers
    customer_count = len(set(o.customer_id for o in orders if o.customer_id))

    return {
        "month": month,
        "year": year,
        "total_revenue": total_revenue,
        "total_tax": total_tax,
        "order_count": order_count,
        "unique_customers": customer_count,
        "avg_order_value": total_revenue / order_count if order_count > 0 else Decimal(0)
    }


@router.get("/chart-of-accounts")
def get_chart_of_accounts(
    token: str,
    db: Session = Depends(get_db),
    account_type: Optional[str] = Query(None)
):
    """Get chart of accounts (standard for all shops)"""
    try:
        token_data = verify_token(token)
    except Exception as e:
        raise UnauthorizedException(str(e))

    query = db.query(ChartOfAccounts)

    if account_type:
        query = query.filter(ChartOfAccounts.account_type == account_type)

    accounts = query.all()

    return [
        {
            "account_code": a.account_code,
            "account_name": a.account_name,
            "account_type": a.account_type,
            "description": a.description
        }
        for a in accounts
    ]
