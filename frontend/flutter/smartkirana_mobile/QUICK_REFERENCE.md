# SmartKirana Mobile App - Quick Reference Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites Check

```bash
# Verify Flutter is installed
flutter --version

# Verify Dart is installed
dart --version

# Check device/emulator
flutter devices
```

### Installation (First Time Only)

```bash
cd frontend/flutter/smartkirana_mobile
flutter pub get
```

### Run App

```bash
flutter run
```

---

## 📱 Common Commands

### Development

```bash
# Run on specific device
flutter run -d <device_id>

# Debug mode with logging
flutter run --verbose

# Hot reload during development
r (in terminal)

# Full restart
R (in terminal)

# Exit app
q (in terminal)
```

### Testing

```bash
# Run unit tests
flutter test

# Run integration tests
flutter drive --target=test_driver/app.dart
```

### Building

```bash
# Debug APK (Android)
flutter build apk --debug

# Release APK (Android)
flutter build apk --release

# Release App Bundle (Google Play)
flutter build appbundle --release

# Release IPA (iOS)
flutter build ios --release
```

### Cleaning

```bash
# Remove build artifacts
flutter clean

# Update dependencies
flutter pub get

# Update packages
flutter pub upgrade
```

---

## 🗂️ File Locations

### Core Files

| Feature      | File                        |
| ------------ | --------------------------- |
| Entry Point  | `lib/main.dart`             |
| Theme System | `lib/core/theme.dart`       |
| HTTP Client  | `lib/core/api_service.dart` |
| Navigation   | `lib/core/router.dart`      |

### Authentication

| Feature  | File                                    |
| -------- | --------------------------------------- |
| Models   | `lib/auth/models/auth_models.dart`      |
| Service  | `lib/auth/services/auth_service.dart`   |
| Provider | `lib/auth/providers/auth_provider.dart` |
| Login    | `lib/auth/screens/login_screen.dart`    |
| Signup   | `lib/auth/screens/signup_screen.dart`   |

### Features

| Feature  | Service                                      | Screen                                      |
| -------- | -------------------------------------------- | ------------------------------------------- |
| Products | `lib/products/services/product_service.dart` | `lib/products/screens/products_screen.dart` |
| Cart     | `lib/cart/providers/cart_provider.dart`      | `lib/cart/screens/cart_screen.dart`         |
| Orders   | `lib/orders/services/order_service.dart`     | `lib/orders/screens/orders_screen.dart`     |
| Profile  | -                                            | `lib/profile/screens/profile_screen.dart`   |
| AI       | -                                            | `lib/ai/screens/ai_insights_screen.dart`    |
| Home     | -                                            | `lib/home/screens/home_screen.dart`         |

---

## 🔗 API Base URL

### Configuration

```dart
// File: lib/core/api_service.dart
static const String _baseUrl = 'http://localhost:8000/api/v1';

// For physical device, use:
static const String _baseUrl = 'http://<YOUR_IP>:8000/api/v1';
```

---

## 🔐 Test Credentials

Use these to test the app (when backend has sample data):

```
Email: customer@example.com
Password: Password123!

OR

Email: test@smartkirana.com
Password: TestPassword123!
```

---

## 🎨 Colors Reference

| Color        | Hex     | Usage             |
| ------------ | ------- | ----------------- |
| Primary      | #2ECC71 | Main brand color  |
| Primary Dark | #27AE60 | Darker shade      |
| Secondary    | #3498DB | Secondary actions |
| Success      | #2ECC71 | Positive states   |
| Warning      | #F39C12 | Warning messages  |
| Error        | #E74C3C | Error messages    |
| Info         | #3498DB | Info messages     |

---

## 📝 Form Fields

### Login Form

- **Email**: Required, valid email format
- **Password**: Required, minimum 8 characters
- **Remember Me**: Optional checkbox

### Signup Form

- **Full Name**: Required, 3+ characters
- **Email**: Required, valid email format
- **Phone**: Optional
- **Password**: Required, 8+ chars, uppercase, lowercase, number
- **Confirm Password**: Must match password
- **Terms**: Must be accepted

### Cart Form

