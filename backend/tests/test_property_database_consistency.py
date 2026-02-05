"""
Property-based tests for database model consistency
Feature: customer-onboarding-agent, Property 10: Data Persistence Consistency
Validates: Requirements 6.3, 6.4
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.database import (
    Base, User, Document, OnboardingSession, StepCompletion, 
    EngagementLog, InterventionLog, UserRole, SessionStatus
)


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


async def create_test_db():
    """Create a fresh test database session"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()


# Hypothesis strategies for generating test data
user_role_strategy = st.sampled_from([UserRole.DEVELOPER, UserRole.BUSINESS_USER, UserRole.ADMIN])
session_status_strategy = st.sampled_from([SessionStatus.ACTIVE, SessionStatus.COMPLETED, SessionStatus.ABANDONED])

email_strategy = st.builds(
    lambda name, domain: f"{name}@{domain}.com",
    name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=1, max_size=20),
    domain=st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=2, max_size=10)
)

password_hash_strategy = st.text(min_size=8, max_size=100)
filename_strategy = st.text(min_size=1, max_size=255).filter(lambda x: '/' not in x and '\\' not in x)
content_strategy = st.text(min_size=1, max_size=10000)
content_hash_strategy = st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=8, max_size=64)

engagement_score_strategy = st.integers(min_value=0, max_value=100)
step_number_strategy = st.integers(min_value=1, max_value=20)
total_steps_strategy = st.integers(min_value=1, max_value=20)
time_spent_strategy = st.integers(min_value=0, max_value=7200)  # 0 to 2 hours in seconds

event_type_strategy = st.sampled_from(["click", "scroll", "focus", "blur", "submit", "load"])
intervention_type_strategy = st.sampled_from(["low_engagement", "step_timeout", "error_help", "contextual_hint"])


