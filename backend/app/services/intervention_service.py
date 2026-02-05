"""
Intervention System for Customer Onboarding Agent
Handles automated assistance triggered by low engagement scores
"""

import asyncio
import logging
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from dataclasses import dataclass
import uuid

from ..database import InterventionLog, User, OnboardingSession, SessionStatus, StepCompletion
from ..schemas import HelpMessage, InterventionLogCreate
from .engagement_service import engagement_service


logger = logging.getLogger(__name__)


@dataclass
class StepContext:
    """Context information for generating contextual help"""
    step_number: int
    total_steps: int
    step_title: str
    user_role: str
    time_on_step: int  # seconds
    previous_interventions: int
    engagement_score: float


class InterventionSystem:
    """
    Automated assistance system triggered by low engagement scores
    
    Features:
    - Threshold-based intervention triggering (score < 30)
    - Contextual help message generation
    - Intervention deduplication (5-minute window)
    - Analytics tracking for intervention effectiveness
    """
    
    def __init__(self):
        self.intervention_threshold = 30.0
        self.deduplication_window_minutes = 5
        self.last_interventions: Dict[int, datetime] = {}
        self.monitoring_active = False
        
    async def start_monitoring(self):
        """Start continuous engagement monitoring"""
        if self.monitoring_active:
            return
            
        self.monitoring_active = True
        logger.info("Starting intervention system monitoring")
        
        # Start background monitoring task
        asyncio.create_task(self._continuous_monitoring())
        
    async def stop_monitoring(self):
        """Stop continuous engagement monitoring"""
        self.monitoring_active = False
        logger.info("Stopping intervention system monitoring")
        
    async def _continuous_monitoring(self):
        """Continuously monitor engagement scores for all active users"""
        from ..database import AsyncSessionLocal
        
        while self.monitoring_active:
            try:
                async with AsyncSessionLocal() as db:
                    # Get all users with active onboarding sessions
                    result = await db.execute(
                        select(OnboardingSession)
                        .where(OnboardingSession.status == SessionStatus.ACTIVE)
                    )
                    active_sessions = result.scalars().all()
                    
                    # Check each active session for intervention needs
                    for session in active_sessions:
                        await self._check_user_for_intervention(db, session.user_id, session.id)
                        
                # Wait 30 seconds before next check
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in continuous monitoring: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
                
    async def _check_user_for_intervention(
        self, 
        db: AsyncSession, 
        user_id: int, 
        session_id: int
    ):
        """Check if a user needs intervention based on engagement score"""
        try:
            # Get current engagement score
            current_score = await engagement_service.get_current_score(
                db=db,
                user_id=user_id,
                session_id=session_id
            )
            
            # Check if intervention is needed
            if await self._should_intervene(user_id, current_score):
                # Get step context
                context = await self._get_step_context(db, user_id, session_id)
                
                # Trigger intervention
                await self.trigger_help(db, user_id, context, session_id)
                
        except Exception as e:
            logger.error(f"Error checking user {user_id} for intervention: {str(e)}")
            
    async def monitor_engagement(self, db: AsyncSession, user_id: int):
        """
        Monitor user engagement and trigger interventions as needed
        
        Args:
            db: Database session
            user_id: ID of the user to monitor
        """
        try:
            # Get user's active onboarding session
            result = await db.execute(
                select(OnboardingSession)
                .where(
                    OnboardingSession.user_id == user_id,
                    OnboardingSession.status == SessionStatus.ACTIVE
                )
            )
            session = result.scalar_one_or_none()
            
            if not session:
                logger.debug(f"No active session found for user {user_id}")
                return
                
            # Get current engagement score
            current_score = await engagement_service.get_current_score(
                db=db,
                user_id=user_id,
                session_id=session.id
            )
            
            # Check if intervention is needed
            if await self._should_intervene(user_id, current_score):
                # Get step context
                context = await self._get_step_context(db, user_id, session.id)
                
                # Trigger intervention
                await self.trigger_help(db, user_id, context, session.id)
                
        except Exception as e:
            logger.error(f"Error monitoring engagement for user {user_id}: {str(e)}")
            
    async def trigger_help(
        self, 
        db: AsyncSession, 
        user_id: int, 
        context: StepContext,
        session_id: Optional[int] = None
    ) -> HelpMessage:
        """
        Generate and trigger contextual help message
        
        Args:
            db: Database session
            user_id: ID of the user
            context: Current step context
            session_id: Optional onboarding session ID
            
        Returns:
            Generated help message
        """
        try:
            # Generate contextual help message
            help_message = await self._generate_contextual_help(context)
            
            # Log the intervention
            intervention_log = InterventionLog(
                user_id=user_id,
                session_id=session_id,
                intervention_type="low_engagement_help",
                message_content=help_message.content,
                triggered_at=datetime.utcnow()
            )
            
            db.add(intervention_log)
            await db.commit()
            
            # Update last intervention timestamp
            self.last_interventions[user_id] = datetime.utcnow()
            
            logger.info(f"Triggered help intervention for user {user_id} on step {context.step_number}")
            
            return help_message
            
        except Exception as e:
            logger.error(f"Error triggering help for user {user_id}: {str(e)}")
            await db.rollback()
            raise
            
    async def _should_intervene(self, user_id: int, engagement_score: float) -> bool:
        """
        Determine if intervention is needed based on score and deduplication rules
        
        Args:
            user_id: ID of the user
            engagement_score: Current engagement score
            
        Returns:
            True if intervention should be triggered
        """
        # Check score threshold
        if engagement_score >= self.intervention_threshold:
            return False
            
        # Check deduplication window
        last_intervention = self.last_interventions.get(user_id)
        if last_intervention:
            time_since_last = datetime.utcnow() - last_intervention
            if time_since_last < timedelta(minutes=self.deduplication_window_minutes):
                logger.debug(f"Intervention blocked for user {user_id} - within deduplication window")
                return False
                
        return True
        
    async def _get_step_context(
        self, 
        db: AsyncSession, 
        user_id: int, 
        session_id: int
    ) -> StepContext:
        """
        Get current step context for generating contextual help
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Onboarding session ID
            
        Returns:
            StepContext object with current step information
        """
        try:
            # Get session and user information
            result = await db.execute(
                select(OnboardingSession, User)
                .join(User, OnboardingSession.user_id == User.id)
                .where(OnboardingSession.id == session_id)
            )
            session_user = result.first()
            
            if not session_user:
                raise ValueError(f"Session {session_id} not found")
                
            session, user = session_user
            
            # Get current step completion info
            result = await db.execute(
                select(StepCompletion)
                .where(
                    and_(
                        StepCompletion.session_id == session_id,
                        StepCompletion.step_number == session.current_step
                    )
                )
            )
            current_step_completion = result.scalar_one_or_none()
            
            # Calculate time on current step
            time_on_step = 0
            if current_step_completion and current_step_completion.started_at:
                time_on_step = int((datetime.utcnow() - current_step_completion.started_at).total_seconds())
                
            # Count previous interventions
            result = await db.execute(
                select(InterventionLog)
                .where(
                    and_(
                        InterventionLog.user_id == user_id,
                        InterventionLog.session_id == session_id
                    )
                )
            )
            previous_interventions = len(result.scalars().all())
            
            # Get current engagement score
            engagement_score = await engagement_service.get_current_score(
                db=db,
                user_id=user_id,
                session_id=session_id
            )
            
            # Generate step title based on role and step number
            step_title = self._generate_step_title(user.role.value, session.current_step)
            
            return StepContext(
                step_number=session.current_step,
                total_steps=session.total_steps,
                step_title=step_title,
                user_role=user.role.value,
                time_on_step=time_on_step,
                previous_interventions=previous_interventions,
                engagement_score=engagement_score
            )
            
        except Exception as e:
            logger.error(f"Error getting step context for session {session_id}: {str(e)}")
            raise
            
    def _generate_step_title(self, user_role: str, step_number: int) -> str:
        """Generate step title based on user role and step number"""
        role_steps = {
            "Developer": [
                "API Authentication Setup",
                "Making Your First API Call", 
                "Handling API Responses",
                "Error Handling and Retries",
                "Advanced API Features"
            ],
            "Business_User": [
                "Understanding the Platform",
                "Creating Your First Workflow",
                "Monitoring and Analytics"
            ],
            "Admin": [
                "System Configuration",
                "User Management",
                "Security Settings",
                "Monitoring and Maintenance"
            ]
        }
        
        steps = role_steps.get(user_role, ["Getting Started", "Next Steps", "Completion"])
        if step_number <= len(steps):
            return steps[step_number - 1]
        else:
            return f"Step {step_number}"
            
    async def _generate_contextual_help(self, context: StepContext) -> HelpMessage:
        """
        Generate contextual help message based on current step context
        
        Args:
            context: Current step context
            
        Returns:
            Generated help message
        """
        try:
            # Generate help content based on context
            help_content = self._get_help_content_for_context(context)
            
            # Create help message
            help_message = HelpMessage(
                message_id=str(uuid.uuid4()),
                content=help_content,
                message_type="contextual_help",
                context={
                    "step_number": context.step_number,
                    "step_title": context.step_title,
                    "user_role": context.user_role,
                    "engagement_score": context.engagement_score,
                    "time_on_step": context.time_on_step
                },
                dismissible=True
            )
            
            return help_message
            
        except Exception as e:
            logger.error(f"Error generating contextual help: {str(e)}")
            # Return generic help message as fallback
            return HelpMessage(
                message_id=str(uuid.uuid4()),
                content="Need help? We're here to assist you with your onboarding journey.",
                message_type="generic_help",
                context={"step_number": context.step_number},
                dismissible=True
            )
            
    def _get_help_content_for_context(self, context: StepContext) -> str:
        """
        Get specific help content based on step context
        
        Args:
            context: Current step context
            
        Returns:
            Contextual help message content
        """
        # Base help messages by role and step
        help_messages = {
            "Developer": {
                1: "Having trouble with API authentication? Check that your API key is correctly formatted and has the right permissions. You can find your API key in the developer console.",
                2: "Stuck on your first API call? Make sure you're using the correct endpoint URL and HTTP method. Try using a tool like Postman to test your request first.",
                3: "Need help handling API responses? Remember to check the response status code first, then parse the JSON data. Our API returns consistent error formats to help with debugging.",
                4: "Error handling giving you trouble? Implement exponential backoff for rate limits and always log errors for debugging. Check our error code documentation for specific handling strategies.",
                5: "Exploring advanced features? Great! Try implementing webhooks for real-time updates, or use our batch endpoints for processing multiple items efficiently."
            },
            "Business_User": {
                1: "New to the platform? Take your time exploring the interface. The dashboard shows your most important metrics, and you can always return to this overview.",
                2: "Creating your first workflow can seem complex, but start simple. Choose a basic template and customize it step by step. You can always add more complexity later.",
                3: "Analytics might look overwhelming at first. Focus on the key metrics that matter to your role - activation rates and user engagement are good starting points."
            },
            "Admin": {
                1: "System configuration is crucial for your organization. Start with the basic settings and security policies. You can always fine-tune these later.",
                2: "User management is straightforward once you understand the role system. Assign roles based on what each user needs to accomplish.",
                3: "Security settings protect your organization. Enable two-factor authentication and review access logs regularly.",
                4: "Monitoring helps you stay ahead of issues. Set up alerts for critical metrics and review system health weekly."
            }
        }
        
        # Get role-specific help
        role_help = help_messages.get(context.user_role, {})
        step_help = role_help.get(context.step_number)
        
        if step_help:
            # Add context-specific additions
            if context.time_on_step > 300:  # More than 5 minutes
                step_help += " You've been on this step for a while - would you like to skip to the next section or get additional resources?"
                
            if context.previous_interventions > 0:
                step_help += " We notice you might need extra support. Consider reaching out to our support team for personalized assistance."
                
            return step_help
        else:
            # Generic help for unknown steps
            return f"Need help with {context.step_title}? This step is important for your {context.user_role.lower()} workflow. Take your time and don't hesitate to explore the available options."
            
    async def get_intervention_history(
        self,
        db: AsyncSession,
        user_id: int,
        session_id: Optional[int] = None,
        limit: int = 10
    ) -> List[InterventionLog]:
        """
        Get intervention history for a user
        
        Args:
            db: Database session
            user_id: ID of the user
            session_id: Optional session ID filter
            limit: Maximum number of interventions to return
            
        Returns:
            List of intervention logs
        """
        try:
            query = select(InterventionLog).where(
                InterventionLog.user_id == user_id
            ).order_by(desc(InterventionLog.triggered_at)).limit(limit)
            
            if session_id:
                query = query.where(InterventionLog.session_id == session_id)
                
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting intervention history for user {user_id}: {str(e)}")
            return []
            
    async def mark_intervention_helpful(
        self,
        db: AsyncSession,
        intervention_id: int,
        was_helpful: bool
    ) -> bool:
        """
        Mark an intervention as helpful or not helpful
        
        Args:
            db: Database session
            intervention_id: ID of the intervention log
            was_helpful: Whether the intervention was helpful
            
        Returns:
            True if successfully updated
        """
        try:
            result = await db.execute(
                select(InterventionLog).where(InterventionLog.id == intervention_id)
            )
            intervention = result.scalar_one_or_none()
            
            if intervention:
                intervention.was_helpful = was_helpful
                await db.commit()
                logger.info(f"Marked intervention {intervention_id} as {'helpful' if was_helpful else 'not helpful'}")
                return True
            else:
                logger.warning(f"Intervention {intervention_id} not found")
                return False
                
        except Exception as e:
            logger.error(f"Error marking intervention {intervention_id} as helpful: {str(e)}")
            await db.rollback()
            return False


# Global intervention system instance
intervention_system = InterventionSystem()