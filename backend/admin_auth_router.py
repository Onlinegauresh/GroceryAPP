"""Admin Authentication Router - /admin/auth routes"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.models import User, Shop, RoleEnum
from shared.auth_utils import (
    hash_password, verify_password,
    set_session_user, clear_session_user, is_admin
)
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter(prefix="/admin", tags=["Admin Auth"])

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
async def admin_login_page(request: Request):
    """Show admin login page"""
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request, "cart_count": 0}
    )


@router.post("/login", response_class=HTMLResponse)
async def admin_login(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle admin login"""
    try:
        # Ensure default shop exists
        ensure_default_shop(db)

        form_data = await request.form()
        phone = form_data.get("phone", "").strip()
        password = form_data.get("password", "").strip()

        # Validation
        if not phone or not password:
            return templates.TemplateResponse(
                "admin/login.html",
                {
                    "request": request,
                    "error": "Phone and password are required",
                    "cart_count": 0
                },
                status_code=400
            )

        # Find user by phone with ADMIN role ONLY
        user = db.query(User).filter(
            User.phone == phone,
            User.role == RoleEnum.ADMIN
        ).first()

        if not user:
            return templates.TemplateResponse(
                "admin/login.html",
                {
                    "request": request,
                    "error": "Invalid admin credentials",
                    "cart_count": 0
                },
                status_code=401
            )

        # Verify password
        if not user.password_hash or not verify_password(password, user.password_hash):
            return templates.TemplateResponse(
                "admin/login.html",
                {
                    "request": request,
                    "error": "Invalid admin credentials",
                    "cart_count": 0
                },
                status_code=401
            )

        # Set session
        set_session_user(request, user.id, "admin", user.name)

        # Redirect to admin dashboard
        return RedirectResponse(url="/admin/", status_code=302)

    except Exception as e:
        return templates.TemplateResponse(
            "admin/login.html",
            {
                "request": request,
                "error": "An error occurred. Please try again.",
                "cart_count": 0
            },
            status_code=500
        )


@router.get("/register", response_class=HTMLResponse)
async def admin_register_page(request: Request):
    """Show admin registration page (restricted)"""
    return templates.TemplateResponse(
        "admin/register_india.html",
        {"request": request, "cart_count": 0}
    )


@router.post("/register", response_class=HTMLResponse)
async def admin_register(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle shopkeeper registration - India only"""
    try:
        # Ensure default shop exists
        ensure_default_shop(db)

        form_data = await request.form()
        name = form_data.get("name", "").strip()
        phone = form_data.get("phone", "").strip()
        email = form_data.get("email", "").strip()
        state = form_data.get("state", "").strip()
        city = form_data.get("city", "").strip()
        pincode = form_data.get("pincode", "").strip()
        gst = form_data.get("gst", "").strip().upper()
        pan = form_data.get("pan", "").strip().upper()
        shop_name = form_data.get("shop_name", "").strip()
        address = form_data.get("address", "").strip()
        password = form_data.get("password", "").strip()
        confirm_password = form_data.get("confirm_password", "").strip()
        admin_code = form_data.get("admin_code", "").strip()

        # Validation
        errors = []
        if not name:
            errors.append(
                "दुकानदार का नाम आवश्यक है / Shopkeeper name is required")

        # Validate Indian phone number (10 digits, starts with 6-9)
        if not phone:
            errors.append(
                "भारतीय मोबाइल नंबर आवश्यक है / Indian mobile number is required")
        elif not (len(phone) == 10 and phone.isdigit() and phone[0] in '6789'):
            errors.append(
                "वैध 10 अंकों का भारतीय मोबाइल नंबर दर्ज करें / Valid 10-digit Indian mobile required")

        if not state:
            errors.append("राज्य आवश्यक है / State is required")

        if not city:
            errors.append("शहर आवश्यक है / City is required")

        if not pincode:
            errors.append("पिनकोड आवश्यक है / Pincode is required")
        elif not (len(pincode) == 6 and pincode.isdigit()):
            errors.append(
                "वैध 6 अंकों का भारतीय पिनकोड दर्ज करें / Valid 6-digit pincode required")

        # GST Validation (15 characters)
        if not gst:
            errors.append("GST नंबर आवश्यक है / GST number is required")
        elif len(gst) != 15:
            errors.append(
                "GST नंबर 15 अक्षरों का होना चाहिए / GST must be 15 characters")
        elif not gst[0:2].isdigit() or not gst[2].isalpha() or not gst[3:8].isdigit():
            errors.append("वैध GST फॉर्मेट दर्ज करें / Invalid GST format")

        # PAN Validation (10 characters)
        if not pan:
            errors.append("PAN आवश्यक है / PAN is required")
        elif len(pan) != 10:
            errors.append(
                "PAN 10 अक्षरों का होना चाहिए / PAN must be 10 characters")
        elif not (pan[0:5].isalpha() and pan[5:9].isdigit() and pan[9].isalpha()):
            errors.append(
                "वैध PAN फॉर्मेट दर्ज करें / Invalid PAN format (AAAAA0000A)")

        if not shop_name:
            errors.append("दुकान का नाम आवश्यक है / Shop name is required")

        if not password or len(password) < 6:
            errors.append(
                "पासवर्ड कम से कम 6 अक्षर का होना चाहिए / Password must be at least 6 characters")

        if password != confirm_password:
            errors.append(
                "पासवर्ड मेल नहीं खा रहे हैं / Passwords do not match")

        # Admin code validation
        if not admin_code or admin_code != "ADMIN123":
            errors.append("अधिकृत कोड गलत है / Invalid authorization code")

        if errors:
            return templates.TemplateResponse(
                "admin/register_india.html",
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
                "admin/register_india.html",
                {
                    "request": request,
                    "error": "यह मोबाइल नंबर पहले से पंजीकृत है / Phone number already registered",
                    "cart_count": 0
                },
                status_code=400
            )

        # Create new shopkeeper/admin
        new_admin = User(
            shop_id=DEFAULT_SHOP_ID,
            phone=phone,
            email=email if email else None,
            name=name,
            role=RoleEnum.ADMIN,  # Set role to ADMIN (shopkeeper)
            address=f"{address} {city} {state} {pincode}" if address else f"{city}, {state} {pincode}",
            city=city,
            password_hash=hash_password(password)
        )

        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)

        print(
            f"✓ Indian Shopkeeper registered: {new_admin.id} - {new_admin.phone}")
        print(f"  Shop: {shop_name}")
        print(f"  GST: {gst}")
        print(f"  PAN: {pan}")
        print(f"  Location: {city}, {state}")

        # Auto-login after registration
        set_session_user(request, new_admin.id, "admin", new_admin.name)

        # Redirect to admin dashboard
        return RedirectResponse(url="/admin/", status_code=302)

    except Exception as e:
        print(f"✗ Shopkeeper registration error: {str(e)}")
        return templates.TemplateResponse(
            "admin/register_india.html",
            {
                "request": request,
                "error": "एक त्रुटि हुई। कृपया फिर से प्रयास करें / An error occurred. Please try again.",
                "cart_count": 0
            },
            status_code=500
        )


@router.get("/logout")
async def admin_logout(request: Request):
    """Handle admin logout"""
    clear_session_user(request)
    return RedirectResponse(url="/admin/login", status_code=302)
