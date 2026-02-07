# Final Upload & Processing Debug Guide

## Current Situation

You're experiencing:
1. ✅ Document uploads successfully to backend
2. ❌ Frontend shows "try again" error
3. ❌ Need to refresh page to see uploaded document
4. ❌ Processing may fail silently

## Root Cause Analysis

The issue is likely one of these:

### 1. **Gemini API Not Initialized** (Most Likely)
- Backend uploads document successfully
- Processing fails because Gemini client is None
- Returns 503 error
- Frontend doesn't handle 503 properly

### 2. **Frontend Error Handling**
- Error response format doesn't match expected format
- Progress state not properly reset
- Error message not displayed correctly

### 3. **CORS or Network Issues**
- Request completes but response blocked
- Timeout during processing
- Network interruption

## Immediate Debugging Steps

### Step 1: Use the Test Tool

Open `TEST_UPLOAD_MANUALLY.html` in your browser:

```bash
# From project root
open TEST_UPLOAD_MANUALLY.html
# or
start TEST_UPLOAD_MANUALLY.html
```

This will show you:
1. Backend health status
2. Gemini API availability
3. Authentication status
4. Exact error responses

### Step 2: Check Backend Health

Visit: http://localhost:8000/api/scaledown/health

Expected response:
```json
{
  "status": "healthy",
  "gemini_available": true
}
```

If `gemini_available` is `false`:
```bash
cd backend
python check_gemini_status.py
```

### Step 3: Check Browser Console

1. Open DevTools (F12)
2. Go to Console tab
3. Try uploading a document
4. Look for errors (red text)

Common errors:
- `401 Unauthorized` → Log in again
- `503 Service Unavailable` → Gemini API issue
- `CORS error` → Backend CORS config
- `Network Error` → Backend not running

### Step 4: Check Network Tab

1. Open DevTools (F12)
2. Go to Network tab
3. Upload a document
4. Find `upload-and-process` request
5. Check:
   - Status code (should be 200)
   - Response tab (see actual error)
   - Headers tab (Authorization present?)

## Fixes

### Fix 1: Gemini API Not Available

**Check:**
```bash
cd backend
python check_gemini_status.py
```

**If it fails:**
1. Check `backend/.env` has `GEMINI_API_KEY`
2. Get new key from: https://makersuite.google.com/app/apikey
3. Restart backend

### Fix 2: Frontend Not Handling Errors

The code has been updated to:
- ✅ Handle 503 errors specifically
- ✅ Show clear error messages
- ✅ Reset progress on errors
- ✅ Auto-reset on success

**To apply:**
1. Make sure you have latest code
2. Restart frontend:
```bash
cd frontend
npm run dev
```

### Fix 3: Backend Not Logging Errors

The code has been updated to:
- ✅ Log all upload attempts
- ✅ Log processing errors with stack traces
- ✅ Include user ID in logs

**To apply:**
1. Restart backend:
```bash
cd backend
python main.py
```

2. Check logs:
```bash
tail -f backend/logs/app.log
```

### Fix 4: Clear Everything and Start Fresh

```bash
# Stop all servers

# Backend
cd backend
rm -rf __pycache__ app/__pycache__
python main.py

# Frontend (new terminal)
cd frontend
rm -rf node_modules/.vite
npm run dev

# Browser
# Clear cache (Ctrl+Shift+Delete)
# Clear localStorage (F12 → Application → Local Storage → Clear)
# Refresh page
```

## Testing Procedure

### Test 1: Health Check
1. Visit: http://localhost:8000/api/scaledown/health
2. Verify: `"gemini_available": true`
3. If false, run `python check_gemini_status.py`

### Test 2: Manual Upload
1. Open `TEST_UPLOAD_MANUALLY.html`
2. Click "Check Health" → Should be healthy
3. Click "Check Auth" → Should be authenticated
4. Select a file
5. Click "Upload & Process"
6. Watch progress bar
7. Check result

### Test 3: Frontend Upload
1. Go to Documents page
2. Upload a document
3. Watch progress (should go 0% → 100%)
4. Should see success message
5. Form should auto-reset after 3 seconds
6. Document should appear in list

## Expected Behavior

### Success Flow:
```
1. User selects file
2. Progress: 0-50% "Uploading..."
3. Progress: 50-70% "Analyzing document content..."
4. Progress: 70-90% "Generating onboarding steps..."
5. Progress: 90-100% "Finalizing..."
6. Success message appears
7. Form resets after 3 seconds
8. Document appears in list as "Processed"
```

### Error Flow (Gemini Unavailable):
```
1. User selects file
2. Progress: 0-50% "Uploading..."
3. Error: "Gemini AI service not available"
4. Document appears in list as "Uploaded" (not processed)
5. Can click "Process" button to retry
```

## Files Modified

### Backend:
1. `backend/app/routers/scaledown.py` - Added logging
2. `backend/app/services/gemini_client.py` - Better error handling
3. `backend/check_gemini_status.py` - New diagnostic tool
4. `backend/test_document_processing.py` - New test script

### Frontend:
1. `frontend/src/services/apiClient.ts` - Better progress & error handling
2. `frontend/src/components/document/DocumentUpload.tsx` - Enhanced error handling

### Documentation:
1. `DEBUG_UPLOAD_ISSUE.md` - Comprehensive debug guide
2. `UPLOAD_PROCESSING_FIX.md` - Technical details
3. `TEST_UPLOAD_MANUALLY.html` - Manual test tool
4. `FINAL_UPLOAD_DEBUG_GUIDE.md` - This file

## Quick Commands

```bash
# Check Gemini status
cd backend && python check_gemini_status.py

# Test processing
cd backend && python test_document_processing.py

# Check backend health
curl http://localhost:8000/api/scaledown/health

# View logs
tail -f backend/logs/app.log

# Restart backend
cd backend && python main.py

# Restart frontend
cd frontend && npm run dev
```

## Still Having Issues?

1. **Open `TEST_UPLOAD_MANUALLY.html`** - This will show exact errors
2. **Check backend logs** - `backend/logs/app.log`
3. **Check browser console** - F12 → Console tab
4. **Check network tab** - F12 → Network tab
5. **Run diagnostic scripts**:
   - `python check_gemini_status.py`
   - `python test_document_processing.py`

## Report Issues

If problem persists, provide:
1. Screenshot of `TEST_UPLOAD_MANUALLY.html` results
2. Browser console errors
3. Network tab screenshot of failed request
4. Last 50 lines of `backend/logs/app.log`
5. Output of `python check_gemini_status.py`

---

**Last Updated:** February 7, 2026
**Status:** Debugging tools and enhanced error handling added
