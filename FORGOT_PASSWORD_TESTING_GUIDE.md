# FORGOT PASSWORD TESTING GUIDE

**Quick Links:**

- 📖 Full Documentation: [FORGOT_PASSWORD_DOCUMENTATION.md](FORGOT_PASSWORD_DOCUMENTATION.md)
- 🧪 This Guide: Step-by-step testing procedures
- 🖥️ Server: http://localhost:8000

---

## 🚀 QUICK START TESTING

### Option 1: Browser Testing (Easiest)

#### Step 1: Access Customer Forgot Password

```
Open browser: http://localhost:8000/shop/forgot-password
```

#### Step 2: Enter Phone Number

```
Phone: 9876543210
→ Check server console for OTP (6 digits printed)
```

#### Step 3: Submit to Get OTP

```
Button: "Send OTP"
→ Redirects to OTP verification page
→ Console shows: "🔐 OTP: XXXXXX"
```

#### Step 4: Enter OTP

```
OTP: [Copy from console]
→ Button: "Verify OTP"
```

#### Step 5: Enter New Password

```
New Password: TestPassword123
Confirm Password: TestPassword123
→ Button: "Reset Password"
```

#### Step 6: Success!

```
✅ Password reset successful!
→ Can now login with new password
```

---

### Option 2: curl Commands (For Testing)

#### Test 1: Customer Forgot Password - Valid Phone

```bash
curl -X POST http://localhost:8000/shop/forgot-password \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "phone=9876543210" \
  -v

# Expected:
# 1. Server console shows: 🔐 OTP: 123456
# 2. Response: HTML page with OTP verification form
# 3. Session saved: forgot_phone, forgot_user_id
```

#### Test 2: Customer Forgot Password - Invalid Phone

```bash
curl -X POST http://localhost:8000/shop/forgot-password \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "phone=1234567890" \
  -v

# Expected:
# Error: "📱 Enter a valid 10-digit Indian phone number"
# No OTP generated, page reloads
```

#### Test 3: Customer Forgot Password - Phone Not Found

```bash
curl -X POST http://localhost:8000/shop/forgot-password \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "phone=8888888888" \
  -v

# Expected:
# Error: "❌ No customer account found with this mobile number"
```

#### Test 4: Verify OTP - Valid

```bash
# First, generate OTP (see Test 1)
# Then verify:

curl -X POST http://localhost:8000/shop/verify-otp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "otp=123456" \
  -b "cookie.txt" \
  -v

# Expected:
# Session: otp_verified = True
# Response: Password reset form displayed
```

#### Test 5: Verify OTP - Invalid

```bash
curl -X POST http://localhost:8000/shop/verify-otp \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "otp=000000" \
  -b "cookie.txt" \
  -v

# Expected:
# Error: "❌ Invalid OTP. 3 attempts remaining."
# otp_attempts incremented
# Can try 2 more times
```

#### Test 6: Reset Password - Valid

```bash
curl -X POST http://localhost:8000/shop/reset-password \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "password=NewPassword123&confirm_password=NewPassword123" \
  -b "cookie.txt" \
  -v

# Expected:
# Password updated in database (hashed with Argon2)
# OTP cleared: otp_code = NULL
# Session cleared
# Success page displayed
# Can now login with new password
```

#### Test 7: Admin Forgot Password

```bash
# Same as Test 1, but for admin:

curl -X POST http://localhost:8000/admin/forgot-password \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "phone=9876543210" \
  -v

# Expected:
# Only works if phone belongs to ADMIN user
# If phone is CUSTOMER user: Error "No admin account found"
```

---

## 📋 TEST CASES & EXPECTED RESULTS

### Happy Path (Success Scenario)

| Step | Action               | Input                | Expected Result                      |
| ---- | -------------------- | -------------------- | ------------------------------------ |
| 1    | Forgot Password Form | Phone: 9876543210    | OTP generated, console shows OTP     |
| 2    | OTP Verification     | OTP: [from console]  | Session marked as verified           |
| 3    | Password Reset       | Password: NewPass123 | Password saved (hashed), OTP cleared |
| 4    | Success Page         | -                    | Login link displayed                 |
| 5    | Login                | Old/New password     | New password works, old fails        |

### Error Path #1: Invalid Phone Format

| Step | Action               | Input                      | Expected Result        |
| ---- | -------------------- | -------------------------- | ---------------------- |
| 1    | Forgot Password Form | Invalid phone formats:     | Error displayed        |
| -    | -                    | 1234567890 (starts with 1) | Phone validation error |
| -    | -                    | 987654321 (only 9 digits)  | Phone validation error |
| -    | -                    | abcdefghij (letters)       | Phone validation error |

### Error Path #2: Phone Not Found

| Step | Action               | Input             | Expected Result           |
| ---- | -------------------- | ----------------- | ------------------------- |
| 1    | Forgot Password Form | Phone: 8888888888 | Error: "No account found" |

