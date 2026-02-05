"""Preview Router - Browser-based UI for viewing backend data"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.models import Product, Order, Shop, User
from sqlalchemy import desc
import os

# Setup templates
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter(tags=["Preview"])


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home preview page"""
    return templates.TemplateResponse("index.html", {"request": request})


@router.get("/preview/products", response_class=HTMLResponse)
async def preview_products(request: Request, db: Session = Depends(get_db)):
    """Preview all products"""
    try:
        products = db.query(Product).limit(50).all()
        return templates.TemplateResponse(
            "products.html",
            {
                "request": request,
                "products": products,
                "total": len(products)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/preview/orders", response_class=HTMLResponse)
async def preview_orders(request: Request, db: Session = Depends(get_db)):
    """Preview all orders"""
    try:
        orders = db.query(Order).order_by(
            desc(Order.created_at)).limit(50).all()
        return templates.TemplateResponse(
            "orders.html",
            {
                "request": request,
                "orders": orders,
                "total": len(orders)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/preview/shops", response_class=HTMLResponse)
async def preview_shops(request: Request, db: Session = Depends(get_db)):
    """Preview all shops"""
    try:
        shops = db.query(Shop).limit(50).all()
        return templates.TemplateResponse(
            "shops.html",
            {
                "request": request,
                "shops": shops,
                "total": len(shops)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )


@router.get("/preview/users", response_class=HTMLResponse)
async def preview_users(request: Request, db: Session = Depends(get_db)):
    """Preview all users"""
    try:
        users = db.query(User).limit(50).all()
        return templates.TemplateResponse(
            "users.html",
            {
                "request": request,
                "users": users,
                "total": len(users)
            }
        )
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)},
            status_code=500
        )