- **Full Name**: Required
- **Delivery Address**: Required, 10+ characters
- **Payment Method**: COD (Cash on Delivery)
- **Terms**: Must be accepted

---

## 🛣️ Navigation Routes

| Route          | Screen      | Auth Required |
| -------------- | ----------- | ------------- |
| `/login`       | Login       | ❌ No         |
| `/signup`      | Signup      | ❌ No         |
| `/`            | Home        | ✅ Yes        |
| `/products`    | Products    | ✅ Yes        |
| `/cart`        | Cart        | ✅ Yes        |
| `/orders`      | Orders      | ✅ Yes        |
| `/profile`     | Profile     | ✅ Yes        |
| `/ai-insights` | AI Insights | ✅ Yes        |

---

## 🔄 API Endpoints Quick Reference

### Authentication

```
POST   /auth/register              # Sign up
POST   /auth/login                 # Sign in
GET    /auth/me                    # Get current user
```

### Products

```
GET    /products                   # List products
GET    /products/{id}              # Single product
GET    /products?search=text       # Search
GET    /products?category=name     # Filter by category
```

### Orders

```
POST   /orders                     # Create order
GET    /orders                     # Get order history
GET    /orders/{id}                # Order details
PUT    /orders/{id}/cancel         # Cancel order
```

### AI

```
GET    /ai/forecast                # Demand forecast
GET    /ai/reorder-suggestions     # Reorder recommendations
GET    /ai/low-stock-risk          # Low stock alerts
```

---

## 🔧 Debugging Tips

### View Logs

```bash
# Run with verbose output
flutter run -v

# Filter logs
flutter logs | grep "YOUR_FILTER"
```

### Debug Print

```dart
// In your code
print('Debug message: $variable');
debugPrint('Debug message: $variable');

// With logger package
final logger = Logger();
logger.i('Info message');
logger.e('Error message');
```

### Network Debugging

```bash
# Check if backend is running
curl http://localhost:8000/docs

# Check specific endpoint
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🐛 Common Issues & Fixes

### Issue: "Cannot connect to localhost:8000"

**Solution**:

```dart
// Use IP address instead
static const String _baseUrl = 'http://192.168.x.x:8000/api/v1';
```

### Issue: "Token not working"

**Solution**:

```dart
// Clear token and re-login
await ApiService.instance.clearToken();
```

### Issue: "Build failure on Android"

**Solution**:

```bash
flutter clean
cd android && ./gradlew clean && cd ..
flutter pub get
flutter run
```

### Issue: "Hot reload not working"

**Solution**:

```bash
# Full restart
R (in terminal)

# Or rebuild
flutter clean && flutter run
```

### Issue: "API returns 401 Unauthorized"

**Solution**:

- Ensure you're logged in
- Token might be expired
- Re-login and try again
- Check token is being stored

---

## 📊 State Management Quick Guide

### AuthProvider Usage

```dart
// Get auth state
final authProvider = context.read<AuthProvider>();
final isAuthenticated = authProvider.isAuthenticated;
final currentUser = authProvider.currentUser;

// Use in Consumer widget
Consumer<AuthProvider>(
  builder: (context, auth, _) {
    return Text(auth.currentUser?.name ?? 'Guest');
  },
)

// Call methods
await authProvider.login(request);
await authProvider.logout();
```

### CartProvider Usage

```dart
// Get cart state
final cart = context.read<CartProvider>();
final totalPrice = cart.totalPrice;
final itemCount = cart.totalItems;

// Use in Consumer widget
Consumer<CartProvider>(
  builder: (context, cart, _) {
    return Text('₹${cart.totalPrice}');
  },
)

