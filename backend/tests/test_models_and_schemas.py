"""
Test database models and Pydantic schemas
"""

import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, User, Document, OnboardingSession, StepCompletion, EngagementLog, InterventionLog, UserRole, SessionStatus
from app.schemas import (
    UserCreate, UserResponse, DocumentCreate, DocumentResponse,
    OnboardingSessionCreate, OnboardingSessionResponse,
    StepCompletionCreate, StepCompletionResponse,
    EngagementLogCreate, EngagementLogResponse,
    InterventionLogCreate, InterventionLogResponse
)


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    """Create test database"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_user_model_creation(test_db: AsyncSession):
    """Test User model creation and relationships"""
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER,
        is_active=True
    )
    
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.role == UserRole.DEVELOPER
    assert user.is_active is True
    assert user.created_at is not None


@pytest.mark.asyncio
async def test_document_model_creation(test_db: AsyncSession):
    """Test Document model creation"""
    document = Document(
        filename="test.pdf",
        original_content="Test content",
        file_size=1024,
        content_hash="abc123"
    )
    
    test_db.add(document)
    await test_db.commit()
    await test_db.refresh(document)
    
    assert document.id is not None
    assert document.filename == "test.pdf"
    assert document.original_content == "Test content"
    assert document.uploaded_at is not None


@pytest.mark.asyncio
async def test_onboarding_session_relationships(test_db: AsyncSession):
    """Test OnboardingSession model with relationships"""
    # Create user
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER
    )
    test_db.add(user)
    
    # Create document
    document = Document(
        filename="test.pdf",
        original_content="Test content",
        content_hash="abc123"
    )
    test_db.add(document)
    
    await test_db.commit()
    await test_db.refresh(user)
    await test_db.refresh(document)
    
    # Create onboarding session
    session = OnboardingSession(
        user_id=user.id,
        document_id=document.id,
        total_steps=5,
        status=SessionStatus.ACTIVE
    )
    test_db.add(session)
    await test_db.commit()
    await test_db.refresh(session)
    
    assert session.id is not None
    assert session.user_id == user.id
    assert session.document_id == document.id
    assert session.total_steps == 5
    assert session.current_step == 1  # Default value


@pytest.mark.asyncio
async def test_engagement_log_creation(test_db: AsyncSession):
    """Test EngagementLog model creation"""
    # Create user first
    user = User(
        email="test@example.com",
        password_hash="hashed_password",
        role=UserRole.DEVELOPER
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    
    # Create engagement log
    engagement_log = EngagementLog(
        user_id=user.id,
        event_type="click",
        event_data={"button": "next"},
        engagement_score=75
    )
    test_db.add(engagement_log)
    await test_db.commit()
    await test_db.refresh(engagement_log)
    
    assert engagement_log.id is not None
    assert engagement_log.user_id == user.id
    assert engagement_log.event_type == "click"
    assert engagement_log.engagement_score == 75
    assert engagement_log.timestamp is not None


def test_user_pydantic_schemas():
    """Test User Pydantic schemas"""
    # Test UserCreate schema
    user_create = UserCreate(
        email="test@example.com",
        password="password123",
        role=UserRole.DEVELOPER
    )
    
    assert user_create.email == "test@example.com"
    assert user_create.password == "password123"
    assert user_create.role == UserRole.DEVELOPER
    assert user_create.is_active is True  # Default value
    
    # Test UserResponse schema
    user_response = UserResponse(
        id=1,
        email="test@example.com",
        role=UserRole.DEVELOPER,
        is_active=True,
        created_at=datetime.utcnow(),
        last_login=None
    )
    
    assert user_response.id == 1
    assert user_response.email == "test@example.com"


def test_document_pydantic_schemas():
    """Test Document Pydantic schemas"""
    # Test DocumentCreate schema
    doc_create = DocumentCreate(
        filename="test.pdf",
        original_content="Test content",
        content_hash="abc123",
        file_size=1024
    )
    
    assert doc_create.filename == "test.pdf"
    assert doc_create.original_content == "Test content"
    
    # Test DocumentResponse schema
    doc_response = DocumentResponse(
        id=1,
        filename="test.pdf",
        file_size=1024,
        processed_summary={"summary": "Test summary"},
        step_tasks=["Task 1", "Task 2"],
        uploaded_at=datetime.utcnow(),
        content_hash="abc123"
    )
    
    assert doc_response.id == 1
    assert doc_response.filename == "test.pdf"


def test_engagement_log_pydantic_schemas():
    """Test EngagementLog Pydantic schemas"""
    # Test EngagementLogCreate schema
    engagement_create = EngagementLogCreate(
        user_id=1,
        event_type="click",
        event_data={"button": "next"},
        engagement_score=75
    )
    
    assert engagement_create.user_id == 1
    assert engagement_create.event_type == "click"
    assert engagement_create.engagement_score == 75
    
    # Test EngagementLogResponse schema
    engagement_response = EngagementLogResponse(
        id=1,
        user_id=1,
        event_type="click",
        event_data={"button": "next"},
        engagement_score=75,
        timestamp=datetime.utcnow()
    )
    
    assert engagement_response.id == 1
    assert engagement_response.user_id == 1


def test_engagement_score_validation():
    """Test engagement score validation in schemas"""
    # Valid score
    engagement_create = EngagementLogCreate(
        user_id=1,
        event_type="click",
        engagement_score=50
    )
    assert engagement_create.engagement_score == 50
    
    # Test boundary values
    engagement_create_min = EngagementLogCreate(
        user_id=1,
        event_type="click",
        engagement_score=0
    )
    assert engagement_create_min.engagement_score == 0
    
    engagement_create_max = EngagementLogCreate(
        user_id=1,
        event_type="click",
        engagement_score=100
    )
    assert engagement_create_max.engagement_score == 100
    
    # Test invalid scores (should raise validation error)
    with pytest.raises(ValueError):
        EngagementLogCreate(
            user_id=1,
            event_type="click",
            engagement_score=-1
        )
    
    with pytest.raises(ValueError):
        EngagementLogCreate(
            user_id=1,
            event_type="click",
            engagement_score=101
        )


def test_user_role_enum():
    """Test UserRole enum values"""
    assert UserRole.DEVELOPER == "Developer"
    assert UserRole.BUSINESS_USER == "Business_User"
    assert UserRole.ADMIN == "Admin"


def test_session_status_enum():
    """Test SessionStatus enum values"""
    assert SessionStatus.ACTIVE == "active"
    assert SessionStatus.COMPLETED == "completed"
    assert SessionStatus.ABANDONED == "abandoned"