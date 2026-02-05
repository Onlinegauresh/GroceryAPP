# 🎯 QUICK START - Admin Dashboard & Customer Shop

## ⚡ Starting the Server

Open PowerShell in the `backend` folder and run:

```powershell
cd "c:\Users\Gaurav\Desktop\GroceryAPP\backend"
.\venv\Scripts\python.exe -m uvicorn main_with_auth:app --host 0.0.0.0 --port 8000
```

You should see:

```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 🔗 Quick Links

### Admin Dashboard

| Section     | URL                                    | What You Can Do                                 |
| ----------- | -------------------------------------- | ----------------------------------------------- |
| Dashboard   | http://localhost:8000/admin/           | View business overview, stats, low stock alerts |
| Orders      | http://localhost:8000/admin/orders     | See all orders, filter by status                |
| Products    | http://localhost:8000/admin/products   | Manage products, view inventory value           |
| Inventory   | http://localhost:8000/admin/inventory  | Track stock levels, identify reorders           |
| Accounting  | http://localhost:8000/admin/accounting | View sales reports, revenue by date             |
| AI Insights | http://localhost:8000/admin/ai         | Get smart recommendations, sales forecasts      |

### Customer Shop

| Section      | URL                                 | What You Can Do                 |
| ------------ | ----------------------------------- | ------------------------------- |
| Home         | http://localhost:8000/shop/         | Browse featured products        |
| All Products | http://localhost:8000/shop/products | Filter by category, add to cart |
| Cart         | http://localhost:8000/shop/cart     | Review items, adjust quantities |
| Checkout     | http://localhost:8000/shop/checkout | Enter shipping/payment info     |
| My Orders    | http://localhost:8000/shop/orders   | View past orders                |

---

## 👨‍💼 Using the Admin Dashboard

### Step 1: Welcome to Dashboard

- Go to http://localhost:8000/admin/
- See 6 stat cards: Products, Orders, Today's Orders, Sales, Shops, Low Stock
- View recent orders in the table
- Click Quick Actions buttons to jump to any section

### Step 2: Check Orders

- Click "Orders" in sidebar
- See table with all orders (Order ID, Customer, Amount, Status, Payment)
- View summary stats at bottom
- Pending & completed order counts

### Step 3: Manage Products

- Click "Products" in sidebar
- Browse all products in table
- See: ID, Name, Category, Price, Stock, Description
- Edit/Delete buttons available (UI ready)
- Summary stats: Total products, inventory value

### Step 4: Monitor Inventory

- Click "Inventory" in sidebar
- Filter buttons: All, Low Stock, Out of Stock, Adequate Stock
- See current stock levels and inventory value per item
- Reorder button available for stock management
- Summary: Total items, low stock count, OOS items

### Step 5: View Sales Reports

- Click "Accounting" in sidebar
- Period selector: Today, This Week, This Month, This Year
- Sales summary cards with totals
- Orders by status breakdown table
- Top products by revenue
- Financial metrics

### Step 6: Get Smart Insights

- Click "AI Insights" in sidebar
- Reorder recommendations based on low stock
- Sales forecasts for upcoming periods
- Product performance analysis
- Best/worst selling products
- Recommended business actions

---

## 🛍️ Using the Customer Shop

### Step 1: Browse Home Page

- Go to http://localhost:8000/shop/
- See hero section with call-to-action
- Browse featured products (12 latest available)
- Each product shows: Name, Category, Price, Stock Status
- Click "Start Shopping" or "Add to Cart"

### Step 2: Shop All Products

- Click "Shop All" or go to http://localhost:8000/shop/products
- **Left Sidebar**: Filter options
  - By Category: All, Groceries, etc.
  - By Stock Level: In Stock, On Sale, Best Sellers
  - Sort By: Price, Best Sellers, Newest, A-Z
- **Products Grid**: Shows all filtered products
- Each product card shows price and stock status
- Select quantity before adding

### Step 3: Add Items to Cart

- Product cards have quantity selector (1-10)
- Click "Add" button
- Cart count appears in header (🛒 Cart badge)
- Can add same item multiple times (increases qty)

### Step 4: Review Shopping Cart

- Click "🛒 Cart" in header or go to /shop/cart
- See table with all items
- Columns: Product, Price, Quantity, Total, Action
- **Update Quantity**: Select new qty + click Update
- **Remove Item**: Click Remove button
- **Sidebar Summary**:
  - Subtotal, Shipping (free), Tax (10%)
  - **Total** amount in green
  - Promo code input (future)
  - Security badges

### Step 5: Proceed to Checkout

- Click "Proceed to Checkout" button
- **Left Side**: Checkout form with sections
  - Shipping Info: Name, Email, Phone, Address
  - City, State, ZIP, Country
  - Shipping Method: Standard (FREE) or Express (+$10)
  - Payment Method: Card, PayPal, Bank Transfer
  - Agree to Terms checkbox
- **Right Side**: Order summary
  - Itemized list of products
  - Subtotal, shipping, tax breakdown
  - Final total in green
  - Trust badges (Security, Money-back guarantee, 24/7 support)

### Step 6: Place Order

- Fill in all required fields
- Select shipping method
- Select payment method
- Check "I agree to Terms & Privacy"
- Click "Place Order" button
- **Success!** Redirected to confirmation page with:
  - ✅ Order Confirmed message
  - Order Number (e.g., #1234)
  - Order date, total, delivery status
  - What happens next steps
  - Links to view orders or continue shopping

### Step 7: Track Your Orders

- Click "My Orders" in header
- See all orders in card layout
- Each card shows: Order ID, Date, Total, Status
- View Details / Download Invoice options
- Return policy information

---

## 📊 Data You'll See

### Products Table (from Database)

Your app has real products in the database. When you:

- Browse products → loads from `Product` table
- Add to cart → temp stored in memory
- Place order → creates `Order` + `OrderItem` records
- Updates stock → decrements `Product.stock`

### Orders

- Admin sees ALL orders ever placed
- Customer sees only their orders (user_id = 1 in demo)
- Status tracking: Pending, Processing, Shipped, Delivered
- Payment tracking: Pending, Paid, Failed

### Stock Management

- Each product has a stock level
- When order is placed, stock decreases
- Low stock < 10 shows warning
- Out of stock items disable "Add to Cart"

---

## 🎨 UI/UX Notes

### Admin Dashboard

- **Color Scheme**: Dark green (#1a472a) with accent green (#27c44f)
- **Layout**: Fixed sidebar + main content
- **Responsive**: Works on mobile (sidebar collapses)
- **Tables**: Hover effects, status badges with colors
- **Cards**: Statistics displayed in colored cards

### Customer Shop

- **Color Scheme**: Bright green (#27c44f) with professional whites
- **Layout**: Full-width with grid products
- **Responsive**: Grid adapts from 4 columns → 1 on mobile
- **Header**: Sticky navigation with cart badge
- **Footer**: Multiple columns with links
- **Forms**: Clean, organized, mobile-friendly

---

## ⚙️ Technical Notes

### What Happens When You Order

1. Customer fills checkout form
2. Clicks "Place Order"
3. Backend validates stock for all items
4. Creates `Order` record (status='pending', payment_status='pending')
5. Creates `OrderItem` for each product
6. **Decrements** `Product.stock` for each item
7. Clears shopping cart (memory)
8. Redirects to confirmation page

### Stock Example

```
Before: Widget stock = 15
Customer orders 3 widgets
After: Widget stock = 12
```

### Cart Management

- Cart stored in memory (dictionary)
- Keyed by product_id
- Stores: name, price, quantity
- Lost on server restart (can upgrade to sessions)

---

## 🐛 Troubleshooting

### Server won't start

**Error**: `Address already in use`

- Another process is using port 8000
- Kill it: `taskkill /F /IM python.exe`
- Or use different port: `--port 8001`

### Templates not loading

**Error**: `TemplateNotFound: admin/dashboard.html`

- Check templates directory exists
- Verify file names match exactly (case-sensitive)
- Check templates/admin/ and templates/shop/ folders

### Cart items disappear

- Shopping cart is in-memory (temporary)
- Restarting server clears it
- Future upgrade: Use persistent sessions

### Orders not showing up

- Admin orders show all orders
- Customer orders filter by user_id=1
- Check database has Order records
- Verify OrderItems were created

---

## 📝 Example Workflows

### Admin Workflow (5 Minutes)

1. Open /admin/ → Check dashboard stats
2. Click Orders → See list of all orders
3. Click Inventory → Check low stock items
4. Click Accounting → View today's sales
5. Click AI → Get reorder recommendations

### Customer Workflow (10 Minutes)

1. Open /shop/ → Browse featured items
2. Click "Shop All" → Filter by category
3. Add 3 items to cart (qty 2, 1, 3)
4. View cart →see total with tax
5. Checkout → Fill form
6. Place order → See confirmation
7. View orders → See order history

---

## 🚀 Next Steps (Optional)

### To Add Authentication

- Uncomment auth checks in routers
- Redirect unauthenticated to /login
- Admin only accessible to admin users
- Shop visible to all

### To Persist Sessions

- Install: `pip install python-multipart`
- Use `Request.session` instead of memory dict
- Store cart in database

### To Add Products

- Admin product form for adding new items
- Upload images
- Set categories, prices, stock

### To Enable Payments

- Integrate Stripe API
- Add payment processing
- Update order status on successful payment

---

## 📞 Help

**Check admin dashboard stats**

- If 0 products: Add products through admin form
- If no orders: Place test order in shop
- If low stock alerts: Stock < 10 triggers alerts

**Check shop products**

- If no products showing: Add products via admin
- If can't add to cart: Check stock > 0
- If checkout fails: Check all required fields filled

**Database Issues**

- Reset database: Delete `grocery.db`
- Recreate tables: Restart server
- Verify data: Admin dashboard shows all data

---

## 💡 Pro Tips

1. **Admin Dashboard**: Start here to understand your business metrics
2. **Low Stock Alerts**: Pay attention to inventory warnings
3. **AI Insights**: Check recommendations for smart decisions
4. **Checkout Test**: Try placing a few orders to see flow
5. **Mobile Test**: Resize browser to test responsive design
6. **Category Filter**: Test filtering products by category

---

**Status**: ✅ Ready to Use!
**Version**: 1.0.0
**Last Updated**: Feb 5, 2026
