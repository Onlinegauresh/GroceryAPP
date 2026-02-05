# 🎯 TERMINAL ERRORS - QUICK REFERENCE

## ❌ **MAIN ERRORS & FIXES**

### 1. `python app.py` - FILE NOT FOUND

```
❌ Wrong: python app.py
✅ Right: python main.py
```

### 2. `tail` / `head` - POWERSHELL DOESN'T HAVE UNIX COMMANDS

```
❌ Wrong: pip list | tail -20
✅ Right: pip list

❌ Wrong: dir venv | head -20
✅ Right: dir venv
```

### 3. `main.py` NOT FOUND - WRONG DIRECTORY

```
❌ Wrong: python main.py (from GroceryAPP folder)
✅ Right:
   cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
   python main.py
```

### 4. DOCKER NOT INSTALLED - ALREADY HANDLED

```
❌ Docker doesn't exist: docker --version
✅ Solution: Using SQLite instead (working perfectly!)
```

---

## ✅ **CORRECT COMMANDS**

```powershell
# Start Server (MAIN COMMAND)
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
python main.py

# Access API
http://localhost:8000/api/docs

# Demo Login
Phone: 9876543210
Password: demo123
```

---

## 📊 **POWERSHELL VS UNIX COMMANDS**

| Need to...          | Unix        | PowerShell                |
| ------------------- | ----------- | ------------------------- |
| List files          | `ls`        | `dir`                     |
| Show last 10 lines  | `tail -10`  | `Select-Object -Last 10`  |
| Show first 10 lines | `head -10`  | `Select-Object -First 10` |
| Search in file      | `grep text` | `Select-String text`      |
| Run in background   | `cmd &`     | `cmd &`                   |

---

## 🚀 **START HERE**

```powershell
1. cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
2. python main.py
3. Open: http://localhost:8000/api/docs
```

That's it! ✅
