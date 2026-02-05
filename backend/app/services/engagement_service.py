"""
Engagement Scoring Service for Customer Onboarding Agent
Handles real-time engagement metrics collection and scoring
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from sqlalchemy.orm import selectinload
import asyncio
import logging
from dataclasses import dataclass

from ..database import EngagementLog, User, OnboardingSession, StepCompletion
from ..schemas import InteractionEvent, EngagementLogCreate, ScorePoint


logger = logging.getLogger(__name__)


@dataclass
class EngagementMetrics:
    """Container for engagement calculation metrics"""
    step_completion_rate: float
    normalized_time_spent: float
    interaction_frequency: float
    inactivity_penalty: float
    total_score: float


class EngagementScoringService:
    """
    Service for tracking user engagement and calculating real-time scores
    
    Implements weighted scoring algorithm:
    - Step completion: 40%
    - Time spent: 30% 
    - Interactions: 20%
    - Inactivity penalty: 10%
    """
    
    def __init__(self):
        self.score_cache: Dict[int, float] = {}
        self.last_activity: Dict[int, datetime] = {}
        
    async def record_interaction(
        self, 
        db: AsyncSession, 
        user_id: int, 
        interaction: InteractionEvent,
        session_id: Optional[int] = None
    ) -> None:
        """
        Record user interaction event for engagement scoring
        
        Args:
            db: Database session
            user_id: ID of the user
            interaction: Interaction event data
            session_id: Optional onboarding session ID
        """
        try:
            # Update last activity timestamp
            self.last_activity[user_id] = datetime.utcnow()
            
            # Create engagement log entry
            engagement_log = EngagementLog(
                user_id=user_id,
                session_id=session_id,
                event_type=interaction.event_type,
                event_data={
                    "element_id": interaction.element_id,
                    "element_type": interaction.element_type,
                    "page_url": interaction.page_url,
                    "additional_data": interaction.additional_data
                },
                timestamp=interaction.timestamp
            )
            
            db.add(engagement_log)
            await db.commit()
            
            # Trigger real-time score update
            await self._update_engagement_score(db, user_id, session_id)
            
            logger.info(f"Recorded interaction for user {user_id}: {interaction.event_type}")
            
        except Exception as e:
            logger.error(f"Error recording interaction for user {user_id}: {str(e)}")
            await db.rollback()
            raise

    async def record_step_completion(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: int,
        step_number: int,
        time_spent_seconds: int
    ) -> None:
        """
        Record step completion for engagement scoring
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Onboarding session ID
            step_number: Completed step number
            time_spent_seconds: Time spent on the step
        """
        try:
            # Update last activity
            self.last_activity[user_id] = datetime.utcnow()
            
            # Create engagement log for step completion
            engagement_log = EngagementLog(
                user_id=user_id,
                session_id=session_id,
                event_type="step_completion",
                event_data={
                    "step_number": step_number,
                    "time_spent_seconds": time_spent_seconds
                },
                timestamp=datetime.utcnow()
            )
            
            db.add(engagement_log)
            await db.commit()
            
            # Trigger real-time score update
            await self._update_engagement_score(db, user_id, session_id)
            
            logger.info(f"Recorded step completion for user {user_id}: step {step_number}")
            
        except Exception as e:
            logger.error(f"Error recording step completion for user {user_id}: {str(e)}")
            await db.rollback()
            raise

    async def record_time_activity(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int],
        activity_type: str,
        duration_seconds: int
    ) -> None:
        """
        Record time-based activity for engagement scoring
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional onboarding session ID
            activity_type: Type of activity (page_view, focus, etc.)
            duration_seconds: Duration of the activity
        """
        try:
            # Update last activity
            self.last_activity[user_id] = datetime.utcnow()
            
            # Create engagement log for time activity
            engagement_log = EngagementLog(
                user_id=user_id,
                session_id=session_id,
                event_type=activity_type,
                event_data={
                    "duration_seconds": duration_seconds
                },
                timestamp=datetime.utcnow()
            )
            
            db.add(engagement_log)
            await db.commit()
            
            # Trigger real-time score update if significant activity
            if duration_seconds > 10:  # Only update for meaningful time periods
                await self._update_engagement_score(db, user_id, session_id)
            
            logger.debug(f"Recorded time activity for user {user_id}: {activity_type} ({duration_seconds}s)")
            
        except Exception as e:
            logger.error(f"Error recording time activity for user {user_id}: {str(e)}")
            await db.rollback()
            raise

    async def detect_inactivity(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int] = None
    ) -> bool:
        """
        Detect user inactivity and apply penalty
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional onboarding session ID
            
        Returns:
            True if inactivity detected and penalty applied
        """
        try:
            # Check last activity time
            last_activity = self.last_activity.get(user_id)
            if not last_activity:
                # Get last activity from database
                result = await db.execute(
                    select(EngagementLog.timestamp)
                    .where(EngagementLog.user_id == user_id)
                    .order_by(desc(EngagementLog.timestamp))
                    .limit(1)
                )
                last_activity_row = result.first()
                if last_activity_row:
                    last_activity = last_activity_row[0]
                else:
                    return False
            
            # Check if inactive for more than 5 minutes
            inactivity_threshold = timedelta(minutes=5)
            if datetime.utcnow() - last_activity > inactivity_threshold:
                # Record inactivity event
                engagement_log = EngagementLog(
                    user_id=user_id,
                    session_id=session_id,
                    event_type="inactivity_detected",
                    event_data={
                        "inactive_duration_seconds": int((datetime.utcnow() - last_activity).total_seconds())
                    },
                    timestamp=datetime.utcnow()
                )
                
                db.add(engagement_log)
                await db.commit()
                
                # Update engagement score with penalty
                await self._update_engagement_score(db, user_id, session_id)
                
                logger.info(f"Inactivity detected for user {user_id}")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Error detecting inactivity for user {user_id}: {str(e)}")
            return False

    async def _update_engagement_score(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int] = None
    ) -> None:
        """
        Update engagement score in real-time (within 5 seconds)
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional onboarding session ID
        """
        try:
            # Calculate new engagement score
            score = await self.calculate_score(db, user_id, session_id)
            
            # Cache the score
            self.score_cache[user_id] = score
            
            # Update the latest engagement log with the new score
            result = await db.execute(
                select(EngagementLog)
                .where(EngagementLog.user_id == user_id)
                .order_by(desc(EngagementLog.timestamp))
                .limit(1)
            )
            latest_log = result.scalar_one_or_none()
            
            if latest_log:
                latest_log.engagement_score = score
                await db.commit()
            
            # Add user to active monitoring for background tasks
            from .background_tasks import background_task_service
            background_task_service.add_active_user(user_id)
            
            # Check if intervention is needed
            from .intervention_service import intervention_system
            if score < intervention_system.intervention_threshold:
                # Trigger intervention check in background
                asyncio.create_task(intervention_system.monitor_engagement(db, user_id))
            
            logger.debug(f"Updated engagement score for user {user_id}: {score}")
            
        except Exception as e:
            logger.error(f"Error updating engagement score for user {user_id}: {str(e)}")

    async def calculate_score(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int] = None
    ) -> float:
        """
        Calculate engagement score using weighted algorithm
        
        Formula: step_completion(40%) + time_spent(30%) + interactions(20%) - inactivity_penalty(10%)
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional onboarding session ID
            
        Returns:
            Engagement score between 0-100
        """
        try:
            metrics = await self._calculate_engagement_metrics(db, user_id, session_id)
            
            # Apply weighted formula
            weighted_score = (
                metrics.step_completion_rate * 0.40 +
                metrics.normalized_time_spent * 0.30 +
                metrics.interaction_frequency * 0.20 -
                metrics.inactivity_penalty * 0.10
            )
            
            # Ensure score is within bounds (0-100)
            final_score = max(0.0, min(100.0, weighted_score))
            
            logger.debug(f"Calculated engagement score for user {user_id}: {final_score}")
            return final_score
            
        except Exception as e:
            logger.error(f"Error calculating engagement score for user {user_id}: {str(e)}")
            return 0.0

    async def _calculate_engagement_metrics(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int] = None
    ) -> EngagementMetrics:
        """
        Calculate individual engagement metrics
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional onboarding session ID
            
        Returns:
            EngagementMetrics object with calculated values
        """
        # Get time window for calculations (last 24 hours or session duration)
        time_window = datetime.utcnow() - timedelta(hours=24)
        
        # Base query for engagement logs
        base_query = select(EngagementLog).where(
            and_(
                EngagementLog.user_id == user_id,
                EngagementLog.timestamp >= time_window
            )
        )
        
        if session_id:
            base_query = base_query.where(EngagementLog.session_id == session_id)
        
        result = await db.execute(base_query)
        engagement_logs = result.scalars().all()
        
        # Calculate step completion rate
        step_completion_rate = await self._calculate_step_completion_rate(
            db, user_id, session_id, engagement_logs
        )
        
        # Calculate normalized time spent
        normalized_time_spent = await self._calculate_normalized_time_spent(
            db, user_id, session_id, engagement_logs
        )
        
        # Calculate interaction frequency
        interaction_frequency = self._calculate_interaction_frequency(engagement_logs)
        
        # Calculate inactivity penalty
        inactivity_penalty = self._calculate_inactivity_penalty(engagement_logs)
        
        # Calculate total score
        total_score = (
            step_completion_rate * 0.40 +
            normalized_time_spent * 0.30 +
            interaction_frequency * 0.20 -
            inactivity_penalty * 0.10
        )
        
        return EngagementMetrics(
            step_completion_rate=step_completion_rate,
            normalized_time_spent=normalized_time_spent,
            interaction_frequency=interaction_frequency,
            inactivity_penalty=inactivity_penalty,
            total_score=max(0.0, min(100.0, total_score))
        )

    async def _calculate_step_completion_rate(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int],
        engagement_logs: List[EngagementLog]
    ) -> float:
        """Calculate step completion rate (0-100)"""
        try:
            if session_id:
                # Get session details
                result = await db.execute(
                    select(OnboardingSession)
                    .where(OnboardingSession.id == session_id)
                    .options(selectinload(OnboardingSession.step_completions))
                )
                session = result.scalar_one_or_none()
                
                if session:
                    completed_steps = len([sc for sc in session.step_completions if sc.completed_at])
                    completion_rate = (completed_steps / session.total_steps) * 100
                    return min(100.0, completion_rate)
            
            # Fallback: count step completion events in logs
            step_completions = [log for log in engagement_logs if log.event_type == "step_completion"]
            # Normalize based on typical flow (assume 5 steps max)
            return min(100.0, len(step_completions) * 20.0)
            
        except Exception as e:
            logger.error(f"Error calculating step completion rate: {str(e)}")
            return 0.0

    async def _calculate_normalized_time_spent(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int],
        engagement_logs: List[EngagementLog]
    ) -> float:
        """Calculate normalized time spent (0-100)"""
        try:
            total_time = 0
            
            # Sum time from time-based activities
            for log in engagement_logs:
                if log.event_data and "duration_seconds" in log.event_data:
                    total_time += log.event_data["duration_seconds"]
                elif log.event_data and "time_spent_seconds" in log.event_data:
                    total_time += log.event_data["time_spent_seconds"]
            
            # Normalize against expected time (30 minutes = 100%)
            expected_time_seconds = 30 * 60
            normalized_score = (total_time / expected_time_seconds) * 100
            
            return min(100.0, normalized_score)
            
        except Exception as e:
            logger.error(f"Error calculating normalized time spent: {str(e)}")
            return 0.0

    def _calculate_interaction_frequency(self, engagement_logs: List[EngagementLog]) -> float:
        """Calculate interaction frequency score (0-100)"""
        try:
            # Count interactive events (excluding passive events)
            interactive_events = [
                log for log in engagement_logs 
                if log.event_type in ["click", "scroll", "focus", "input", "button_click"]
            ]
            
            # Normalize based on time window and expected interactions
            # Assume 1 interaction per minute = 100%
            time_window_minutes = 60  # 1 hour window
            expected_interactions = time_window_minutes
            
            frequency_score = (len(interactive_events) / expected_interactions) * 100
            return min(100.0, frequency_score)
            
        except Exception as e:
            logger.error(f"Error calculating interaction frequency: {str(e)}")
            return 0.0

    def _calculate_inactivity_penalty(self, engagement_logs: List[EngagementLog]) -> float:
        """Calculate inactivity penalty (0-100)"""
        try:
            # Count inactivity events
            inactivity_events = [
                log for log in engagement_logs 
                if log.event_type == "inactivity_detected"
            ]
            
            # Calculate penalty based on number and duration of inactivity periods
            total_penalty = 0
            for event in inactivity_events:
                if event.event_data and "inactive_duration_seconds" in event.event_data:
                    duration_minutes = event.event_data["inactive_duration_seconds"] / 60
                    # 5 minutes inactivity = 10 penalty points
                    penalty = min(20.0, (duration_minutes / 5) * 10)
                    total_penalty += penalty
            
            return min(100.0, total_penalty)
            
        except Exception as e:
            logger.error(f"Error calculating inactivity penalty: {str(e)}")
            return 0.0

    async def get_score_history(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int] = None,
        limit: int = 50
    ) -> List[ScorePoint]:
        """
        Get engagement score history for a user
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional onboarding session ID
            limit: Maximum number of score points to return
            
        Returns:
            List of ScorePoint objects
        """
        try:
            query = select(EngagementLog).where(
                and_(
                    EngagementLog.user_id == user_id,
                    EngagementLog.engagement_score.isnot(None)
                )
            ).order_by(desc(EngagementLog.timestamp)).limit(limit)
            
            if session_id:
                query = query.where(EngagementLog.session_id == session_id)
            
            result = await db.execute(query)
            logs = result.scalars().all()
            
            return [
                ScorePoint(
                    timestamp=log.timestamp,
                    score=log.engagement_score or 0
                )
                for log in logs
            ]
            
        except Exception as e:
            logger.error(f"Error getting score history for user {user_id}: {str(e)}")
            return []

    async def get_current_score(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int] = None
    ) -> float:
        """
        Get current engagement score for a user
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional onboarding session ID
            
        Returns:
            Current engagement score (0-100)
        """
        # Check cache first
        if user_id in self.score_cache:
            return self.score_cache[user_id]
        
        # Calculate fresh score
        score = await self.calculate_score(db, user_id, session_id)
        self.score_cache[user_id] = score
        return score


# Global service instance
engagement_service = EngagementScoringService()