# Quick Debug Steps - Upload Issues

## 🚨 Problem
- Upload shows "try again" error
- Document appears after refresh
- Processing fails

## ⚡ Quick Fix (2 minutes)

### 1. Open Test Tool
```bash
# Open in browser
TEST_UPLOAD_MANUALLY.html
```

### 2. Click These Buttons in Order:
1. ✅ "Check Health" → Should show `gemini_available: true`
2. ✅ "Check Auth" → Should show your user info
3. ✅ Select a file and click "Upload & Process"

### 3. If Health Check Fails:
```bash
cd backend
python check_gemini_status.py
```

## 🔍 What to Look For

### Test Tool Shows:
- ❌ `gemini_available: false` → Gemini API issue
- ❌ `401 Unauthorized` → Log in again
- ❌ `503 Service Unavailable` → Backend can't process
- ✅ `200 OK` → Working correctly!

## 🛠️ Common Fixes

### Fix 1: Gemini Not Available
```bash
cd backend
python check_gemini_status.py
# If it fails, check GEMINI_API_KEY in backend/.env
```

### Fix 2: Auth Token Expired
- Log out and log back in
- Or clear browser cache

### Fix 3: Restart Everything
```bash
# Stop backend (Ctrl+C)
# Stop frontend (Ctrl+C)

# Start backend
cd backend
python main.py

# Start frontend (new terminal)
cd frontend
npm run dev
```

## 📊 Check Backend Logs
```bash
cd backend
tail -f logs/app.log
```

Look for:
- "Failed to initialize Gemini client"
- "Error processing document"
- Any red ERROR lines

## ✅ Success Looks Like:

### In Test Tool:
```json
{
  "status": "healthy",
  "gemini_available": true
}
```

### In Frontend:
- Progress goes 0% → 100% smoothly
- Success message appears
- Document shows as "Processed"

## 🆘 Still Broken?

1. Open browser DevTools (F12)
2. Go to Console tab
3. Try upload again
4. Screenshot any red errors
5. Check `DEBUG_UPLOAD_ISSUE.md` for detailed steps

## 📝 Quick Commands

```bash
# Check everything is working
cd backend && python check_gemini_status.py

# Test processing directly
cd backend && python test_document_processing.py

# View real-time logs
cd backend && tail -f logs/app.log

# Check backend health
curl http://localhost:8000/api/scaledown/health
```

---

**TL;DR:** Open `TEST_UPLOAD_MANUALLY.html` → Click "Check Health" → If `gemini_available: false`, run `python check_gemini_status.py`
