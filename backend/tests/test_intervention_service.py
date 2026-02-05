"""
Unit tests for Intervention Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.intervention_service import InterventionSystem, StepContext
from app.database import User, OnboardingSession, InterventionLog, UserRole, SessionStatus
from app.schemas import HelpMessage


class TestInterventionSystem:
    """Test cases for InterventionSystem"""
    
    @pytest.fixture
    def intervention_system(self):
        """Create intervention system instance for testing"""
        return InterventionSystem()
    
    @pytest.fixture
    async def test_user(self, db_session: AsyncSession):
        """Create test user"""
        user = User(
            email="test@example.com",
            password_hash="hashed_password",
            role=UserRole.DEVELOPER,
            created_at=datetime.utcnow()
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        return user
    
    @pytest.fixture
    async def test_session(self, db_session: AsyncSession, test_user):
        """Create test onboarding session"""
        session = OnboardingSession(
            user_id=test_user.id,
            document_id=1,
            status=SessionStatus.ACTIVE,
            current_step=2,
            total_steps=5,
            started_at=datetime.utcnow()
        )
        db_session.add(session)
        await db_session.commit()
        await db_session.refresh(session)
        return session
    
    @pytest.mark.asyncio
    async def test_should_intervene_score_above_threshold(self, intervention_system):
        """Test that intervention is not triggered when score is above threshold"""
        user_id = 1
        engagement_score = 50.0  # Above threshold of 30
        
        result = await intervention_system._should_intervene(user_id, engagement_score)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_intervene_score_below_threshold(self, intervention_system):
        """Test that intervention is triggered when score is below threshold"""
        user_id = 1
        engagement_score = 25.0  # Below threshold of 30
        
        result = await intervention_system._should_intervene(user_id, engagement_score)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_intervene_deduplication_window(self, intervention_system):
        """Test that intervention is blocked within deduplication window"""
        user_id = 1
        engagement_score = 25.0  # Below threshold
        
        # Set recent intervention
        intervention_system.last_interventions[user_id] = datetime.utcnow() - timedelta(minutes=2)
        
        result = await intervention_system._should_intervene(user_id, engagement_score)
        
        assert result is False  # Should be blocked by deduplication
    
    @pytest.mark.asyncio
    async def test_should_intervene_after_deduplication_window(self, intervention_system):
        """Test that intervention is allowed after deduplication window"""
        user_id = 1
        engagement_score = 25.0  # Below threshold
        
        # Set old intervention (beyond deduplication window)
        intervention_system.last_interventions[user_id] = datetime.utcnow() - timedelta(minutes=10)
        
        result = await intervention_system._should_intervene(user_id, engagement_score)
        
        assert result is True  # Should be allowed after window
    
    def test_generate_step_title_developer(self, intervention_system):
        """Test step title generation for developer role"""
        title = intervention_system._generate_step_title("Developer", 1)
        assert title == "API Authentication Setup"
        
        title = intervention_system._generate_step_title("Developer", 3)
        assert title == "Handling API Responses"
    
    def test_generate_step_title_business_user(self, intervention_system):
        """Test step title generation for business user role"""
        title = intervention_system._generate_step_title("Business_User", 1)
        assert title == "Understanding the Platform"
        
        title = intervention_system._generate_step_title("Business_User", 2)
        assert title == "Creating Your First Workflow"
    
    def test_generate_step_title_admin(self, intervention_system):
        """Test step title generation for admin role"""
        title = intervention_system._generate_step_title("Admin", 1)
        assert title == "System Configuration"
        
        title = intervention_system._generate_step_title("Admin", 4)
        assert title == "Monitoring and Maintenance"
    
    def test_generate_step_title_unknown_step(self, intervention_system):
        """Test step title generation for unknown step number"""
        title = intervention_system._generate_step_title("Developer", 10)
        assert title == "Step 10"
    
    @pytest.mark.asyncio
    async def test_generate_contextual_help_developer(self, intervention_system):
        """Test contextual help generation for developer"""
        context = StepContext(
            step_number=1,
            total_steps=5,
            step_title="API Authentication Setup",
            user_role="Developer",
            time_on_step=120,
            previous_interventions=0,
            engagement_score=25.0
        )
        
        help_message = await intervention_system._generate_contextual_help(context)
        
        assert isinstance(help_message, HelpMessage)
        assert "api authentication" in help_message.content.lower()
        assert help_message.message_type == "contextual_help"
        assert help_message.dismissible is True
    
    @pytest.mark.asyncio
    async def test_generate_contextual_help_business_user(self, intervention_system):
        """Test contextual help generation for business user"""
        context = StepContext(
            step_number=2,
            total_steps=3,
            step_title="Creating Your First Workflow",
            user_role="Business_User",
            time_on_step=400,  # Long time on step
            previous_interventions=1,
            engagement_score=20.0
        )
        
        help_message = await intervention_system._generate_contextual_help(context)
        
        assert isinstance(help_message, HelpMessage)
        assert "workflow" in help_message.content.lower()
        # Should include additional help for long time on step
        assert "while" in help_message.content.lower()
        # Should include additional help for previous interventions
        assert "support" in help_message.content.lower()
    
    @pytest.mark.asyncio
    async def test_trigger_help(self, intervention_system, db_session, test_user, test_session):
        """Test triggering help intervention"""
        context = StepContext(
            step_number=2,
            total_steps=5,
            step_title="Making Your First API Call",
            user_role="Developer",
            time_on_step=120,
            previous_interventions=0,
            engagement_score=25.0
        )
        
        help_message = await intervention_system.trigger_help(
            db=db_session,
            user_id=test_user.id,
            context=context,
            session_id=test_session.id
        )
        
        # Verify help message
        assert isinstance(help_message, HelpMessage)
        assert help_message.content is not None
        
        # Verify last intervention timestamp was updated
        assert test_user.id in intervention_system.last_interventions
    
    @pytest.mark.asyncio
    async def test_get_intervention_history(self, intervention_system, db_session, test_user, test_session):
        """Test getting intervention history"""
        # Create test intervention log
        intervention_log = InterventionLog(
            user_id=test_user.id,
            session_id=test_session.id,
            intervention_type="low_engagement_help",
            message_content="Test help message",
            triggered_at=datetime.utcnow()
        )
        db_session.add(intervention_log)
        await db_session.commit()
        
        # Get intervention history
        history = await intervention_system.get_intervention_history(
            db=db_session,
            user_id=test_user.id,
            session_id=test_session.id
        )
        
        assert len(history) == 1
        assert history[0].user_id == test_user.id
        assert history[0].intervention_type == "low_engagement_help"
        assert history[0].message_content == "Test help message"
    
    @pytest.mark.asyncio
    async def test_mark_intervention_helpful(self, intervention_system, db_session, test_user, test_session):
        """Test marking intervention as helpful"""
        # Create test intervention log
        intervention_log = InterventionLog(
            user_id=test_user.id,
            session_id=test_session.id,
            intervention_type="low_engagement_help",
            message_content="Test help message",
            triggered_at=datetime.utcnow()
        )
        db_session.add(intervention_log)
        await db_session.commit()
        await db_session.refresh(intervention_log)
        
        # Mark as helpful
        success = await intervention_system.mark_intervention_helpful(
            db=db_session,
            intervention_id=intervention_log.id,
            was_helpful=True
        )
        
        assert success is True
        
        # Verify update
        await db_session.refresh(intervention_log)
        assert intervention_log.was_helpful is True
    
    @pytest.mark.asyncio
    async def test_mark_intervention_helpful_not_found(self, intervention_system, db_session):
        """Test marking non-existent intervention as helpful"""
        success = await intervention_system.mark_intervention_helpful(
            db=db_session,
            intervention_id=999,  # Non-existent ID
            was_helpful=True
        )
        
        assert success is False