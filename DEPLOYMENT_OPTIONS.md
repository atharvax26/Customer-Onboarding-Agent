# Deployment Options for Customer Onboarding Agent

**Date**: February 7, 2026  
**Status**: Ready to Deploy

---

## Your Project is Clean and Ready! ✅

All unnecessary files have been removed. Your repository is now production-ready and can be deployed to any platform.

---

## Recommended Deployment Platforms

### 🥇 Option 1: Render (Recommended - Easiest)

**Why Render?**
- ✅ Free tier available
- ✅ Supports SQLite with persistent disks
- ✅ Auto-deploy from GitHub
- ✅ Separate services for frontend/backend
- ✅ Built-in PostgreSQL (when you're ready to upgrade)
- ✅ Automatic HTTPS

**Pricing**: Free tier (with limitations), then $7/month per service

**Steps to Deploy:**

1. **Go to**: https://render.com
2. **Sign up** with GitHub
3. **Create Web Service** for Backend:
   - Connect your repository
   - **Root Directory**: `backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Add Environment Variables**:
     ```
     GEMINI_API_KEY=your_key
     DATABASE_URL=sqlite:///./customer_onboarding.db
     SECRET_KEY=your_secret_key
     ```
   - **Add Disk**: Mount at `/opt/render/project/src` for SQLite persistence

4. **Create Static Site** for Frontend:
   - Connect same repository
   - **Root Directory**: `frontend`
   - **Build Command**: `npm install && npm run build`
   - **Publish Directory**: `dist`
   - **Add Environment Variable**:
     ```
     VITE_API_URL=https://your-backend-url.onrender.com
     ```

5. **Update CORS** in `backend/main.py`:
   ```python
   allow_origins=[
       "https://your-frontend-url.onrender.com"
   ]
   ```

---

### 🥈 Option 2: Fly.io (Good Performance)

**Why Fly.io?**
- ✅ Excellent performance (edge deployment)
- ✅ Supports SQLite with volumes
- ✅ Free tier: 3 VMs, 3GB storage
- ✅ Simple CLI deployment
- ✅ Docker-based

**Pricing**: Free tier, then ~$5-20/month

**Steps to Deploy:**

1. **Install Fly CLI**:
   ```bash
   # Windows (PowerShell)
   iwr https://fly.io/install.ps1 -useb | iex
   ```

2. **Login**:
   ```bash
   fly auth login
   ```

3. **Deploy Backend**:
   ```bash
   cd backend
   fly launch
   # Follow prompts, select region
   fly volumes create data --size 1
   fly secrets set GEMINI_API_KEY=your_key
   fly deploy
   ```

4. **Deploy Frontend**:
   ```bash
   cd frontend
   fly launch
   fly deploy
   ```

---

### 🥉 Option 3: DigitalOcean App Platform

**Why DigitalOcean?**
- ✅ Simple deployment
- ✅ Good documentation
- ✅ Supports Docker Compose
- ✅ Predictable pricing
- ✅ Good for learning

**Pricing**: $5-12/month per service

**Steps to Deploy:**

1. **Go to**: https://cloud.digitalocean.com/apps
2. **Create App** → Connect GitHub
3. **Configure Backend**:
   - **Source Directory**: `backend`
   - **Type**: Web Service
   - **Build Command**: `pip install -r requirements.txt`
   - **Run Command**: `uvicorn main:app --host 0.0.0.0 --port 8080`
   - **Environment Variables**: Add GEMINI_API_KEY, etc.

4. **Configure Frontend**:
   - **Source Directory**: `frontend`
   - **Type**: Static Site
   - **Build Command**: `npm install && npm run build`
   - **Output Directory**: `dist`

---

### 🏢 Option 4: AWS (Enterprise-Grade)

**Why AWS?**
- ✅ Most scalable
- ✅ Enterprise features
- ✅ Global infrastructure
- ✅ Many services available

**Pricing**: ~$20-100/month (depending on usage)

**Services to Use:**
- **Backend**: ECS Fargate or App Runner
- **Frontend**: S3 + CloudFront
- **Database**: RDS PostgreSQL (recommended over SQLite)
- **Storage**: S3 for uploaded documents

**Complexity**: High (requires AWS knowledge)

---

### 🚀 Option 5: Vercel (Frontend) + Backend Elsewhere

**Why This Combo?**
- ✅ Vercel is excellent for React/Vite
- ✅ Free tier for frontend
- ✅ Deploy backend to Render/Fly.io

**Steps:**

1. **Deploy Frontend to Vercel**:
   - Go to https://vercel.com
   - Import your GitHub repository
   - **Root Directory**: `frontend`
   - **Framework**: Vite
   - **Environment Variable**: `VITE_API_URL=your_backend_url`

2. **Deploy Backend to Render** (see Option 1)

---

## Quick Comparison

| Platform | Ease of Use | SQLite Support | Free Tier | Best For |
|----------|-------------|----------------|-----------|----------|
| **Render** | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ Yes | Quick deployment |
| **Fly.io** | ⭐⭐⭐⭐ | ✅ Yes | ✅ Yes | Performance |
| **DigitalOcean** | ⭐⭐⭐⭐ | ✅ Yes | ❌ No | Learning |
| **AWS** | ⭐⭐ | ⚠️ Use RDS | ❌ No | Enterprise |
| **Vercel** | ⭐⭐⭐⭐⭐ | ❌ No | ✅ Yes | Frontend only |

---

## Environment Variables Needed

For any platform, you'll need these environment variables:

### Backend:
```
GEMINI_API_KEY=your_gemini_api_key
SECRET_KEY=your_secret_key_for_jwt
DATABASE_URL=sqlite:///./customer_onboarding.db
FRONTEND_URL=https://your-frontend-url.com
```

### Frontend:
```
VITE_API_URL=https://your-backend-url.com
```

---

## Database Considerations

### Current: SQLite
- ✅ Good for: Development, small projects, single-server deployments
- ❌ Not good for: Multiple servers, high concurrency

### Recommended for Production: PostgreSQL
- ✅ Better for: Scaling, multiple servers, high traffic
- ✅ Available on: Render, Fly.io, DigitalOcean, AWS RDS

**Migration Path:**
1. Deploy with SQLite first (easier)
2. Migrate to PostgreSQL when you need to scale
3. Update `DATABASE_URL` environment variable
4. Run migrations: `alembic upgrade head`

---

## Pre-Deployment Checklist

- [ ] Choose hosting platform
- [ ] Create account on chosen platform
- [ ] Prepare environment variables
- [ ] Update CORS settings for production domain
- [ ] Test locally one more time
- [ ] Commit and push all changes
- [ ] Deploy backend first
- [ ] Get backend URL
- [ ] Deploy frontend with backend URL
- [ ] Test deployed application
- [ ] Monitor logs for errors

---

## Post-Deployment

### Testing Your Deployment:

1. **Backend Health Check**:
   ```
   https://your-backend-url.com/health
   ```
   Should return: `{"status": "healthy"}`

2. **API Documentation**:
   ```
   https://your-backend-url.com/docs
   ```
   Should show FastAPI interactive docs

3. **Frontend**:
   ```
   https://your-frontend-url.com
   ```
   Should load your React app

4. **Test Full Flow**:
   - Register a new user
   - Login
   - Upload a document
   - Check onboarding tips
   - Verify everything works

### Monitoring:

- Check application logs regularly
- Set up error alerts
- Monitor API response times
- Track user registrations

---

## My Recommendation

**Start with Render** (Option 1):
- Easiest to set up
- Free tier to test
- Supports SQLite
- Can upgrade to PostgreSQL later
- Good documentation
- Auto-deploy from GitHub

**Time to Deploy**: 15-30 minutes

---

## Need Help?

1. Choose a platform from above
2. Follow the steps for that platform
3. If you get stuck, let me know which platform you chose and what error you're seeing

---

**Your repository is clean and ready!** Pick a platform and let's deploy! 🚀
