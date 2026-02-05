"""Main FastAPI application with Authentication & RBAC"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from shared.config import get_settings
from shared.database import engine, Base
import logging
import os

# Import routers
from app.auth.router import router as auth_router
from product_service.routes_rbac import router as product_router
from app.shops.router import router as shops_router
from app.inventory.router import router as inventory_router
from app.orders.router import router as orders_router
from app.accounting.router import router as accounting_router
from app.ai.router import router as ai_router
from preview_router import router as preview_router
from admin_router import router as admin_router
from shop_router import router as shop_router
from shop_auth_router import router as shop_auth_router
from admin_auth_router import router as admin_auth_router
from shop_forgot_password_router import router as shop_forgot_password_router
from admin_forgot_password_router import router as admin_forgot_password_router

# For backward compatibility, also import old services if they exist
try:
    from accounting_service.routes import router as accounting_router
except ImportError:
    accounting_router = None

try:
    from inventory_service.routes import router as inventory_router
except ImportError:
    inventory_router = None

try:
    from order_service.routes import router as order_router
except ImportError:
    order_router = None

try:
    from auth_service.routes import router as old_auth_router
except ImportError:
    old_auth_router = None

# Load settings
settings = get_settings()

# Create database tables
Base.metadata.create_all(bind=engine)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle events"""
    logger.info("=" * 60)
    logger.info("🚀 SmartKirana AI Backend Starting...")
    logger.info(
        f"🔧 Environment: {'DEBUG' if settings.DEBUG else 'PRODUCTION'}")
    logger.info(f"📊 API Version: {settings.API_VERSION}")
    logger.info(f"🔐 Auth: JWT-based with Role-Based Access Control (RBAC)")
    logger.info("=" * 60)
    yield
    logger.info("🛑 SmartKirana AI Backend Shutting Down...")


# Initialize FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Open-source grocery retail platform with offline-first architecture. Features: JWT Auth, RBAC, Multi-tenancy, Inventory Management, Accounting",
    lifespan=lifespan,
    openapi_url="/api/openapi.json",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware - Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware - for authentication sessions
app.add_middleware(
    SessionMiddleware,
    secret_key="your-secret-key-change-in-production",
    max_age=86400  # 24 hours
)


# ===== REQUEST LOGGING MIDDLEWARE =====
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests"""
    logger.info(f"📨 {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(
        f"📤 {request.method} {request.url.path} → {response.status_code}")
    return response


# ===== MOUNT STATIC FILES =====
# Serve static files (CSS, JS, images) from the /static directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ===== REGISTER ROUTERS =====

# Authentication routers (NEW - Separate flows for customer and admin)
# Customer auth: /shop/login, /shop/register
app.include_router(shop_auth_router)
# Admin auth: /admin/login, /admin/register
app.include_router(admin_auth_router)
# Customer forgot password: /shop/forgot-password, /shop/verify-otp, /shop/reset-password
app.include_router(shop_forgot_password_router)
# Admin forgot password: /admin/forgot-password, /admin/verify-otp, /admin/reset-password
app.include_router(admin_forgot_password_router)

# Authentication router (legacy)
app.include_router(auth_router)

# Products router with RBAC (NEW)
app.include_router(product_router)

# Shop management router
app.include_router(shops_router)

# Inventory management router
app.include_router(inventory_router)

# Orders management router
app.include_router(orders_router)

# Accounting management router (PHASE F - Integration)
app.include_router(accounting_router)

# AI Intelligence router (STEP 5 - AI Features)
app.include_router(ai_router)

# Preview UI router (Browser-based visualization)
app.include_router(preview_router)

# Admin Dashboard router
app.include_router(admin_router)

# Customer Shop router
app.include_router(shop_router)

# Legacy routers (backward compatibility)
if accounting_router:
    app.include_router(accounting_router)

if inventory_router:
    app.include_router(inventory_router)

if order_router:
    app.include_router(order_router)

if old_auth_router:
    # Don't include old auth router if new one is already registered
    logger.warning(
        "⚠️ Old auth_service router found - using new app.auth router instead")


# ===== HEALTH CHECK =====
@app.get(
    "/api/health",
    summary="Health Check",
    description="API health status"
)
def health_check() -> dict:
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "SmartKirana AI Backend",
        "version": settings.API_VERSION,
        "auth": "JWT with RBAC"
    }


# ===== ROOT ENDPOINT =====
@app.get(
    "/",
    summary="Root Endpoint",
    description="API documentation and information"
)
def root() -> dict:
    """Root endpoint with API information"""
    return {
        "name": "SmartKirana AI",
        "version": settings.API_VERSION,
        "description": "Open-source grocery retail platform",
        "documentation": "/api/docs",
        "auth_required": True,
        "auth_scheme": "Bearer JWT",
        "endpoints": {
            "auth": "/api/v1/auth/register, /api/v1/auth/login, /api/v1/auth/me",
            "products": "/api/v1/products (with RBAC)",
            "health": "/api/health"
        }
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info"
    )
