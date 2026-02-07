"""
Onboarding Engine Service for Customer Onboarding Agent
Manages role-based onboarding flows with linear step progression
"""

from typing import Dict, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime
import json

from app.database import (
    User, Document, OnboardingSession, StepCompletion, 
    UserRole, SessionStatus
)
from app.schemas import (
    OnboardingSessionCreate, OnboardingSessionResponse,
    OnboardingStepResponse, OnboardingProgressResponse,
    StepCompletionCreate, StepCompletionResponse
)


class OnboardingFlowConfig:
    """Configuration for role-based onboarding flows"""
    
    # Role-specific step configurations
    ROLE_CONFIGS = {
        UserRole.DEVELOPER: {
            "total_steps": 5,
            "flow_type": "api_focused",
            "steps": [
                {
                    "step_number": 1,
                    "title": "API Authentication Setup",
                    "content": "Learn how to authenticate with our REST API using JWT tokens",
                    "estimated_time": 10,
                    "tasks": [
                        "Generate API key from dashboard",
                        "Configure authentication headers",
                        "Test authentication endpoint"
                    ]
                },
                {
                    "step_number": 2,
                    "title": "Core API Endpoints",
                    "content": "Explore the main API endpoints for data operations",
                    "estimated_time": 15,
                    "tasks": [
                        "Review API documentation",
                        "Test GET endpoints",
                        "Implement POST operations"
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Error Handling & Rate Limits",
                    "content": "Implement proper error handling and respect rate limits",
                    "estimated_time": 12,
                    "tasks": [
                        "Handle HTTP error codes",
                        "Implement retry logic",
                        "Monitor rate limit headers"
                    ]
                },
                {
                    "step_number": 4,
                    "title": "Webhooks Integration",
                    "content": "Set up webhooks for real-time notifications",
                    "estimated_time": 20,
                    "tasks": [
                        "Configure webhook endpoints",
                        "Verify webhook signatures",
                        "Handle webhook events"
                    ]
                },
                {
                    "step_number": 5,
                    "title": "SDK and Code Examples",
                    "content": "Use our SDKs and explore code examples",
                    "estimated_time": 18,
                    "tasks": [
                        "Install SDK for your language",
                        "Run example applications",
                        "Build a sample integration"
                    ]
                }
            ]
        },
        UserRole.BUSINESS_USER: {
            "total_steps": 3,
            "flow_type": "workflow_focused",
            "steps": [
                {
                    "step_number": 1,
                    "title": "Business Process Overview",
                    "content": "Understand how our platform fits into your business workflow",
                    "estimated_time": 15,
                    "tasks": [
                        "Review business value proposition",
                        "Identify key use cases",
                        "Map to existing processes"
                    ]
                },
                {
                    "step_number": 2,
                    "title": "Dashboard and Analytics",
                    "content": "Learn to use the dashboard for insights and reporting",
                    "estimated_time": 20,
                    "tasks": [
                        "Navigate main dashboard",
                        "Generate custom reports",
                        "Set up automated alerts"
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Team Collaboration",
                    "content": "Set up team access and collaboration features",
                    "estimated_time": 12,
                    "tasks": [
                        "Invite team members",
                        "Configure role permissions",
                        "Share reports and insights"
                    ]
                }
            ]
        },
        UserRole.ADMIN: {
            "total_steps": 4,
            "flow_type": "administrative",
            "steps": [
                {
                    "step_number": 1,
                    "title": "System Configuration",
                    "content": "Configure system-wide settings and preferences",
                    "estimated_time": 25,
                    "tasks": [
                        "Review system settings",
                        "Configure security policies",
                        "Set up backup procedures"
                    ]
                },
                {
                    "step_number": 2,
                    "title": "User Management",
                    "content": "Manage user accounts, roles, and permissions",
                    "estimated_time": 20,
                    "tasks": [
                        "Create user accounts",
                        "Assign roles and permissions",
                        "Monitor user activity"
                    ]
                },
                {
                    "step_number": 3,
                    "title": "Analytics and Monitoring",
                    "content": "Set up system monitoring and analytics tracking",
                    "estimated_time": 18,
                    "tasks": [
                        "Configure monitoring alerts",
                        "Review system metrics",
                        "Set up custom dashboards"
                    ]
                },
                {
                    "step_number": 4,
                    "title": "Integration Management",
                    "content": "Manage third-party integrations and API access",
                    "estimated_time": 15,
                    "tasks": [
                        "Configure API access",
                        "Manage integrations",
                        "Review security logs"
                    ]
                }
            ]
        }
    }
    
    @classmethod
    def get_role_config(cls, role: UserRole) -> Dict[str, Any]:
        """Get configuration for a specific user role"""
        return cls.ROLE_CONFIGS.get(role, cls.ROLE_CONFIGS[UserRole.BUSINESS_USER])
    
    @classmethod
    def get_total_steps(cls, role: UserRole) -> int:
        """Get total number of steps for a role"""
        return cls.get_role_config(role)["total_steps"]
    
    @classmethod
    def get_step_content(cls, role: UserRole, step_number: int) -> Optional[Dict[str, Any]]:
        """Get content for a specific step and role"""
        config = cls.get_role_config(role)
        steps = config.get("steps", [])
        
        for step in steps:
            if step["step_number"] == step_number:
                return step
        return None


class OnboardingEngine:
    """
    Core onboarding engine that manages role-based flows and linear progression
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.flow_config = OnboardingFlowConfig()
    
    async def start_onboarding_session(
        self, 
        user_id: int, 
        document_id: int
    ) -> OnboardingSessionResponse:
        """
        Start a new onboarding session for a user
        
        Args:
            user_id: ID of the user starting onboarding
            document_id: ID of the processed document to base onboarding on
            
        Returns:
            OnboardingSessionResponse with session details
        """
        # Get user to determine role
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            raise ValueError(f"User with ID {user_id} not found")
        
        # Get document to ensure it exists
        doc_result = await self.db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = doc_result.scalar_one_or_none()
        
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")
        
        # Determine total steps: use AI-generated tasks if available, otherwise use role config
        if document.step_tasks and isinstance(document.step_tasks, list) and len(document.step_tasks) > 0:
            total_steps = len(document.step_tasks)
        else:
            # Fallback to role-based configuration
            total_steps = self.flow_config.get_total_steps(user.role)
        
        # Create onboarding session
        session_data = OnboardingSessionCreate(
            user_id=user_id,
            document_id=document_id,
            current_step=1,
            total_steps=total_steps,
            session_metadata={
                "user_role": user.role.value,
                "flow_type": self.flow_config.get_role_config(user.role)["flow_type"],
                "started_at": datetime.utcnow().isoformat()
            }
        )
        
        # Create database record
        db_session = OnboardingSession(
            user_id=session_data.user_id,
            document_id=session_data.document_id,
            current_step=session_data.current_step,
            total_steps=session_data.total_steps,
            session_metadata=session_data.session_metadata,
            status=SessionStatus.ACTIVE
        )
        
        self.db.add(db_session)
        await self.db.commit()
        await self.db.refresh(db_session)
        
        return OnboardingSessionResponse.model_validate(db_session)
    
    async def get_current_step(self, session_id: int) -> OnboardingStepResponse:
        """
        Get the current step content for an onboarding session
        
        Uses AI-generated content from the document if available,
        otherwise falls back to role-based hardcoded steps.
        
        Args:
            session_id: ID of the onboarding session
            
        Returns:
            OnboardingStepResponse with step content and metadata
        """
        # Get session with user and document information
        session_result = await self.db.execute(
            select(OnboardingSession, User, Document)
            .join(User, OnboardingSession.user_id == User.id)
            .join(Document, OnboardingSession.document_id == Document.id)
            .where(OnboardingSession.id == session_id)
        )
        result = session_result.first()
        
        if not result:
            raise ValueError(f"Onboarding session with ID {session_id} not found")
        
        session, user, document = result
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Getting step for session {session_id}: document_id={document.id}, has_step_tasks={document.step_tasks is not None}, step_tasks_count={len(document.step_tasks) if document.step_tasks else 0}")
        
        # Try to use AI-generated content from document first
        if document.step_tasks and isinstance(document.step_tasks, list) and len(document.step_tasks) > 0:
            step_index = session.current_step - 1
            logger.info(f"Using AI-generated content: step_index={step_index}, current_step={session.current_step}")
            
            if 0 <= step_index < len(document.step_tasks):
                ai_task = document.step_tasks[step_index]
                logger.info(f"AI task data: {ai_task}")
                
                # Extract content from AI-generated task
                title = ai_task.get('title', f'Step {session.current_step}')
                description = ai_task.get('description', '')
                
                # Use document summary as additional context if description is short
                if len(description) < 50 and document.processed_summary:
                    summary = document.processed_summary.get('summary', '')
                    if summary:
                        description = f"{description}\n\n{summary}" if description else summary
                
                # Get subtasks from AI-generated content
                # Handle different formats: subtasks, tasks, or create from description
                subtasks = ai_task.get('subtasks', ai_task.get('tasks', []))
                if not subtasks and description:
                    # If no subtasks, create a simple task list from the description
                    subtasks = [description]
                
                # Parse estimated_time (could be string like "5 minutes" or integer)
                estimated_time_raw = ai_task.get('estimated_time', 15)
                if isinstance(estimated_time_raw, str):
                    # Extract number from string like "5 minutes" or "10 min"
                    import re
                    match = re.search(r'(\d+)', estimated_time_raw)
                    estimated_time = int(match.group(1)) if match else 15
                else:
                    estimated_time = estimated_time_raw
                
                logger.info(f"Returning AI-generated step: title='{title}', tasks_count={len(subtasks)}, estimated_time={estimated_time}")
                
                # Get tip from AI-generated content
                tip = ai_task.get('tip', None)
                
                return OnboardingStepResponse(
                    step_number=session.current_step,
                    total_steps=session.total_steps,
                    title=title,
                    content=description,
                    description=description,
                    tasks=subtasks,
                    subtasks=subtasks,
                    estimated_time=estimated_time,
                    tip=tip
                )
        
        # Fallback to hardcoded role-based steps if no AI data available
        logger.info(f"Falling back to hardcoded steps for role {user.role}")
        step_content = self.flow_config.get_step_content(user.role, session.current_step)
        
        if not step_content:
            raise ValueError(f"Step {session.current_step} not found for role {user.role}")
        
        return OnboardingStepResponse(
            step_number=session.current_step,
            total_steps=session.total_steps,
            title=step_content["title"],
            content=step_content["content"],
            tasks=step_content["tasks"],
            estimated_time=step_content["estimated_time"]
        )
    
    async def advance_step(self, session_id: int) -> Dict[str, Any]:
        """
        Advance to the next step in the onboarding flow
        
        Args:
            session_id: ID of the onboarding session
            
        Returns:
            Dictionary with advancement result and next step info
        """
        # Get current session
        session_result = await self.db.execute(
            select(OnboardingSession, User)
            .join(User, OnboardingSession.user_id == User.id)
            .where(OnboardingSession.id == session_id)
        )
        result = session_result.first()
        
        if not result:
            raise ValueError(f"Onboarding session with ID {session_id} not found")
        
        session, user = result
        
        if session.status != SessionStatus.ACTIVE:
            raise ValueError(f"Cannot advance inactive session {session_id}")
        
        # Complete current step
        await self._complete_current_step(session_id, session.current_step)
        
        # Check if this was the final step
        if session.current_step >= session.total_steps:
            # Mark session as completed
            await self.db.execute(
                update(OnboardingSession)
                .where(OnboardingSession.id == session_id)
                .values(
                    status=SessionStatus.COMPLETED,
                    completed_at=datetime.utcnow()
                )
            )
            await self.db.commit()
            
            return {
                "session_id": session_id,
                "status": "completed",
                "message": "Onboarding completed successfully",
                "total_steps_completed": session.total_steps
            }
        
        # Advance to next step
        next_step = session.current_step + 1
        await self.db.execute(
            update(OnboardingSession)
            .where(OnboardingSession.id == session_id)
            .values(current_step=next_step)
        )
        await self.db.commit()
        
        # Get next step content
        next_step_content = self.flow_config.get_step_content(user.role, next_step)
        
        return {
            "session_id": session_id,
            "status": "advanced",
            "current_step": next_step,
            "total_steps": session.total_steps,
            "next_step_title": next_step_content["title"] if next_step_content else None,
            "message": f"Advanced to step {next_step} of {session.total_steps}"
        }
    
    async def get_session_progress(self, session_id: int) -> OnboardingProgressResponse:
        """
        Get detailed progress information for an onboarding session
        
        Args:
            session_id: ID of the onboarding session
            
        Returns:
            OnboardingProgressResponse with detailed progress info
        """
        # Get session
        session_result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if not session:
            raise ValueError(f"Onboarding session with ID {session_id} not found")
        
        # Get completed steps
        steps_result = await self.db.execute(
            select(StepCompletion)
            .where(StepCompletion.session_id == session_id)
            .order_by(StepCompletion.step_number)
        )
        completed_steps = steps_result.scalars().all()
        
        # Calculate completion percentage
        completion_percentage = (len(completed_steps) / session.total_steps) * 100
        
        # Convert to response format
        steps_completed = [
            StepCompletionResponse.model_validate(step) 
            for step in completed_steps
        ]
        
        return OnboardingProgressResponse(
            session_id=session_id,
            current_step=session.current_step,
            total_steps=session.total_steps,
            completion_percentage=completion_percentage,
            steps_completed=steps_completed
        )
    
    async def _complete_current_step(self, session_id: int, step_number: int):
        """
        Mark the current step as completed
        
        Args:
            session_id: ID of the onboarding session
            step_number: Number of the step to complete
        """
        # Check if step completion already exists
        existing_result = await self.db.execute(
            select(StepCompletion)
            .where(
                StepCompletion.session_id == session_id,
                StepCompletion.step_number == step_number
            )
        )
        existing_completion = existing_result.scalar_one_or_none()
        
        if existing_completion:
            # Update existing completion
            if not existing_completion.completed_at:
                existing_completion.completed_at = datetime.utcnow()
                if existing_completion.started_at:
                    time_spent = (existing_completion.completed_at - existing_completion.started_at).total_seconds()
                    existing_completion.time_spent_seconds = int(time_spent)
        else:
            # Create new step completion
            step_completion = StepCompletion(
                session_id=session_id,
                step_number=step_number,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                time_spent_seconds=0,  # Will be calculated when step is actually completed
                step_data={"auto_completed": True}
            )
            self.db.add(step_completion)
        
        await self.db.commit()
    
    async def get_user_sessions(self, user_id: int) -> List[OnboardingSessionResponse]:
        """
        Get all onboarding sessions for a user
        
        Args:
            user_id: ID of the user
            
        Returns:
            List of OnboardingSessionResponse objects
        """
        sessions_result = await self.db.execute(
            select(OnboardingSession)
            .where(OnboardingSession.user_id == user_id)
            .order_by(OnboardingSession.started_at.desc())
        )
        sessions = sessions_result.scalars().all()
        
        return [
            OnboardingSessionResponse.model_validate(session) 
            for session in sessions
        ]
    
    async def get_session_by_id(self, session_id: int) -> Optional[OnboardingSessionResponse]:
        """
        Get a specific onboarding session by ID
        
        Args:
            session_id: ID of the session
            
        Returns:
            OnboardingSessionResponse or None if not found
        """
        session_result = await self.db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        session = session_result.scalar_one_or_none()
        
        if session:
            return OnboardingSessionResponse.model_validate(session)
        return None

