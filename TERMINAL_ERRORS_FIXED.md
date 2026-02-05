# 🔴 Terminal Error Diagnosis & Fixes

**Date:** February 4, 2026  
**Issue:** Server not starting properly - Command errors in terminal

---

## ❌ **ERRORS FOUND**

### Error 1: `python app.py` (Exit Code: 1)

```
Command: python app.py
Error: [Errno 2] No such file or directory
Reason: File named 'app.py' doesn't exist
```

**Solution:**

```powershell
# Use this instead:
python main.py
```

The entry point is **`main.py`**, NOT `app.py`

---

### Error 2: PowerShell Unix Commands (Exit Code: 1)

```
Command: pip list | tail -20
Error: tail : The term 'tail' is not recognized
Reason: Windows PowerShell doesn't have Unix commands
```

**Solutions:**

```powershell
# Instead of: pip list | tail -20
# Use this:
pip list

# Instead of: dir venv | head -20
# Use this:
dir venv

# Instead of: ls -la
# Use this:
dir
```

**Windows PowerShell equivalents:**
| Unix | PowerShell |
|------|-----------|
| `tail` | `Select-Object -Last N` |
| `head` | `Select-Object -First N` |
| `grep` | `Select-String` |
| `cat` | `Get-Content` |
| `ls` | `dir` or `Get-ChildItem` |

---

### Error 3: Docker Not Available (Exit Code: 1)

```
Command: docker --version
Error: 'docker' is not recognized
Reason: Docker not installed on Windows
```

**Solution:**

```powershell
# Already handled! Using SQLite instead of Docker
# Your backend works perfectly with SQLite locally
python main.py
```

---

### Error 4: Python Path Issues (Exit Code: 1)

```
Command: C:\Users\Gaurav\...\main.py (from wrong directory)
Error: can't open file 'main.py'
Reason: Must run from backend folder
```

**Solution:**

```powershell
# First, navigate to backend folder
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend

# Then run
python main.py

# OR use full path and correct command:
C:\Users\Gaurav\Desktop\GroceryAPP\backend\venv\Scripts\python.exe c:\Users\Gaurav\Desktop\GroceryAPP\backend\main.py
```

---

## ✅ **CORRECT COMMANDS TO USE**

### Start API Server

```powershell
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
python main.py
```

**Output should show:**

```
2026-02-04 19:39:50,901 INFO sqlalchemy.engine.Engine BEGIN
...
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Seed Database

```powershell
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
python scripts/seed_data.py
```

### Run Tests

```powershell
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
pytest tests/
```

### Install Packages (if needed)

```powershell
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
pip install -r requirements.txt
```

### Check Installed Packages

```powershell
pip list
```

---

## 🎯 **TERMINAL COMMAND CHEAT SHEET (PowerShell)**

```powershell
# Navigation
cd path\to\folder          # Change directory
pwd                        # Print working directory
dir                        # List files (not ls!)
dir folder                 # List specific folder

# Python
python --version          # Check Python version
python script.py          # Run Python script
python -m pip list        # List installed packages
pip install package       # Install package

# Development
pytest tests/              # Run tests
pytest tests/ -v          # Verbose output

# Background Jobs
# Start background job:
python main.py &
Get-Job                    # List background jobs
Stop-Job -ID 1             # Stop job #1

# Port/Network
netstat -ano | Select-String ":8000"  # Check if port listening
curl http://localhost:8000            # Test endpoint

# Database
sqlite3 database.db       # Open SQLite database
.tables                   # List tables (inside sqlite3)
.quit                     # Exit sqlite3
```

---

## 📊 **Command Mapping: Unix → PowerShell**

| Task           | Unix                          | PowerShell                                    |
| -------------- | ----------------------------- | --------------------------------------------- |
| List files     | `ls -la`                      | `dir` or `Get-ChildItem`                      |
| Show file      | `cat file.txt`                | `Get-Content file.txt`                        |
| Search text    | `grep "text" file`            | `Select-String "text" file`                   |
| Count lines    | `wc -l file`                  | `(Get-Content file).Count`                    |
| Last N lines   | `tail -20 file`               | `Get-Content file \| Select-Object -Last 20`  |
| First N lines  | `head -20 file`               | `Get-Content file \| Select-Object -First 20` |
| Pipe output    | `\|`                          | `\|` (same)                                   |
| Background job | `cmd &`                       | `cmd &` (same)                                |
| Kill process   | `kill PID`                    | `taskkill /PID <PID> /F`                      |
| Check port     | `netstat -tuln \| grep :8000` | `netstat -ano \| Select-String ":8000"`       |

---

## 🚀 **QUICK FIX - START YOUR SERVER NOW**

```powershell
# 1. Navigate to backend
cd c:\Users\Gaurav\Desktop\GroceryAPP\backend

# 2. Activate virtual environment (optional, already in venv)
.\venv\Scripts\Activate.ps1

# 3. Start server
python main.py

# 4. In another PowerShell, test it
curl http://localhost:8000/api/docs
```

**Server should now be running at:** http://localhost:8000 ✅

---

## 📝 **Error Summary Table**

| Error                    | Cause                | Fix                                   |
| ------------------------ | -------------------- | ------------------------------------- |
| `app.py` not found       | Wrong filename       | Use `main.py`                         |
| `tail` not recognized    | Unix command         | Use `Select-Object -Last N`           |
| `head` not recognized    | Unix command         | Use `Select-Object -First N`          |
| `docker` not found       | Docker not installed | Use SQLite (already set up)           |
| Main.py not found        | Wrong directory      | Run from `backend/` folder            |
| Port 8000 not responding | Server not running   | Run `python main.py`                  |
| Import errors            | Missing packages     | Run `pip install -r requirements.txt` |

---

## ✨ **VERIFICATION CHECKLIST**

```
☑ In backend folder
☑ Virtual environment activated (or using full python path)
☑ Running: python main.py
☑ Check: http://localhost:8000/api/docs works
☑ Database: smartkirana.db exists
☑ Demo data: Seeded (4 users, 6 products)
☑ All set!
```

---

## 🎯 **NEXT STEPS**

1. **Start server:**

   ```powershell
   cd c:\Users\Gaurav\Desktop\GroceryAPP\backend
   python main.py
   ```

2. **Wait for output:**

   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   ```

3. **Open in browser:**

   ```
   http://localhost:8000/api/docs
   ```

4. **Test with demo credentials:**
   - Phone: 9876543210
   - Password: demo123

---

**Status:** All errors resolved ✅  
**Ready to use:** YES  
**Next:** Open http://localhost:8000/api/docs
