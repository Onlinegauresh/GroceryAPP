"""Pydantic schemas for accounting operations"""
from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import List, Optional


# ===== LEDGER ENTRY SCHEMAS =====
class LedgerEntryBase(BaseModel):
    """Base schema for ledger entry"""
    description: str = Field(..., min_length=1, max_length=500)
    debit_account: str
    debit_amount: Decimal
    credit_account: str
    credit_amount: Decimal
    notes: Optional[str] = None


class LedgerEntryCreate(LedgerEntryBase):
    """Schema for creating ledger entry"""
    pass


class LedgerEntryResponse(LedgerEntryBase):
    """Schema for ledger entry response"""
    id: int
    shop_id: int
    entry_date: datetime
    entry_number: Optional[str]
    reference_type: Optional[str]
    reference_id: Optional[int]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===== CASH BOOK SCHEMAS =====
class CashBookBase(BaseModel):
    """Base schema for cash book"""
    amount: Decimal = Field(..., gt=0)
    entry_type: str = Field(..., pattern="^(IN|OUT)$")
    description: Optional[str] = None


class CashBookResponse(CashBookBase):
    """Schema for cash book response"""
    id: int
    shop_id: int
    order_id: Optional[int]
    reference_number: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===== BANK BOOK SCHEMAS =====
class BankBookBase(BaseModel):
    """Base schema for bank book"""
    amount: Decimal = Field(..., gt=0)
    entry_type: str = Field(..., pattern="^(IN|OUT)$")
    description: Optional[str] = None
    bank_account: Optional[str] = None
    cheque_number: Optional[str] = None


class BankBookResponse(BankBookBase):
    """Schema for bank book response"""
    id: int
    shop_id: int
    order_id: Optional[int]
    reference_number: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===== KHATA ACCOUNT SCHEMAS =====
class KhataAccountBase(BaseModel):
    """Base schema for khata account"""
    customer_id: int
    credit_limit: Decimal = Field(default=10000, ge=0)


class KhataAccountResponse(KhataAccountBase):
    """Schema for khata account response"""
    id: int
    shop_id: int
    balance: Decimal
    total_credit_given: Decimal
    total_credit_received: Decimal
    last_transaction_date: Optional[datetime]
    last_updated: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ===== GST RECORD SCHEMAS =====
class GSTRecordBase(BaseModel):
    """Base schema for GST record"""
    taxable_amount: Decimal
    gst_rate: Decimal
    gst_amount: Decimal


class GSTRecordResponse(GSTRecordBase):
    """Schema for GST record response"""
    id: int
    shop_id: int
    order_id: int
    cgst_amount: Decimal
    sgst_amount: Decimal
    igst_amount: Decimal
    invoice_number: Optional[str]
    created_by: int
    created_at: datetime

    class Config:
        from_attributes = True


# ===== REPORT SCHEMAS =====
class DailySalesReportItem(BaseModel):
    """Item in daily sales report"""
    order_id: int
    order_number: str
    customer_name: str
    subtotal: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    payment_method: str
    is_credit_sale: bool
    created_at: datetime


class DailySalesReport(BaseModel):
    """Daily sales report"""
    shop_id: int
    report_date: str  # YYYY-MM-DD format
    total_orders: int
    total_sales: Decimal
    total_tax: Decimal
    cash_sales: Decimal
    credit_sales: Decimal
    items: List[DailySalesReportItem]


class ProfitLossReport(BaseModel):
    """Profit & Loss statement"""
    shop_id: int
    report_period: str  # e.g., "2024-01" for January 2024

    # Revenue
    gross_sales: Decimal
    discounts: Decimal
    net_sales: Decimal

    # Expenses (simplified - cost of goods sold)
    cost_of_goods_sold: Decimal

    # Results
    gross_profit: Decimal
    gross_profit_margin: Decimal  # percentage

    # Tax
    total_tax_collected: Decimal
    total_tax_payable: Decimal


class CashBookSummary(BaseModel):
    """Cash book summary"""
    shop_id: int
    period: str  # YYYY-MM-DD to YYYY-MM-DD

    opening_balance: Decimal
    cash_in: Decimal
    cash_out: Decimal
    closing_balance: Decimal

    transactions: List[CashBookResponse]


class KhataStatement(BaseModel):
    """Customer khata statement"""
    customer_id: int
    customer_name: str
    shop_id: int

    balance: Decimal
    credit_limit: Decimal
    available_credit: Decimal

    total_credit_given: Decimal
    total_credit_received: Decimal
    last_transaction_date: Optional[datetime]


# ===== ACCOUNTING ENTRY (INTERNAL) =====
class AccountingEntry(BaseModel):
    """Internal accounting entry for double-entry bookkeeping"""
    shop_id: int
    entry_date: datetime
    description: str
    reference_type: str  # 'order', 'purchase', etc.
    reference_id: int

    debit_account: str
    debit_amount: Decimal
    credit_account: str
    credit_amount: Decimal

    notes: Optional[str] = None


class ChartOfAccountsResponse(BaseModel):
    """Chart of accounts response"""
    id: int
    account_code: str
    account_name: str
    account_type: str
    description: Optional[str]

    class Config:
        from_attributes = True
