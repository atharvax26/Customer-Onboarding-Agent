# Customer Onboarding Agent - Complete Documentation

**Last Updated**: February 6, 2026  
**Version**: 2.0  
**Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Project Overview](#project-overview)
3. [Architecture](#architecture)
4. [Installation](#installation)
5. [Features](#features)
6. [AI Integration (Gemini)](#ai-integration-gemini)
7. [Error Handling System](#error-handling-system)
8. [API Documentation](#api-documentation)
9. [Frontend Components](#frontend-components)
10. [Testing](#testing)
11. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Google Gemini API key

### Get Running in 3 Steps

#### Step 1: Install Node.js (if not installed)
1. Download from https://nodejs.org/ (LTS version)
2. Run installer and ensure "Add to PATH" is checked
3. Verify: `node --version` and `npm --version`

#### Step 2: Start Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Backend runs at: http://localhost:8000

#### Step 3: Start Frontend
```bash
cd frontend
npm install
npm run dev
```
Frontend runs at: http://localhost:5173

### Quick Test
- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

---

## 📖 Project Overview

A single-tenant SaaS platform that transforms product documentation into personalized, role-based onboarding experiences using AI-powered document processing and real-time engagement analytics.

### Key Features
- ✅ **AI-Powered Document Processing** - Uses Google Gemini AI to generate onboarding guides
- ✅ **Role-Based Onboarding** - Customized flows for Developers, Business Users, and Admins
- ✅ **Real-Time Engagement Scoring** - Monitors user activity and calculates engagement
- ✅ **Automated Interventions** - Provides contextual help when engagement drops
- ✅ **Analytics Dashboard** - Comprehensive reporting on activation rates
- ✅ **Enhanced Error Handling** - Multi-layered error tracking and recovery
- ✅ **Interactive Step-by-Step Guides** - Expandable tasks with progress tracking

### Tech Stack
- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: React, TypeScript, Vite
- **AI**: Google Gemini AI
- **Testing**: pytest + Hypothesis (backend), Vitest (frontend)

---

## 🏗️ Architecture

### Project Structure
```
customer-onboarding-agent/
├── backend/
│   ├── app/
│   │   ├── database.py              # SQLAlchemy models
│   │   ├── routers/                 # API endpoints
│   │   ├── services/
│   │   │   ├── gemini_client.py     # Gemini AI integration
│   │   │   ├── error_tracking_service.py
│   │   │   └── system_monitor.py
│   │   ├── error_handlers.py        # Global error handling
│   │   └── exceptions.py            # Custom exceptions
│   ├── tests/                       # Backend tests
│   ├── main.py                      # FastAPI app entry
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── onboarding/          # Onboarding components
│   │   │   └── ErrorBoundary.tsx    # Error boundary
│   │   ├── pages/                   # Page components
│   │   ├── services/
│   │   │   ├── apiClient.ts         # API client
│   │   │   └── engagementService.ts
│   │   └── hooks/
│   │       └── useErrorHandler.ts   # Error handling hook
│   ├── package.json
│   └── vite.config.ts
└── docker-compose.yml
```

### Data Flow
```
User Upload → Gemini AI Processing → Database Storage → 
Role-Based Onboarding → Engagement Tracking → Analytics
```

---

## 💻 Installation

### Environment Setup

1. **Clone Repository**
```bash
git clone <repository-url>
cd customer-onboarding-agent
```

2. **Configure Environment Variables**
```bash
cp .env.example .env
```

Edit `.env` file:
```env
# Gemini AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Database
DATABASE_URL=sqlite:///./customer_onboarding.db

# Security
SECRET_KEY=your_secret_key_here
```

3. **Backend Setup**
```bash
cd backend
pip install -r requirements.txt

# Run migrations (if needed)
alembic upgrade head

# Start server
uvicorn main:app --reload
```

4. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

### Docker Setup (Alternative)
```bash
docker-compose up -d
```

---

## ✨ Features

### 1. AI-Powered Document Processing

**How It Works:**
- Upload PDF documents
- Gemini AI analyzes content
- Generates 5-7 actionable onboarding steps
- Creates role-specific subtasks
- Estimates time for each step

**Supported Formats:**
- PDF documents
- Text files
- Markdown files

### 2. Role-Based Onboarding

**Developer Role:**
- 5 technical steps
- Code examples
- API integration guides
- Testing instructions

**Business User Role:**
- 3 workflow-focused steps
- No technical jargon
- Business process focus
- UI/UX guidance

**Admin Role:**
- Configuration steps
- Security setup
- User management
- System monitoring

### 3. Interactive Step-by-Step Guides

**Features:**
- ✅ Expandable task cards
- ✅ Checkbox tracking for sub-steps
- ✅ Progress bars per task
- ✅ Contextual tips and best practices
- ✅ Code examples with copy button
- ✅ Mobile-responsive design

**Progress Tracking:**
- Per-task completion (e.g., "3/5 steps")
- Visual progress bars
- Real-time updates
- Overall completion percentage

### 4. Engagement Tracking

**Metrics Tracked:**
- Page views
- Time on page
- Task completions
- Document interactions
- Click events

**Engagement Score:**
- Calculated in real-time
- Ranges from 0-100
- Triggers interventions when low
- Displayed in analytics dashboard

### 5. Analytics Dashboard (Admin Only)

**Metrics:**
- Total users
- Active onboarding sessions
- Completion rates
- Average engagement scores
- Document processing stats

---

## 🤖 AI Integration (Gemini)

### Current Status
✅ **Fully Operational** - Gemini AI is integrated and working

### Configuration

**API Key Setup:**
```env
GEMINI_API_KEY=AIzaSyDBUT-2IPillQpJSH5VPZXQCKHXEYhffuc
```

### How Gemini Processes Documents

1. **Document Analysis**
   - Reads entire document content
   - Identifies key concepts and topics
   - Understands structure and flow

2. **Guide Generation**
   - Creates concise summary
   - Generates 5-7 actionable steps
   - Provides detailed descriptions
   - Creates specific subtasks
   - Estimates time for each step

3. **Personalization**
   - Tailors content to user role
   - Focuses on practical actions
   - Uses clear, professional language

### Reprocess Existing Documents

If you have documents with mock data, reprocess them:

```bash
cd backend
python reprocess_with_gemini.py <document_id>
```

Example:
```bash
python reprocess_with_gemini.py 1
```

**Expected Output:**
- Document loaded from database
- Sent to Gemini AI for analysis
- 5-7 detailed steps generated
- Subtasks created for each step
- Saved to database
- Processing time: 30-60 seconds

### Best Practices for Documents

**✅ Good Documents:**
- Clear structure with headings
- Detailed explanations
- Step-by-step instructions
- Examples and use cases
- Technical specifications
- 500+ words

**❌ Avoid:**
- Very short documents (< 500 words)
- Pure image-based PDFs
- Heavily formatted tables without context
- Documents without clear topics

---

## 🛡️ Error Handling System

### Overview

Comprehensive, multi-layered error handling with:
- Consistent error responses
- Real-time error tracking
- Pattern detection
- Automated alerting
- Frontend error boundaries
- System health monitoring

### Backend Error Handling

**Custom Exceptions:**
- `DocumentProcessingError`
- `AuthenticationError`
- `AuthorizationError`
- `OnboardingError`
- `EngagementTrackingError`
- `DatabaseError`
- `ValidationError`
- `RateLimitError`
- `SystemHealthError`

**Error Response Format:**
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Technical message",
    "user_message": "User-friendly explanation",
    "details": {},
    "request_id": "unique-id",
    "timestamp": "2024-01-01T00:00:00Z",
    "suggestions": ["Suggestion 1", "Suggestion 2"],
    "recovery_actions": ["Action 1", "Action 2"]
  }
}
```

**Error Tracking Service:**
- Centralized error event tracking
- Pattern detection and analysis
- Error rate monitoring
- Severity-based alerting
- Trend analysis

**System Monitor:**
- Real-time health monitoring
- Component-specific checks
- Automated alerting
- Performance metrics
- Alert deduplication

### Frontend Error Handling

**Error Boundary:**
- Multiple severity levels (critical, page, component)
- Automatic retry with exponential backoff
- Error reporting integration
- User-friendly error messages
- Recovery action buttons

**Error Handler Hook:**
```typescript
const { handleError, handleAsyncError } = useErrorHandler({
  context: 'DocumentUpload',
  maxRetries: 3
})

// Handle async operations
const result = await handleAsyncError(
  () => uploadDocument(file),
  'document-upload',
  null,
  {
    retry: () => uploadDocument(file),
    fallback: () => showOfflineMessage()
  }
)
```

### Health Check Endpoints

- `GET /health` - Overall system health
- `GET /health/{component}` - Component health
- `GET /health-history` - Historical data (Admin)
- `GET /api/system/alerts` - System alerts (Admin)
- `GET /api/system/metrics` - System metrics (Admin)

---

## 📡 API Documentation

### Authentication Endpoints

**Register User**
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password",
  "role": "developer"
}
```

**Login**
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password"
}
```

### Document Endpoints

**Upload Document**
```http
POST /api/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <pdf_file>
```

**Get Documents**
```http
GET /api/documents
Authorization: Bearer <token>
```

**Get Document by ID**
```http
GET /api/documents/{document_id}
Authorization: Bearer <token>
```

### Onboarding Endpoints

**Start Onboarding**
```http
POST /api/onboarding/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "document_id": 1
}
```

**Get Onboarding Steps**
```http
GET /api/onboarding/steps
Authorization: Bearer <token>
```

**Complete Step**
```http
POST /api/onboarding/steps/{step_id}/complete
Authorization: Bearer <token>
```

### Engagement Endpoints

**Track Interaction**
```http
POST /engagement/track-interaction
Authorization: Bearer <token>
Content-Type: application/json

{
  "event_type": "page_view",
  "page_url": "/onboarding",
  "additional_data": {}
}
```

**Get Engagement Score**
```http
GET /engagement/score
Authorization: Bearer <token>
```

### Analytics Endpoints (Admin Only)

**Get Analytics**
```http
GET /api/analytics
Authorization: Bearer <admin_token>
```

**Interactive API Documentation:**
Visit http://localhost:8000/docs for Swagger UI

---

## 🎨 Frontend Components

### Key Components

**1. ErrorBoundary**
- Catches React errors
- Provides retry functionality
- Shows user-friendly messages
- Tracks errors

**2. StepContent**
- Displays onboarding steps
- Expandable task cards
- Checkbox tracking
- Progress bars
- Tips and code examples

**3. OnboardingFlow**
- Manages onboarding state
- Navigation between steps
- Progress tracking
- Completion handling

**4. AnalyticsDashboard**
- Admin-only view
- Real-time metrics
- Charts and graphs
- Export functionality

### Styling

**CSS Architecture:**
- Component-scoped styles
- Responsive breakpoints
- Mobile-first approach
- Consistent color palette

**Color Palette:**
- Primary (Purple): `#667eea`
- Success (Green): `#38a169`
- Warning (Orange): `#f6ad55`
- Neutral (Gray): `#e2e8f0`
- Dark: `#2d3748`

---

## 🧪 Testing

### Backend Tests

**Run All Tests:**
```bash
cd backend
pytest
```

**Run Specific Test:**
```bash
pytest tests/test_gemini_integration.py
```

**Run with Coverage:**
```bash
pytest --cov=app --cov-report=html
```

**Test Categories:**
- Unit tests
- Integration tests
- API endpoint tests
- Database tests
- Error handling tests

### Frontend Tests

**Run All Tests:**
```bash
cd frontend
npm run test
```

**Run with Coverage:**
```bash
npm run test:coverage
```

**Test Categories:**
- Component tests
- Hook tests
- Service tests
- Integration tests

### Manual Testing Checklist

**Authentication:**
- [ ] Register new user
- [ ] Login with credentials
- [ ] Logout
- [ ] Invalid credentials handling

**Document Upload:**
- [ ] Upload PDF
- [ ] View document list
- [ ] Delete document
- [ ] Error handling for invalid files

**Onboarding:**
- [ ] Start onboarding
- [ ] Navigate between steps
- [ ] Complete tasks
- [ ] Track progress
- [ ] Expand/collapse tasks
- [ ] Check/uncheck subtasks

**Analytics (Admin):**
- [ ] View dashboard
- [ ] Check metrics
- [ ] Export data

---

## 🔧 Troubleshooting

### Common Issues

#### "npm is not recognized"
**Problem:** Node.js not installed or not in PATH  
**Solution:**
1. Install Node.js from https://nodejs.org/
2. Restart terminal
3. Verify: `node --version`

#### Port Already in Use
**Problem:** Port 8000 or 5173 already occupied  
**Solution:**
```bash
# Backend - use different port
uvicorn main:app --reload --port 8001

# Frontend - Vite auto-increments to 5174, 5175, etc.
```

#### Gemini API Errors
**Problem:** "API request failed" or "Invalid API key"  
**Solution:**
1. Check `.env` file has correct `GEMINI_API_KEY`
2. Verify API key is valid
3. Check internet connection
4. Verify Gemini API status

#### Database Errors
**Problem:** "Database locked" or "Connection failed"  
**Solution:**
```bash
# Delete and recreate database
rm customer_onboarding.db
alembic upgrade head
```

#### Frontend Build Errors
**Problem:** Module not found or build failures  
**Solution:**
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

#### Backend Import Errors
**Problem:** "Module not found" errors  
**Solution:**
```bash
cd backend
pip install -r requirements.txt
```

### Debug Mode

**Backend Debug:**
```bash
# Enable debug logging
export LOG_LEVEL=DEBUG
uvicorn main:app --reload --log-level debug
```

**Frontend Debug:**
```bash
# Check browser console (F12)
# Enable React DevTools
```

### Getting Help

1. Check logs:
   - Backend: `logs/app.log` and `logs/error.log`
   - Frontend: Browser console (F12)

2. Check health endpoint: http://localhost:8000/health

3. Review error messages in UI

4. Check API documentation: http://localhost:8000/docs

---

## 📊 Performance

### Optimization Tips

**Backend:**
- Use database indexes
- Implement caching
- Optimize queries
- Use async operations

**Frontend:**
- Code splitting
- Lazy loading
- Image optimization
- Bundle size optimization

### Monitoring

**Metrics to Track:**
- Response times
- Error rates
- Memory usage
- CPU usage
- Database performance

---

## 🚀 Deployment

### Production Checklist

- [ ] Set strong `SECRET_KEY` in `.env`
- [ ] Use production database (PostgreSQL recommended)
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure logging
- [ ] Set up backups
- [ ] Configure CORS properly
- [ ] Set rate limiting
- [ ] Enable error tracking (Sentry)
- [ ] Set up CI/CD pipeline

### Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

### Environment Variables for Production

```env
# Production settings
ENVIRONMENT=production
DEBUG=false
SECRET_KEY=<strong_random_key>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
GEMINI_API_KEY=<your_key>
ALLOWED_ORIGINS=https://yourdomain.com
```

---

## 📝 License

MIT License - See LICENSE file for details

---

## 🎉 Summary

This Customer Onboarding Agent provides:

✅ **AI-Powered** - Gemini AI generates personalized guides  
✅ **Role-Based** - Customized for Developers, Business Users, Admins  
✅ **Interactive** - Expandable tasks, progress tracking, tips  
✅ **Robust** - Comprehensive error handling and monitoring  
✅ **Scalable** - Ready for production deployment  
✅ **Well-Tested** - Comprehensive test coverage  
✅ **Well-Documented** - Complete documentation and guides  

**Ready to use!** Follow the Quick Start guide to get running in minutes.

---

**Last Updated**: February 6, 2026  
**Version**: 2.0  
**Status**: ✅ Production Ready
