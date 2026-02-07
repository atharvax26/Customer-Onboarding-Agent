# Debugging Upload & Processing Issues

## Current Status

✅ Gemini API Key is configured and working
✅ Backend can process documents
✅ Document uploads successfully
❌ Frontend shows "try again" error despite successful upload
❌ Processing may be failing silently

## Steps to Debug

### 1. Check Browser Console

Open browser DevTools (F12) and check for errors:

**Look for:**
- Network errors (red in Network tab)
- Console errors (red in Console tab)
- Failed API calls
- CORS errors
- Authentication errors (401)

**Common Issues:**
- `401 Unauthorized` - Auth token expired or missing
- `503 Service Unavailable` - Gemini API not initialized
- `CORS error` - Backend not allowing frontend origin
- `Network Error` - Backend not running

### 2. Check Backend Logs

Look at `backend/logs/app.log` for errors:

```bash
cd backend
tail -f logs/app.log
```

**Look for:**
- "Failed to initialize Gemini client"
- "Error processing document"
- "HTTPException"
- Stack traces

### 3. Test Upload Manually

#### Test with curl:

```bash
# Get auth token first
TOKEN="your_jwt_token_here"

# Upload document
curl -X POST http://localhost:8000/api/scaledown/upload-and-process \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@test.txt"
```

#### Expected Response:
```json
{
  "id": 1,
  "filename": "test.txt",
  "summary": "...",
  "tasks": [...],
  "processing_time": 2.5
}
```

#### Error Responses:
- `401`: Token missing or invalid
- `503`: Gemini API not available
- `500`: Processing error

### 4. Check Frontend Network Tab

1. Open DevTools → Network tab
2. Upload a document
3. Find the `upload-and-process` request
4. Check:
   - Status code (should be 200)
   - Response body
   - Request headers (Authorization present?)
   - Response time

### 5. Common Issues & Fixes

#### Issue: "Try again" but document uploaded
**Cause:** Upload succeeds but processing fails
**Check:**
- Backend logs for processing errors
- Network tab for 503 or 500 errors
- Gemini API status

**Fix:**
```bash
cd backend
python check_gemini_status.py
```

#### Issue: Progress stuck at 50%
**Cause:** Processing taking too long or timing out
**Check:**
- Document size (should be < 10MB)
- Backend logs for timeout errors
- Network tab for request duration

**Fix:**
- Use smaller documents
- Check Gemini API quota
- Increase timeout in frontend

#### Issue: 401 Unauthorized
**Cause:** Auth token expired or missing
**Fix:**
- Log out and log back in
- Check localStorage for 'auth_token'
- Verify token in Network tab headers

#### Issue: CORS Error
**Cause:** Backend not allowing frontend origin
**Fix:**
Check `backend/.env`:
```
CORS_ORIGINS=http://localhost:5173,http://localhost:5174
```

### 6. Enable Debug Mode

#### Backend:
Edit `backend/.env`:
```
DEBUG=true
LOG_LEVEL=DEBUG
```

Restart backend:
```bash
cd backend
python main.py
```

#### Frontend:
Add to browser console:
```javascript
localStorage.setItem('debug', 'true')
```

### 7. Test Processing Separately

If upload works but processing fails:

```bash
cd backend
python test_document_processing.py
```

This will show exactly where processing fails.

### 8. Check Database

```bash
cd backend
python -c "import sqlite3; conn = sqlite3.connect('customer_onboarding.db'); cursor = conn.cursor(); cursor.execute('SELECT id, filename, processed_summary IS NOT NULL as processed FROM documents'); print([row for row in cursor.fetchall()])"
```

Shows which documents are processed vs unprocessed.

## Quick Fixes

### Fix 1: Restart Everything
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

### Fix 2: Clear Browser Cache
1. Open DevTools (F12)
2. Right-click refresh button
3. Select "Empty Cache and Hard Reload"
4. Log out and log back in

### Fix 3: Check Gemini API
```bash
cd backend
python check_gemini_status.py
```

If it fails, check your API key at:
https://makersuite.google.com/app/apikey

### Fix 4: Reset Upload State
In browser console:
```javascript
localStorage.clear()
location.reload()
```

## Expected Behavior

### Successful Upload & Process:
1. Select file
2. Progress: 0% → 50% (uploading)
3. Progress: 50% → 100% (processing)
4. Success message appears
5. Form resets after 3 seconds
6. Document appears in list as "Processed"

### Successful Upload, Failed Process:
1. Select file
2. Progress: 0% → 50% (uploading)
3. Error message appears
4. Document appears in list as "Uploaded" (not processed)
5. Can click "Process" button to retry

## Report Issues

If problem persists, provide:
1. Browser console errors (screenshot)
2. Network tab for failed request (screenshot)
3. Backend logs (last 50 lines)
4. Steps to reproduce
5. Document type and size

## Contact

Check these files for more info:
- `UPLOAD_PROCESSING_FIX.md` - Recent fixes
- `QUICK_UPLOAD_FIX_SUMMARY.md` - Quick reference
- `backend/logs/app.log` - Backend logs
