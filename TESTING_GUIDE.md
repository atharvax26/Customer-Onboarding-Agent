# Testing Guide - Customer Onboarding Agent

## Quick Local Test

### 1. Start Backend (Terminal 1)

```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

**Test Backend:**
- Open: http://localhost:8000/health
- Should see: `{"status":"healthy"}`
- Open: http://localhost:8000/docs
- Should see: FastAPI interactive documentation

### 2. Start Frontend (Terminal 2)

```bash
cd frontend
npm run dev
```

**Expected Output:**
```
VITE v4.5.0  ready in XXX ms
➜  Local:   http://localhost:5173/
```

**Test Frontend:**
- Open: http://localhost:5173
- Should see: Your React application

### 3. Test Full Flow

1. **Register a User:**
   - Go to http://localhost:5173
   - Click "Register" or "Sign Up"
   - Fill in details
   - Submit

2. **Login:**
   - Use the credentials you just created
   - Should redirect to dashboard

3. **Upload Document:**
   - Click "Upload Document" or similar
   - Select a text file
   - Upload
   - Wait for processing

4. **View Onboarding Tips:**
   - Should see AI-generated tips
   - Verify they make sense

## Deployment Testing Checklist

### If You've Already Deployed:

#### Backend Tests:

1. **Health Check:**
   ```
   https://your-backend-url.com/health
   ```
   Expected: `{"status":"healthy"}`

2. **API Documentation:**
   ```
   https://your-backend-url.com/docs
   ```
   Expected: FastAPI Swagger UI

3. **CORS Test:**
   - Open browser console on frontend
   - Try to login/register
   - Check for CORS errors (should be none)

#### Frontend Tests:

1. **Load Test:**
   ```
   https://your-frontend-url.com
   ```
   Expected: React app loads

2. **API Connection:**
   - Open browser DevTools → Network tab
   - Try to register/login
   - Check API calls go to correct backend URL
   - Verify responses are successful (200 status)

3. **Full User Journey:**
   - Register new user
   - Login
   - Upload document
   - View onboarding tips
   - Logout

### Common Issues & Solutions:

#### Issue 1: CORS Error
**Symptom:** "Access to fetch at 'https://backend...' from origin 'https://frontend...' has been blocked by CORS policy"

**Solution:** Update `backend/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://your-frontend-url.com",  # Add your deployed frontend URL
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Issue 2: Frontend Can't Connect to Backend
**Symptom:** API calls fail, network errors

**Solution:** Check frontend environment variable:
- Vercel/Render: Set `VITE_API_URL=https://your-backend-url.com`
- Rebuild frontend after setting variable

#### Issue 3: Database Not Persisting
**Symptom:** Data disappears after restart

**Solution:** 
- Render: Add persistent disk mounted at `/opt/render/project/src`
- Fly.io: Create volume with `fly volumes create data --size 1`
- Verify `DATABASE_URL` points to correct path

#### Issue 4: 500 Internal Server Error
**Symptom:** Backend returns 500 errors

**Solution:**
- Check backend logs
- Verify `GEMINI_API_KEY` is set correctly
- Verify `SECRET_KEY` is set
- Check database is accessible

## Database Inspection

### Local SQLite Database:

**Location:** `backend/customer_onboarding.db`

**View with DB Browser:**
1. Download: https://sqlitebrowser.org/
2. Open `backend/customer_onboarding.db`
3. Browse tables: users, documents, onboarding_tips

**View with Python:**
```python
import sqlite3

conn = sqlite3.connect('backend/customer_onboarding.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables:", cursor.fetchall())

# View users
cursor.execute("SELECT id, email, created_at FROM users;")
print("Users:", cursor.fetchall())

# View documents
cursor.execute("SELECT id, filename, user_id, created_at FROM documents;")
print("Documents:", cursor.fetchall())

conn.close()
```

### Deployed Database:

**Render:**
- Dashboard → Your Service → Shell
- Run: `sqlite3 customer_onboarding.db`
- SQL commands: `.tables`, `SELECT * FROM users;`

**Fly.io:**
```bash
fly ssh console
sqlite3 /data/customer_onboarding.db
```

## Performance Testing

### Load Test (Optional):

```bash
# Install Apache Bench
# Windows: Download from Apache website
# Mac: brew install httpd

# Test backend health endpoint
ab -n 1000 -c 10 https://your-backend-url.com/health

# Test API endpoint (with auth token)
ab -n 100 -c 5 -H "Authorization: Bearer YOUR_TOKEN" https://your-backend-url.com/api/documents
```

## Monitoring

### Check Logs:

**Local:**
- Backend: `backend/logs/app.log`
- Backend errors: `backend/logs/error.log`

**Deployed:**
- Render: Dashboard → Logs tab
- Fly.io: `fly logs`
- Vercel: Dashboard → Deployments → View Function Logs

### Health Monitoring:

Set up monitoring with:
- UptimeRobot (free): https://uptimerobot.com
- Pingdom
- StatusCake

Monitor these endpoints:
- `https://your-backend-url.com/health`
- `https://your-frontend-url.com`

## Security Checklist

- [ ] GEMINI_API_KEY is set as environment variable (not in code)
- [ ] SECRET_KEY is changed from default
- [ ] CORS is configured for production domain only
- [ ] HTTPS is enabled (automatic on most platforms)
- [ ] Database backups are configured
- [ ] Error messages don't expose sensitive info

## What to Share for Help

If you need help debugging, share:

1. **Platform:** Where did you deploy? (Render, Vercel, etc.)
2. **URLs:** 
   - Frontend URL
   - Backend URL
3. **Error Message:** Exact error from browser console or logs
4. **What You Tried:** Steps you took before the error
5. **Screenshots:** Of error messages or unexpected behavior

## Quick Verification Commands

```bash
# Check if backend is running
curl https://your-backend-url.com/health

# Check if frontend is accessible
curl -I https://your-frontend-url.com

# Test API endpoint (replace with your URL)
curl https://your-backend-url.com/api/health
```

---

## Next Steps

1. Test locally first (if not already done)
2. Deploy to chosen platform
3. Test deployed version
4. Share URLs and any issues you encounter
5. I'll help debug based on the specific errors

**Ready to test?** Start with the local test above, then share your deployment URLs and I'll guide you through verification!
