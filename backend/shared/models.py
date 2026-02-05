"""SQLAlchemy ORM models for all database tables"""
from sqlalchemy import (
    Column, Integer, String, Numeric, Text, Boolean,
    DateTime, ForeignKey, Enum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from shared.database import Base
import enum


# ===== ENUMS =====
class RoleEnum(str, enum.Enum):
    """User roles"""
    CUSTOMER = "customer"
    STAFF = "staff"
    OWNER = "owner"
    ADMIN = "admin"


class OrderStatusEnum(str, enum.Enum):
    """Order statuses - Complete order lifecycle"""
    PLACED = "placed"
    ACCEPTED = "accepted"
    PACKED = "packed"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatusEnum(str, enum.Enum):
    """Payment statuses"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


# ===== SHOPS =====
class Shop(Base):
    """Shop/Store master data"""
    __tablename__ = "shops"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    address = Column(Text, nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    country = Column(String(100), default="India")

    gst_number = Column(String(15), unique=True)
    pan_number = Column(String(10), unique=True)
    shop_category = Column(String(50))
    monthly_revenue_est = Column(Numeric(15, 2))

    subscription_plan = Column(String(50), default="free")
    is_active = Column(Boolean, default=True)
    onboarded_at = Column(DateTime, default=datetime.utcnow)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    users = relationship("User", back_populates="shop",
                         cascade="all, delete-orphan")
    products = relationship(
        "Product", back_populates="shop", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="shop",
                          cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_shops_email", "email"),
        Index("idx_shops_active", "is_active", "deleted_at"),
    )


# ===== USERS =====
class User(Base):
    """Users (customers, staff, owners, admins)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    phone = Column(String(20), nullable=False)
    email = Column(String(255))
    name = Column(String(255), nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.CUSTOMER)

    password_hash = Column(String(255))
    otp_secret = Column(String(100))

    # Forgot password OTP fields
    otp_code = Column(String(6), nullable=True)
    otp_expiry = Column(DateTime, nullable=True)
    otp_attempts = Column(Integer, default=0)

    address = Column(Text)
    city = Column(String(100))

    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    # Relationships
    shop = relationship("Shop", back_populates="users")

    __table_args__ = (
        UniqueConstraint("shop_id", "phone", name="unique_shop_phone"),
        Index("idx_users_role", "shop_id", "role"),
        Index("idx_users_active", "shop_id", "is_active"),
    )


# ===== PRODUCTS =====
class Product(Base):
    """Product/SKU master data"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    name = Column(String(255), nullable=False)
    sku = Column(String(100), nullable=False)
    description = Column(Text)
    barcode = Column(String(50))

    category = Column(String(100), nullable=False)
    subcategory = Column(String(100))
    unit = Column(String(50), nullable=False)
    unit_quantity = Column(Numeric(10, 2))

    cost_price = Column(Numeric(10, 2), nullable=False)
    mrp = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)

    gst_rate = Column(Numeric(5, 2), default=0)
    hsn_code = Column(String(8))

    current_stock = Column(Integer, default=0)
    min_stock_level = Column(Integer, default=10)
    max_stock_level = Column(Integer)
    reorder_quantity = Column(Integer)

    supplier_id = Column(Integer, ForeignKey("users.id"))
    last_purchase_price = Column(Numeric(10, 2))
    last_purchase_date = Column(DateTime)

    expiry_date = Column(DateTime)
    is_perishable = Column(Boolean, default=False)
    shelf_life_days = Column(Integer)

    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)
    popularity_score = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)
    deleted_at = Column(DateTime)

    # Relationships
    shop = relationship("Shop", back_populates="products")

    __table_args__ = (
        UniqueConstraint("shop_id", "sku", name="unique_shop_sku"),
        Index("idx_products_category", "shop_id", "category"),
        Index("idx_products_active", "shop_id", "is_active"),
        Index("idx_products_stock_low", "shop_id", "current_stock"),
    )


# ===== STOCK MOVEMENTS =====
class StockMovement(Base):
    """Inventory stock movement audit trail"""
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # 'inbound', 'sale', 'adjustment', 'damaged', 'return'
    movement_type = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)

    reference_type = Column(String(50))  # 'order', 'purchase_order', 'manual'
    reference_id = Column(Integer)
    notes = Column(Text)

    moved_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_stock_movements_product",
              "shop_id", "product_id", "created_at"),
        Index("idx_stock_movements_reference",
              "reference_type", "reference_id"),
    )


# ===== INVENTORY =====
class Inventory(Base):
    """Product inventory tracking per shop"""
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Stock levels
    quantity = Column(Integer, nullable=False, default=0)
    min_quantity = Column(Integer, nullable=False, default=10)

    # Pricing at shop level (can override product pricing)
    cost_price = Column(Numeric(10, 2), nullable=False)
    selling_price = Column(Numeric(10, 2), nullable=False)

    # Batch tracking (for expiry date management)
    batch_no = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)

    last_updated = Column(DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship("Shop")
    product = relationship("Product")

    __table_args__ = (
        UniqueConstraint("shop_id", "product_id", "batch_no",
                         name="unique_shop_product_batch"),
        Index("idx_inventory_shop", "shop_id"),
        Index("idx_inventory_product", "product_id"),
        Index("idx_inventory_low_stock", "shop_id", "quantity"),
        Index("idx_inventory_expiry", "shop_id", "expiry_date"),
    )


# ===== ORDERS =====
class Order(Base):
    """Customer orders/transactions"""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"))

    order_number = Column(String(50), nullable=False)
    order_date = Column(DateTime, default=datetime.utcnow)

    subtotal = Column(Numeric(15, 2), nullable=False)
    discount_amount = Column(Numeric(15, 2), default=0)
    tax_amount = Column(Numeric(15, 2), default=0)
    total_amount = Column(Numeric(15, 2), nullable=False)

    payment_method = Column(String(50))
    payment_status = Column(Enum(PaymentStatusEnum),
                            default=PaymentStatusEnum.PENDING)
    payment_date = Column(DateTime)

    order_status = Column(Enum(OrderStatusEnum),
                          default=OrderStatusEnum.PLACED)
    delivery_date = Column(DateTime)

    shipping_address = Column(Text)
    customer_phone = Column(String(20))
    customer_name = Column(String(255))

    is_credit_sale = Column(Boolean, default=False)
    credit_duration_days = Column(Integer)

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    shop = relationship("Shop", back_populates="orders")
    items = relationship("OrderItem", back_populates="order",
                         cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("shop_id", "order_number",
                         name="unique_order_number"),
        Index("idx_orders_customer", "shop_id", "customer_id"),
        Index("idx_orders_date", "shop_id", "order_date"),
        Index("idx_orders_status", "shop_id", "order_status"),
    )


class OrderItem(Base):
    """Order line items"""
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey(
        "orders.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    product_name = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)

    gst_rate = Column(Numeric(5, 2))
    gst_amount = Column(Numeric(10, 2))

    discount_on_item = Column(Numeric(10, 2), default=0)
    line_total = Column(Numeric(15, 2), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    order = relationship("Order", back_populates="items")

    __table_args__ = (
        Index("idx_order_items_order", "order_id"),
        Index("idx_order_items_product", "shop_id", "product_id"),
    )


# ===== ACCOUNTING =====
class LedgerEntry(Base):
    """Double-entry bookkeeping ledger"""
    __tablename__ = "ledger_entries"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)

    entry_date = Column(DateTime, nullable=False)
    entry_number = Column(String(50))
    description = Column(String(500), nullable=False)

    # 'order', 'purchase', 'manual', 'adjustment'
    reference_type = Column(String(50))
    reference_id = Column(Integer)

    debit_account = Column(String(100), nullable=False)
    debit_amount = Column(Numeric(15, 2), nullable=False)

    credit_account = Column(String(100), nullable=False)
    credit_amount = Column(Numeric(15, 2), nullable=False)

    notes = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship("Shop")

    __table_args__ = (
        Index("idx_ledger_date", "shop_id", "entry_date"),
        Index("idx_ledger_account", "shop_id",
              "debit_account", "credit_account"),
        Index("idx_ledger_reference", "reference_type", "reference_id"),
    )


class CashBook(Base):
    """Cash book for cash transactions"""
    __tablename__ = "cash_book"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    amount = Column(Numeric(15, 2), nullable=False)
    # 'IN' for cash received, 'OUT' for cash paid
    entry_type = Column(String(10), nullable=False)
    description = Column(String(500))

    reference_number = Column(String(50))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship("Shop")
    order = relationship("Order")

    __table_args__ = (
        Index("idx_cash_book_shop", "shop_id"),
        Index("idx_cash_book_date", "shop_id", "created_at"),
        Index("idx_cash_book_order", "order_id"),
    )


class BankBook(Base):
    """Bank book for bank transactions"""
    __tablename__ = "bank_book"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    amount = Column(Numeric(15, 2), nullable=False)
    # 'IN' for deposit, 'OUT' for withdrawal
    entry_type = Column(String(10), nullable=False)
    description = Column(String(500))

    bank_account = Column(String(100))
    cheque_number = Column(String(50))
    reference_number = Column(String(50))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship("Shop")
    order = relationship("Order")

    __table_args__ = (
        Index("idx_bank_book_shop", "shop_id"),
        Index("idx_bank_book_date", "shop_id", "created_at"),
        Index("idx_bank_book_order", "order_id"),
    )


class KhataAccount(Base):
    """Customer credit accounts (khata/credit)"""
    __tablename__ = "khata_accounts"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Current balance (positive = customer owes, negative = customer is owed)
    balance = Column(Numeric(15, 2), default=0)
    credit_limit = Column(Numeric(15, 2), default=10000)

    total_credit_given = Column(Numeric(15, 2), default=0)
    total_credit_received = Column(Numeric(15, 2), default=0)

    last_transaction_date = Column(DateTime)
    last_updated = Column(DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship("Shop")
    customer = relationship("User")

    __table_args__ = (
        UniqueConstraint("shop_id", "customer_id",
                         name="unique_shop_customer"),
        Index("idx_khata_shop", "shop_id"),
        Index("idx_khata_customer", "customer_id"),
        Index("idx_khata_balance", "shop_id", "balance"),
    )


class GSTRecord(Base):
    """GST tracking for tax compliance"""
    __tablename__ = "gst_records"

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey("shops.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)

    # Taxable amount (on which GST is calculated)
    taxable_amount = Column(Numeric(15, 2), nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    gst_amount = Column(Numeric(15, 2), nullable=False)

    # GST breakdown
    cgst_amount = Column(Numeric(15, 2), default=0)  # Central GST
    sgst_amount = Column(Numeric(15, 2), default=0)  # State GST
    igst_amount = Column(Numeric(15, 2), default=0)  # Integrated GST

    invoice_number = Column(String(50))
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship("Shop")
    order = relationship("Order")

    __table_args__ = (
        UniqueConstraint("order_id", name="unique_gst_per_order"),
        Index("idx_gst_shop", "shop_id"),
        Index("idx_gst_date", "shop_id", "created_at"),
        Index("idx_gst_order", "order_id"),
    )


class ChartOfAccounts(Base):
    """Standard chart of accounts"""
    __tablename__ = "chart_of_accounts"

    id = Column(Integer, primary_key=True)
    account_code = Column(String(20), unique=True, nullable=False)
    account_name = Column(String(100), nullable=False)
    # 'asset', 'liability', 'equity', 'revenue', 'expense'
    account_type = Column(String(50), nullable=False)
    description = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
