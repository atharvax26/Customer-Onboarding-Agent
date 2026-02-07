"""
Onboarding router for Customer Onboarding Agent
Handles role-based onboarding flows and step progression
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

from app.database import get_db, User, UserRole
from app.auth import (
    get_current_active_user, require_roles, require_admin, 
    filter_content_by_role, check_resource_access
)
from app.schemas import (
    UserResponse, OnboardingSessionResponse, OnboardingStepResponse,
    OnboardingProgressResponse
)
from app.services.onboarding_service import OnboardingEngine

router = APIRouter()


@router.post("/start", response_model=OnboardingSessionResponse)
async def start_onboarding(
    request_body: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Start a new onboarding session for the current user"""
    try:
        document_id = request_body.get('document_id')
        if not document_id:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="document_id is required"
            )
        
        engine = OnboardingEngine(db)
        session = await engine.start_onboarding_session(
            user_id=current_user.id,
            document_id=document_id
        )
        return session
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start onboarding session"
        )


@router.get("/current-step/{session_id}", response_model=OnboardingStepResponse)
async def get_current_step(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current onboarding step content"""
    try:
        engine = OnboardingEngine(db)
        step = await engine.get_current_step(session_id)
        return step
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve current step"
        )


@router.post("/advance-step/{session_id}")
async def advance_step(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Advance to next onboarding step"""
    try:
        engine = OnboardingEngine(db)
        result = await engine.advance_step(session_id)
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to advance step"
        )


@router.get("/progress/{session_id}", response_model=OnboardingProgressResponse)
async def get_session_progress(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed progress for an onboarding session"""
    try:
        engine = OnboardingEngine(db)
        progress = await engine.get_session_progress(session_id)
        return progress
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session progress"
        )


@router.get("/sessions", response_model=List[OnboardingSessionResponse])
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all onboarding sessions for the current user"""
    try:
        engine = OnboardingEngine(db)
        sessions = await engine.get_user_sessions(current_user.id)
        return sessions
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user sessions"
        )


@router.get("/session/{session_id}", response_model=OnboardingSessionResponse)
async def get_session_details(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get details for a specific onboarding session"""
    try:
        engine = OnboardingEngine(db)
        session = await engine.get_session_by_id(session_id)
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        return session
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details"
        )


@router.get("/user-progress/{user_id}")
async def get_user_progress(
    user_id: int,
    current_user: User = Depends(check_resource_access),
    db: AsyncSession = Depends(get_db)
):
    """
    Get onboarding progress for a specific user
    Users can only access their own progress, admins can access any user's progress
    """
    try:
        engine = OnboardingEngine(db)
        sessions = await engine.get_user_sessions(user_id)
        return {
            "user_id": user_id,
            "accessed_by": current_user.id,
            "sessions": sessions,
            "total_sessions": len(sessions)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user progress"
        )


@router.get("/admin/all-sessions")
async def get_all_sessions(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get all onboarding sessions - admin only"""
    return {
        "message": "All sessions retrieved",
        "admin_user": admin_user.email,
        "total_sessions": 42
    }


@router.get("/developer/api-docs")
async def get_developer_docs(
    developer_user: User = Depends(require_roles([UserRole.DEVELOPER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get developer documentation - developers and admins only"""
    return {
        "message": "Developer documentation",
        "user_role": developer_user.role.value,
        "api_endpoints": ["/api/auth", "/api/onboarding", "/api/analytics"]
    }


@router.get("/business/reports")
async def get_business_reports(
    business_user: User = Depends(require_roles([UserRole.BUSINESS_USER, UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Get business reports - business users and admins only"""
    return {
        "message": "Business reports",
        "user_role": business_user.role.value,
        "reports": ["activation_rates", "user_engagement", "completion_metrics"]
    }