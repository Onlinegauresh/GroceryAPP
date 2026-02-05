# SmartKirana Mobile App - Setup & Run Instructions

## Project Structure

```
smartkirana_mobile/
├── lib/
│   ├── main.dart                          # App entry point
│   ├── core/
│   │   ├── theme.dart                     # Design system (colors, typography, spacing)
│   │   ├── api_service.dart              # HTTP client with JWT token management
│   │   └── router.dart                    # GoRouter navigation configuration
│   ├── auth/
│   │   ├── models/
│   │   │   └── auth_models.dart          # User, LoginRequest, AuthResponse models
│   │   ├── services/
│   │   │   └── auth_service.dart         # Authentication service layer
│   │   ├── providers/
│   │   │   └── auth_provider.dart        # Auth state management
│   │   └── screens/
│   │       ├── login_screen.dart         # Login UI
│   │       └── signup_screen.dart        # Signup UI
│   ├── home/
│   │   └── screens/
│   │       └── home_screen.dart          # Home screen with navigation
│   ├── products/
│   │   ├── models/
│   │   │   └── product_models.dart       # Product, CartItem, Order models
│   │   ├── services/
│   │   │   └── product_service.dart      # Product API service
│   │   └── screens/
│   │       └── products_screen.dart      # Products list and search
│   ├── cart/
│   │   ├── providers/
│   │   │   └── cart_provider.dart        # Cart state management
│   │   └── screens/
│   │       └── cart_screen.dart          # Shopping cart UI
│   ├── orders/
│   │   ├── services/
│   │   │   └── order_service.dart        # Order API service
│   │   └── screens/
│   │       └── orders_screen.dart        # Order history and tracking
│   ├── profile/
│   │   └── screens/
│   │       └── profile_screen.dart       # User profile and settings
│   └── ai/
│       └── screens/
│           └── ai_insights_screen.dart   # AI recommendations and alerts
├── pubspec.yaml                           # Flutter dependencies and configuration
└── README.md
```

---

## Prerequisites

### Required Software

- **Flutter SDK** (3.0 or later)
  - Download: https://flutter.dev/docs/get-started/install
  - Verify: `flutter --version`

- **Dart SDK** (included with Flutter)
  - Verify: `dart --version`

- **Android/iOS Development Tools**
  - Android: Android Studio + SDK
  - iOS: Xcode (macOS only)

### Backend API

- SmartKirana backend running on `http://localhost:8000/api/v1`
- Backend must have the following endpoints available:
  - `/auth/register` - User registration
  - `/auth/login` - User login
  - `/auth/me` - Get current user
  - `/products` - Get products list
  - `/orders` - Orders management
  - `/ai/*` - AI insights endpoints

---

## Installation Steps

### 1. Install Flutter Dependencies

```bash
cd frontend/flutter/smartkirana_mobile
flutter pub get
```

### 2. Generate JSON Serialization Code (if needed)

```bash
# For models with @JsonSerializable annotations
flutter pub run build_runner build
```

### 3. Configure Backend URL (if needed)

Edit `lib/core/api_service.dart` to update the API base URL:

```dart
static const String _baseUrl = 'http://localhost:8000/api/v1';
```

For production, use your actual backend domain.

### 4. Check Project Structure

Verify all files are in place:

```bash
flutter doctor -v
```

---

## Running the App

### Run on Android Emulator

```bash
# Start Android emulator first, then:
flutter run

# Or specify device:
flutter run -d emulator-5554
```

### Run on iOS Simulator (macOS only)

```bash
# Start iOS simulator:
open -a Simulator

# Then run:
flutter run
```

### Run on Physical Device

```bash
# Connect device via USB
adb devices  # List connected Android devices

# Run app:
flutter run -d <device_id>
```

### Build for Release

```bash
# Android APK
flutter build apk --release

# Android App Bundle
flutter build appbundle --release

# iOS IPA
flutter build ios --release
```

---

## Architecture Overview

### Clean Architecture with MVVM Pattern

```
Presentation Layer (UI/Screens)
    ↓
State Management Layer (Providers)
    ↓
Service Layer (Services)
    ↓
API Layer (ApiService)
    ↓
Backend API
```

### Key Components

#### **1. Core Module** (`lib/core/`)

**api_service.dart**

- Singleton HTTP client
- JWT token management
- Bearer token injection
- Response parsing and error handling
- Automatic token refresh

**theme.dart**

- Centralized design system
- Colors, typography, spacing, shadows
- Consistent styling across app

**router.dart**

