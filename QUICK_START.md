# 🚀 Quick Start - Fixed!

## ✅ Issue Fixed!

The "site cannot be reached" error has been fixed. The backend was trying to access a directory that didn't exist.

---

## 🎯 Start Your Application (3 Steps)

### Step 1: Test Backend (Optional but Recommended)

Double-click: **`test-backend.bat`**

This will verify the backend can start without errors.

---

### Step 2: Start Backend

**Double-click: `start-backend.bat`**

You should see:
```
========================================
Starting Customer Onboarding Backend
========================================

Starting server on http://localhost:8000
API Docs will be at: http://localhost:8000/docs

INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

✅ **Keep this window open!**

**Test it:** Open http://localhost:8000/health in your browser
- Should show: `{"status":"healthy"}`

---

### Step 3: Start Frontend (New Window)

**Double-click: `start-frontend.bat`**

You should see:
```
========================================
Starting Customer Onboarding Frontend
========================================

VITE v4.5.0  ready in XXX ms

➜  Local:   http://localhost:5173/
```

✅ **Keep this window open!**

---

## 🌐 Open Your Application

**Your app is now running!**

Open in your browser: **http://localhost:5173**

---

## 🎮 Try It Out

1. **Register** a new account
   - Email: test@example.com
   - Password: Test123!
   - Name: Test User

2. **Login** with your credentials

3. **Upload a document**
   - Create a simple .txt file with some product information
   - Upload it through the interface
   - Wait 5-10 seconds for AI processing

4. **View AI-generated onboarding tips!**

---

## 🔍 Verify Everything Works

### Backend Checks:

1. **Health Check:** http://localhost:8000/health
   - Should return: `{"status":"healthy"}`

2. **API Docs:** http://localhost:8000/docs
   - Should show interactive API documentation

3. **Database:** Check `backend/customer_onboarding.db`
   - File should exist after you register

### Frontend Checks:

1. **Main App:** http://localhost:5173
   - Should load the React application

2. **Console:** Open browser DevTools (F12)
   - Should see no errors in console
   - Network tab should show successful API calls

---

## 🛑 To Stop

1. Go to each terminal window
2. Press **Ctrl+C**
3. Type **Y** if asked to terminate

---

## ❓ Still Having Issues?

### Issue: Backend won't start

**Check:**
```bash
cd backend
python -m pip install -r requirements.txt
```

### Issue: Frontend won't start

**Check:**
```bash
cd frontend
npm install
```

### Issue: Port already in use

**Backend (port 8000):**
```bash
# Find what's using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or use different port
cd backend
python -m uvicorn main:app --reload --port 8001
```

**Frontend (port 5173):**
```bash
# Kill any node processes
taskkill /IM node.exe /F

# Restart frontend
cd frontend
npm run dev
```

### Issue: "Module not found"

**Backend:**
```bash
cd backend
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
rm -rf node_modules
npm install
```

---

## 📊 What's Running?

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | http://localhost:5173 | Your React app (main interface) |
| **Backend API** | http://localhost:8000 | FastAPI server |
| **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| **Health Check** | http://localhost:8000/health | Server status |

---

## ✅ Success Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] http://localhost:8000/health returns healthy
- [ ] http://localhost:5173 loads the app
- [ ] Can register a new user
- [ ] Can login
- [ ] Can upload a document
- [ ] Can see AI-generated tips

---

## 🎉 You're All Set!

Your Customer Onboarding Agent is now running locally. Enjoy testing it!

**Next:** When ready to deploy, check `DEPLOYMENT_OPTIONS.md`

---

## 💡 Pro Tips

1. **Keep both terminals open** while using the app
2. **Check backend logs** if something doesn't work
3. **Use API docs** (http://localhost:8000/docs) to test endpoints directly
4. **Check browser console** (F12) for frontend errors
5. **Database file** is at `backend/customer_onboarding.db`

---

**Need help?** Check the error messages in the terminal windows and let me know what you see!
