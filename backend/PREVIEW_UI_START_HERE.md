# ⚡ SmartKirana Preview UI - Step by Step Guide

## 🎯 Goal: See Your Data Visually in the Browser

This guide will take you from 0 to fully functional in **3 steps**.

---

## STEP 1: Start the Server ⚙️

### Windows (PowerShell)

```powershell
# Open PowerShell and run:
cd "c:\Users\Gaurav\Desktop\GroceryAPP\backend"
python main_with_auth.py
```

### Mac/Linux

```bash
cd ~/GroceryAPP/backend
python main_with_auth.py
```

### You should see:

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## STEP 2: Open Your Browser 🌐

Copy and paste this into your browser address bar:

```
http://localhost:8000
```

**That's it!** You'll see the SmartKirana home page.

---

## STEP 3: Explore and Test 🚀

### Click on these links in the app:

| Link            | Shows           | What You'll See         |
| --------------- | --------------- | ----------------------- |
| **Products**    | All products    | Table with inventory    |
| **Orders**      | Recent orders   | Order list with status  |
| **Shops**       | Store locations | Shop information        |
| **Users**       | Team members    | User profiles & roles   |
| **Home**        | Dashboard       | Quick stats             |
| **Swagger API** | Full API docs   | Technical API reference |

---

## 🎨 What You're Looking At

### Home Page

A beautiful dashboard showing:

- 4 quick navigation cards
- System status information
- Feature list
- Links to all other pages

### Product Page

A searchable table with all your products:

- Product name
- Category
- Price
- Unit of sale
- When it was added

### Orders Page

Your order history with:

- Order ID and status
- Customer information
- Total amount
- Number of items
- Order date

### Shops Page

All your retail locations:

- Shop name
- Location address
- Phone & email
- Creation date

### Users Page

Your team members:

- Name and contact info
- Role (Admin, Owner, Staff, Customer)
- Active/Inactive status
- Shop assignment

---

## 🔧 Troubleshooting (If Something Goes Wrong)

### Problem: "Connection refused"

**Solution**: Make sure the server is still running in the terminal. You should see:

```
Uvicorn running on http://0.0.0.0:8000
```

If not, go back to STEP 1.

### Problem: "Application not responding"

**Solution**: Wait a few seconds, then refresh the page (F5 or Cmd+R)

### Problem: Page shows but has no styling (looks plain)

**Solution**:

1. Make sure there's a `static/` folder in `backend/`
2. Inside it should be a `style.css` file
3. Refresh your browser (Ctrl+F5 to clear cache)

### Problem: "No products/orders/shops/users showing"

**Solution**: You need to seed the database with sample data:

```bash
# In backend folder, run:
python scripts/seed_data.py
```

Then refresh your browser.

### Problem: Port 8000 already in use

**Solution**: Kill the other app using port 8000 or edit line 177 in `main_with_auth.py`:

```python
# Change port to 8001
uvicorn.run(
    app,
    host="0.0.0.0",
    port=8001,  # Change this
    ...
)
```

Then access: `http://localhost:8001`

---

## 📱 View on Mobile

### Using Same Computer

1. Open a web browser
2. Type: `http://localhost:8000`
3. Done! It's responsive to mobile size

### Using Different Computer on Same Network

1. Find your computer's IP (Windows: `ipconfig`, look for IPv4 Address)
2. From other computer, visit: `http://YOUR_IP:8000`
3. Example: `http://192.168.1.100:8000`

### Using iPhone/Android on Same Network

1. Open browser
2. Type: `http://YOUR_IP:8000`
3. Example: `http://192.168.1.100:8000`

---

## ✨ Cool Features to Try

### 1. Click Links

- Every page has links to navigate
- Scroll down to see more content
- Click "Home" to go back

### 2. Hover Effects

- Hover over cards - they float up slightly
- Hover over buttons - they change color
- Hover over table rows - they highlight

### 3. Status Badges

- **Red badges** = Inactive/Cancelled
- **Green badges** = Active/Completed
- **Yellow badges** = Pending
- **Blue badges** = Staff/General info

### 4. Responsive Design

- Resize browser window
- Notice how layout changes
- Try on phone too

### 5. View More

- Some pages have both table AND card views
- Scroll down to see all views
- Lots of beautiful data presentation

---

## 🔗 Related Pages

While the preview UI is running, you can also access:

| URL                              | What It Is              |
| -------------------------------- | ----------------------- |
| http://localhost:8000            | Home page (NEW)         |
| http://localhost:8000/api/docs   | Swagger API (original)  |
| http://localhost:8000/api/redoc  | ReDoc Docs (original)   |
| http://localhost:8000/api/health | Health check (original) |

---

## 📊 What Data This Shows

### From Your Database:

- ✅ All products in inventory
- ✅ All orders and their status
- ✅ All shops and locations
- ✅ All users and their roles
- ✅ Creation dates and updates

### What It DOESN'T Do:

- ❌ Doesn't allow creating new data
- ❌ Doesn't allow editing existing data
- ❌ Doesn't allow deleting anything
- ✅ (Use the API for those - links in documentation)

---

## 🎯 Summary

You now have:

1. ✅ A beautiful browser-based interface
2. ✅ Real-time view of your backend data
3. ✅ Responsive design that works everywhere
4. ✅ No configuration needed
5. ✅ Production-ready code
6. ✅ All existing APIs unchanged

---

## 📝 Quick Reference

### Start Server

```bash
cd backend
python main_with_auth.py
```

### View in Browser

```
http://localhost:8000
```

### Common URLs

```
Home:       http://localhost:8000
Products:   http://localhost:8000/preview/products
Orders:     http://localhost:8000/preview/orders
Shops:      http://localhost:8000/preview/shops
Users:      http://localhost:8000/preview/users
API Docs:   http://localhost:8000/api/docs
```

### Stop Server

```
Press Ctrl+C in terminal
```

---

## 🎉 You're Good to Go!

Your FastAPI backend now has a beautiful, lightweight web UI.

**No Flutter. No Android Studio. No complex setup.**

Just run the server, open a browser, and explore your data!

Enjoy! 🚀

---

**Questions?** Check these docs:

- Full setup: `PREVIEW_UI_SETUP.md`
- Quick reference: `PREVIEW_UI_QUICK_START.md`
- Implementation details: `PREVIEW_UI_IMPLEMENTATION.md`