// Call methods
cart.addToCart(product);
cart.removeFromCart(productId);
cart.updateQuantity(productId, 5);
```

---

## 🎯 Workflows

### User Registration Workflow

1. User taps signup on login screen
2. Navigate to signup screen
3. User fills form and taps signup
4. AuthProvider validates input
5. AuthService calls `/auth/register`
6. Token stored in SharedPreferences
7. Redirect to home screen

### Shopping Workflow

1. User browses products
2. User adds items to cart
3. User navigates to cart
4. User enters delivery details
5. User taps "Place Order"
6. CartProvider creates Order
7. OrderService calls `/orders`
8. Order ID returned
9. Navigate to orders screen

### Reordering Workflow

1. User views order history
2. User sees order status
3. User can cancel if PLACED
4. User views AI recommendations
5. User taps "Order Recommended Amount"
6. Suggested quantity added to cart
7. Proceed to checkout

---

## 📈 Performance Tips

### Avoid

❌ Rebuilding entire widget tree  
❌ Calling setState excessively  
❌ Loading all products at once  
❌ Keeping unnecessary listeners active

### Do

✅ Use Consumer selectively  
✅ Use FutureBuilder for async data  
✅ Implement pagination  
✅ Cache images and data

---

## 🔒 Security Checklist

When making changes, ensure:

- ✅ No hardcoded passwords
- ✅ No sensitive data in logs
- ✅ Token properly managed
- ✅ HTTPS in production
- ✅ Input validation on all forms
- ✅ Error messages are generic

---

## 📚 Documentation Files

Quick access to documentation:

| Document                        | Purpose                   | Location                               |
| ------------------------------- | ------------------------- | -------------------------------------- |
| **PROJECT_INDEX.md**            | Overall project overview  | `GroceryAPP/`                          |
| **SETUP_INSTRUCTIONS.md**       | Complete setup guide      | `frontend/flutter/smartkirana_mobile/` |
| **README.md**                   | Architecture and features | `frontend/flutter/smartkirana_mobile/` |
| **STEP6_COMPLETION_SUMMARY.md** | Mobile app completion     | `GroceryAPP/`                          |

---

## 🆘 Getting Help

### For Setup Issues

→ Check `SETUP_INSTRUCTIONS.md` Troubleshooting section

### For Architecture Questions

→ Check `README.md` Architecture section

### For API Issues

→ Check backend documentation or run:

```bash
curl http://localhost:8000/docs
```

### For Code Issues

→ Check the relevant module file with comments

---

## ⌨️ Keyboard Shortcuts

### Flutter DevTools

| Action       | Shortcut |
| ------------ | -------- |
| Hot Reload   | r        |
| Full Restart | R        |
| Exit         | q        |
| Show help    | h        |

### IDE Shortcuts (VS Code)

| Action           | Shortcut        |
| ---------------- | --------------- |
| Format Code      | Shift + Alt + F |
| Find             | Ctrl + F        |
| Replace          | Ctrl + H        |
| Go to Definition | F12             |

---

## 📞 Quick Support Checklist

When debugging, check:

- [ ] Is backend running on localhost:8000?
- [ ] Is device/emulator running?
- [ ] Are dependencies installed? (`flutter pub get`)
- [ ] Is the code formatted? (`flutter format .`)
- [ ] Any build errors? (`flutter analyze`)
- [ ] Is token being stored? (Check SharedPreferences)
- [ ] Is API base URL correct? (Check api_service.dart)

---

## 🎓 Key Concepts

### JWT Token Flow

```
Login → Backend returns token → Stored in SharedPreferences
→ Token auto-added to requests → On 401 → Logout
```

### State Management Flow

```
UI Event → Provider Method → Service Call → Response → State Update → UI Rebuild
```

### Navigation Flow

```
context.go(route) → GoRouter checks auth → Redirects if needed → Shows screen
```

---

## 🚀 Ready to Launch?

### Pre-Launch Checklist

- [ ] Backend running on localhost:8000
- [ ] Flutter dependencies installed
- [ ] No compilation errors
- [ ] Tested login/signup
- [ ] Tested product browsing
- [ ] Tested cart operations
- [ ] Tested order placement
- [ ] API base URL configured

### If All Good

```bash
flutter run
# or
flutter run -d <device_id>
```

---

**Last Updated**: 2024  
**Version**: 1.0.0  
**Status**: Ready for Use ✅

---

## 🎉 You're All Set!

The SmartKirana Flutter app is ready to run. For detailed information, refer to the complete documentation files in the project root.

**Happy coding! 🚀**
