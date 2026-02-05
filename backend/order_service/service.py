"""Order creation and management business logic"""
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime, date

from shared.models import (
    Order, OrderItem, Product, StockMovement, LedgerEntry, OrderStatusEnum
)
from shared.exceptions import ValidationException


class OrderService:
    """Business logic for order operations"""

    @staticmethod
    def create_order(
        shop_id: int,
        customer_id: int,
        items: list,  # [{"product_id": 1, "quantity": 5}, ...]
        payment_method: str,
        created_by: int,
        is_credit_sale: bool = False,
        credit_duration_days: int = None,
        db: Session = None
    ) -> Order:
        """
        Create order with automatic inventory deduction and ledger entries.

        Steps:
        1. Validate stock availability
        2. Calculate amounts (subtotal, tax, total)
        3. Create order and items
        4. Deduct inventory
        5. Create accounting ledger entries
        """

        if not items:
            raise ValidationException("Order must have at least one item")

        # ===== STEP 1: Validate stock =====
        items_data = []
        for item in items:
            product = db.query(Product).filter(
                Product.id == item["product_id"],
                Product.shop_id == shop_id,
                Product.deleted_at == None
            ).first()

            if not product:
                raise ValidationException(
                    f"Product ID {item['product_id']} not found")

            if product.current_stock < item["quantity"]:
                raise ValidationException(
                    f"Insufficient stock: {product.name} has {product.current_stock} units, "
                    f"but {item['quantity']} requested"
                )

            items_data.append(
                {"product": product, "quantity": item["quantity"]})

        # ===== STEP 2: Calculate amounts =====
        subtotal = Decimal(0)
        tax_amount = Decimal(0)
        order_items_list = []

        for item_data in items_data:
            product = item_data["product"]
            qty = item_data["quantity"]

            unit_price = product.selling_price
            gst_rate = product.gst_rate

            # Calculate tax on this line
            gst_amount = (unit_price * qty * gst_rate) / Decimal(100)
            line_total = (unit_price * qty) + gst_amount

            subtotal += unit_price * qty
            tax_amount += gst_amount

            order_items_list.append({
                "product": product,
                "quantity": qty,
                "unit_price": unit_price,
                "gst_rate": gst_rate,
                "gst_amount": gst_amount,
                "line_total": line_total
            })

        total_amount = subtotal + tax_amount

        # ===== STEP 3: Generate order number =====
        today = date.today()
        order_count = db.query(Order).filter(
            Order.shop_id == shop_id,
            Order.order_date >= datetime(today.year, today.month, today.day)
        ).count()
        order_number = f"ORD-{today.strftime('%Y%m%d')}-{order_count + 1:04d}"

        # ===== STEP 4: Create order =====
        order = Order(
            shop_id=shop_id,
            customer_id=customer_id,
            order_number=order_number,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_method=payment_method,
            created_by=created_by,
            is_credit_sale=is_credit_sale,
            credit_duration_days=credit_duration_days
        )

        db.add(order)
        db.flush()  # Get order.id without committing

        # ===== STEP 5: Add order items =====
        for item_data in order_items_list:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product"].id,
                shop_id=shop_id,
                product_name=item_data["product"].name,
                quantity=item_data["quantity"],
                unit_price=item_data["unit_price"],
                gst_rate=item_data["gst_rate"],
                gst_amount=item_data["gst_amount"],
                line_total=item_data["line_total"]
            )
            db.add(order_item)

        # ===== STEP 6: Auto-deduct inventory =====
        for item_data in order_items_list:
            product = item_data["product"]
            quantity = item_data["quantity"]

            # Update current stock
            product.current_stock -= quantity

            # Log stock movement (immutable)
            movement = StockMovement(
                shop_id=shop_id,
                product_id=product.id,
                movement_type="sale",
                quantity=-quantity,  # Negative for outbound
                reference_type="order",
                reference_id=order.id,
                moved_by=created_by
            )
            db.add(movement)

        # ===== STEP 7: Create ledger entries (double-entry bookkeeping) =====
        # Entry: Debit Cash, Credit Sales Revenue
        # This records the sale in the accounting ledger

        ledger_entry = LedgerEntry(
            shop_id=shop_id,
            entry_date=datetime.utcnow(),
            description=f"Sale - Order {order_number}",
            reference_type="order",
            reference_id=order.id,
            debit_account="1001",  # Cash account
            debit_amount=total_amount,
            credit_account="4001",  # Sales revenue
            credit_amount=total_amount,
            created_by=created_by
        )
        db.add(ledger_entry)

        # Commit all changes
        db.commit()
        db.refresh(order)

        return order

    @staticmethod
    def get_order_summary(order_id: int, shop_id: int, db: Session) -> dict:
        """Get detailed order summary with items"""
        order = db.query(Order).filter(
            Order.id == order_id,
            Order.shop_id == shop_id
        ).first()

        if not order:
            raise ValidationException("Order not found")

        items = db.query(OrderItem).filter(
            OrderItem.order_id == order_id).all()

        return {
            "order": order,
            "items": items,
            "item_count": len(items),
            "total_quantity": sum(item.quantity for item in items)
        }
