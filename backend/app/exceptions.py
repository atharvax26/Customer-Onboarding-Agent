"""
Custom exceptions for Customer Onboarding Agent
Provides structured error handling with user-friendly messages
"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class BaseCustomException(HTTPException):
    """Base exception class for custom application errors"""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        error_code: str,
        user_message: str,
        headers: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.error_code = error_code
        self.user_message = user_message


class DocumentProcessingError(BaseCustomException):
    """Raised when document processing fails"""
    
    def __init__(self, detail: str, user_message: str = "Failed to process document"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="DOCUMENT_PROCESSING_ERROR",
            user_message=user_message
        )


class DocumentValidationError(BaseCustomException):
    """Raised when document validation fails"""
    
    def __init__(self, detail: str, user_message: str = "Invalid document format"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="DOCUMENT_VALIDATION_ERROR",
            user_message=user_message
        )


class ExternalAPIError(BaseCustomException):
    """Raised when external API calls fail"""
    
    def __init__(self, detail: str, service_name: str, user_message: str = "External service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"{service_name}: {detail}",
            error_code="EXTERNAL_API_ERROR",
            user_message=user_message
        )


class AuthenticationError(BaseCustomException):
    """Raised when authentication fails"""
    
    def __init__(self, detail: str = "Authentication failed", user_message: str = "Invalid credentials"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            error_code="AUTHENTICATION_ERROR",
            user_message=user_message,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(BaseCustomException):
    """Raised when authorization fails"""
    
    def __init__(self, detail: str = "Access denied", user_message: str = "You don't have permission to access this resource"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            error_code="AUTHORIZATION_ERROR",
            user_message=user_message
        )


class OnboardingError(BaseCustomException):
    """Raised when onboarding operations fail"""
    
    def __init__(self, detail: str, user_message: str = "Onboarding operation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="ONBOARDING_ERROR",
            user_message=user_message
        )


class EngagementTrackingError(BaseCustomException):
    """Raised when engagement tracking fails"""
    
    def __init__(self, detail: str, user_message: str = "Failed to track user engagement"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="ENGAGEMENT_TRACKING_ERROR",
            user_message=user_message
        )


class DatabaseError(BaseCustomException):
    """Raised when database operations fail"""
    
    def __init__(self, detail: str, user_message: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
            error_code="DATABASE_ERROR",
            user_message=user_message
        )


class ValidationError(BaseCustomException):
    """Raised when input validation fails"""
    
    def __init__(self, detail: str, field: str = None, user_message: str = "Invalid input provided"):
        if field:
            detail = f"{field}: {detail}"
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            error_code="VALIDATION_ERROR",
            user_message=user_message
        )


class RateLimitError(BaseCustomException):
    """Raised when rate limits are exceeded"""
    
    def __init__(self, detail: str = "Rate limit exceeded", user_message: str = "Too many requests. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            error_code="RATE_LIMIT_ERROR",
            user_message=user_message
        )


class SystemHealthError(BaseCustomException):
    """Raised when system health checks fail"""
    
    def __init__(self, detail: str, component: str, user_message: str = "System temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{component}: {detail}",
            error_code="SYSTEM_HEALTH_ERROR",
            user_message=user_message
        )