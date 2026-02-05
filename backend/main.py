"""
Customer Onboarding Agent - FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import auth, onboarding, scaledown, analytics, engagement, intervention
from app.services.background_tasks import start_background_tasks, stop_background_tasks


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Initialize database on startup
    await init_db()
    
    # Start background tasks
    await start_background_tasks()
    
    yield
    
    # Stop background tasks on shutdown
    await stop_background_tasks()


app = FastAPI(
    title="Customer Onboarding Agent",
    description="AI-powered customer onboarding platform with role-based flows",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(onboarding.router, prefix="/api/onboarding", tags=["onboarding"])
app.include_router(scaledown.router, prefix="/api/scaledown", tags=["document-processing"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(engagement.router, prefix="/api/engagement", tags=["engagement"])
app.include_router(intervention.router, prefix="/api/intervention", tags=["intervention"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Customer Onboarding Agent API", "status": "running"}


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)