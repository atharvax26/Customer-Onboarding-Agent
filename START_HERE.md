# 🚀 Start Your Customer Onboarding Agent

## Quick Start (2 Steps)

### Step 1: Start Backend

**Option A - Double Click:**
- Double-click `start-backend.bat`
- A terminal window will open
- Wait for: "Application startup complete"
- Keep this window open!

**Option B - Manual:**
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Backend will be running at:**
- 🌐 API: http://localhost:8000
- 📚 API Docs: http://localhost:8000/docs
- ❤️ Health Check: http://localhost:8000/health

---

### Step 2: Start Frontend (New Terminal)

**Option A - Double Click:**
- Double-click `start-frontend.bat`
- A new terminal window will open
- Wait for: "Local: http://localhost:5173/"
- Keep this window open!

**Option B - Manual:**
```bash
cd frontend
npm run dev
```

**Frontend will be running at:**
- 🌐 App: http://localhost:5173

---

## 🎉 You're Ready!

1. **Open your browser:** http://localhost:5173
2. **Register a new account**
3. **Login**
4. **Upload a document** (any .txt file)
5. **See AI-generated onboarding tips!**

---

## 🔍 Testing the Backend

### Test 1: Health Check
Open: http://localhost:8000/health

**Expected:**
```json
{"status": "healthy"}
```

### Test 2: API Documentation
Open: http://localhost:8000/docs

**Expected:**
- Interactive API documentation (Swagger UI)
- Try out endpoints directly

### Test 3: Database
Check: `backend/customer_onboarding.db`
- This file is created automatically
- Contains all your data (users, documents, tips)

---

## 📱 What You'll See

### Frontend (http://localhost:5173)
- Landing page with Register/Login
- Dashboard after login
- Document upload interface
- Onboarding tips display
- User profile

### Backend (http://localhost:8000/docs)
- All API endpoints
- Authentication endpoints
- Document processing endpoints
- User management endpoints

---

## 🛑 To Stop

1. **Backend:** Press `Ctrl+C` in the backend terminal
2. **Frontend:** Press `Ctrl+C` in the frontend terminal

---

## ❓ Troubleshooting

### Backend won't start:
```bash
# Check if port 8000 is already in use
netstat -ano | findstr :8000

# If something is using it, kill the process or use different port:
python -m uvicorn main:app --reload --port 8001
```

### Frontend won't start:
```bash
# Install dependencies first
cd frontend
npm install

# Then start
npm run dev
```

### "Module not found" errors:
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Database errors:
```bash
# Reset database
cd backend
rm customer_onboarding.db
python -m alembic upgrade head
```

---

## 🎯 Quick Demo Flow

1. **Start both servers** (backend + frontend)
2. **Open** http://localhost:5173
3. **Register** with:
   - Email: test@example.com
   - Password: Test123!
   - Name: Test User
4. **Login** with same credentials
5. **Upload a document:**
   - Create a simple .txt file with product info
   - Upload it
   - Wait 5-10 seconds
6. **View onboarding tips:**
   - AI-generated tips appear
   - Based on your document content

---

## 📊 What's Happening Behind the Scenes

1. **Backend** receives document upload
2. **Gemini AI** analyzes the document
3. **Tips are generated** based on content
4. **Stored in database** (SQLite)
5. **Frontend displays** the tips

---

## 🔗 Useful URLs

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:5173 | Main application |
| Backend API | http://localhost:8000 | API server |
| API Docs | http://localhost:8000/docs | Interactive API docs |
| Health Check | http://localhost:8000/health | Server status |

---

## 🎨 Next Steps

After testing locally:
1. ✅ Verify everything works
2. ✅ Test all features
3. ✅ Check database is saving data
4. ✅ Ready to deploy!

See `DEPLOYMENT_OPTIONS.md` for deployment guides.

---

**Enjoy your Customer Onboarding Agent!** 🚀
