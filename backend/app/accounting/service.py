"""Accounting service - Business logic for accounting operations"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
import logging

from shared.models import (
    Order, OrderItem, Shop, User, Inventory, Product,
    LedgerEntry, CashBook, BankBook, KhataAccount, GSTRecord,
    OrderStatusEnum, RoleEnum
)
from app.accounting.schemas import (
    DailySalesReport, DailySalesReportItem, ProfitLossReport,
    CashBookSummary, CashBookResponse, KhataStatement
)

logger = logging.getLogger(__name__)


class AccountingService:
    """Service for accounting operations and automatic entry generation"""

    # ===== ACCOUNT NAMES (Tally-style) =====
    ACCOUNTS = {
        "Sales": "Sales",
        "Cash": "Cash",
        "Bank": "Bank",
        "Debtors": "Debtors (Credit Sales)",
        "CGST Payable": "CGST Payable",
        "SGST Payable": "SGST Payable",
        "IGST Payable": "IGST Payable",
        "Cost of Goods Sold": "Cost of Goods Sold",
        "Inventory": "Inventory",
        "Discount": "Discount Given",
    }

    @staticmethod
    def process_order_delivery(order: Order, db: Session, current_user: User) -> bool:
        """
        Process accounting entries when order status changes to DELIVERED.

        This is called ONCE per order when status → DELIVERED.
        Implements PHASE C logic.

        Entries created:
        1. Sales Ledger: Debit Cash/Debtors, Credit Sales
        2. GST Record: Tax tracking for compliance
        3. Cash/Khata: Payment method tracking

        Args:
            order: Order object being delivered
            db: Database session
            current_user: User performing the action

        Returns:
            True if successful, False if failed
        """
        try:
            # Check if accounting entries already exist for this order
            existing_entry = db.query(LedgerEntry).filter(
                and_(
                    LedgerEntry.shop_id == order.shop_id,
                    LedgerEntry.reference_type == "order",
                    LedgerEntry.reference_id == order.id
                )
            ).first()

            if existing_entry:
                logger.warning(
                    f"Accounting entry already exists for order {order.id}")
                return False

            # ===== ENTRY 1: SALES LEDGER =====
            # Debit: Cash/Debtors Account
            # Credit: Sales Account

            debit_account = "Cash" if not order.is_credit_sale else "Debtors"

            entry = LedgerEntry(
                shop_id=order.shop_id,
                entry_date=datetime.utcnow(),
                entry_number=f"ORD{order.id}{datetime.utcnow().strftime('%Y%m%d')}",
                description=f"Sales from order {order.order_number}",
                reference_type="order",
                reference_id=order.id,
                debit_account=debit_account,
                debit_amount=order.total_amount,
                credit_account="Sales",
                credit_amount=order.total_amount,
                notes=f"Customer: {order.customer_name}",
                created_by=current_user.id
            )
            db.add(entry)

            # ===== ENTRY 2: GST RECORD =====
            # Track GST for tax compliance and reports

            gst_record = GSTRecord(
                shop_id=order.shop_id,
                order_id=order.id,
                taxable_amount=order.subtotal,
                gst_rate=order.tax_amount / order.subtotal * 100 if order.subtotal > 0 else 0,
                gst_amount=order.tax_amount,
                # Simplified: assume equal CGST and SGST (not IGST for now)
                cgst_amount=order.tax_amount / 2,
                sgst_amount=order.tax_amount / 2,
                igst_amount=Decimal(0),
                invoice_number=order.order_number,
                created_by=current_user.id
            )
            db.add(gst_record)

            # ===== ENTRY 3: PAYMENT TRACKING =====

            if order.is_credit_sale:
                # Credit sale: Create khata entry
                AccountingService._update_khata_account(
                    order, db, current_user, is_credit=True
                )
            else:
                # Cash/COD sale: Record in cash book
                cash_entry = CashBook(
                    shop_id=order.shop_id,
                    order_id=order.id,
                    amount=order.total_amount,
                    entry_type="IN",
                    description=f"Cash received from {order.customer_name}",
                    reference_number=order.order_number,
                    created_by=current_user.id
                )
                db.add(cash_entry)

            # Commit all entries
            db.commit()
            logger.info(f"✓ Accounting entries created for order {order.id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to create accounting entries: {str(e)}")
            return False

    @staticmethod
    def _update_khata_account(order: Order, db: Session, current_user: User, is_credit: bool = True):
        """
        Update or create khata account for credit sales.

        Args:
            order: Order object
            db: Database session
            current_user: User performing action
            is_credit: Whether this is a credit sale
        """
        if not order.customer_id:
            return

        # Get or create khata account
        khata = db.query(KhataAccount).filter(
            and_(
                KhataAccount.shop_id == order.shop_id,
                KhataAccount.customer_id == order.customer_id
            )
        ).first()

        if not khata:
            khata = KhataAccount(
                shop_id=order.shop_id,
                customer_id=order.customer_id,
                balance=Decimal(0),
                credit_limit=Decimal(10000),
                total_credit_given=Decimal(0),
                total_credit_received=Decimal(0)
            )
            db.add(khata)

        # Update balance (customer owes amount)
        khata.balance += order.total_amount
        khata.total_credit_given += order.total_amount
        khata.last_transaction_date = datetime.utcnow()

    @staticmethod
    def reverse_accounting_entries(order: Order, db: Session, current_user: User) -> bool:
        """
        Reverse accounting entries when order is CANCELLED.

        Args:
            order: Order object being cancelled
            db: Database session
            current_user: User performing action

        Returns:
            True if successful
        """
        try:
            # Find and reverse ledger entry
            entry = db.query(LedgerEntry).filter(
                and_(
                    LedgerEntry.shop_id == order.shop_id,
                    LedgerEntry.reference_type == "order",
                    LedgerEntry.reference_id == order.id
                )
            ).first()

            if entry:
                # Create reverse entry
                reverse_entry = LedgerEntry(
                    shop_id=order.shop_id,
                    entry_date=datetime.utcnow(),
                    entry_number=f"REV{order.id}{datetime.utcnow().strftime('%Y%m%d')}",
                    description=f"Reversal of order {order.order_number}",
                    reference_type="order_reversal",
                    reference_id=order.id,
                    debit_account=entry.credit_account,
                    debit_amount=entry.credit_amount,
                    credit_account=entry.debit_account,
                    credit_amount=entry.debit_amount,
                    notes="Cancellation reversal",
                    created_by=current_user.id
                )
                db.add(reverse_entry)

            # Reverse GST record
            gst_record = db.query(GSTRecord).filter(
                GSTRecord.order_id == order.id
            ).first()

            if gst_record:
                db.delete(gst_record)

            # Reverse cash/khata entry
            if order.is_credit_sale and order.customer_id:
                khata = db.query(KhataAccount).filter(
                    and_(
                        KhataAccount.shop_id == order.shop_id,
                        KhataAccount.customer_id == order.customer_id
                    )
                ).first()
                if khata:
                    khata.balance -= order.total_amount
                    khata.last_transaction_date = datetime.utcnow()
            else:
                # Remove cash entry
                cash_entry = db.query(CashBook).filter(
                    CashBook.order_id == order.id
                ).first()
                if cash_entry:
                    db.delete(cash_entry)

            db.commit()
            logger.info(f"✓ Accounting entries reversed for order {order.id}")
            return True

        except Exception as e:
            db.rollback()
            logger.error(f"✗ Failed to reverse accounting entries: {str(e)}")
            return False

    # ===== REPORT GENERATION =====

    @staticmethod
    def get_daily_sales_report(shop_id: int, report_date: str, db: Session) -> DailySalesReport:
        """
        Generate daily sales report.

        PHASE D: API Endpoint 1

        Args:
            shop_id: Shop ID
            report_date: YYYY-MM-DD format
            db: Database session

        Returns:
            DailySalesReport with all sales data
        """
        from datetime import datetime as dt

        # Parse date
        date_obj = dt.strptime(report_date, "%Y-%m-%d").date()
        start = dt.combine(date_obj, dt.min.time())
        end = dt.combine(date_obj, dt.max.time())

        # Get all delivered orders for this date
        orders = db.query(Order).filter(
            and_(
                Order.shop_id == shop_id,
                Order.order_status == OrderStatusEnum.DELIVERED,
                Order.delivery_date >= start,
                Order.delivery_date <= end
            )
        ).all()

        # Calculate totals
        total_sales = Decimal(0)
        total_tax = Decimal(0)
        cash_sales = Decimal(0)
        credit_sales = Decimal(0)

        items = []
        for order in orders:
            total_sales += order.total_amount or Decimal(0)
            total_tax += order.tax_amount or Decimal(0)

            if order.is_credit_sale:
                credit_sales += order.total_amount or Decimal(0)
            else:
                cash_sales += order.total_amount or Decimal(0)

            items.append(DailySalesReportItem(
                order_id=order.id,
                order_number=order.order_number,
                customer_name=order.customer_name or "Unknown",
                subtotal=order.subtotal or Decimal(0),
                tax_amount=order.tax_amount or Decimal(0),
                total_amount=order.total_amount or Decimal(0),
                payment_method="Credit" if order.is_credit_sale else "Cash",
                is_credit_sale=order.is_credit_sale,
                created_at=order.created_at
            ))

        return DailySalesReport(
            shop_id=shop_id,
            report_date=report_date,
            total_orders=len(orders),
            total_sales=total_sales,
            total_tax=total_tax,
            cash_sales=cash_sales,
            credit_sales=credit_sales,
            items=items
        )

    @staticmethod
    def get_profit_loss_report(shop_id: int, period: str, db: Session) -> ProfitLossReport:
        """
        Generate Profit & Loss statement.

        PHASE D: API Endpoint 2

        Args:
            shop_id: Shop ID
            period: YYYY-MM format (e.g., "2024-01")
            db: Database session

        Returns:
            ProfitLossReport with P&L data
        """
        from datetime import datetime as dt

        # Parse period
        year, month = period.split("-")
        start = dt(int(year), int(month), 1)
        if int(month) == 12:
            end = dt(int(year) + 1, 1, 1)
        else:
            end = dt(int(year), int(month) + 1, 1)

        # Get all delivered orders in period
        orders = db.query(Order).filter(
            and_(
                Order.shop_id == shop_id,
                Order.order_status == OrderStatusEnum.DELIVERED,
                Order.delivery_date >= start,
                Order.delivery_date < end
            )
        ).all()

        # Calculate revenue
        gross_sales = sum(o.total_amount or Decimal(0) for o in orders)
        discounts = sum(o.discount_amount or Decimal(0) for o in orders)
        net_sales = gross_sales - discounts

        # Calculate COGS (simplified: cost of all items sold)
        cost_of_goods = Decimal(0)
        for order in orders:
            for item in order.items:
                # Get inventory to find cost price
                inv = db.query(Inventory).filter(
                    and_(
                        Inventory.shop_id == shop_id,
                        Inventory.product_id == item.product_id
                    )
                ).first()
                if inv:
                    cost_of_goods += inv.cost_price * item.quantity

        # Calculate profit
        gross_profit = net_sales - cost_of_goods
        gross_profit_margin = (gross_profit / net_sales *
                               100) if net_sales > 0 else Decimal(0)

        # Tax
        total_tax_collected = sum(o.tax_amount or Decimal(0) for o in orders)
        total_tax_payable = total_tax_collected  # Simplified

        return ProfitLossReport(
            shop_id=shop_id,
            report_period=period,
            gross_sales=gross_sales,
            discounts=discounts,
            net_sales=net_sales,
            cost_of_goods_sold=cost_of_goods,
            gross_profit=gross_profit,
            gross_profit_margin=gross_profit_margin,
            total_tax_collected=total_tax_collected,
            total_tax_payable=total_tax_payable
        )

    @staticmethod
    def get_cash_book(shop_id: int, from_date: str, to_date: str, db: Session) -> CashBookSummary:
        """
        Get cash book for a period.

        PHASE D: API Endpoint 3

        Args:
            shop_id: Shop ID
            from_date: YYYY-MM-DD format
            to_date: YYYY-MM-DD format
            db: Database session

        Returns:
            CashBookSummary with cash transactions
        """
        from datetime import datetime as dt

        start = dt.strptime(from_date, "%Y-%m-%d")
        end = dt.strptime(to_date, "%Y-%m-%d")

        # Get opening balance (all IN before from_date)
        opening = db.query(func.sum(CashBook.amount)).filter(
            and_(
                CashBook.shop_id == shop_id,
                CashBook.entry_type == "IN",
                CashBook.created_at < start
            )
        ).scalar() or Decimal(0)

        opening -= db.query(func.sum(CashBook.amount)).filter(
            and_(
                CashBook.shop_id == shop_id,
                CashBook.entry_type == "OUT",
                CashBook.created_at < start
            )
        ).scalar() or Decimal(0)

        # Get transactions in period
        transactions = db.query(CashBook).filter(
            and_(
                CashBook.shop_id == shop_id,
                CashBook.created_at >= start,
                CashBook.created_at <= end
            )
        ).order_by(CashBook.created_at).all()

        # Calculate totals
        cash_in = sum(
            t.amount for t in transactions if t.entry_type == "IN") or Decimal(0)
        cash_out = sum(
            t.amount for t in transactions if t.entry_type == "OUT") or Decimal(0)
        closing = opening + cash_in - cash_out

        return CashBookSummary(
            shop_id=shop_id,
            period=f"{from_date} to {to_date}",
            opening_balance=opening,
            cash_in=cash_in,
            cash_out=cash_out,
            closing_balance=closing,
            transactions=[
                CashBookResponse.model_validate(t) for t in transactions
            ]
        )

    @staticmethod
    def get_khata_statement(shop_id: int, customer_id: int, db: Session) -> KhataStatement:
        """
        Get customer khata statement.

        PHASE D: API Endpoint 4

        Args:
            shop_id: Shop ID
            customer_id: Customer ID
            db: Database session

        Returns:
            KhataStatement with customer credit details
        """
        khata = db.query(KhataAccount).filter(
            and_(
                KhataAccount.shop_id == shop_id,
                KhataAccount.customer_id == customer_id
            )
        ).first()

        customer = db.query(User).filter(User.id == customer_id).first()

        if not khata:
            khata = KhataAccount(
                shop_id=shop_id,
                customer_id=customer_id,
                balance=Decimal(0),
                credit_limit=Decimal(10000),
                total_credit_given=Decimal(0),
                total_credit_received=Decimal(0)
            )

        available_credit = khata.credit_limit - khata.balance

        return KhataStatement(
            customer_id=customer_id,
            customer_name=customer.name if customer else "Unknown",
            shop_id=shop_id,
            balance=khata.balance,
            credit_limit=khata.credit_limit,
            available_credit=available_credit,
            total_credit_given=khata.total_credit_given,
            total_credit_received=khata.total_credit_received,
            last_transaction_date=khata.last_transaction_date
        )
