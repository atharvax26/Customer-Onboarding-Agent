# Analytics Page Diagnostic & Fix Guide

## 🔍 Current Status

The Analytics page is showing a "Page Error" which means the ErrorBoundary caught a JavaScript error during rendering.

## 📋 Changes Made

### Backend Changes:
1. ✅ Fixed `analytics_service.py` - Changed `recent_interventions` to `total_interventions_today`
2. ✅ Backend endpoint should now return correct field names

### Frontend Changes:
1. ✅ Added better error handling in `Analytics.tsx`
2. ✅ Fixed useEffect dependencies
3. ✅ Added individual error catching for each API call

### Test Pages Created:
1. ✅ `/analytics-simple` - Basic page to test if routing works
2. ✅ `/analytics-test` - Tests just the real-time metrics API
3. ✅ `/analytics-full` - Full analytics page (original)

## 🧪 Diagnostic Steps

### Step 1: Test Simple Page
1. Navigate to: `http://localhost:5173/analytics-simple`
2. **If this works**: The routing and authentication are fine
3. **If this fails**: There's an issue with routing or auth

### Step 2: Test API Connection
1. Navigate to: `http://localhost:5173/analytics-test`
2. Check browser console (F12) for errors
3. **If this works**: The API connection is fine
4. **If this fails**: Backend issue or API client problem

### Step 3: Check Error Details
1. On the error page, click "Error Details (Development Only)"
2. Look for:
   - **Error Message**: What went wrong
   - **Stack Trace**: Where it happened
   - **Component Stack**: Which component failed

### Step 4: Check Browser Console
1. Press F12 to open Developer Tools
2. Go to Console tab
3. Look for red error messages
4. Common errors:
   - Import errors: "Cannot find module..."
   - Type errors: "undefined is not an object..."
   - Network errors: "Failed to fetch..."

### Step 5: Check Network Tab
1. In Developer Tools, go to Network tab
2. Refresh the page
3. Look for failed requests (red)
4. Click on failed requests to see:
   - Status code (401, 403, 404, 500, etc.)
   - Response body
   - Request headers

## 🔧 Common Issues & Fixes

### Issue 1: Backend Not Restarted
**Symptom**: API returns old field names
**Fix**:
```bash
# Stop backend (Ctrl+C)
cd backend
uvicorn main:app --reload
```

### Issue 2: Import Error
**Symptom**: "Cannot find module" or "undefined"
**Fix**: Check that all components are properly exported in `frontend/src/components/analytics/index.ts`

### Issue 3: Type Mismatch
**Symptom**: TypeScript errors or undefined properties
**Fix**: Check that backend response matches frontend types in `frontend/src/types/analytics.ts`

### Issue 4: Authentication Issue
**Symptom**: 401 or 403 errors
**Fix**: 
- Make sure you're logged in as Admin
- Check that token is valid
- Try logging out and back in

### Issue 5: Missing Data
**Symptom**: Components fail because data is null/undefined
**Fix**: Add null checks in components

## 🐛 Debug Commands

### Test Backend Endpoint Directly:
```bash
cd backend
python test_analytics_endpoint.py
```

### Check Backend Logs:
Look at the terminal where backend is running for error messages

### Check Frontend Build:
```bash
cd frontend
npm run build
```

## 📊 What to Report

If the issue persists, please provide:

1. **Error Message** from "Error Details" section
2. **Browser Console** errors (screenshot or copy/paste)
3. **Network Tab** - any failed requests
4. **Which test page works**:
   - `/analytics-simple` - Works? Yes/No
   - `/analytics-test` - Works? Yes/No
   - `/analytics-full` - Works? Yes/No

## 🎯 Next Steps

1. **First**: Try `/analytics-simple` to see if basic page loads
2. **Second**: Try `/analytics-test` to test API
3. **Third**: Check error details and browser console
4. **Fourth**: Report findings with the information above

## 🔄 Quick Reset

If nothing works, try this:

```bash
# Backend
cd backend
# Stop server (Ctrl+C)
rm customer_onboarding.db
alembic upgrade head
uvicorn main:app --reload

# Frontend (in new terminal)
cd frontend
rm -rf node_modules
npm install
npm run dev
```

## ✅ Success Criteria

The Analytics page should:
- Load without errors
- Show real-time metrics
- Display activation rates chart
- Show dropoff analysis
- Display engagement trends
- Allow filtering by role/date
- Refresh data automatically

---

**Created**: February 7, 2026
**Status**: Awaiting diagnostic results
