"""
Engagement API endpoints for Customer Onboarding Agent
Handles engagement tracking and scoring operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime

from ..database import get_db
from ..schemas import (
    InteractionEvent, 
    InteractionTrackingResponse,
    EngagementScoreResponse,
    ScorePoint,
    EngagementLogResponse
)
from ..services.engagement_service import engagement_service
from ..auth import get_current_user, User


router = APIRouter()


@router.post("/track-interaction", response_model=InteractionTrackingResponse)
async def track_interaction(
    interaction: InteractionEvent,
    session_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Track user interaction for engagement scoring
    
    Args:
        interaction: Interaction event data
        session_id: Optional onboarding session ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success response
    """
    try:
        await engagement_service.record_interaction(
            db=db,
            user_id=current_user.id,
            interaction=interaction,
            session_id=session_id
        )
        
        return InteractionTrackingResponse(
            success=True,
            message="Interaction tracked successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track interaction: {str(e)}"
        )


@router.post("/track-step-completion")
async def track_step_completion(
    session_id: int,
    step_number: int,
    time_spent_seconds: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Track step completion for engagement scoring
    
    Args:
        session_id: Onboarding session ID
        step_number: Completed step number
        time_spent_seconds: Time spent on the step
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success response
    """
    try:
        await engagement_service.record_step_completion(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            step_number=step_number,
            time_spent_seconds=time_spent_seconds
        )
        
        return InteractionTrackingResponse(
            success=True,
            message="Step completion tracked successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track step completion: {str(e)}"
        )


@router.post("/track-time-activity")
async def track_time_activity(
    activity_type: str,
    duration_seconds: int,
    session_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Track time-based activity for engagement scoring
    
    Args:
        activity_type: Type of activity (page_view, focus, etc.)
        duration_seconds: Duration of the activity
        session_id: Optional onboarding session ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Success response
    """
    try:
        await engagement_service.record_time_activity(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            activity_type=activity_type,
            duration_seconds=duration_seconds
        )
        
        return InteractionTrackingResponse(
            success=True,
            message="Time activity tracked successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track time activity: {str(e)}"
        )


@router.get("/score", response_model=EngagementScoreResponse)
async def get_engagement_score(
    session_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current engagement score and history for the user
    
    Args:
        session_id: Optional onboarding session ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Current engagement score and history
    """
    try:
        # Get current score
        current_score = await engagement_service.get_current_score(
            db=db,
            user_id=current_user.id,
            session_id=session_id
        )
        
        # Get score history
        score_history = await engagement_service.get_score_history(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            limit=20
        )
        
        return EngagementScoreResponse(
            current_score=current_score,
            score_history=score_history,
            last_updated=datetime.utcnow()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get engagement score: {str(e)}"
        )


@router.post("/detect-inactivity")
async def detect_inactivity(
    session_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger inactivity detection for the user
    
    Args:
        session_id: Optional onboarding session ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Inactivity detection result
    """
    try:
        inactivity_detected = await engagement_service.detect_inactivity(
            db=db,
            user_id=current_user.id,
            session_id=session_id
        )
        
        return {
            "inactivity_detected": inactivity_detected,
            "message": "Inactivity detected and penalty applied" if inactivity_detected else "No inactivity detected"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to detect inactivity: {str(e)}"
        )


@router.get("/score/calculate", response_model=dict)
async def calculate_engagement_score(
    session_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Force recalculation of engagement score with detailed metrics
    
    Args:
        session_id: Optional onboarding session ID
        current_user: Authenticated user
        db: Database session
        
    Returns:
        Detailed engagement metrics and calculated score
    """
    try:
        # Calculate detailed metrics
        metrics = await engagement_service._calculate_engagement_metrics(
            db=db,
            user_id=current_user.id,
            session_id=session_id
        )
        
        return {
            "user_id": current_user.id,
            "session_id": session_id,
            "metrics": {
                "step_completion_rate": metrics.step_completion_rate,
                "normalized_time_spent": metrics.normalized_time_spent,
                "interaction_frequency": metrics.interaction_frequency,
                "inactivity_penalty": metrics.inactivity_penalty,
                "total_score": metrics.total_score
            },
            "weights": {
                "step_completion": 0.40,
                "time_spent": 0.30,
                "interactions": 0.20,
                "inactivity_penalty": 0.10
            },
            "calculated_at": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate engagement score: {str(e)}"
        )


@router.get("/score/history", response_model=List[ScorePoint])
async def get_score_history(
    session_id: Optional[int] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get engagement score history for the user
    
    Args:
        session_id: Optional onboarding session ID
        limit: Maximum number of score points to return
        current_user: Authenticated user
        db: Database session
        
    Returns:
        List of historical score points
    """
    try:
        score_history = await engagement_service.get_score_history(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            limit=limit
        )
        
        return score_history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get score history: {str(e)}"
        )