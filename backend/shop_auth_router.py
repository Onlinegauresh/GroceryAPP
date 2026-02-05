"""Customer Authentication Router - /shop/auth routes"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.models import User, Shop, RoleEnum
from shared.auth_utils import (
    hash_password, verify_password,
    set_session_user, clear_session_user, is_customer
)
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter(prefix="/shop", tags=["Customer Auth"])

# Default shop for single-store mode
DEFAULT_SHOP_ID = 1


def ensure_default_shop(db: Session):
    """Ensure default shop exists in database"""
    try:
        # Check if shop with ID 1 exists
        shop = db.query(Shop).filter(Shop.id == DEFAULT_SHOP_ID).first()

        if not shop:
            # Create default shop if it doesn't exist
            default_shop = Shop(
                id=DEFAULT_SHOP_ID,
                name="SmartKirana",
                email="admin@smartkirana.local",
                phone="1000000000",
                address="123 Main Street",
                city="City",
                state="State",
                pincode="000000",
                country="India",
                is_active=True
            )
            db.add(default_shop)
            db.commit()
            db.refresh(default_shop)
            print(f"✓ Default shop created: ID={default_shop.id}")
            return default_shop

        print(f"✓ Default shop exists: ID={shop.id}")
        return shop
    except Exception as e:
        print(f"⚠ Error ensuring default shop: {str(e)}")
        # Try to recover by rolling back and retrying
        try:
            db.rollback()
        except:
            pass
        raise


@router.get("/login", response_class=HTMLResponse)
async def customer_login_page(request: Request):
    """Show customer login page"""
    return templates.TemplateResponse(
        "shop/login.html",
        {"request": request, "cart_count": 0}
    )


@router.post("/login", response_class=HTMLResponse)
async def customer_login(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle customer login"""
    try:
        # Ensure default shop exists
        ensure_default_shop(db)

        form_data = await request.form()
        phone = form_data.get("phone", "").strip()
        password = form_data.get("password", "").strip()

        # Validation
        if not phone or not password:
            return templates.TemplateResponse(
                "shop/login.html",
                {
                    "request": request,
                    "error": "Phone and password are required",
                    "cart_count": 0
                },
                status_code=400
            )

        # Find user by phone with CUSTOMER role
        user = db.query(User).filter(
            User.phone == phone,
            User.role == RoleEnum.CUSTOMER
        ).first()

        if not user:
            return templates.TemplateResponse(
                "shop/login.html",
                {
                    "request": request,
                    "error": "Invalid phone number or password",
                    "cart_count": 0
                },
                status_code=401
            )

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            return templates.TemplateResponse(
                "shop/login.html",
                {
                    "request": request,
                    "error": "Invalid phone number or password",
                    "cart_count": 0
                },
                status_code=401
            )

        # Set session
        set_session_user(request, user.id, "customer", user.name)

        # Redirect to shop home
        return RedirectResponse(url="/shop/", status_code=302)

    except Exception as e:
        return templates.TemplateResponse(
            "shop/login.html",
            {
                "request": request,
                "error": "An error occurred. Please try again.",
                "cart_count": 0
            },
            status_code=500
        )


@router.get("/register", response_class=HTMLResponse)
async def customer_register_page(request: Request):
    """Show customer registration page"""
    return templates.TemplateResponse(
        "shop/register_india.html",
        {"request": request, "cart_count": 0}
    )


@router.post("/register", response_class=HTMLResponse)
async def customer_register(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle customer registration - India only"""
    try:
        # Ensure default shop exists
        ensure_default_shop(db)

        form_data = await request.form()
        name = form_data.get("name", "").strip()
        phone = form_data.get("phone", "").strip()
        email = form_data.get("email", "").strip()
        state = form_data.get("state", "").strip()
        city = form_data.get("city", "").strip()
        password = form_data.get("password", "").strip()
        confirm_password = form_data.get("confirm_password", "").strip()

        # Validation - India-specific
        errors = []
        if not name:
            errors.append("नाम आवश्यक है / Name is required")

        # Validate Indian phone number (10 digits, starts with 6-9)
        if not phone:
            errors.append(
                "भारतीय मोबाइल नंबर आवश्यक है / Indian mobile number is required")
        elif not (len(phone) == 10 and phone.isdigit() and phone[0] in '6789'):
            errors.append(
                "वैध 10 अंकों का भारतीय मोबाइल नंबर दर्ज करें / Valid 10-digit Indian mobile number required (start with 6-9)")

        if not state:
            errors.append("राज्य आवश्यक है / State is required")

        if not city:
            errors.append("शहर आवश्यक है / City is required")

        if not password or len(password) < 6:
            errors.append(
                "पासवर्ड कम से कम 6 अक्षर का होना चाहिए / Password must be at least 6 characters")

        if password != confirm_password:
            errors.append(
                "पासवर्ड मेल नहीं खा रहे हैं / Passwords do not match")

        if errors:
            return templates.TemplateResponse(
                "shop/register_india.html",
                {
                    "request": request,
                    "errors": errors,
                    "cart_count": 0
                },
                status_code=400
            )

        # Check if phone already exists
        existing_user = db.query(User).filter(User.phone == phone).first()
        if existing_user:
            return templates.TemplateResponse(
                "shop/register_india.html",
                {
                    "request": request,
                    "error": "यह मोबाइल नंबर पहले से पंजीकृत है / Phone number already registered",
                    "cart_count": 0
                },
                status_code=400
            )

        # Create new customer
        new_user = User(
            shop_id=DEFAULT_SHOP_ID,
            phone=phone,
            email=email if email else None,
            name=name,
            role=RoleEnum.CUSTOMER,  # Auto-set to CUSTOMER
            city=city,  # Store city for India
            address=state,  # Store state (can be extended)
            password_hash=hash_password(password)
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(
            f"✓ Indian Customer registered: {new_user.id} - {new_user.phone} ({city}, {state})")

        # Auto-login after registration
        set_session_user(request, new_user.id, "customer", new_user.name)

        # Redirect to shop home
        return RedirectResponse(url="/shop/", status_code=302)

    except Exception as e:
        print(f"✗ Customer registration error: {str(e)}")
        return templates.TemplateResponse(
            "shop/register_india.html",
            {
                "request": request,
                "error": "एक त्रुटि हुई। कृपया फिर से प्रयास करें / An error occurred. Please try again.",
                "cart_count": 0
            },
            status_code=500
        )


@router.get("/logout")
async def customer_logout(request: Request):
    """Handle customer logout"""
    clear_session_user(request)
    return RedirectResponse(url="/shop/", status_code=302)