- GoRouter navigation configuration
- Route definitions (7 routes total)
- Auth-based redirect logic

#### **2. Auth Module** (`lib/auth/`)

**Models** (auth_models.dart)

- `User` - Current user data
- `LoginRequest` - Login form data
- `SignupRequest` - Registration form data
- `AuthResponse` - API response with token

**Service** (auth_service.dart)

- signup(SignupRequest) - User registration
- login(LoginRequest) - User authentication
- getCurrentUser() - Fetch current user
- changePassword() - Password change
- logout() - Clear session

**Provider** (auth_provider.dart)

- State: AuthState enum (initial, authenticating, authenticated, unauthenticated, error)
- Methods: init(), signup(), login(), logout(), refreshUser(), changePassword()
- Input validation and error handling
- Persistent state management

**Screens**

- `login_screen.dart` - Email/password login with validation
- `signup_screen.dart` - Full registration form with validation

#### **3. Products Module** (`lib/products/`)

**Models** (product_models.dart)

- `Product` - Product details with pricing and inventory
- `CartItem` - Shopping cart item
- `Order` - Order information
- `OrderItem` - Individual order item

**Service** (product_service.dart)

- getProducts() - Fetch product list
- getProduct(id) - Fetch single product
- searchProducts() - Search functionality
- getProductsByCategory() - Filter by category
- getLowStockProducts() - Stock monitoring

**Screen** (products_screen.dart)

- Product grid with search and filter
- Category filtering
- Add to cart functionality

#### **4. Cart Module** (`lib/cart/`)

**Provider** (cart_provider.dart)

- State: List<CartItem>, totals, GST calculation
- Methods: addToCart(), removeFromCart(), updateQuantity(), clearCart()
- Quantity adjustments with increment/decrement
- Order creation from cart

**Screen** (cart_screen.dart)

- Cart items display
- Quantity management
- Order summary with totals
- Delivery details form
- Payment method selection
- Place order button

#### **5. Orders Module** (`lib/orders/`)

**Service** (order_service.dart)

- placeOrder() - Create new order
- getOrders() - Fetch order history
- getOrderDetail() - Single order details
- cancelOrder() - Cancel existing order
- getOrdersByStatus() - Filter by status

**Screen** (orders_screen.dart)

- Order history list
- Status filtering (PLACED, CONFIRMED, PREPARING, DELIVERED, CANCELLED)
- Order details with items
- Cancel order functionality
- Order tracking information

#### **6. Profile Module** (`lib/profile/`)

**Screen** (profile_screen.dart)

- User profile display (name, email, role)
- Account information editing
- Password change form
- Logout functionality

#### **7. AI Module** (`lib/ai/`)

**Screen** (ai_insights_screen.dart)

- Reorder suggestions with priority levels
- Low-stock critical alerts
- Demand forecast for upcoming days
- Confidence scores for predictions
- One-click reorder functionality

---

## Authentication Flow

```
User Input (Login/Signup)
    ↓
AuthProvider validates input
    ↓
AuthService makes API call to backend
    ↓
Backend returns JWT token
    ↓
ApiService stores token in SharedPreferences
    ↓
Token automatically added to all requests
    ↓
On 401 response → Auto logout and redirect to login
```

### Token Storage

- **Location**: Device SharedPreferences
- **Key**: `auth_token`
- **Persistence**: Survives app restart
- **Expiration**: Handled by backend (refresh token logic can be added)

---

## API Integration

### Available Endpoints

#### Auth Endpoints

```
POST   /auth/register              # Sign up
POST   /auth/login                 # Sign in
GET    /auth/me                    # Get current user
PUT    /auth/change-password       # Change password
```

#### Product Endpoints

```
GET    /products                   # List products with filters
GET    /products/{id}              # Single product
GET    /products/low-stock         # Low stock products
GET    /products?search=...        # Search
GET    /products?category=...      # Filter by category
```

#### Order Endpoints

```
POST   /orders                     # Create order
GET    /orders                     # Get order history
GET    /orders/{id}                # Order details
PUT    /orders/{id}/cancel         # Cancel order
GET    /orders?status=...          # Filter by status
```

#### AI Endpoints

```
GET    /ai/forecast                # Demand forecast
GET    /ai/reorder-suggestions     # Suggested reorders
GET    /ai/low-stock-risk          # Low stock alerts
GET    /ai/anomalies               # Anomaly detection
```

### Request/Response Format

