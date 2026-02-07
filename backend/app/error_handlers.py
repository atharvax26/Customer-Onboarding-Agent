"""
Global error handlers for Customer Onboarding Agent
Provides consistent error responses and logging with enhanced monitoring
"""

import traceback
import uuid
from datetime import datetime
from typing import Dict, Any
import asyncio

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError

from app.exceptions import BaseCustomException
from app.logging_config import get_context_logger


logger = get_context_logger(__name__, component="error_handler")


class ErrorResponse:
    """Standardized error response format with enhanced user messaging"""
    
    def __init__(
        self,
        error_code: str,
        message: str,
        user_message: str,
        details: Dict[str, Any] = None,
        request_id: str = None,
        suggestions: list = None,
        recovery_actions: list = None
    ):
        self.error_code = error_code
        self.message = message
        self.user_message = user_message
        self.details = details or {}
        self.request_id = request_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.suggestions = suggestions or []
        self.recovery_actions = recovery_actions or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response"""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "user_message": self.user_message,
                "details": self.details,
                "request_id": self.request_id,
                "timestamp": self.timestamp
            }
        }
        
        if self.suggestions:
            response["error"]["suggestions"] = self.suggestions
            
        if self.recovery_actions:
            response["error"]["recovery_actions"] = self.recovery_actions
            
        return response


async def custom_exception_handler(request: Request, exc: BaseCustomException) -> JSONResponse:
    """Handle custom application exceptions with enhanced error tracking"""
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Log the error with context
    logger.error(
        f"Custom exception: {exc.error_code}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "user_message": exc.user_message,
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "client_ip": request.client.host if request.client else "unknown"
        },
        exc_info=True
    )
    
    # Generate contextual suggestions and recovery actions
    suggestions, recovery_actions = _generate_error_guidance(exc.error_code, exc.status_code)
    
    # Track error for system monitoring
    asyncio.create_task(_track_error_for_monitoring(exc.error_code, request.url.path, exc.status_code))
    
    error_response = ErrorResponse(
        error_code=exc.error_code,
        message=exc.detail,
        user_message=exc.user_message,
        request_id=request_id,
        suggestions=suggestions,
        recovery_actions=recovery_actions
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
        headers=exc.headers
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle FastAPI HTTP exceptions with enhanced user guidance"""
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Determine user-friendly message and guidance based on status code
    user_messages = {
        400: "Invalid request. Please check your input and try again.",
        401: "Authentication required. Please log in to continue.",
        403: "Access denied. You don't have permission for this action.",
        404: "The requested resource was not found.",
        405: "Method not allowed for this endpoint.",
        422: "Invalid input data provided. Please check the highlighted fields.",
        429: "Too many requests. Please wait a moment before trying again.",
        500: "Internal server error. Our team has been notified.",
        502: "External service temporarily unavailable. Please try again later.",
        503: "Service temporarily unavailable. Please try again in a few minutes."
    }
    
    user_message = user_messages.get(exc.status_code, "An error occurred. Please try again.")
    
    # Generate contextual suggestions and recovery actions
    suggestions, recovery_actions = _generate_error_guidance(f"HTTP_{exc.status_code}", exc.status_code)
    
    # Log the error with enhanced context
    logger.error(
        f"HTTP exception: {exc.status_code}",
        extra={
            "request_id": request_id,
            "status_code": exc.status_code,
            "detail": exc.detail,
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "client_ip": request.client.host if request.client else "unknown",
            "referer": request.headers.get("referer", "unknown")
        }
    )
    
    # Track error for system monitoring
    asyncio.create_task(_track_error_for_monitoring(f"HTTP_{exc.status_code}", request.url.path, exc.status_code))
    
    error_response = ErrorResponse(
        error_code=f"HTTP_{exc.status_code}",
        message=exc.detail,
        user_message=user_message,
        request_id=request_id,
        suggestions=suggestions,
        recovery_actions=recovery_actions
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.to_dict(),
        headers=exc.headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors"""
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Extract validation error details
    validation_errors = []
    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        validation_errors.append({
            "field": field_path,
            "message": error["msg"],
            "type": error["type"]
        })
    
    # Log the validation error
    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "validation_errors": validation_errors,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    error_response = ErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        user_message="Invalid input data. Please check the highlighted fields.",
        details={"validation_errors": validation_errors},
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.to_dict()
    )


async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError) -> JSONResponse:
    """Handle SQLAlchemy database errors"""
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Log the database error (don't expose sensitive details)
    logger.error(
        "Database error",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )
    
    error_response = ErrorResponse(
        error_code="DATABASE_ERROR",
        message="Database operation failed",
        user_message="A database error occurred. Please try again later.",
        request_id=request_id
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict()
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with comprehensive error tracking"""
    
    request_id = getattr(request.state, 'request_id', str(uuid.uuid4()))
    
    # Log the unexpected error with full context and traceback
    logger.critical(
        "Unexpected error",
        extra={
            "request_id": request_id,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "path": request.url.path,
            "method": request.method,
            "user_agent": request.headers.get("user-agent", "unknown"),
            "client_ip": request.client.host if request.client else "unknown",
            "traceback": traceback.format_exc(),
            "request_body": await _safe_get_request_body(request)
        },
        exc_info=True
    )
    
    # Track critical error for immediate attention
    asyncio.create_task(_track_critical_error(exc, request))
    
    # Generate recovery actions for unexpected errors
    recovery_actions = [
        "Refresh the page and try again",
        "Clear your browser cache and cookies",
        "Try again in a few minutes",
        "Contact support if the problem persists"
    ]
    
    error_response = ErrorResponse(
        error_code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        user_message="Something went wrong. Our team has been notified and is working on a fix.",
        request_id=request_id,
        suggestions=["This appears to be a temporary issue"],
        recovery_actions=recovery_actions
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.to_dict()
    )


def _generate_error_guidance(error_code: str, status_code: int) -> tuple[list, list]:
    """Generate contextual suggestions and recovery actions for errors"""
    
    suggestions = []
    recovery_actions = []
    
    # Error-specific guidance
    if error_code == "AUTHENTICATION_ERROR":
        suggestions = [
            "Your session may have expired",
            "Check if your credentials are correct"
        ]
        recovery_actions = [
            "Try logging in again",
            "Reset your password if needed",
            "Clear browser cookies and try again"
        ]
    
    elif error_code == "AUTHORIZATION_ERROR":
        suggestions = [
            "You may not have the required permissions",
            "Contact your administrator for access"
        ]
        recovery_actions = [
            "Log in with a different account",
            "Request access from your administrator",
            "Check if your role has the required permissions"
        ]
    
    elif error_code == "DOCUMENT_PROCESSING_ERROR":
        suggestions = [
            "The document format may not be supported",
            "The document might be corrupted or too large"
        ]
        recovery_actions = [
            "Try uploading a different document",
            "Check the file format (PDF or text files only)",
            "Reduce the file size if it's very large",
            "Try again in a few minutes"
        ]
    
    elif error_code == "EXTERNAL_API_ERROR":
        suggestions = [
            "External service is temporarily unavailable",
            "This is usually a temporary issue"
        ]
        recovery_actions = [
            "Wait a few minutes and try again",
            "Check your internet connection",
            "Contact support if the issue persists"
        ]
    
    elif error_code == "VALIDATION_ERROR":
        suggestions = [
            "Check the highlighted fields for errors",
            "Make sure all required fields are filled"
        ]
        recovery_actions = [
            "Correct the invalid fields",
            "Check the format requirements",
            "Try submitting again"
        ]
    
    elif status_code == 429:  # Rate limit
        suggestions = [
            "You're making requests too quickly",
            "Rate limits help maintain system performance"
        ]
        recovery_actions = [
            "Wait 30 seconds before trying again",
            "Reduce the frequency of your requests",
            "Try again later"
        ]
    
    elif status_code >= 500:  # Server errors
        suggestions = [
            "This is a temporary server issue",
            "Our team has been automatically notified"
        ]
        recovery_actions = [
            "Try again in a few minutes",
            "Refresh the page",
            "Contact support if the issue persists"
        ]
    
    # Default guidance for unhandled cases
    if not suggestions:
        suggestions = ["An unexpected error occurred"]
    
    if not recovery_actions:
        recovery_actions = [
            "Try refreshing the page",
            "Try again in a few minutes",
            "Contact support if the problem continues"
        ]
    
    return suggestions, recovery_actions


async def _track_error_for_monitoring(error_code: str, path: str, status_code: int):
    """Track error for system monitoring and alerting"""
    try:
        from app.services.system_monitor import system_monitor, AlertLevel
        
        # Determine alert level based on error severity
        if status_code >= 500:
            alert_level = AlertLevel.ERROR
        elif status_code == 429:
            alert_level = AlertLevel.WARNING
        elif status_code >= 400:
            alert_level = AlertLevel.INFO
        else:
            alert_level = AlertLevel.INFO
        
        # Create alert for monitoring
        await system_monitor._create_alert(
            level=alert_level,
            component="api_error",
            message=f"API error: {error_code} on {path}",
            details={
                "error_code": error_code,
                "path": path,
                "status_code": status_code,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to track error for monitoring: {e}")


async def _track_critical_error(exc: Exception, request: Request):
    """Track critical errors for immediate attention"""
    try:
        from app.services.system_monitor import system_monitor, AlertLevel
        
        # Create critical alert
        await system_monitor._create_alert(
            level=AlertLevel.CRITICAL,
            component="critical_error",
            message=f"Critical error: {type(exc).__name__}",
            details={
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "path": request.url.path,
                "method": request.method,
                "timestamp": datetime.utcnow().isoformat(),
                "requires_immediate_attention": True
            }
        )
        
    except Exception as e:
        logger.error(f"Failed to track critical error: {e}")


async def _safe_get_request_body(request: Request) -> str:
    """Safely get request body for logging (avoiding sensitive data)"""
    try:
        # Only log request body for non-sensitive endpoints
        sensitive_paths = ['/auth/login', '/auth/register', '/auth/']
        
        if any(path in request.url.path for path in sensitive_paths):
            return "[REDACTED - Sensitive endpoint]"
        
        # Limit body size for logging
        body = await request.body()
        if len(body) > 1000:  # Limit to 1KB
            return f"[TRUNCATED - Body too large: {len(body)} bytes]"
        
        return body.decode('utf-8', errors='ignore')
        
    except Exception:
        return "[ERROR - Could not read request body]"


def register_error_handlers(app):
    """Register all error handlers with the FastAPI app"""
    
    # Custom exception handlers
    app.add_exception_handler(BaseCustomException, custom_exception_handler)
    
    # Built-in exception handlers
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    
    # Catch-all handler for unexpected exceptions
    app.add_exception_handler(Exception, general_exception_handler)
    
    logger.info("Error handlers registered successfully")