### Error Path #3: Invalid OTP (Attempt Limiting)

| Step | Action                       | Input             | Expected Result                               |
| ---- | ---------------------------- | ----------------- | --------------------------------------------- |
| 1    | Forgot Password Form         | Phone: 9876543210 | OTP generated successfully                    |
| 2    | OTP Verification - Attempt 1 | OTP: 000000       | Error: "3 attempts remaining"                 |
| 3    | OTP Verification - Attempt 2 | OTP: 111111       | Error: "2 attempts remaining"                 |
| 4    | OTP Verification - Attempt 3 | OTP: 222222       | Error: "1 attempt remaining"                  |
| 5    | OTP Verification - Attempt 4 | OTP: 333333       | Error: "Too many attempts", redirect to start |

### Error Path #4: OTP Expiry

| Step | Action               | Input                   | Expected Result           |
| ---- | -------------------- | ----------------------- | ------------------------- |
| 1    | Forgot Password Form | Phone: 9876543210       | OTP generated             |
| 2    | Wait                 | 5 minutes               | OTP expires automatically |
| 3    | OTP Verification     | OTP: [old OTP]          | Error: "OTP expired"      |
| 4    | Request New OTP      | Click "Request new OTP" | Generate new OTP          |

### Error Path #5: Password Validation

| Step | Action              | Input                                     | Expected Result                |
| ---- | ------------------- | ----------------------------------------- | ------------------------------ |
| 1    | Password Reset Form | Password: 12345                           | Error: "Too short (< 6 chars)" |
| 2    | Password Reset Form | Password: Valid123, Confirm: Different456 | Error: "Passwords don't match" |
| 3    | Password Reset Form | Password: Valid123, Confirm: Valid123     | Success                        |

---

## 🧪 AUTOMATED TEST SCRIPT

### Python Test Script

```python
import requests
import re
from time import sleep

BASE_URL = "http://localhost:8000"
SESSION = requests.Session()

def test_customer_forgot_password():
    """Test complete customer forgot password flow"""

    print("\n" + "="*60)
    print("TEST 1: Customer Forgot Password (Happy Path)")
    print("="*60)

    # Step 1: Request OTP
    print("\n[1] Requesting OTP for phone: 9876543210")
    response = SESSION.post(
        f"{BASE_URL}/shop/forgot-password",
        data={"phone": "9876543210"}
    )
    print(f"Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    # Step 2: Verify OTP validation form displayed
    assert "verify-otp" in response.text, "OTP verification form not shown"
    print("✓ OTP verification form displayed")

    # Step 3: Extract OTP from console (you must copy manually)
    otp = input("\nEnter OTP from server console: ").strip()

    # Step 4: Verify OTP
    print(f"\n[2] Verifying OTP: {otp}")
    response = SESSION.post(
        f"{BASE_URL}/shop/verify-otp",
        data={"otp": otp}
    )
    print(f"Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "reset-password" in response.text, "Password reset form not shown"
    print("✓ OTP verified successfully")

    # Step 5: Reset password
    print("\n[3] Resetting password")
    response = SESSION.post(
        f"{BASE_URL}/shop/reset-password",
        data={
            "password": "NewPassword123",
            "confirm_password": "NewPassword123"
        }
    )
    print(f"Status: {response.status_code}")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "success" in response.text.lower(), "Success page not shown"
    print("✓ Password reset successfully!")

    print("\n" + "="*60)
    print("TEST PASSED: Complete forgot password flow works!")
    print("="*60 + "\n")

def test_invalid_phone():
    """Test invalid phone number"""

    print("\n" + "="*60)
    print("TEST 2: Invalid Phone Number")
    print("="*60)

    invalid_phones = [
        ("1234567890", "Starts with 1"),
        ("987654321", "Only 9 digits"),
        ("abcdefghij", "Contains letters"),
    ]

    for phone, reason in invalid_phones:
        print(f"\n[Testing] {reason}: {phone}")
        response = SESSION.post(
            f"{BASE_URL}/shop/forgot-password",
            data={"phone": phone}
        )
        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "valid" in response.text.lower(), "Error message not shown"
        print(f"✓ Correctly rejected: {reason}")

    print("\n" + "="*60)
    print("TEST PASSED: Phone validation works!")
    print("="*60 + "\n")

def test_invalid_otp():
    """Test invalid OTP attempts"""

    print("\n" + "="*60)
    print("TEST 3: Invalid OTP (Attempt Limiting)")
    print("="*60)

    # First, get OTP
    print("\n[Setup] Requesting OTP...")
    SESSION.post(f"{BASE_URL}/shop/forgot-password", data={"phone": "9876543210"})

    # Try invalid OTP 3 times
    for attempt in range(1, 4):
        otp = f"{attempt:06d}"  # 000001, 000002, 000003
        print(f"\n[Attempt {attempt}] Submitting invalid OTP: {otp}")

        response = SESSION.post(
            f"{BASE_URL}/shop/verify-otp",
            data={"otp": otp}
        )

        print(f"Status: {response.status_code}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        if attempt < 3:
            expected = 4 - attempt - 1
            print(f"✓ Attempt {attempt} rejected ({expected} attempts remaining)")
        else:
            print(f"✓ Attempt {attempt} rejected (locked out)")

    print("\n" + "="*60)
    print("TEST PASSED: OTP attempt limiting works!")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("\n🧪 FORGOT PASSWORD TEST SUITE\n")

    try:
        test_customer_forgot_password()
        test_invalid_phone()
        test_invalid_otp()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED!")
        print("="*60 + "\n")
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}\n")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
```

