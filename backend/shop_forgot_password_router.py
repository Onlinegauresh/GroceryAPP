"""Customer Forgot Password Router - /shop/forgot-password routes"""
from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from shared.database import get_db
from shared.models import User, Shop, RoleEnum
from shared.auth_utils import hash_password
from datetime import datetime, timedelta
import random
import os

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=TEMPLATE_DIR)

router = APIRouter(prefix="/shop", tags=["Customer Password Recovery"])

DEFAULT_SHOP_ID = 1
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3


def generate_otp() -> str:
    """Generate a 6-digit OTP"""
    return str(random.randint(100000, 999999))


def is_indian_phone(phone: str) -> bool:
    """Validate Indian phone number format (10 digits, starts with 6-9)"""
    phone = phone.strip()
    if len(phone) != 10 or not phone.isdigit():
        return False
    if phone[0] not in ['6', '7', '8', '9']:
        return False
    return True


# ===== FORGOT PASSWORD PAGE =====
@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    """Show forgot password form - mobile number input"""
    return templates.TemplateResponse(
        "shop/forgot_password.html",
        {"request": request, "cart_count": 0, "error": None}
    )


@router.post("/forgot-password", response_class=HTMLResponse)
async def forgot_password_submit(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle forgot password submission - validate mobile and generate OTP"""
    try:
        form_data = await request.form()
        phone = form_data.get("phone", "").strip()
        error = None

        # Validate phone format
        if not phone:
            error = "📱 Mobile number is required"
            return templates.TemplateResponse(
                "shop/forgot_password.html",
                {"request": request, "cart_count": 0, "error": error},
                status_code=400
            )

        if not is_indian_phone(phone):
            error = "📱 Enter a valid 10-digit Indian phone number (6-9)"
            return templates.TemplateResponse(
                "shop/forgot_password.html",
                {"request": request, "cart_count": 0, "error": error},
                status_code=400
            )

        # Find user with this phone number and CUSTOMER role
        user = db.query(User).filter(
            User.shop_id == DEFAULT_SHOP_ID,
            User.phone == phone,
            User.role == RoleEnum.CUSTOMER
        ).first()

        if not user:
            error = "❌ No customer account found with this mobile number"
            return templates.TemplateResponse(
                "shop/forgot_password.html",
                {"request": request, "cart_count": 0, "error": error},
                status_code=404
            )

        # Generate OTP
        otp = generate_otp()
        expiry = datetime.utcnow() + timedelta(minutes=OTP_EXPIRY_MINUTES)

        # Save OTP to user record
        user.otp_code = otp
        user.otp_expiry = expiry
        user.otp_attempts = 0
        db.commit()

        # DEV MODE: Print OTP to console
        # IMPORTANT: Replace with SMS gateway in production
        print("\n" + "=" * 60)
        print("📱 FORGOT PASSWORD - OTP GENERATED (DEV MODE)")
        print("=" * 60)
        print(f"📞 Phone: {phone}")
        print(f"🔐 OTP: {otp}")
        print(f"⏰ Expires: {expiry.strftime('%Y-%m-%d %H:%M:%S')} (5 minutes)")
        print("=" * 60 + "\n")
        print("⚠️  PRODUCTION: Replace console output with SMS gateway (Twilio, AWS SNS, etc.)")
        print("=" * 60 + "\n")

        # Store phone in session for next step
        request.session["forgot_phone"] = phone
        request.session["forgot_user_id"] = user.id

        return templates.TemplateResponse(
            "shop/verify_otp.html",
            {
                "request": request,
                "cart_count": 0,
                "phone": phone,
                "message": f"✅ OTP sent to {phone}. Valid for 5 minutes.",
                "error": None
            }
        )

    except Exception as e:
        print(f"❌ Error in forgot_password_submit: {str(e)}")
        error = f"An error occurred: {str(e)}"
        return templates.TemplateResponse(
            "shop/forgot_password.html",
            {"request": request, "cart_count": 0, "error": error},
            status_code=500
        )


# ===== VERIFY OTP PAGE =====
@router.get("/verify-otp", response_class=HTMLResponse)
async def verify_otp_page(request: Request):
    """Show OTP verification form"""
    phone = request.session.get("forgot_phone")
    if not phone:
        return RedirectResponse(url="/shop/forgot-password", status_code=302)

    return templates.TemplateResponse(
        "shop/verify_otp.html",
        {
            "request": request,
            "cart_count": 0,
            "phone": phone,
            "message": f"✅ OTP sent to {phone}. Valid for 5 minutes.",
            "error": None
        }
    )


@router.post("/verify-otp", response_class=HTMLResponse)
async def verify_otp_submit(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle OTP verification"""
    try:
        form_data = await request.form()
        otp = form_data.get("otp", "").strip()
        phone = request.session.get("forgot_phone")
        user_id = request.session.get("forgot_user_id")

        error = None

        # Validate session data
        if not phone or not user_id:
            error = "❌ Session expired. Start over."
            return RedirectResponse(url="/shop/forgot-password", status_code=302)

        # Validate OTP format
        if not otp or not otp.isdigit() or len(otp) != 6:
            error = "🔐 OTP must be 6 digits"
            return templates.TemplateResponse(
                "shop/verify_otp.html",
                {
                    "request": request,
                    "cart_count": 0,
                    "phone": phone,
                    "message": f"Enter the OTP sent to {phone}",
                    "error": error
                },
                status_code=400
            )

        # Fetch user
        user = db.query(User).filter(
            User.id == user_id,
            User.shop_id == DEFAULT_SHOP_ID,
            User.role == RoleEnum.CUSTOMER
        ).first()

        if not user:
            error = "❌ Invalid session. Please try again."
            return RedirectResponse(url="/shop/forgot-password", status_code=302)

        # Check if OTP exists and is not expired
        if not user.otp_code or not user.otp_expiry:
            error = "❌ No OTP found. Request a new one."
            return templates.TemplateResponse(
                "shop/verify_otp.html",
                {
                    "request": request,
                    "cart_count": 0,
                    "phone": phone,
                    "message": f"Enter the OTP sent to {phone}",
                    "error": error
                },
                status_code=400
            )

        # Check OTP expiry
        if datetime.utcnow() > user.otp_expiry:
            error = "⏰ OTP expired. Request a new one."
            user.otp_code = None
            user.otp_expiry = None
            user.otp_attempts = 0
            db.commit()
            return templates.TemplateResponse(
                "shop/verify_otp.html",
                {
                    "request": request,
                    "cart_count": 0,
                    "phone": phone,
                    "message": f"Enter the OTP sent to {phone}",
                    "error": error
                },
                status_code=400
            )

        # Check OTP attempts
        if user.otp_attempts >= OTP_MAX_ATTEMPTS:
            error = f"❌ Too many failed attempts. Request a new OTP."
            user.otp_code = None
            user.otp_expiry = None
            user.otp_attempts = 0
            db.commit()
            return RedirectResponse(url="/shop/forgot-password", status_code=302)

        # Verify OTP
        if user.otp_code != otp:
            user.otp_attempts += 1
            db.commit()
            remaining = OTP_MAX_ATTEMPTS - user.otp_attempts
            error = f"❌ Invalid OTP. {remaining} attempt{'s' if remaining != 1 else ''} remaining."
            return templates.TemplateResponse(
                "shop/verify_otp.html",
                {
                    "request": request,
                    "cart_count": 0,
                    "phone": phone,
                    "message": f"Enter the OTP sent to {phone}",
                    "error": error
                },
                status_code=400
            )

        # OTP verified! Move to reset password
        request.session["otp_verified"] = True
        print(f"✓ OTP verified for customer {phone}")

        return templates.TemplateResponse(
            "shop/reset_password.html",
            {
                "request": request,
                "cart_count": 0,
                "phone": phone,
                "error": None,
                "message": "✅ OTP verified. Enter your new password."
            }
        )

    except Exception as e:
        print(f"❌ Error in verify_otp_submit: {str(e)}")
        error = f"An error occurred: {str(e)}"
        phone = request.session.get("forgot_phone")
        return templates.TemplateResponse(
            "shop/verify_otp.html",
            {
                "request": request,
                "cart_count": 0,
                "phone": phone,
                "message": f"Enter the OTP sent to {phone}",
                "error": error
            },
            status_code=500
        )


# ===== RESET PASSWORD PAGE =====
@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    """Show reset password form"""
    if not request.session.get("otp_verified"):
        return RedirectResponse(url="/shop/forgot-password", status_code=302)

    phone = request.session.get("forgot_phone")
    return templates.TemplateResponse(
        "shop/reset_password.html",
        {
            "request": request,
            "cart_count": 0,
            "phone": phone,
            "error": None,
            "message": "Enter your new password (minimum 6 characters)"
        }
    )


@router.post("/reset-password", response_class=HTMLResponse)
async def reset_password_submit(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle password reset"""
    try:
        form_data = await request.form()
        password = form_data.get("password", "").strip()
        confirm_password = form_data.get("confirm_password", "").strip()
        user_id = request.session.get("forgot_user_id")
        phone = request.session.get("forgot_phone")

        error = None

        # Validate session
        if not request.session.get("otp_verified") or not user_id:
            error = "❌ Session expired. Start over."
            return RedirectResponse(url="/shop/forgot-password", status_code=302)

        # Validate password
        if not password:
            error = "🔐 Password is required"
            return templates.TemplateResponse(
                "shop/reset_password.html",
                {
                    "request": request,
                    "cart_count": 0,
                    "phone": phone,
                    "error": error,
                    "message": "Enter your new password"
                },
                status_code=400
            )

        if len(password) < 6:
            error = "🔐 Password must be at least 6 characters"
            return templates.TemplateResponse(
                "shop/reset_password.html",
                {
                    "request": request,
                    "cart_count": 0,
                    "phone": phone,
                    "error": error,
                    "message": "Enter your new password"
                },
                status_code=400
            )

        if password != confirm_password:
            error = "🔐 Passwords do not match"
            return templates.TemplateResponse(
                "shop/reset_password.html",
                {
                    "request": request,
                    "cart_count": 0,
                    "phone": phone,
                    "error": error,
                    "message": "Enter your new password"
                },
                status_code=400
            )

        # Update password
        user = db.query(User).filter(
            User.id == user_id,
            User.shop_id == DEFAULT_SHOP_ID,
            User.role == RoleEnum.CUSTOMER
        ).first()

        if not user:
            error = "❌ User not found"
            return RedirectResponse(url="/shop/forgot-password", status_code=302)

        # Hash and save new password
        user.password_hash = hash_password(password)
        user.otp_code = None
        user.otp_expiry = None
        user.otp_attempts = 0
        db.commit()

        # Clear session
        request.session["forgot_phone"] = None
        request.session["forgot_user_id"] = None
        request.session["otp_verified"] = None

        print(f"✓ Password reset successfully for customer {phone}")

        return templates.TemplateResponse(
            "shop/password_reset_success.html",
            {
                "request": request,
                "cart_count": 0,
                "phone": phone
            }
        )

    except Exception as e:
        print(f"❌ Error in reset_password_submit: {str(e)}")
        error = f"An error occurred: {str(e)}"
        phone = request.session.get("forgot_phone")
        return templates.TemplateResponse(
            "shop/reset_password.html",
            {
                "request": request,
                "cart_count": 0,
                "phone": phone,
                "error": error,
                "message": "Enter your new password"
            },
            status_code=500
        )