@pytest.mark.asyncio
@given(
    email=email_strategy,
    password_hash=password_hash_strategy,
    role=user_role_strategy,
    is_active=st.booleans()
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_user_data_persistence_consistency(email, password_hash, role, is_active):
    """
    **Feature: customer-onboarding-agent, Property 10: Data Persistence Consistency**
    **Validates: Requirements 6.3, 6.4**
    
    For any user data operation, information should be correctly persisted to SQLite 
    using SQLAlchemy and maintain user profiles with accurate role assignments and onboarding progress.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create user with generated data
        user = User(
            email=email,
            password_hash=password_hash,
            role=role,
            is_active=is_active
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Verify persistence consistency
        assert user.id is not None, "User ID should be assigned after persistence"
        assert user.email == email, "Email should be persisted correctly"
        assert user.password_hash == password_hash, "Password hash should be persisted correctly"
        assert user.role == role, "Role should be persisted correctly"
        assert user.is_active == is_active, "Active status should be persisted correctly"
        assert user.created_at is not None, "Created timestamp should be set"
        
        # Verify data can be retrieved from database
        result = await test_db.execute(select(User).where(User.id == user.id))
        retrieved_user = result.scalar_one_or_none()
        
        assert retrieved_user is not None, "User should be retrievable from database"
        assert retrieved_user.email == email, "Retrieved email should match original"
        assert retrieved_user.role == role, "Retrieved role should match original"
        assert retrieved_user.is_active == is_active, "Retrieved active status should match original"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    filename=filename_strategy,
    content=content_strategy,
    content_hash=content_hash_strategy,
    file_size=st.integers(min_value=1, max_value=10000000)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_document_data_persistence_consistency(filename, content, content_hash, file_size):
    """
    **Feature: customer-onboarding-agent, Property 10: Data Persistence Consistency**
    **Validates: Requirements 6.3, 6.4**
    
    For any document data operation, information should be correctly persisted to SQLite 
    using SQLAlchemy with proper content handling and metadata storage.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create document with generated data
        document = Document(
            filename=filename,
            original_content=content,
            content_hash=content_hash,
            file_size=file_size
        )
        
        test_db.add(document)
        await test_db.commit()
        await test_db.refresh(document)
        
        # Verify persistence consistency
        assert document.id is not None, "Document ID should be assigned after persistence"
        assert document.filename == filename, "Filename should be persisted correctly"
        assert document.original_content == content, "Content should be persisted correctly"
        assert document.content_hash == content_hash, "Content hash should be persisted correctly"
        assert document.file_size == file_size, "File size should be persisted correctly"
        assert document.uploaded_at is not None, "Upload timestamp should be set"
        
        # Verify data can be retrieved from database
        result = await test_db.execute(select(Document).where(Document.id == document.id))
        retrieved_doc = result.scalar_one_or_none()
        
        assert retrieved_doc is not None, "Document should be retrievable from database"
        assert retrieved_doc.filename == filename, "Retrieved filename should match original"
        assert retrieved_doc.original_content == content, "Retrieved content should match original"
        assert retrieved_doc.content_hash == content_hash, "Retrieved hash should match original"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_email=email_strategy,
    user_role=user_role_strategy,
    doc_filename=filename_strategy,
    doc_content=content_strategy,
    doc_hash=content_hash_strategy,
    current_step=step_number_strategy,
    total_steps=total_steps_strategy,
    status=session_status_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_onboarding_session_relationship_consistency(
    user_email, user_role, doc_filename, doc_content, 
    doc_hash, current_step, total_steps, status
):
    """
    **Feature: customer-onboarding-agent, Property 10: Data Persistence Consistency**
    **Validates: Requirements 6.3, 6.4**
    
    For any onboarding session data operation, relationships between users, documents, 
    and sessions should be correctly maintained with proper foreign key constraints.
    """
    assume(current_step <= total_steps)  # Ensure logical consistency
    
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create user
        user = User(
            email=user_email,
            password_hash="test_hash",
            role=user_role
        )
        test_db.add(user)
        
        # Create document
        document = Document(
            filename=doc_filename,
            original_content=doc_content,
            content_hash=doc_hash
        )
        test_db.add(document)
        
        await test_db.commit()
        await test_db.refresh(user)
        await test_db.refresh(document)
        
        # Create onboarding session with relationships
        session = OnboardingSession(
            user_id=user.id,
            document_id=document.id,
            current_step=current_step,
            total_steps=total_steps,
            status=status
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)
        
        # Verify relationship consistency
        assert session.id is not None, "Session ID should be assigned after persistence"
        assert session.user_id == user.id, "User ID relationship should be correct"
        assert session.document_id == document.id, "Document ID relationship should be correct"
        assert session.current_step == current_step, "Current step should be persisted correctly"
        assert session.total_steps == total_steps, "Total steps should be persisted correctly"
        assert session.status == status, "Status should be persisted correctly"
        
        # Verify relationships can be navigated
        result = await test_db.execute(
            select(OnboardingSession)
            .where(OnboardingSession.id == session.id)
        )
        retrieved_session = result.scalar_one_or_none()
        
        assert retrieved_session is not None, "Session should be retrievable"
        assert retrieved_session.user_id == user.id, "User relationship should be maintained"
        assert retrieved_session.document_id == document.id, "Document relationship should be maintained"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_email=email_strategy,
    user_role=user_role_strategy,
    event_type=event_type_strategy,
    engagement_score=engagement_score_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_engagement_log_data_consistency(user_email, user_role, event_type, engagement_score):
    """
    **Feature: customer-onboarding-agent, Property 10: Data Persistence Consistency**
    **Validates: Requirements 6.3, 6.4**
    
    For any engagement log data operation, engagement scores and event data should be 
    correctly persisted with proper validation and timestamp handling.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create user first
        user = User(
            email=user_email,
            password_hash="test_hash",
            role=user_role
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Create engagement log
        engagement_log = EngagementLog(
            user_id=user.id,
            event_type=event_type,
            engagement_score=engagement_score,
            event_data={"test": "data"}
        )
        test_db.add(engagement_log)
        await test_db.commit()
        await test_db.refresh(engagement_log)
        
        # Verify persistence consistency
        assert engagement_log.id is not None, "Engagement log ID should be assigned"
        assert engagement_log.user_id == user.id, "User ID should be correct"
        assert engagement_log.event_type == event_type, "Event type should be persisted correctly"
        assert engagement_log.engagement_score == engagement_score, "Engagement score should be persisted correctly"
        assert 0 <= engagement_log.engagement_score <= 100, "Engagement score should be within valid range"
        assert engagement_log.timestamp is not None, "Timestamp should be set"
        
        # Verify data retrieval
        result = await test_db.execute(
            select(EngagementLog).where(EngagementLog.id == engagement_log.id)
        )
        retrieved_log = result.scalar_one_or_none()
        
        assert retrieved_log is not None, "Engagement log should be retrievable"
        assert retrieved_log.engagement_score == engagement_score, "Retrieved score should match original"
        assert retrieved_log.event_type == event_type, "Retrieved event type should match original"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_email=email_strategy,
    user_role=user_role_strategy,
    intervention_type=intervention_type_strategy,
    message_content=st.text(min_size=1, max_size=1000),
    was_helpful=st.booleans()
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_intervention_log_data_consistency(
    user_email, user_role, intervention_type, message_content, was_helpful
):
    """
    **Feature: customer-onboarding-agent, Property 10: Data Persistence Consistency**
    **Validates: Requirements 6.3, 6.4**
    
    For any intervention log data operation, intervention records should be correctly 
    persisted with proper user relationships and timestamp handling.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create user first
        user = User(
            email=user_email,
            password_hash="test_hash",
            role=user_role
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Create intervention log
        intervention_log = InterventionLog(
            user_id=user.id,
            intervention_type=intervention_type,
            message_content=message_content,
            was_helpful=was_helpful
        )
        test_db.add(intervention_log)
        await test_db.commit()
        await test_db.refresh(intervention_log)
        
        # Verify persistence consistency
        assert intervention_log.id is not None, "Intervention log ID should be assigned"
        assert intervention_log.user_id == user.id, "User ID should be correct"
        assert intervention_log.intervention_type == intervention_type, "Intervention type should be persisted correctly"
        assert intervention_log.message_content == message_content, "Message content should be persisted correctly"
        assert intervention_log.was_helpful == was_helpful, "Helpful flag should be persisted correctly"
        assert intervention_log.triggered_at is not None, "Triggered timestamp should be set"
        
        # Verify data retrieval
        result = await test_db.execute(
            select(InterventionLog).where(InterventionLog.id == intervention_log.id)
        )
        retrieved_log = result.scalar_one_or_none()
        
        assert retrieved_log is not None, "Intervention log should be retrievable"
        assert retrieved_log.intervention_type == intervention_type, "Retrieved type should match original"
        assert retrieved_log.message_content == message_content, "Retrieved content should match original"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_email=email_strategy,
    user_role=user_role_strategy,
    doc_filename=filename_strategy,
    step_number=step_number_strategy,
    time_spent=time_spent_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_step_completion_data_consistency(
    user_email, user_role, doc_filename, step_number, time_spent
):
    """
    **Feature: customer-onboarding-agent, Property 10: Data Persistence Consistency**
    **Validates: Requirements 6.3, 6.4**
    
    For any step completion data operation, completion records should be correctly 
    persisted with proper session relationships and timing data.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create user
        user = User(
            email=user_email,
            password_hash="test_hash",
            role=user_role
        )
        test_db.add(user)
        
        # Create document
        document = Document(
            filename=doc_filename,
            original_content="test content",
            content_hash="test_hash"
        )
        test_db.add(document)
        
        await test_db.commit()
        await test_db.refresh(user)
        await test_db.refresh(document)
        
        # Create onboarding session
        session = OnboardingSession(
            user_id=user.id,
            document_id=document.id,
            total_steps=max(step_number, 5)  # Ensure total_steps >= step_number
        )
        test_db.add(session)
        await test_db.commit()
        await test_db.refresh(session)
        
        # Create step completion
        step_completion = StepCompletion(
            session_id=session.id,
            step_number=step_number,
            time_spent_seconds=time_spent,
            step_data={"test": "data"}
        )
        test_db.add(step_completion)
        await test_db.commit()
        await test_db.refresh(step_completion)
        
        # Verify persistence consistency
        assert step_completion.id is not None, "Step completion ID should be assigned"
        assert step_completion.session_id == session.id, "Session ID should be correct"
        assert step_completion.step_number == step_number, "Step number should be persisted correctly"
        assert step_completion.time_spent_seconds == time_spent, "Time spent should be persisted correctly"
        assert step_completion.started_at is not None, "Started timestamp should be set"
        
        # Verify data retrieval and relationships
        result = await test_db.execute(
            select(StepCompletion).where(StepCompletion.id == step_completion.id)
        )
        retrieved_completion = result.scalar_one_or_none()
        
        assert retrieved_completion is not None, "Step completion should be retrievable"
        assert retrieved_completion.session_id == session.id, "Retrieved session ID should match original"
        assert retrieved_completion.step_number == step_number, "Retrieved step number should match original"
        assert retrieved_completion.time_spent_seconds == time_spent, "Retrieved time should match original"
    
    await engine.dispose()