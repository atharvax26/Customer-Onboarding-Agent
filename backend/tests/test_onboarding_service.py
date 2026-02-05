"""
Unit tests for OnboardingEngine service
Tests role-based flow management and linear step progression
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.database import User, Document, OnboardingSession, StepCompletion, UserRole, SessionStatus
from app.services.onboarding_service import OnboardingEngine, OnboardingFlowConfig
from app.schemas import OnboardingSessionResponse, OnboardingStepResponse


class TestOnboardingFlowConfig:
    """Test the OnboardingFlowConfig class"""
    
    def test_role_configs_exist(self):
        """Test that all user roles have configurations"""
        for role in UserRole:
            config = OnboardingFlowConfig.get_role_config(role)
            assert config is not None
            assert "total_steps" in config
            assert "flow_type" in config
            assert "steps" in config
    
    def test_developer_role_config(self):
        """Test Developer role configuration"""
        config = OnboardingFlowConfig.get_role_config(UserRole.DEVELOPER)
        assert config["total_steps"] == 5
        assert config["flow_type"] == "api_focused"
        assert len(config["steps"]) == 5
        
        # Check first step
        first_step = config["steps"][0]
        assert first_step["step_number"] == 1
        assert "API" in first_step["title"]
        assert "tasks" in first_step
        assert isinstance(first_step["tasks"], list)
    
    def test_business_user_role_config(self):
        """Test Business_User role configuration"""
        config = OnboardingFlowConfig.get_role_config(UserRole.BUSINESS_USER)
        assert config["total_steps"] == 3
        assert config["flow_type"] == "workflow_focused"
        assert len(config["steps"]) == 3
        
        # Check first step
        first_step = config["steps"][0]
        assert first_step["step_number"] == 1
        assert "Business" in first_step["title"]
    
    def test_admin_role_config(self):
        """Test Admin role configuration"""
        config = OnboardingFlowConfig.get_role_config(UserRole.ADMIN)
        assert config["total_steps"] == 4
        assert config["flow_type"] == "administrative"
        assert len(config["steps"]) == 4
    
    def test_get_total_steps(self):
        """Test getting total steps for each role"""
        assert OnboardingFlowConfig.get_total_steps(UserRole.DEVELOPER) == 5
        assert OnboardingFlowConfig.get_total_steps(UserRole.BUSINESS_USER) == 3
        assert OnboardingFlowConfig.get_total_steps(UserRole.ADMIN) == 4
    
    def test_get_step_content(self):
        """Test getting step content for specific role and step"""
        # Test valid step
        step_content = OnboardingFlowConfig.get_step_content(UserRole.DEVELOPER, 1)
        assert step_content is not None
        assert step_content["step_number"] == 1
        assert "title" in step_content
        assert "content" in step_content
        assert "tasks" in step_content
        
        # Test invalid step
        invalid_step = OnboardingFlowConfig.get_step_content(UserRole.DEVELOPER, 10)
        assert invalid_step is None


@pytest.mark.asyncio
async def test_start_onboarding_session_developer(db_session: AsyncSession):
    """Test starting onboarding session for Developer role"""
    # Create test user
    user = User(
        email="developer@test.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test document
    document = Document(
        filename="test_doc.txt",
        original_content="Test content",
        content_hash="test_hash_123",
        file_size=100
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Start onboarding session
    engine = OnboardingEngine(db_session)
    session = await engine.start_onboarding_session(user.id, document.id)
    
    # Verify session details
    assert isinstance(session, OnboardingSessionResponse)
    assert session.user_id == user.id
    assert session.document_id == document.id
    assert session.current_step == 1
    assert session.total_steps == 5  # Developer role has 5 steps
    assert session.status == SessionStatus.ACTIVE
    assert session.session_metadata["user_role"] == "Developer"
    assert session.session_metadata["flow_type"] == "api_focused"


@pytest.mark.asyncio
async def test_start_onboarding_session_business_user(db_session: AsyncSession):
    """Test starting onboarding session for Business_User role"""
    # Create test user
    user = User(
        email="business@test.com",
        password_hash="hashed_password",
        role=UserRole.BUSINESS_USER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create test document
    document = Document(
        filename="business_doc.txt",
        original_content="Business content",
        content_hash="business_hash_123",
        file_size=200
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Start onboarding session
    engine = OnboardingEngine(db_session)
    session = await engine.start_onboarding_session(user.id, document.id)
    
    # Verify session details
    assert session.total_steps == 3  # Business_User role has 3 steps
    assert session.session_metadata["user_role"] == "Business_User"
    assert session.session_metadata["flow_type"] == "workflow_focused"


@pytest.mark.asyncio
async def test_start_onboarding_invalid_user(db_session: AsyncSession):
    """Test starting onboarding with invalid user ID"""
    # Create test document
    document = Document(
        filename="test_doc.txt",
        original_content="Test content",
        content_hash="test_hash_456",
        file_size=100
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Try to start session with invalid user
    engine = OnboardingEngine(db_session)
    with pytest.raises(ValueError, match="User with ID 999 not found"):
        await engine.start_onboarding_session(999, document.id)


@pytest.mark.asyncio
async def test_start_onboarding_invalid_document(db_session: AsyncSession):
    """Test starting onboarding with invalid document ID"""
    # Create test user
    user = User(
        email="test@test.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Try to start session with invalid document
    engine = OnboardingEngine(db_session)
    with pytest.raises(ValueError, match="Document with ID 999 not found"):
        await engine.start_onboarding_session(user.id, 999)


@pytest.mark.asyncio
async def test_get_current_step(db_session: AsyncSession):
    """Test getting current step content"""
    # Create test data
    user = User(
        email="step_test@test.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    document = Document(
        filename="step_doc.txt",
        original_content="Step content",
        content_hash="step_hash_123",
        file_size=150
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create onboarding session
    engine = OnboardingEngine(db_session)
    session = await engine.start_onboarding_session(user.id, document.id)
    
    # Get current step
    step = await engine.get_current_step(session.id)
    
    # Verify step content
    assert isinstance(step, OnboardingStepResponse)
    assert step.step_number == 1
    assert step.total_steps == 5
    assert "API Authentication Setup" in step.title
    assert len(step.tasks) > 0
    assert step.estimated_time > 0


@pytest.mark.asyncio
async def test_advance_step(db_session: AsyncSession):
    """Test advancing to next step"""
    # Create test data
    user = User(
        email="advance_test@test.com",
        password_hash="hashed_password",
        role=UserRole.BUSINESS_USER,  # Use Business_User for shorter flow
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    document = Document(
        filename="advance_doc.txt",
        original_content="Advance content",
        content_hash="advance_hash_123",
        file_size=120
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create onboarding session
    engine = OnboardingEngine(db_session)
    session = await engine.start_onboarding_session(user.id, document.id)
    
    # Advance step
    result = await engine.advance_step(session.id)
    
    # Verify advancement
    assert result["status"] == "advanced"
    assert result["current_step"] == 2
    assert result["total_steps"] == 3
    assert "next_step_title" in result


@pytest.mark.asyncio
async def test_complete_onboarding_flow(db_session: AsyncSession):
    """Test completing entire onboarding flow"""
    # Create test data
    user = User(
        email="complete_test@test.com",
        password_hash="hashed_password",
        role=UserRole.BUSINESS_USER,  # 3 steps for faster test
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    document = Document(
        filename="complete_doc.txt",
        original_content="Complete content",
        content_hash="complete_hash_123",
        file_size=180
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create onboarding session
    engine = OnboardingEngine(db_session)
    session = await engine.start_onboarding_session(user.id, document.id)
    
    # Advance through all steps
    for step in range(1, 3):  # Steps 1 and 2
        result = await engine.advance_step(session.id)
        assert result["status"] == "advanced"
    
    # Complete final step
    result = await engine.advance_step(session.id)
    assert result["status"] == "completed"
    assert result["total_steps_completed"] == 3


@pytest.mark.asyncio
async def test_get_session_progress(db_session: AsyncSession):
    """Test getting session progress"""
    # Create test data
    user = User(
        email="progress_test@test.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    document = Document(
        filename="progress_doc.txt",
        original_content="Progress content",
        content_hash="progress_hash_123",
        file_size=160
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create onboarding session and advance one step
    engine = OnboardingEngine(db_session)
    session = await engine.start_onboarding_session(user.id, document.id)
    await engine.advance_step(session.id)
    
    # Get progress
    progress = await engine.get_session_progress(session.id)
    
    # Verify progress
    assert progress.session_id == session.id
    assert progress.current_step == 2
    assert progress.total_steps == 5
    assert progress.completion_percentage == 20.0  # 1 out of 5 steps completed
    assert len(progress.steps_completed) == 1


@pytest.mark.asyncio
async def test_get_user_sessions(db_session: AsyncSession):
    """Test getting all sessions for a user"""
    # Create test data
    user = User(
        email="sessions_test@test.com",
        password_hash="hashed_password",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    document = Document(
        filename="sessions_doc.txt",
        original_content="Sessions content",
        content_hash="sessions_hash_123",
        file_size=140
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create multiple sessions
    engine = OnboardingEngine(db_session)
    session1 = await engine.start_onboarding_session(user.id, document.id)
    session2 = await engine.start_onboarding_session(user.id, document.id)
    
    # Get user sessions
    sessions = await engine.get_user_sessions(user.id)
    
    # Verify sessions
    assert len(sessions) == 2
    session_ids = [s.id for s in sessions]
    assert session1.id in session_ids
    assert session2.id in session_ids


@pytest.mark.asyncio
async def test_get_session_by_id(db_session: AsyncSession):
    """Test getting session by ID"""
    # Create test data
    user = User(
        email="session_id_test@test.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    document = Document(
        filename="session_id_doc.txt",
        original_content="Session ID content",
        content_hash="session_id_hash_123",
        file_size=130
    )
    db_session.add(document)
    await db_session.commit()
    await db_session.refresh(document)
    
    # Create session
    engine = OnboardingEngine(db_session)
    created_session = await engine.start_onboarding_session(user.id, document.id)
    
    # Get session by ID
    retrieved_session = await engine.get_session_by_id(created_session.id)
    
    # Verify session
    assert retrieved_session is not None
    assert retrieved_session.id == created_session.id
    assert retrieved_session.user_id == user.id
    assert retrieved_session.document_id == document.id
    
    # Test non-existent session
    non_existent = await engine.get_session_by_id(999)
    assert non_existent is None