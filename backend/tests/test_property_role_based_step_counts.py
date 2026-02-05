"""
Property-based tests for role-based step count consistency
Feature: customer-onboarding-agent, Property 2: Role-Based Step Count Consistency
Validates: Requirements 2.1, 2.2
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import Base, User, Document, OnboardingSession, UserRole, SessionStatus
from app.services.onboarding_service import OnboardingEngine, OnboardingFlowConfig
from app.schemas import OnboardingSessionResponse


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Hypothesis strategies for generating test data
user_role_strategy = st.sampled_from([UserRole.DEVELOPER, UserRole.BUSINESS_USER, UserRole.ADMIN])

email_strategy = st.builds(
    lambda name, domain: f"{name}@{domain}.com",
    name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=1, max_size=20),
    domain=st.text(alphabet=st.characters(whitelist_categories=("Ll",)), min_size=2, max_size=10)
)

document_content_strategy = st.text(
    alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd", "Po", "Zs")),
    min_size=50,
    max_size=1000
)

filename_strategy = st.builds(
    lambda name, ext: f"{name}.{ext}",
    name=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=1, max_size=20),
    ext=st.sampled_from(["txt", "pdf", "doc"])
)


@pytest.mark.asyncio
@given(
    user_role=user_role_strategy,
    email=email_strategy,
    filename=filename_strategy,
    document_content=document_content_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_role_based_step_count_consistency(user_role, email, filename, document_content):
    """
    **Feature: customer-onboarding-agent, Property 2: Role-Based Step Count Consistency**
    **Validates: Requirements 2.1, 2.2**
    
    For any user with a specific role, the Onboarding_Engine should serve the correct number of steps:
    Developers get exactly 5 API-focused steps, Business_Users get exactly 3 workflow-focused steps,
    Admins get exactly 4 administrative steps.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create test user with specified role
        user = User(
            email=email,
            password_hash="hashed_password",
            role=user_role,
            is_active=True
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Create test document
        document = Document(
            filename=filename,
            original_content=document_content,
            processed_summary={"summary": "Test summary"},
            step_tasks={"tasks": ["Task 1", "Task 2"]},
            file_size=len(document_content.encode()),
            content_hash=f"hash_{hash(document_content)}"
        )
        
        test_db.add(document)
        await test_db.commit()
        await test_db.refresh(document)
        
        # Initialize onboarding engine
        onboarding_engine = OnboardingEngine(test_db)
        
        # Test step count configuration from OnboardingFlowConfig
        expected_steps = OnboardingFlowConfig.get_total_steps(user_role)
        
        # Verify expected step counts based on requirements
        if user_role == UserRole.DEVELOPER:
            assert expected_steps == 5, "Developers should get exactly 5 API-focused steps (Requirement 2.1)"
        elif user_role == UserRole.BUSINESS_USER:
            assert expected_steps == 3, "Business Users should get exactly 3 workflow-focused steps (Requirement 2.2)"
        elif user_role == UserRole.ADMIN:
            assert expected_steps == 4, "Admins should get exactly 4 administrative steps"
        
        # Test onboarding session creation with correct step count
        session_response = await onboarding_engine.start_onboarding_session(
            user_id=user.id,
            document_id=document.id
        )
        
        # Verify session was created with correct step count
        assert isinstance(session_response, OnboardingSessionResponse), "Should return OnboardingSessionResponse"
        assert session_response.total_steps == expected_steps, \
            f"Session should have {expected_steps} steps for {user_role.value} role"
        assert session_response.current_step == 1, "Session should start at step 1"
        assert session_response.user_id == user.id, "Session should be associated with correct user"
        assert session_response.document_id == document.id, "Session should be associated with correct document"
        
        # Verify role-specific flow configuration
        role_config = OnboardingFlowConfig.get_role_config(user_role)
        assert role_config["total_steps"] == expected_steps, "Role config should match expected step count"
        
        if user_role == UserRole.DEVELOPER:
            assert role_config["flow_type"] == "api_focused", "Developer flow should be API-focused"
            assert len(role_config["steps"]) == 5, "Developer config should have 5 step definitions"
        elif user_role == UserRole.BUSINESS_USER:
            assert role_config["flow_type"] == "workflow_focused", "Business User flow should be workflow-focused"
            assert len(role_config["steps"]) == 3, "Business User config should have 3 step definitions"
        elif user_role == UserRole.ADMIN:
            assert role_config["flow_type"] == "administrative", "Admin flow should be administrative"
            assert len(role_config["steps"]) == 4, "Admin config should have 4 step definitions"
        
        # Verify each step in the configuration is properly defined
        for i, step in enumerate(role_config["steps"], 1):
            assert step["step_number"] == i, f"Step {i} should have correct step number"
            assert "title" in step, f"Step {i} should have a title"
            assert "content" in step, f"Step {i} should have content"
            assert "tasks" in step, f"Step {i} should have tasks"
            assert "estimated_time" in step, f"Step {i} should have estimated time"
            assert isinstance(step["tasks"], list), f"Step {i} tasks should be a list"
            assert len(step["tasks"]) > 0, f"Step {i} should have at least one task"
        
        # Test that step content can be retrieved for each step
        for step_number in range(1, expected_steps + 1):
            step_content = OnboardingFlowConfig.get_step_content(user_role, step_number)
            assert step_content is not None, f"Step {step_number} content should be available for {user_role.value}"
            assert step_content["step_number"] == step_number, f"Step content should have correct step number"
        
        # Test that requesting a step beyond the total returns None
        invalid_step = OnboardingFlowConfig.get_step_content(user_role, expected_steps + 1)
        assert invalid_step is None, f"Step {expected_steps + 1} should not exist for {user_role.value}"
        
        # Verify database session record matches expectations
        db_session_result = await test_db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_response.id)
        )
        db_session = db_session_result.scalar_one()
        
        assert db_session.total_steps == expected_steps, "Database record should have correct total steps"
        assert db_session.current_step == 1, "Database record should start at step 1"
        assert db_session.status == SessionStatus.ACTIVE, "Database record should be active"
        assert db_session.user_id == user.id, "Database record should reference correct user"
        assert db_session.document_id == document.id, "Database record should reference correct document"
        
        # Verify session metadata contains role information
        metadata = db_session.session_metadata
        assert metadata is not None, "Session should have metadata"
        assert metadata["user_role"] == user_role.value, "Metadata should contain user role"
        assert metadata["flow_type"] == role_config["flow_type"], "Metadata should contain flow type"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    roles=st.lists(user_role_strategy, min_size=2, max_size=3, unique=True),
    base_email=st.text(alphabet=st.characters(whitelist_categories=("Ll", "Lu", "Nd")), min_size=1, max_size=15),
    filename=filename_strategy,
    document_content=document_content_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_different_roles_different_step_counts(roles, base_email, filename, document_content):
    """
    **Feature: customer-onboarding-agent, Property 2: Role-Based Step Count Consistency**
    **Validates: Requirements 2.1, 2.2**
    
    For any set of users with different roles, each role should consistently get its designated
    number of steps, and different roles should get different step counts where specified.
    """
    assume(len(roles) >= 2)  # Ensure we have at least 2 different roles
    
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create test document
        document = Document(
            filename=filename,
            original_content=document_content,
            processed_summary={"summary": "Test summary"},
            step_tasks={"tasks": ["Task 1", "Task 2"]},
            file_size=len(document_content.encode()),
            content_hash=f"hash_{hash(document_content)}"
        )
        
        test_db.add(document)
        await test_db.commit()
        await test_db.refresh(document)
        
        # Create users with different roles and test their step counts
        users_and_sessions = []
        onboarding_engine = OnboardingEngine(test_db)
        
        for i, role in enumerate(roles):
            # Create user with unique email
            user = User(
                email=f"{base_email}_{i}@example.com",
                password_hash="hashed_password",
                role=role,
                is_active=True
            )
            
            test_db.add(user)
            await test_db.commit()
            await test_db.refresh(user)
            
            # Create onboarding session
            session_response = await onboarding_engine.start_onboarding_session(
                user_id=user.id,
                document_id=document.id
            )
            
            users_and_sessions.append((user, session_response, role))
        
        # Verify each role gets its expected step count
        role_step_counts = {}
        for user, session, role in users_and_sessions:
            expected_steps = OnboardingFlowConfig.get_total_steps(role)
            
            # Verify session has correct step count
            assert session.total_steps == expected_steps, \
                f"User with role {role.value} should get {expected_steps} steps"
            
            # Track step counts by role
            if role not in role_step_counts:
                role_step_counts[role] = expected_steps
            else:
                assert role_step_counts[role] == expected_steps, \
                    f"All users with role {role.value} should get same step count"
        
        # Verify that different roles get different step counts where expected
        if UserRole.DEVELOPER in role_step_counts and UserRole.BUSINESS_USER in role_step_counts:
            assert role_step_counts[UserRole.DEVELOPER] != role_step_counts[UserRole.BUSINESS_USER], \
                "Developers (5 steps) and Business Users (3 steps) should have different step counts"
        
        if UserRole.DEVELOPER in role_step_counts and UserRole.ADMIN in role_step_counts:
            assert role_step_counts[UserRole.DEVELOPER] != role_step_counts[UserRole.ADMIN], \
                "Developers (5 steps) and Admins (4 steps) should have different step counts"
        
        if UserRole.BUSINESS_USER in role_step_counts and UserRole.ADMIN in role_step_counts:
            assert role_step_counts[UserRole.BUSINESS_USER] != role_step_counts[UserRole.ADMIN], \
                "Business Users (3 steps) and Admins (4 steps) should have different step counts"
        
        # Verify specific step count requirements
        if UserRole.DEVELOPER in role_step_counts:
            assert role_step_counts[UserRole.DEVELOPER] == 5, \
                "Developers should always get exactly 5 steps (Requirement 2.1)"
        
        if UserRole.BUSINESS_USER in role_step_counts:
            assert role_step_counts[UserRole.BUSINESS_USER] == 3, \
                "Business Users should always get exactly 3 steps (Requirement 2.2)"
        
        if UserRole.ADMIN in role_step_counts:
            assert role_step_counts[UserRole.ADMIN] == 4, \
                "Admins should always get exactly 4 steps"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_role=user_role_strategy,
    email=email_strategy,
    filename=filename_strategy,
    document_content=document_content_strategy,
    num_sessions=st.integers(min_value=1, max_value=5)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_consistent_step_counts_across_sessions(user_role, email, filename, document_content, num_sessions):
    """
    **Feature: customer-onboarding-agent, Property 2: Role-Based Step Count Consistency**
    **Validates: Requirements 2.1, 2.2**
    
    For any user with a specific role, multiple onboarding sessions should consistently
    return the same number of steps based on the user's role.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as test_db:
        # Create test user
        user = User(
            email=email,
            password_hash="hashed_password",
            role=user_role,
            is_active=True
        )
        
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
        
        # Create multiple documents and sessions
        onboarding_engine = OnboardingEngine(test_db)
        expected_steps = OnboardingFlowConfig.get_total_steps(user_role)
        session_step_counts = []
        
        for i in range(num_sessions):
            # Create unique document for each session
            document = Document(
                filename=f"{i}_{filename}",
                original_content=f"{i}_{document_content}",
                processed_summary={"summary": f"Test summary {i}"},
                step_tasks={"tasks": [f"Task {i}.1", f"Task {i}.2"]},
                file_size=len(document_content.encode()) + i,
                content_hash=f"hash_{hash(document_content)}_{i}"
            )
            
            test_db.add(document)
            await test_db.commit()
            await test_db.refresh(document)
            
            # Create onboarding session
            session_response = await onboarding_engine.start_onboarding_session(
                user_id=user.id,
                document_id=document.id
            )
            
            session_step_counts.append(session_response.total_steps)
        
        # Verify all sessions have the same step count
        assert len(set(session_step_counts)) == 1, \
            f"All sessions for {user_role.value} should have the same step count"
        
        # Verify the step count matches the expected value for the role
        consistent_step_count = session_step_counts[0]
        assert consistent_step_count == expected_steps, \
            f"All sessions should have {expected_steps} steps for {user_role.value} role"
        
        # Verify role-specific requirements
        if user_role == UserRole.DEVELOPER:
            assert consistent_step_count == 5, \
                "All Developer sessions should have exactly 5 steps (Requirement 2.1)"
        elif user_role == UserRole.BUSINESS_USER:
            assert consistent_step_count == 3, \
                "All Business User sessions should have exactly 3 steps (Requirement 2.2)"
        elif user_role == UserRole.ADMIN:
            assert consistent_step_count == 4, \
                "All Admin sessions should have exactly 4 steps"
    
    await engine.dispose()