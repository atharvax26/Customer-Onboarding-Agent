"""
Customer Onboarding Agent - FastAPI Backend
Main application entry point with comprehensive error handling and monitoring
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import init_db
from app.routers import auth, onboarding, scaledown, analytics, engagement, intervention
from app.services.background_tasks import start_background_tasks, stop_background_tasks

# Import error handling and monitoring components
from app.logging_config import setup_logging, get_context_logger
from app.error_handlers import register_error_handlers
from app.middleware import register_middleware
from app.health_monitor import health_monitor


# Setup logging
log_level = os.getenv("LOG_LEVEL", "INFO")
enable_json_logging = os.getenv("ENABLE_JSON_LOGGING", "false").lower() == "true"
setup_logging(
    log_level=log_level,
    log_file="logs/app.log",
    enable_json_logging=enable_json_logging,
    enable_console_logging=True
)

logger = get_context_logger(__name__, component="main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with error handling"""
    try:
        logger.info("Starting Customer Onboarding Agent application")
        
        # Initialize database on startup
        await init_db()
        logger.info("Database initialized successfully")
        
        # Start background tasks
        await start_background_tasks()
        logger.info("Background tasks started successfully")
        
        # Perform initial health check
        health_status = await health_monitor.check_system_health()
        logger.info(
            f"Initial health check completed: {health_status['status']}",
            extra={"health_status": health_status['status']}
        )
        
        yield
        
    except Exception as e:
        logger.critical(
            "Failed to start application",
            extra={"error": str(e)},
            exc_info=True
        )
        raise
    finally:
        try:
            # Stop background tasks on shutdown
            await stop_background_tasks()
            logger.info("Background tasks stopped successfully")
            logger.info("Customer Onboarding Agent application shutdown complete")
        except Exception as e:
            logger.error(
                "Error during application shutdown",
                extra={"error": str(e)},
                exc_info=True
            )


app = FastAPI(
    title="Customer Onboarding Agent",
    description="AI-powered customer onboarding platform with role-based flows and comprehensive error handling",
    version="1.0.0",
    lifespan=lifespan
)

# Register error handlers
register_error_handlers(app)

# Register middleware
register_middleware(app)

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

# Import and include system router
from app.routers import system
app.include_router(system.router, prefix="/api/system", tags=["system-monitoring"])


@app.get("/")
async def root():
    """Root endpoint with basic status"""
    logger.info("Root endpoint accessed")
    return {
        "message": "Customer Onboarding Agent API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    try:
        health_status = await health_monitor.check_system_health()
        return health_status
    except Exception as e:
        logger.error(
            "Health check failed",
            extra={"error": str(e)},
            exc_info=True
        )
        return {
            "status": "unhealthy",
            "error": "Health check failed",
            "timestamp": "2024-01-01T00:00:00Z"
        }


@app.get("/health/{component}")
async def component_health_check(component: str):
    """Check health of specific component"""
    try:
        component_health = await health_monitor.check_component_health(component)
        return component_health.to_dict()
    except Exception as e:
        logger.error(
            f"Component health check failed for {component}",
            extra={"component": component, "error": str(e)},
            exc_info=True
        )
        return {
            "name": component,
            "status": "unhealthy",
            "error": str(e),
            "timestamp": "2024-01-01T00:00:00Z"
        }


@app.get("/health-history")
async def health_history(limit: int = 10):
    """Get recent health check history"""
    try:
        history = health_monitor.get_health_history(limit)
        return {"history": history}
    except Exception as e:
        logger.error(
            "Failed to retrieve health history",
            extra={"error": str(e)},
            exc_info=True
        )
        return {"history": [], "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    
    # Configure uvicorn logging
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": log_level,
            "handlers": ["default"],
        },
    }
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=log_config,
        access_log=True
    )