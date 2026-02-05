"""
Background task service for Customer Onboarding Agent
Handles periodic tasks like inactivity detection and score updates
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import AsyncSessionLocal, User, OnboardingSession, SessionStatus
from .engagement_service import engagement_service
from .intervention_service import intervention_system


logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """
    Service for running background tasks
    """
    
    def __init__(self):
        self.running = False
        self.active_users: Set[int] = set()
        
    async def start(self):
        """Start background task monitoring"""
        if self.running:
            return
            
        self.running = True
        logger.info("Starting background task service")
        
        # Start intervention system monitoring
        await intervention_system.start_monitoring()
        
        # Start periodic tasks
        asyncio.create_task(self._periodic_inactivity_check())
        asyncio.create_task(self._periodic_score_updates())
        asyncio.create_task(self._periodic_intervention_check())
        
    async def stop(self):
        """Stop background task monitoring"""
        self.running = False
        
        # Stop intervention system monitoring
        await intervention_system.stop_monitoring()
        
        logger.info("Stopping background task service")
        
    def add_active_user(self, user_id: int):
        """Add user to active monitoring"""
        self.active_users.add(user_id)
        logger.debug(f"Added user {user_id} to active monitoring")
        
    def remove_active_user(self, user_id: int):
        """Remove user from active monitoring"""
        self.active_users.discard(user_id)
        logger.debug(f"Removed user {user_id} from active monitoring")
        
    async def _periodic_inactivity_check(self):
        """Periodically check for user inactivity"""
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    # Check inactivity for all active users
                    for user_id in list(self.active_users):
                        await self._check_user_inactivity(db, user_id)
                        
                # Wait 2 minutes before next check
                await asyncio.sleep(120)
                
            except Exception as e:
                logger.error(f"Error in periodic inactivity check: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
                
    async def _periodic_score_updates(self):
        """Periodically update engagement scores for active users"""
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    # Update scores for all active users
                    for user_id in list(self.active_users):
                        await self._update_user_score(db, user_id)
                        
                # Wait 30 seconds before next update
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error in periodic score updates: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 minute on error
                
    async def _check_user_inactivity(self, db: AsyncSession, user_id: int):
        """Check inactivity for a specific user"""
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
            
            session_id = session.id if session else None
            
            # Check for inactivity
            inactivity_detected = await engagement_service.detect_inactivity(
                db=db,
                user_id=user_id,
                session_id=session_id
            )
            
            if inactivity_detected:
                logger.info(f"Inactivity detected for user {user_id}")
                
        except Exception as e:
            logger.error(f"Error checking inactivity for user {user_id}: {str(e)}")
            
    async def _update_user_score(self, db: AsyncSession, user_id: int):
        """Update engagement score for a specific user"""
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
            
            session_id = session.id if session else None
            
            # Calculate and cache current score
            score = await engagement_service.calculate_score(
                db=db,
                user_id=user_id,
                session_id=session_id
            )
            
            # Update cache
            engagement_service.score_cache[user_id] = score
            
            logger.debug(f"Updated engagement score for user {user_id}: {score}")
            
        except Exception as e:
            logger.error(f"Error updating score for user {user_id}: {str(e)}")
            
    async def _periodic_intervention_check(self):
        """Periodically check for intervention needs"""
        while self.running:
            try:
                async with AsyncSessionLocal() as db:
                    # Check intervention needs for all active users
                    for user_id in list(self.active_users):
                        await intervention_system.monitor_engagement(db, user_id)
                        
                # Wait 1 minute before next check
                await asyncio.sleep(60)
                
            except Exception as e:
                logger.error(f"Error in periodic intervention check: {str(e)}")
                await asyncio.sleep(120)  # Wait 2 minutes on error


# Global background task service instance
background_task_service = BackgroundTaskService()


async def start_background_tasks():
    """Start background task service"""
    await background_task_service.start()


async def stop_background_tasks():
    """Stop background task service"""
    await background_task_service.stop()