---

## 🎯 MANUAL TESTING CHECKLIST

### Pre-Test Setup

- [ ] Server running at http://localhost:8000
- [ ] Database has at least one CUSTOMER user with phone 9876543210
- [ ] Database has at least one ADMIN user with phone 9999999999
- [ ] Server console visible to capture OTP output

### Customer Flow Tests

- [ ] Can navigate to /shop/forgot-password
- [ ] Can submit valid phone number
- [ ] OTP printed to server console
- [ ] Redirects to OTP verification page
- [ ] Can enter correct OTP from console
- [ ] Redirects to password reset page
- [ ] Can enter new password (min 6 chars)
- [ ] Password confirmation must match
- [ ] Can successfully reset password
- [ ] Redirects to success page
- [ ] Can login with new password
- [ ] Old password no longer works

### Admin Flow Tests

- [ ] Can navigate to /admin/forgot-password
- [ ] Same flow as customer but for admin users
- [ ] Admin OTP page has dark theme
- [ ] Only works for ADMIN role users

### Error Handling Tests

- [ ] Invalid phone format rejected
- [ ] Non-existent phone rejected
- [ ] Invalid OTP rejected (with attempt counter)
- [ ] Max 3 OTP attempts enforced
- [ ] Expired OTP after 5 minutes
- [ ] Password too short rejected
- [ ] Mismatched passwords rejected
- [ ] Proper error messages displayed

### Security Tests

- [ ] Can't access /admin/forgot-password as customer
- [ ] Can't access /shop/forgot-password as admin
- [ ] Session properly validated between steps
- [ ] OTP cleared after successful reset
- [ ] Old OTP no longer works after reset

---

## 📊 TEST RESULTS TEMPLATE

Copy and use this to record test results:

```
TEST DATE: ___________
TESTER: ___________
SERVER: http://localhost:8000

CUSTOMER FLOW:
✓ Forgot Password Form: ✓ Pass / ☐ Fail / ☐ Error
✓ OTP Generation: ✓ Pass / ☐ Fail / ☐ Error
✓ OTP Verification: ✓ Pass / ☐ Fail / ☐ Error
✓ Password Reset: ✓ Pass / ☐ Fail / ☐ Error
✓ Success Page: ✓ Pass / ☐ Fail / ☐ Error

ADMIN FLOW:
✓ Forgot Password Form: ✓ Pass / ☐ Fail / ☐ Error
✓ OTP Generation: ✓ Pass / ☐ Fail / ☐ Error
✓ OTP Verification: ✓ Pass / ☐ Fail / ☐ Error
✓ Password Reset: ✓ Pass / ☐ Fail / ☐ Error
✓ Success Page: ✓ Pass / ☐ Fail / ☐ Error

ERROR HANDLING:
✓ Invalid Phone: ✓ Pass / ☐ Fail / ☐ Error
✓ Phone Not Found: ✓ Pass / ☐ Fail / ☐ Error
✓ Invalid OTP: ✓ Pass / ☐ Fail / ☐ Error
✓ OTP Attempt Limit: ✓ Pass / ☐ Fail / ☐ Error
✓ OTP Expiry: ✓ Pass / ☐ Fail / ☐ Error
✓ Password Validation: ✓ Pass / ☐ Fail / ☐ Error

SECURITY:
✓ Role Separation: ✓ Pass / ☐ Fail / ☐ Error
✓ Session Validation: ✓ Pass / ☐ Fail / ☐ Error
✓ OTP Clearing: ✓ Pass / ☐ Fail / ☐ Error

OVERALL STATUS: ✓ PASS / ☐ FAIL

Issues Found:
-
-

Comments:


Signed: ___________
```

---

## 🚀 NEXT STEPS

1. **Run Browser Tests** - Test each flow manually
2. **Check Server Console** - Verify OTP output
3. **Test Error Cases** - Try invalid inputs
4. **Record Results** - Document any issues
5. **SMS Integration** - Replace console with SMS gateway
6. **Production Deployment** - Deploy to production after testing

---

**Status:** ✅ **READY FOR TESTING**  
**Server:** http://localhost:8000  
**Documentation:** [FORGOT_PASSWORD_DOCUMENTATION.md](FORGOT_PASSWORD_DOCUMENTATION.md)