```json
// Request (POST /auth/login)
{
  "email": "user@example.com",
  "password": "SecurePassword123"
}

// Response (Success)
{
  "status": "success",
  "data": {
    "access_token": "eyJhbGc...",
    "token_type": "bearer",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "name": "John Doe",
      "role": "customer",
      "shop_id": null
    }
  }
}

// Response (Error)
{
  "status": "error",
  "message": "Invalid credentials"
}
```

---

## Troubleshooting

### Common Issues

#### 1. "Cannot connect to backend"

- Ensure backend is running on `localhost:8000`
- Check API base URL in `lib/core/api_service.dart`
- For physical device: Use actual IP instead of localhost
  ```dart
  static const String _baseUrl = 'http://<your_ip>:8000/api/v1';
  ```

#### 2. "Dependency conflicts"

- Run: `flutter clean && flutter pub get`
- Delete: `pubspec.lock` file and retry

#### 3. "Build errors on Android"

- Update Android SDK: `flutter doctor --android-licenses`
- Accept all licenses when prompted

#### 4. "iOS build fails"

- Run: `cd ios && pod repo update && cd ..`
- Clean: `flutter clean`
- Rebuild: `flutter pub get`

#### 5. "Token not persisting"

- Verify `SharedPreferences` dependency in `pubspec.yaml`
- Check device storage permissions

#### 6. "Navigation not working"

- Ensure all screens are imported in `lib/core/router.dart`
- Verify route paths match GoRouter configuration
- Check `context.go()` is used (not `Navigator.push()`)

---

## Development Guidelines

### File Naming

- Dart files: `snake_case.dart`
- Classes: `PascalCase`
- Variables/methods: `camelCase`
- Constants: `SCREAMING_SNAKE_CASE`

### Folder Structure

- Keep related files in same module
- Models → Services → Providers → Screens
- Separate concerns (auth, products, orders, etc.)

### Error Handling

All services return `ApiResponse<T>` wrapper:

```dart
Future<ApiResponse<List<Product>>> getProducts() async {
  try {
    // API call
    return ApiResponse<List<Product>>.success(data);
  } catch (e) {
    return ApiResponse<List<Product>>.error('Error message');
  }
}

// Usage
final response = await productService.getProducts();
if (response.isSuccess) {
  // Use response.data
} else {
  // Show response.message error
}
```

### State Management

- Use `Provider` for global state (auth, cart)
- Use `ChangeNotifier` for mutable state
- Use `Consumer` widget for reactive UI updates
- Avoid passing data via constructor parameters

### Navigation

- Always use `context.go()` from GoRouter
- Don't mix Navigator and GoRouter
- Implement proper auth-based redirects
- Update `lib/core/router.dart` for new routes

---

## Performance Tips

1. **Lazy Load Images**: Implement image caching
2. **Pagination**: Fetch products in batches
3. **Debounce Search**: Add delay to search requests
4. **Minimize Rebuilds**: Use Consumer selectively
5. **Cache Data**: Implement local caching strategy

---

## Security Checklist

- ✅ JWT tokens stored in SharedPreferences
- ✅ Bearer token added to all authenticated requests
- ✅ HTTPS enforced in production
- ✅ Password validation on client-side
- ✅ Session timeout implementation
- ✅ Input validation for all forms
- ✅ Error messages don't expose sensitive data

---

## Next Steps

### Features to Implement

1. **Product Reviews & Ratings**
   - Create review model
   - Build review submission form
   - Display reviews on product detail screen

2. **Wishlist Feature**
   - Add WishlistProvider
   - Save to local storage
   - Wishlist screen

3. **Order Tracking**
   - Real-time location tracking
   - Estimated delivery time
   - Push notifications

4. **Payment Integration**
   - Online payment gateway (Razorpay, PhonePe)
   - Payment status tracking
   - Invoice generation

5. **Push Notifications**
   - Order status updates
   - AI recommendations
   - Promotional offers

6. **Dark Mode**
   - Add theme provider
   - Implement theme toggle
   - Persist theme preference

---

## Support & Documentation

- **Flutter Docs**: https://flutter.dev/docs
- **Provider Package**: https://pub.dev/packages/provider
- **GoRouter**: https://pub.dev/packages/go_router
- **API Documentation**: Check backend README.md

---

## Version History

**v1.0.0** (Current)

- Initial release with core features
- Authentication (signup/login)
- Product browsing and search
- Shopping cart with checkout
- Order history and tracking
- AI insights and recommendations
- User profile management

---

## License & Credits

Built for SmartKirana AI Grocery Platform  
Developed with Flutter 3.0+  
Backend: FastAPI + PostgreSQL

---

**Last Updated**: 2024  
**Maintainer**: SmartKirana Team
