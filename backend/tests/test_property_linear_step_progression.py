"""
Property-based tests for linear step progression
Feature: customer-onboarding-agent, Property 3: Linear Step Progression
Validates: Requirements 2.4, 2.5
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select

from app.database import Base, User, Document, OnboardingSession, StepCompletion, UserRole, SessionStatus
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
async def test_property_linear_step_progression_single_advance(user_role, email, filename, document_content):
    """
    **Feature: customer-onboarding-agent, Property 3: Linear Step Progression**
    **Validates: Requirements 2.4, 2.5**
    
    For any user in an active onboarding session, completing the current step should advance 
    them to the next step in sequence (linear progression).
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
        
        # Initialize onboarding engine and start session
        onboarding_engine = OnboardingEngine(test_db)
        session_response = await onboarding_engine.start_onboarding_session(
            user_id=user.id,
            document_id=document.id
        )
        
        # Verify initial state
        assert session_response.current_step == 1, "Session should start at step 1"
        assert session_response.total_steps > 1, "Session should have multiple steps for progression test"
        
        # Get initial session state from database
        initial_session_result = await test_db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_response.id)
        )
        initial_session = initial_session_result.scalar_one()
        
        assert initial_session.current_step == 1, "Database should show session at step 1"
        assert initial_session.status == SessionStatus.ACTIVE, "Session should be active"
        
        # Advance one step (not the final step)
        if session_response.total_steps > 1:
            advance_result = await onboarding_engine.advance_step(session_response.id)
            
            # Verify advancement result
            assert advance_result["status"] == "advanced", "Step advancement should succeed"
            assert advance_result["current_step"] == 2, "Should advance to step 2"
            assert advance_result["session_id"] == session_response.id, "Should reference correct session"
            
            # Verify database state after advancement
            updated_session_result = await test_db.execute(
                select(OnboardingSession).where(OnboardingSession.id == session_response.id)
            )
            updated_session = updated_session_result.scalar_one()
            
            assert updated_session.current_step == 2, "Database should show session at step 2"
            assert updated_session.status == SessionStatus.ACTIVE, "Session should remain active"
            assert updated_session.completed_at is None, "Session should not be marked completed yet"
            
            # Verify step completion was recorded
            step_completion_result = await test_db.execute(
                select(StepCompletion).where(
                    StepCompletion.session_id == session_response.id,
                    StepCompletion.step_number == 1
                )
            )
            step_completion = step_completion_result.scalar_one_or_none()
            
            assert step_completion is not None, "Step 1 completion should be recorded"
            assert step_completion.completed_at is not None, "Step 1 should have completion timestamp"
            assert step_completion.step_number == 1, "Completion should be for step 1"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_role=user_role_strategy,
    email=email_strategy,
    filename=filename_strategy,
    document_content=document_content_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_linear_step_progression_complete_flow(user_role, email, filename, document_content):
    """
    **Feature: customer-onboarding-agent, Property 3: Linear Step Progression**
    **Validates: Requirements 2.4, 2.5**
    
    For any user in an active onboarding session, completing all steps in sequence should 
    result in linear progression through each step, and completing the final step should 
    mark the onboarding as complete.
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
        
        # Initialize onboarding engine and start session
        onboarding_engine = OnboardingEngine(test_db)
        session_response = await onboarding_engine.start_onboarding_session(
            user_id=user.id,
            document_id=document.id
        )
        
        total_steps = session_response.total_steps
        session_id = session_response.id
        
        # Track progression through all steps
        progression_log = []
        
        # Advance through all steps except the last one
        for expected_step in range(1, total_steps):
            # Get current session state
            current_session_result = await test_db.execute(
                select(OnboardingSession).where(OnboardingSession.id == session_id)
            )
            current_session = current_session_result.scalar_one()
            
            # Verify we're at the expected step
            assert current_session.current_step == expected_step, \
                f"Should be at step {expected_step}, but at step {current_session.current_step}"
            assert current_session.status == SessionStatus.ACTIVE, \
                f"Session should be active at step {expected_step}"
            
            progression_log.append({
                "step": expected_step,
                "status": "active",
                "session_status": current_session.status
            })
            
            # Advance to next step
            advance_result = await onboarding_engine.advance_step(session_id)
            
            # Verify advancement (not final step yet)
            if expected_step < total_steps - 1:
                assert advance_result["status"] == "advanced", \
                    f"Step {expected_step} advancement should succeed"
                assert advance_result["current_step"] == expected_step + 1, \
                    f"Should advance from step {expected_step} to {expected_step + 1}"
            
            progression_log.append({
                "step": expected_step,
                "status": "completed",
                "advance_result": advance_result["status"]
            })
        
        # Now advance the final step
        final_advance_result = await onboarding_engine.advance_step(session_id)
        
        # Verify final step completion marks session as completed (Requirement 2.5)
        assert final_advance_result["status"] == "completed", \
            "Final step advancement should mark session as completed"
        assert final_advance_result["total_steps_completed"] == total_steps, \
            f"Should complete all {total_steps} steps"
        
        # Verify database state after completion
        final_session_result = await test_db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        final_session = final_session_result.scalar_one()
        
        assert final_session.status == SessionStatus.COMPLETED, \
            "Session should be marked as completed in database"
        assert final_session.completed_at is not None, \
            "Session should have completion timestamp"
        assert final_session.current_step == total_steps, \
            f"Session should remain at final step {total_steps}"
        
        # Verify all step completions were recorded
        all_completions_result = await test_db.execute(
            select(StepCompletion).where(StepCompletion.session_id == session_id)
        )
        all_completions = all_completions_result.scalars().all()
        
        assert len(all_completions) == total_steps, \
            f"Should have {total_steps} step completions recorded"
        
        # Verify step completions are in correct sequence
        completion_steps = sorted([comp.step_number for comp in all_completions])
        expected_steps = list(range(1, total_steps + 1))
        assert completion_steps == expected_steps, \
            f"Step completions should be sequential: {expected_steps}"
        
        # Verify each completion has proper timestamps
        for completion in all_completions:
            assert completion.completed_at is not None, \
                f"Step {completion.step_number} should have completion timestamp"
            assert completion.step_number >= 1, \
                f"Step number should be positive: {completion.step_number}"
            assert completion.step_number <= total_steps, \
                f"Step number should not exceed total: {completion.step_number}"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_role=user_role_strategy,
    email=email_strategy,
    filename=filename_strategy,
    document_content=document_content_strategy,
    steps_to_advance=st.integers(min_value=1, max_value=3)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_linear_step_progression_partial_completion(user_role, email, filename, document_content, steps_to_advance):
    """
    **Feature: customer-onboarding-agent, Property 3: Linear Step Progression**
    **Validates: Requirements 2.4, 2.5**
    
    For any user in an active onboarding session, advancing through multiple steps should 
    maintain linear progression, with each step advancing exactly to the next step in sequence.
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
        
        # Initialize onboarding engine and start session
        onboarding_engine = OnboardingEngine(test_db)
        session_response = await onboarding_engine.start_onboarding_session(
            user_id=user.id,
            document_id=document.id
        )
        
        total_steps = session_response.total_steps
        session_id = session_response.id
        
        # Limit steps to advance to not exceed total steps
        max_advances = min(steps_to_advance, total_steps - 1)  # Don't complete final step
        assume(max_advances >= 1)  # Ensure we can advance at least one step
        
        # Track each step advancement
        for advance_count in range(max_advances):
            expected_current_step = advance_count + 1
            expected_next_step = advance_count + 2
            
            # Get session state before advancement
            pre_advance_result = await test_db.execute(
                select(OnboardingSession).where(OnboardingSession.id == session_id)
            )
            pre_advance_session = pre_advance_result.scalar_one()
            
            # Verify current step before advancement
            assert pre_advance_session.current_step == expected_current_step, \
                f"Before advance {advance_count + 1}, should be at step {expected_current_step}"
            assert pre_advance_session.status == SessionStatus.ACTIVE, \
                f"Session should be active before advance {advance_count + 1}"
            
            # Advance step
            advance_result = await onboarding_engine.advance_step(session_id)
            
            # Verify advancement result
            assert advance_result["status"] == "advanced", \
                f"Advance {advance_count + 1} should succeed"
            assert advance_result["current_step"] == expected_next_step, \
                f"After advance {advance_count + 1}, should be at step {expected_next_step}"
            assert advance_result["session_id"] == session_id, \
                f"Advance result should reference correct session"
            
            # Verify database state after advancement
            post_advance_result = await test_db.execute(
                select(OnboardingSession).where(OnboardingSession.id == session_id)
            )
            post_advance_session = post_advance_result.scalar_one()
            
            assert post_advance_session.current_step == expected_next_step, \
                f"Database should show step {expected_next_step} after advance {advance_count + 1}"
            assert post_advance_session.status == SessionStatus.ACTIVE, \
                f"Session should remain active after advance {advance_count + 1}"
            
            # Verify step completion was recorded for the completed step
            completion_result = await test_db.execute(
                select(StepCompletion).where(
                    StepCompletion.session_id == session_id,
                    StepCompletion.step_number == expected_current_step
                )
            )
            completion = completion_result.scalar_one_or_none()
            
            assert completion is not None, \
                f"Step {expected_current_step} completion should be recorded"
            assert completion.completed_at is not None, \
                f"Step {expected_current_step} should have completion timestamp"
        
        # Verify final state
        final_session_result = await test_db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        final_session = final_session_result.scalar_one()
        
        expected_final_step = max_advances + 1
        assert final_session.current_step == expected_final_step, \
            f"Final step should be {expected_final_step}"
        assert final_session.status == SessionStatus.ACTIVE, \
            "Session should still be active (not completed)"
        assert final_session.completed_at is None, \
            "Session should not have completion timestamp yet"
        
        # Verify correct number of completions
        all_completions_result = await test_db.execute(
            select(StepCompletion).where(StepCompletion.session_id == session_id)
        )
        all_completions = all_completions_result.scalars().all()
        
        assert len(all_completions) == max_advances, \
            f"Should have {max_advances} step completions"
        
        # Verify completions are sequential
        completion_steps = sorted([comp.step_number for comp in all_completions])
        expected_completed_steps = list(range(1, max_advances + 1))
        assert completion_steps == expected_completed_steps, \
            f"Completed steps should be sequential: {expected_completed_steps}"
    
    await engine.dispose()


