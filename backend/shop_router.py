"""Customer Shop Router - E-commerce Web App"""
from fastapi import APIRouter, Depends, Request as FastAPIRequest
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.models import Product, Order, OrderItem, Shop
import os
from datetime import datetime
from decimal import Decimal

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter(
    prefix="/shop",
    tags=["Customer Shop"],
)

# In-memory cart storage (demo - in production use sessions/database)
customer_carts = {}


def get_cart(customer_id: str = "demo_customer"):
    """Get or create a cart for a customer"""
    if customer_id not in customer_carts:
        customer_carts[customer_id] = {}
    return customer_carts[customer_id]


@router.get("/", response_class=HTMLResponse)
async def shop_home(request: Request, db: Session = Depends(get_db)):
    """Customer Shop Home"""
    try:
        # Get featured products (with checking current_stock instead of stock)
        products = db.query(Product).filter(
            Product.current_stock > 0).limit(12).all()
        cart = get_cart()
        cart_count = len(cart)

        context = {
            "request": request,
            "products": products,
            "cart_count": cart_count
        }
        return templates.TemplateResponse("shop/home.html", context)
    except Exception as e:
        return templates.TemplateResponse(
            "shop/error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/products", response_class=HTMLResponse)
async def shop_products(request: Request, category: str = None, db: Session = Depends(get_db)):
    """Browse all available products"""
    try:
        if category:
            products = db.query(Product).filter(
                Product.category == category,
                Product.current_stock > 0
            ).all()
        else:
            products = db.query(Product).filter(
                Product.current_stock > 0).all()

        # Get categories
        all_products = db.query(Product).all()
        categories = list(set(p.category for p in all_products if p.category))

        cart = get_cart()
        cart_count = len(cart)

        context = {
            "request": request,
            "products": products,
            "categories": categories,
            "selected_category": category,
            "cart_count": cart_count
        }
        return templates.TemplateResponse("shop/products.html", context)
    except Exception as e:
        return templates.TemplateResponse(
            "shop/error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/cart/add/{product_id}")
