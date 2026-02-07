"""
Intervention System API endpoints for Customer Onboarding Agent
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from ..schemas import (
    HelpMessage, HelpMessageResponse, InterventionLogResponse, 
    InterventionLogCreate, ErrorResponse
)
from ..services.intervention_service import intervention_system
from ..auth import get_current_user, User


router = APIRouter()


class ManualHelpRequest(BaseModel):
    session_id: int
    step_number: int


class InterventionFeedbackRequest(BaseModel):
    intervention_id: int
    was_helpful: bool


@router.get("/check/{session_id}")
async def check_for_intervention(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if user needs intervention based on current engagement
    
    Args:
        session_id: Onboarding session ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Help message if intervention is needed, null otherwise
    """
    try:
        # Get current engagement score
        from ..services.engagement_service import engagement_service
        current_score = await engagement_service.get_current_score(
            db=db,
            user_id=current_user.id,
            session_id=session_id
        )
        
        # Check if intervention is needed
        if intervention_system._should_intervene(current_user.id, current_score):
            # Get step context
            context = await intervention_system._get_step_context(
                db, current_user.id, session_id
            )
            
            # Trigger help intervention
            help_message = await intervention_system.trigger_help(
                db, current_user.id, context, session_id
            )
            
            return HelpMessageResponse(
                help_message=help_message,
                triggered_at=help_message.context.get("triggered_at", "now")
            )
        
        # Return empty response if no intervention is needed
        return {"help_message": None}
        
    except Exception as e:
        # Log error but don't fail the request
        print(f"Error checking for intervention: {str(e)}")
        return {"help_message": None}


@router.post("/manual-help", response_model=HelpMessageResponse)
async def trigger_manual_help_endpoint(
    request: ManualHelpRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger help intervention for current user
    
    Args:
        request: Manual help request with session and step info
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated help message response
    """
    try:
        # Get step context
        context = await intervention_system._get_step_context(
            db, current_user.id, request.session_id
        )
        
        # Override step number if provided
        context.step_number = request.step_number
        
        # Trigger help intervention
        help_message = await intervention_system.trigger_help(
            db, current_user.id, context, request.session_id
        )
        
        return HelpMessageResponse(
            help_message=help_message,
            triggered_at=help_message.context.get("triggered_at", "now")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering manual help: {str(e)}"
        )


@router.post("/feedback")
async def submit_intervention_feedback(
    request: InterventionFeedbackRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit feedback for an intervention
    
    Args:
        request: Feedback request with intervention ID and helpfulness
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success response
    """
    try:
        # Update intervention feedback
        success = await intervention_system.mark_intervention_helpful(
            db=db,
            intervention_id=request.intervention_id,
            was_helpful=request.was_helpful
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intervention not found"
            )
            
        return {"success": True}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting feedback: {str(e)}"
        )


@router.get("/history")
async def get_user_intervention_history(
    session_id: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get intervention history for current user
    
    Args:
        session_id: Optional session ID filter
        limit: Maximum number of interventions to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of intervention logs
    """
    try:
        # Get intervention history for current user
        interventions = await intervention_system.get_intervention_history(
            db=db,
            user_id=current_user.id,
            session_id=session_id,
            limit=limit
        )
        
        return [
            InterventionLogResponse(
                id=intervention.id,
                user_id=intervention.user_id,
                session_id=intervention.session_id,
                intervention_type=intervention.intervention_type,
                message_content=intervention.message_content,
                triggered_at=intervention.triggered_at,
                was_helpful=intervention.was_helpful
            )
            for intervention in interventions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting intervention history: {str(e)}"
        )


@router.post("/trigger-help/{user_id}", response_model=HelpMessageResponse)
async def trigger_manual_help(
    user_id: int,
    session_id: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger help intervention for a user (Admin only)
    
    Args:
        user_id: ID of the user to help
        session_id: Optional onboarding session ID
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Generated help message response
    """
    try:
        # Check authorization (admin or self)
        if current_user.id != user_id and current_user.role.value != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to trigger help for this user"
            )
            
        # Get step context
        context = await intervention_system._get_step_context(db, user_id, session_id)
        
        # Trigger help intervention
        help_message = await intervention_system.trigger_help(db, user_id, context, session_id)
        
        return HelpMessageResponse(
            help_message=help_message,
            triggered_at=help_message.context.get("triggered_at", "now")
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering help: {str(e)}"
        )


@router.get("/history/{user_id}", response_model=List[InterventionLogResponse])
async def get_intervention_history(
    user_id: int,
    session_id: Optional[int] = None,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get intervention history for a user (Admin only)
    
    Args:
        user_id: ID of the user
        session_id: Optional session ID filter
        limit: Maximum number of interventions to return
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        List of intervention logs
    """
    try:
        # Check authorization (admin or self)
        if current_user.id != user_id and current_user.role.value != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view intervention history for this user"
            )
            
        # Get intervention history
        interventions = await intervention_system.get_intervention_history(
            db=db,
            user_id=user_id,
            session_id=session_id,
            limit=limit
        )
        
        return [
            InterventionLogResponse(
                id=intervention.id,
                user_id=intervention.user_id,
                session_id=intervention.session_id,
                intervention_type=intervention.intervention_type,
                message_content=intervention.message_content,
                triggered_at=intervention.triggered_at,
                was_helpful=intervention.was_helpful
            )
            for intervention in interventions
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting intervention history: {str(e)}"
        )


@router.post("/feedback/{intervention_id}")
async def mark_intervention_helpful(
    intervention_id: int,
    was_helpful: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark an intervention as helpful or not helpful (Admin endpoint)
    
    Args:
        intervention_id: ID of the intervention log
        was_helpful: Whether the intervention was helpful
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Success response
    """
    try:
        # Update intervention feedback
        success = await intervention_system.mark_intervention_helpful(
            db=db,
            intervention_id=intervention_id,
            was_helpful=was_helpful
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intervention not found"
            )
            
        return {"success": True, "message": "Feedback recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recording feedback: {str(e)}"
        )


@router.get("/status")
async def get_intervention_status(
    current_user: User = Depends(get_current_user)
):
    """
    Get intervention system status
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        System status information
    """
    try:
        return {
            "monitoring_active": intervention_system.monitoring_active,
            "intervention_threshold": intervention_system.intervention_threshold,
            "deduplication_window_minutes": intervention_system.deduplication_window_minutes,
            "active_users_count": len(intervention_system.last_interventions)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting intervention status: {str(e)}"
        )


@router.post("/configure")
async def configure_intervention_system(
    threshold: Optional[float] = None,
    deduplication_minutes: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Configure intervention system parameters (Admin only)
    
    Args:
        threshold: New intervention threshold (0-100)
        deduplication_minutes: New deduplication window in minutes
        db: Database session
        current_user: Current authenticated user
        
    Returns:
        Updated configuration
    """
    try:
        # Check admin authorization
        if current_user.role.value != "Admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
            
        # Update configuration
        if threshold is not None:
            if not 0 <= threshold <= 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Threshold must be between 0 and 100"
                )
            intervention_system.intervention_threshold = threshold
            
        if deduplication_minutes is not None:
            if deduplication_minutes < 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Deduplication window must be at least 1 minute"
                )
            intervention_system.deduplication_window_minutes = deduplication_minutes
            
        return {
            "intervention_threshold": intervention_system.intervention_threshold,
            "deduplication_window_minutes": intervention_system.deduplication_window_minutes,
            "message": "Configuration updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error configuring intervention system: {str(e)}"
        )