@pytest.mark.asyncio
@given(
    user_role=user_role_strategy,
    email=email_strategy,
    filename=filename_strategy,
    document_content=document_content_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_linear_step_progression_no_step_skipping(user_role, email, filename, document_content):
    """
    **Feature: customer-onboarding-agent, Property 3: Linear Step Progression**
    **Validates: Requirements 2.4, 2.5**
    
    For any user in an active onboarding session, the system should enforce linear progression
    and prevent skipping steps. Each step must be completed in sequence.
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
        
        # Initialize onboarding engine and start session
        onboarding_engine = OnboardingEngine(test_db)
        session_response = await onboarding_engine.start_onboarding_session(
            user_id=user.id,
            document_id=document.id
        )
        
        total_steps = session_response.total_steps
        session_id = session_response.id
        
        # Verify initial state
        assert session_response.current_step == 1, "Should start at step 1"
        
        # Test linear progression by advancing through each step
        for expected_step in range(1, total_steps + 1):
            # Get current session state
            session_result = await test_db.execute(
                select(OnboardingSession).where(OnboardingSession.id == session_id)
            )
            current_session = session_result.scalar_one()
            
            # Verify we're at the expected step (no skipping)
            assert current_session.current_step == expected_step, \
                f"Should be at step {expected_step} (no skipping allowed)"
            
            # Verify we can get step content for current step
            step_content = await onboarding_engine.get_current_step(session_id)
            assert step_content.step_number == expected_step, \
                f"Step content should be for step {expected_step}"
            assert step_content.total_steps == total_steps, \
                f"Step content should show total of {total_steps} steps"
            
            # If not the final step, advance and verify linear progression
            if expected_step < total_steps:
                advance_result = await onboarding_engine.advance_step(session_id)
                
                # Verify advancement is exactly to next step (linear)
                assert advance_result["status"] == "advanced", \
                    f"Should advance from step {expected_step}"
                assert advance_result["current_step"] == expected_step + 1, \
                    f"Should advance to exactly step {expected_step + 1} (linear progression)"
                
                # Verify no steps were skipped by checking step completion
                completion_result = await test_db.execute(
                    select(StepCompletion).where(
                        StepCompletion.session_id == session_id,
                        StepCompletion.step_number == expected_step
                    )
                )
                completion = completion_result.scalar_one_or_none()
                
                assert completion is not None, \
                    f"Step {expected_step} must be completed before advancing (no skipping)"
                assert completion.step_number == expected_step, \
                    f"Completion should be for step {expected_step}"
            
            else:
                # Final step - should complete the session
                advance_result = await onboarding_engine.advance_step(session_id)
                
                assert advance_result["status"] == "completed", \
                    "Final step should complete the session"
                assert advance_result["total_steps_completed"] == total_steps, \
                    f"Should complete all {total_steps} steps"
        
        # Verify final state - all steps completed in sequence
        final_completions_result = await test_db.execute(
            select(StepCompletion).where(StepCompletion.session_id == session_id)
        )
        final_completions = final_completions_result.scalars().all()
        
        # Verify all steps were completed
        assert len(final_completions) == total_steps, \
            f"All {total_steps} steps should be completed"
        
        # Verify no steps were skipped (sequential completion)
        completed_step_numbers = sorted([comp.step_number for comp in final_completions])
        expected_sequence = list(range(1, total_steps + 1))
        assert completed_step_numbers == expected_sequence, \
            f"Steps should be completed in sequence {expected_sequence} (no skipping)"
        
        # Verify session is marked as completed
        final_session_result = await test_db.execute(
            select(OnboardingSession).where(OnboardingSession.id == session_id)
        )
        final_session = final_session_result.scalar_one()
        
        assert final_session.status == SessionStatus.COMPLETED, \
            "Session should be completed after all steps"
        assert final_session.completed_at is not None, \
            "Session should have completion timestamp"
    
    await engine.dispose()