async def add_to_cart(product_id: int, quantity: int = 1, db: Session = Depends(get_db)):
    """Add item to cart"""
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return RedirectResponse("/shop/products?error=Product not found", status_code=302)

        cart = get_cart()

        if str(product_id) in cart:
            cart[str(product_id)]["quantity"] += quantity
        else:
            cart[str(product_id)] = {
                "id": product.id,
                "name": product.name,
                "price": float(product.selling_price or 0),
                "quantity": quantity
            }

        return RedirectResponse("/shop/products?success=Added to cart", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/shop/products?error={str(e)}", status_code=302)


@router.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    """View shopping cart"""
    try:
        cart = get_cart()
        cart_items = []
        total_amount = 0

        for product_id, item in cart.items():
            item_total = item["price"] * item["quantity"]
            total_amount += item_total
            cart_items.append({
                "product_id": product_id,
                "name": item["name"],
                "price": item["price"],
                "quantity": item["quantity"],
                "total": item_total
            })

        context = {
            "request": request,
            "cart_items": cart_items,
            "total_amount": round(total_amount, 2),
            "cart_count": len(cart)
        }
        return templates.TemplateResponse("shop/cart.html", context)
    except Exception as e:
        return templates.TemplateResponse(
            "shop/error.html",
            {"request": request, "error": str(e), "cart_count": 0},
            status_code=500
        )


@router.post("/cart/remove/{product_id}")
async def remove_from_cart(product_id: str):
    """Remove item from cart"""
    try:
        cart = get_cart()
        if product_id in cart:
            del cart[product_id]
        return RedirectResponse("/shop/cart", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/shop/cart?error={str(e)}", status_code=302)


@router.post("/cart/update/{product_id}")
async def update_cart_item(product_id: str, quantity: int):
    """Update item quantity in cart"""
    try:
        cart = get_cart()
        if product_id in cart:
            if quantity <= 0:
                del cart[product_id]
            else:
                cart[product_id]["quantity"] = quantity
        return RedirectResponse("/shop/cart", status_code=302)
    except Exception as e:
        return RedirectResponse(f"/shop/cart?error={str(e)}", status_code=302)


@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, db: Session = Depends(get_db)):
    """Checkout page"""
    try:
        cart = get_cart()
        if not cart:
            return RedirectResponse("/shop/cart", status_code=302)

        cart_items = []
        total_amount = Decimal("0")

        for product_id, item in cart.items():
            item_total = Decimal(
                str(item["price"])) * Decimal(str(item["quantity"]))
            total_amount += item_total
            cart_items.append({
                "product_id": product_id,
                "name": item["name"],
                "price": item["price"],
                "quantity": item["quantity"],
                "total": float(item_total)
            })

        context = {
            "request": request,
            "cart_items": cart_items,
            "total_amount": float(total_amount),
            "cart_count": len(cart)
        }
        return templates.TemplateResponse("shop/checkout.html", context)
    except Exception as e:
        return templates.TemplateResponse(
            "shop/error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.post("/checkout/place-order")
async def place_order(
    request: Request,
    customer_name: str = None,
    customer_phone: str = None,
    db: Session = Depends(get_db)
):
    """Place an order"""
    try:
        cart = get_cart()
        if not cart:
            return RedirectResponse("/shop/cart?error=Cart is empty", status_code=302)

        # Calculate total
        total_amount = Decimal("0")
        order_items = []

        for product_id, item in cart.items():
            product = db.query(Product).filter(
                Product.id == int(product_id)).first()
            if not product:
                return RedirectResponse(f"/shop/cart?error=Product {product_id} not found", status_code=302)

            if product.current_stock < item["quantity"]:
                return RedirectResponse(
                    f"/shop/cart?error={product.name} not enough stock",
                    status_code=302
                )

            item_total = Decimal(str(product.selling_price or 0)) * \
                Decimal(str(item["quantity"]))
            total_amount += item_total

            order_items.append({
                "product_id": product.id,
                "product_name": product.name,
                "quantity": item["quantity"],
                "unit_price": float(product.selling_price or 0),
                "total_price": float(item_total)
            })

            # Reduce stock
            product.current_stock -= item["quantity"]

        # Create order with required fields
        order = Order(
            shop_id=1,
            order_number=f"ORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            customer_name=customer_name or "Guest",
            customer_phone=customer_phone or "0000000000",
            shipping_address="Demo Address",
            subtotal=float(total_amount),
            tax_amount=0,
            total_amount=float(total_amount),
            payment_method="cash",
            payment_status="pending",
            order_status="placed",
            created_by=1,
            created_at=datetime.utcnow()
        )
        db.add(order)
        db.flush()

        # Create order items
        for item_data in order_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data["product_id"],
                shop_id=1,
                product_name=item_data["product_name"],
                quantity=item_data["quantity"],
                unit_price=Decimal(str(item_data["unit_price"])),
                line_total=Decimal(str(item_data["total_price"]))
            )
            db.add(order_item)

        db.commit()

        # Clear cart
        customer_carts.clear()

        return RedirectResponse(f"/shop/order-confirmation/{order.id}", status_code=302)
    except Exception as e:
        db.rollback()
        return RedirectResponse(f"/shop/checkout?error={str(e)}", status_code=302)


@router.get("/order-confirmation/{order_id}", response_class=HTMLResponse)
async def order_confirmation(order_id: int, request: Request, db: Session = Depends(get_db)):
    """Order confirmation page"""
    try:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return RedirectResponse("/shop?error=Order not found", status_code=302)

        context = {
            "request": request,
            "order": order,
            "order_id": order.id,
            "total_amount": order.total_amount
        }
        return templates.TemplateResponse("shop/order_confirmation.html", context)
    except Exception as e:
        return templates.TemplateResponse(
            "shop/error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/orders", response_class=HTMLResponse)
async def customer_orders(request: Request, db: Session = Depends(get_db)):
    """View customer's past orders"""
    try:
        # Demo: get orders for demo customer (customer_id = 1)
        orders = db.query(Order).filter(Order.customer_id == 1).order_by(
            Order.order_date.desc()
        ).all()

        # For each order, set created_at to order_date for template compatibility
        for order in orders:
            if not hasattr(order, 'created_at') or order.created_at is None:
                order.created_at = order.order_date

        context = {
            "request": request,
            "orders": orders,
            "total_orders": len(orders),
            "cart_count": len(get_cart()),
            "status_breakdown": {}  # Add this for template compatibility
        }
        return templates.TemplateResponse("shop/orders.html", context)
    except Exception as e:
        return templates.TemplateResponse(
            "shop/error.html",
            {"request": request, "error": str(e), "cart_count": 0},
            status_code=500
        )
