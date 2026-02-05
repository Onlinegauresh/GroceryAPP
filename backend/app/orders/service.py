"""Order management service - Business logic for order operations"""
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Tuple
import random
import string

from shared.models import Order, OrderItem, Product, Inventory, Shop, User
from shared.models import OrderStatusEnum, RoleEnum
from app.orders.schemas import (
    OrderCreateRequest, OrderStatusUpdate, OrderResponse, OrderListResponse
)


class OrderService:
    """Service for order management operations"""

    @staticmethod
    def generate_order_number(shop_id: int) -> str:
        """Generate unique order number"""
        # Format: ORD{TIMESTAMP}{SHOP_ID}{RANDOM}
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = "".join(random.choices(
            string.ascii_uppercase + string.digits, k=4))
        return f"ORD{timestamp}{shop_id}{random_suffix}"

    @staticmethod
    def verify_shop_access(user: User, shop_id: int, db: Session) -> Tuple[bool, str]:
        """Verify user has access to shop"""
        if user.role == RoleEnum.ADMIN:
            return True, "Admin access"

        if user.role == RoleEnum.CUSTOMER:
            return False, "Customers cannot manage orders"

        if user.role in [RoleEnum.OWNER, RoleEnum.STAFF]:
            # Verify shop exists and user belongs to it
            if user.shop_id != shop_id:
                return False, f"User does not belong to shop {shop_id}"
            shop = db.query(Shop).filter(Shop.id == shop_id).first()
            if not shop:
                return False, f"Shop {shop_id} not found"
            return True, "Shop staff access"

        return False, "Invalid role"

    @staticmethod
    def validate_inventory_availability(
        db: Session,
        shop_id: int,
        items: List[Tuple[int, int]],  # [(product_id, quantity), ...]
    ) -> Tuple[bool, str, Optional[str]]:
        """Validate that inventory is available for all items

        Returns: (success, message, error_product_name)
        """
        for product_id, quantity in items:
            inventory = db.query(Inventory).filter(
                and_(
                    Inventory.shop_id == shop_id,
                    Inventory.product_id == product_id
                )
            ).first()

            if not inventory:
                product = db.query(Product).filter(
                    Product.id == product_id
                ).first()
                product_name = product.name if product else f"Product {product_id}"
                return False, f"Product {product_name} not available in inventory", product_name

            if inventory.quantity < quantity:
                product = db.query(Product).filter(
                    Product.id == product_id
                ).first()
                product_name = product.name if product else f"Product {product_id}"
                return False, f"Insufficient stock for {product_name}. Available: {inventory.quantity}, Requested: {quantity}", product_name

        return True, "All items available", None

    @staticmethod
    def deduct_inventory(
        db: Session,
        shop_id: int,
        items: List[Tuple[int, int]],  # [(product_id, quantity), ...]
    ) -> Tuple[bool, str]:
        """Deduct inventory for all items

        Returns: (success, message)
        """
        try:
            for product_id, quantity in items:
                inventory = db.query(Inventory).filter(
                    and_(
                        Inventory.shop_id == shop_id,
                        Inventory.product_id == product_id
                    )
                ).first()

                if not inventory or inventory.quantity < quantity:
                    return False, f"Inventory deduction failed for product {product_id}"

                # Deduct from inventory
                inventory.quantity -= quantity
                inventory.last_updated = datetime.utcnow()

            db.commit()
            return True, "Inventory deducted successfully"
        except Exception as e:
            db.rollback()
            return False, f"Error deducting inventory: {str(e)}"

    @staticmethod
    def restore_inventory(
        db: Session,
        shop_id: int,
        items: List[Tuple[int, int]],  # [(product_id, quantity), ...]
    ) -> bool:
        """Restore inventory when order is cancelled

        Returns: success
        """
        try:
            for product_id, quantity in items:
                inventory = db.query(Inventory).filter(
                    and_(
                        Inventory.shop_id == shop_id,
                        Inventory.product_id == product_id
                    )
                ).first()

                if inventory:
                    inventory.quantity += quantity
                    inventory.last_updated = datetime.utcnow()

            db.commit()
            return True
        except Exception as e:
            db.rollback()
            return False

    @staticmethod
    def calculate_order_totals(
        db: Session,
        shop_id: int,
        items: List[dict],  # [{product_id, quantity, unit_price}, ...]
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate order subtotal, tax, and total

        Returns: (subtotal, tax_amount, total)
        """
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")

        for item in items:
            product_id = item.get("product_id")
            quantity = item.get("quantity", 0)
            unit_price = Decimal(str(item.get("unit_price", 0)))

            # Get product for tax info
            product = db.query(Product).filter(
                Product.id == product_id
            ).first()

            line_total = unit_price * quantity
            subtotal += line_total

            if product and product.gst_rate:
                item_tax = line_total * \
                    (Decimal(str(product.gst_rate)) / Decimal("100"))
                tax_amount += item_tax

        total = subtotal + tax_amount
        return subtotal, tax_amount, total

    @staticmethod
    def create_order(
        db: Session,
        shop_id: int,
        user: User,
        request: OrderCreateRequest,
    ) -> Tuple[bool, str, Optional[Order]]:
        """Create new order with inventory deduction

        Returns: (success, message, order_object)
        """
        # Verify access
        access_ok, access_msg = OrderService.verify_shop_access(
            user, shop_id, db)
        if not access_ok:
            return False, access_msg, None

        # Prepare items list for validation
        items_for_validation = [(item.product_id, item.quantity)
                                for item in request.items]

        # Validate inventory availability
        inv_ok, inv_msg, error_product = OrderService.validate_inventory_availability(
            db, shop_id, items_for_validation
        )
        if not inv_ok:
            return False, inv_msg, None

        # Prepare items data for total calculation
        items_data = [
            {
                "product_id": item.product_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price
            }
            for item in request.items
        ]

        # Calculate totals
        subtotal, tax_amount, total_amount = OrderService.calculate_order_totals(
            db, shop_id, items_data
        )

        # Deduct inventory
        deduct_ok, deduct_msg = OrderService.deduct_inventory(
            db, shop_id, items_for_validation)
        if not deduct_ok:
            return False, deduct_msg, None

        # Create order
        try:
            order_number = OrderService.generate_order_number(shop_id)

            order = Order(
                shop_id=shop_id,
                customer_id=request.customer_id,
                order_number=order_number,
                order_date=datetime.utcnow(),
                subtotal=subtotal,
                tax_amount=tax_amount,
                total_amount=total_amount,
                order_status=OrderStatusEnum.PLACED,
                created_by=user.id,
                notes=request.notes,
                customer_name=request.customer_name,
                customer_phone=request.customer_phone,
                shipping_address=request.shipping_address,
                is_credit_sale=request.is_credit_sale,
                credit_duration_days=request.credit_duration_days,
            )

            db.add(order)
            db.flush()  # Get order ID without committing

            # Create order items
            for item in request.items:
                product = db.query(Product).filter(
                    Product.id == item.product_id
                ).first()

                if not product:
                    db.rollback()
                    OrderService.restore_inventory(
                        db, shop_id, items_for_validation)
                    return False, f"Product {item.product_id} not found", None

                line_total = item.unit_price * item.quantity
                gst_amount = line_total * \
                    (Decimal(str(product.gst_rate or 0)) / Decimal("100"))

                order_item = OrderItem(
                    order_id=order.id,
                    product_id=item.product_id,
                    shop_id=shop_id,
                    product_name=product.name,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    gst_rate=product.gst_rate or Decimal("0"),
                    gst_amount=gst_amount,
                    line_total=line_total,
                )
                db.add(order_item)

            db.commit()
            db.refresh(order)

            return True, f"Order {order_number} created successfully", order

        except Exception as e:
            db.rollback()
            OrderService.restore_inventory(db, shop_id, items_for_validation)
            return False, f"Error creating order: {str(e)}", None

    @staticmethod
    def get_order(db: Session, shop_id: int, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        return db.query(Order).filter(
            and_(
                Order.id == order_id,
                Order.shop_id == shop_id
            )
        ).first()

    @staticmethod
    def list_orders(
        db: Session,
        shop_id: int,
        skip: int = 0,
        limit: int = 20,
        status: Optional[OrderStatusEnum] = None,
    ) -> Tuple[List[Order], int]:
        """List orders for shop with optional filtering

        Returns: (orders_list, total_count)
        """
        query = db.query(Order).filter(Order.shop_id == shop_id)

        if status:
            query = query.filter(Order.order_status == status)

        total = query.count()
        orders = query.order_by(desc(Order.order_date)).offset(
            skip).limit(limit).all()

        return orders, total

    @staticmethod
    def list_customer_orders(
        db: Session,
        shop_id: int,
        customer_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Order], int]:
        """List orders for specific customer"""
        query = db.query(Order).filter(
            and_(
                Order.shop_id == shop_id,
                Order.customer_id == customer_id
            )
        )

        total = query.count()
        orders = query.order_by(desc(Order.order_date)).offset(
            skip).limit(limit).all()

        return orders, total

    @staticmethod
    def update_order_status(
        db: Session,
        shop_id: int,
        order_id: int,
        update_request: OrderStatusUpdate,
        user: User,
    ) -> Tuple[bool, str, Optional[Order]]:
        """Update order status with validation

        Returns: (success, message, order)
        """
        # Verify access
        access_ok, _ = OrderService.verify_shop_access(user, shop_id, db)
        if not access_ok and user.role != RoleEnum.ADMIN:
            return False, "Unauthorized to update order status", None

        order = OrderService.get_order(db, shop_id, order_id)
        if not order:
            return False, f"Order {order_id} not found", None

        # Validate status transition
        current_status = order.order_status
        new_status = update_request.new_status

        # Define valid transitions
        valid_transitions = {
            OrderStatusEnum.PLACED: [OrderStatusEnum.ACCEPTED, OrderStatusEnum.CANCELLED],
            OrderStatusEnum.ACCEPTED: [OrderStatusEnum.PACKED, OrderStatusEnum.CANCELLED],
            OrderStatusEnum.PACKED: [OrderStatusEnum.OUT_FOR_DELIVERY, OrderStatusEnum.CANCELLED],
            OrderStatusEnum.OUT_FOR_DELIVERY: [OrderStatusEnum.DELIVERED, OrderStatusEnum.CANCELLED],
            OrderStatusEnum.DELIVERED: [],  # Final state
            OrderStatusEnum.CANCELLED: [],  # Final state
        }

        if new_status not in valid_transitions.get(current_status, []):
            return False, f"Cannot transition from {current_status} to {new_status}", order

        try:
            # If cancelling, restore inventory
            if new_status == OrderStatusEnum.CANCELLED and current_status != OrderStatusEnum.CANCELLED:
                items_to_restore = [
                    (item.product_id, item.quantity)
                    for item in order.items
                ]
                restore_ok = OrderService.restore_inventory(
                    db, shop_id, items_to_restore)
                if not restore_ok:
                    return False, "Failed to restore inventory when cancelling order", order

            order.order_status = new_status
            if update_request.notes:
                order.notes = (
                    order.notes or "") + f"\n[{datetime.utcnow().isoformat()}] {update_request.notes}"
            order.updated_at = datetime.utcnow()

            if new_status == OrderStatusEnum.DELIVERED:
                order.delivery_date = datetime.utcnow()

            db.commit()
            db.refresh(order)

            return True, f"Order status updated to {new_status}", order

        except Exception as e:
            db.rollback()
            return False, f"Error updating order status: {str(e)}", order

    @staticmethod
    def get_order_dashboard(
        db: Session,
        shop_id: int,
    ) -> dict:
        """Get order dashboard statistics"""
        query = db.query(Order).filter(Order.shop_id == shop_id)

        total_orders = query.count()
        placed_orders = query.filter(
            Order.order_status == OrderStatusEnum.PLACED).count()
        accepted_orders = query.filter(
            Order.order_status == OrderStatusEnum.ACCEPTED).count()
        packed_orders = query.filter(
            Order.order_status == OrderStatusEnum.PACKED).count()
        out_for_delivery_orders = query.filter(
            Order.order_status == OrderStatusEnum.OUT_FOR_DELIVERY
        ).count()
        delivered_orders = query.filter(
            Order.order_status == OrderStatusEnum.DELIVERED).count()
        cancelled_orders = query.filter(
            Order.order_status == OrderStatusEnum.CANCELLED).count()

        # Calculate revenue from delivered orders
        delivered_query = db.query(Order).filter(
            and_(
                Order.shop_id == shop_id,
                Order.order_status == OrderStatusEnum.DELIVERED
            )
        )

        total_revenue = Decimal("0.00")
        for order in delivered_query:
            total_revenue += order.total_amount

        average_order_value = (
            total_revenue /
            total_orders if total_orders > 0 else Decimal("0.00")
        )

        # Recent orders
        recent_orders = (
            db.query(Order)
            .filter(Order.shop_id == shop_id)
            .order_by(desc(Order.order_date))
            .limit(5)
            .all()
        )

        return {
            "total_orders": total_orders,
            "placed_orders": placed_orders,
            "accepted_orders": accepted_orders,
            "packed_orders": packed_orders,
            "out_for_delivery_orders": out_for_delivery_orders,
            "delivered_orders": delivered_orders,
            "cancelled_orders": cancelled_orders,
            "total_revenue": float(total_revenue),
            "average_order_value": float(average_order_value),
            "recent_orders": recent_orders,
        }
