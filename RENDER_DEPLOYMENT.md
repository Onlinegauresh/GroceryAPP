# GroceryAPP Deployment to Render.com

## Prerequisites

- GitHub account (https://github.com)
- Render account (https://render.com - free)

## Step-by-Step Deployment

### 1. Create GitHub Repository

1. Go to https://github.com/new
2. Name: `GroceryAPP`
3. Click "Create repository"
4. Copy the HTTPS URL (e.g., `https://github.com/YOUR_USERNAME/GroceryAPP.git`)

### 2. Push Code to GitHub

```powershell
cd c:\Users\Gaurav\Desktop\GroceryAPP

# Configure git (if not done)
git config --global user.email "gaurav@groceryapp.local"
git config --global user.name "Gaurav"

# Add remote and push
git remote add origin https://github.com/YOUR_USERNAME/GroceryAPP.git
git branch -M main
git push -u origin main
```

### 3. Create Render Account & Deploy

1. Go to https://render.com
2. Click "Sign Up" → Connect with GitHub
3. Authorize GitHub access
4. Click "New" → "Web Service"
5. Select your `GroceryAPP` repository
6. Fill in details:
   - **Name**: `groceryapp`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r backend/requirements.txt`
   - **Start Command**: `cd backend && uvicorn main_with_auth:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or paid for better performance)

7. Click "Advanced" → "Add Environment Variable":
   - Key: `PYTHON_VERSION` → Value: `3.11`
   - Key: `DEBUG` → Value: `false`

8. Click "Create Web Service"

### 4. Create Database

1. Go to Render Dashboard
2. Click "New" → "PostgreSQL"
3. Fill in:
   - **Name**: `groceryapp-db`
   - **Plan**: Free
   - Click "Create Database"

4. Copy the `Internal Database URL`
5. Go back to Web Service settings
6. Add Environment Variable:
   - Key: `DATABASE_URL`
   - Value: (paste the database URL)

### 5. Deploy

- Render will automatically deploy when you push to GitHub
- Live URL will appear in form: `https://groceryapp.onrender.com`

## Access Your Live Website

- **Home**: `https://groceryapp.onrender.com/`
- **Shop**: `https://groceryapp.onrender.com/shop/`
- **Products**: `https://groceryapp.onrender.com/preview/products`
- **API Docs**: `https://groceryapp.onrender.com/api/docs`

## Demo Credentials

- **Admin Email**: `admin@groceryapp.com` / Password: `AdminPass123!`
- **Customer Email**: `customer@groceryapp.com` / Password: `CustomerPass123!`

## Notes

- Free tier may sleep after 15 min of inactivity (wakes on first request)
- Database is persistent even with free tier
- Upgrade anytime for production needs
