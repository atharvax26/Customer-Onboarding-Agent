"""
Property-based tests for intervention threshold triggering
Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering
Validates: Requirements 4.1, 4.2, 4.3, 4.4
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.intervention_service import InterventionSystem, StepContext
from app.database import (
    User, OnboardingSession, InterventionLog, StepCompletion,
    UserRole, SessionStatus
)
from app.schemas import HelpMessage


# Hypothesis strategies for generating test data
engagement_score_strategy = st.floats(min_value=0.0, max_value=100.0)
user_id_strategy = st.integers(min_value=1, max_value=1000)
session_id_strategy = st.integers(min_value=1, max_value=1000)
step_number_strategy = st.integers(min_value=1, max_value=10)
user_role_strategy = st.sampled_from(["Developer", "Business_User", "Admin"])
time_on_step_strategy = st.integers(min_value=0, max_value=3600)  # 0 to 1 hour
previous_interventions_strategy = st.integers(min_value=0, max_value=10)

# Strategy for generating step context with valid step numbers
step_context_strategy = st.builds(
    StepContext,
    step_number=st.integers(min_value=1, max_value=5),  # Limit to valid step range
    total_steps=st.integers(min_value=3, max_value=10),
    step_title=st.text(min_size=5, max_size=50),
    user_role=user_role_strategy,
    time_on_step=time_on_step_strategy,
    previous_interventions=previous_interventions_strategy,
    engagement_score=engagement_score_strategy
)

# Strategy for time deltas (for deduplication testing)
time_delta_strategy = st.integers(min_value=0, max_value=600)  # 0 to 10 minutes


@pytest.fixture
def fresh_mock_db():
    """Create a fresh mock database session for each test"""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    db.refresh = AsyncMock()
    return db


@pytest.fixture
def intervention_system():
    """Create intervention system instance"""
    return InterventionSystem()


@pytest.mark.asyncio
@given(
    engagement_score=engagement_score_strategy,
    user_id=user_id_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_intervention_threshold_triggering(
    engagement_score,
    user_id
):
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
    
    For any user whose engagement score falls below 30, the Intervention_System should 
    trigger exactly one contextual help message and log the intervention event, with 
    no duplicate messages within a 5-minute window.
    """
    system = InterventionSystem()
    
    # Clear any existing intervention history for this test
    system.last_interventions.clear()
    
    # Test the threshold logic
    should_trigger = system._should_intervene(user_id, engagement_score)
    
    # Verify threshold behavior
    if engagement_score < 30.0:
        assert should_trigger is True, (
            f"Intervention should be triggered for score {engagement_score} < 30"
        )
    else:
        assert should_trigger is False, (
            f"Intervention should NOT be triggered for score {engagement_score} >= 30"
        )
    
    # Test that threshold is exactly 30 (boundary condition)
    boundary_result = system._should_intervene(user_id, 30.0)
    assert boundary_result is False, "Score of exactly 30.0 should NOT trigger intervention"
    
    just_below_result = system._should_intervene(user_id, 29.999)
    assert just_below_result is True, "Score just below 30.0 should trigger intervention"


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    time_since_last_minutes=time_delta_strategy,
    current_score=st.floats(min_value=0.0, max_value=29.9)  # Always below threshold
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_intervention_deduplication_window(
    user_id,
    time_since_last_minutes,
    current_score
):
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.4**
    
    For any user with a low engagement score, the system should prevent duplicate 
    help messages within a 5-minute window, regardless of how many times the 
    threshold is crossed.
    """
    system = InterventionSystem()
    
    # Clear intervention history
    system.last_interventions.clear()
    
    # Set last intervention time
    last_intervention_time = datetime.utcnow() - timedelta(minutes=time_since_last_minutes)
    system.last_interventions[user_id] = last_intervention_time
    
    # Test intervention decision
    should_trigger = system._should_intervene(user_id, current_score)
    
    # Verify deduplication logic
    if time_since_last_minutes < 5:
        assert should_trigger is False, (
            f"Intervention should be blocked within 5-minute window "
            f"(last intervention {time_since_last_minutes} minutes ago)"
        )
    else:
        assert should_trigger is True, (
            f"Intervention should be allowed after 5-minute window "
            f"(last intervention {time_since_last_minutes} minutes ago)"
        )
    
    # Test exact boundary conditions
    system.last_interventions[user_id] = datetime.utcnow() - timedelta(minutes=5, seconds=1)
    boundary_result = system._should_intervene(user_id, current_score)
    assert boundary_result is True, "Intervention should be allowed after exactly 5 minutes + 1 second"
    
    system.last_interventions[user_id] = datetime.utcnow() - timedelta(minutes=4, seconds=59)
    boundary_result = system._should_intervene(user_id, current_score)
    assert boundary_result is False, "Intervention should be blocked at 4 minutes 59 seconds"


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy,
    context=step_context_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_contextual_help_generation(
    user_id,
    session_id,
    context
):
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.2**
    
    For any intervention trigger, the system should display contextual assistance 
    relevant to the current step, with proper message structure and content.
    """
    system = InterventionSystem()
    
    # Create fresh mock database for this test
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    # Mock database operations for intervention logging
    mock_intervention_log = InterventionLog(
        id=1,
        user_id=user_id,
        session_id=session_id,
        intervention_type="low_engagement_help",
        message_content="Test message",
        triggered_at=datetime.utcnow()
    )
    
    # Trigger help message generation
    help_message = await system.trigger_help(
        db=mock_db,
        user_id=user_id,
        context=context,
        session_id=session_id
    )
    
    # Verify help message structure
    assert isinstance(help_message, HelpMessage), "Should return HelpMessage object"
    assert help_message.message_id is not None, "Message should have unique ID"
    assert help_message.content is not None, "Message should have content"
    assert len(help_message.content) > 0, "Message content should not be empty"
    assert help_message.message_type in ["contextual_help", "generic_help"], (
        "Message type should be contextual_help or generic_help"
    )
    assert help_message.dismissible is True, "Help messages should be dismissible"
    
    # Verify contextual information is included
    assert help_message.context is not None, "Message should include context information"
    assert help_message.context["step_number"] == context.step_number, (
        "Context should include correct step number"
    )
    assert help_message.context["user_role"] == context.user_role, (
        "Context should include correct user role"
    )
    
    # Verify database operations were called
    mock_db.add.assert_called_once(), "Should add intervention log to database"
    mock_db.commit.assert_called_once(), "Should commit intervention log"
    
    # Verify last intervention timestamp was updated
    assert user_id in system.last_interventions, "Should update last intervention timestamp"
    assert isinstance(system.last_interventions[user_id], datetime), (
        "Last intervention should be datetime object"
    )


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy,
    context=step_context_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_intervention_logging(
    user_id,
    session_id,
    context
):
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.3**
    
    For any intervention occurrence, the system should log the event with proper 
    details for analytics tracking, including user ID, session ID, intervention 
    type, and timestamp.
    """
    system = InterventionSystem()
    
    # Create fresh mock database for this test
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.rollback = AsyncMock()
    mock_db.execute = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    # Capture the intervention log that gets added to the database
    added_logs = []
    
    def capture_add(log):
        added_logs.append(log)
    
    mock_db.add.side_effect = capture_add
    
    # Trigger intervention
    help_message = await system.trigger_help(
        db=mock_db,
        user_id=user_id,
        context=context,
        session_id=session_id
    )
    
    # Verify intervention was logged
    assert len(added_logs) == 1, "Exactly one intervention log should be created"
    
    intervention_log = added_logs[0]
    assert isinstance(intervention_log, InterventionLog), "Should create InterventionLog object"
    
    # Verify log contents
    assert intervention_log.user_id == user_id, "Log should have correct user ID"
    assert intervention_log.session_id == session_id, "Log should have correct session ID"
    assert intervention_log.intervention_type == "low_engagement_help", (
        "Log should have correct intervention type"
    )
    assert intervention_log.message_content == help_message.content, (
        "Log should contain the help message content"
    )
    assert intervention_log.triggered_at is not None, "Log should have timestamp"
    assert isinstance(intervention_log.triggered_at, datetime), (
        "Timestamp should be datetime object"
    )
    
    # Verify timestamp is recent (within last minute)
    time_diff = datetime.utcnow() - intervention_log.triggered_at
    assert time_diff.total_seconds() < 60, "Timestamp should be recent"
    
    # Verify database commit was called
    mock_db.commit.assert_called_once(), "Should commit the intervention log"


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    engagement_scores=st.lists(
        st.floats(min_value=0.0, max_value=100.0),
        min_size=2,
        max_size=10
    )
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_multiple_threshold_crossings(
    user_id,
    engagement_scores
):
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.1, 4.4**
    
    For any sequence of engagement score changes, the system should trigger 
    interventions only when crossing below the threshold, and respect the 
    deduplication window for subsequent crossings.
    """
    system = InterventionSystem()
    system.last_interventions.clear()
    
    intervention_count = 0
    last_intervention_time = None
    
    for i, score in enumerate(engagement_scores):
        # Simulate time passing between score updates (30 seconds each)
        current_time = datetime.utcnow() + timedelta(seconds=i * 30)
        
        # Mock the current time for consistent testing
        with patch('app.services.intervention_service.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = current_time
            
            should_trigger = system._should_intervene(user_id, score)
            
            if should_trigger:
                intervention_count += 1
                system.last_interventions[user_id] = current_time
                last_intervention_time = current_time
    
    # Verify intervention logic
    below_threshold_scores = [s for s in engagement_scores if s < 30.0]
    
    if not below_threshold_scores:
        # No scores below threshold, no interventions should occur
        assert intervention_count == 0, (
            f"No interventions should occur for scores {engagement_scores} (all >= 30)"
        )
    else:
        # At least one score below threshold
        assert intervention_count >= 1, (
            f"At least one intervention should occur for scores {engagement_scores}"
        )
        
        # Should not exceed the number of 5-minute windows possible
        total_time_minutes = len(engagement_scores) * 0.5  # 30 seconds per score
        max_possible_interventions = max(1, int(total_time_minutes / 5) + 1)
        
        assert intervention_count <= max_possible_interventions, (
            f"Intervention count {intervention_count} should not exceed maximum possible "
            f"{max_possible_interventions} for {total_time_minutes} minutes"
        )


@pytest.mark.asyncio
@given(
    user_role=user_role_strategy,
    time_on_step=time_on_step_strategy,
    previous_interventions=previous_interventions_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_contextual_help_content_relevance(
    user_role,
    time_on_step,
    previous_interventions
):
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.2**
    
    For any step context, the generated help message should be relevant to the 
    user's role and current step, with additional context for extended time 
    or repeated interventions.
    """
    system = InterventionSystem()
    
    # Define valid step ranges for each role
    role_step_ranges = {
        "Developer": 5,
        "Business_User": 3,
        "Admin": 4
    }
    
    # Get valid step number for the role
    max_steps = role_step_ranges.get(user_role, 3)
    step_number = 1 if max_steps == 1 else (hash(user_role + str(time_on_step)) % max_steps) + 1
    
    # Create step context
    context = StepContext(
        step_number=step_number,
        total_steps=max(step_number, 5),  # Ensure total >= current
        step_title=system._generate_step_title(user_role, step_number),
        user_role=user_role,
        time_on_step=time_on_step,
        previous_interventions=previous_interventions,
        engagement_score=25.0  # Below threshold
    )
    
    # Generate help message
    help_message = await system._generate_contextual_help(context)
    
    # Verify message structure
    assert isinstance(help_message, HelpMessage), "Should return HelpMessage"
    assert len(help_message.content) > 0, "Help content should not be empty"
    
    # Verify role-specific content
    content_lower = help_message.content.lower()
    
    if user_role == "Developer":
        # Developer help should mention API-related terms
        api_terms = ["api", "endpoint", "authentication", "response", "request", "code"]
        assert any(term in content_lower for term in api_terms), (
            f"Developer help should contain API-related terms, got: {help_message.content}"
        )
    elif user_role == "Business_User":
        # Business user help should mention workflow/process terms
        business_terms = ["workflow", "process", "dashboard", "metrics", "platform"]
        assert any(term in content_lower for term in business_terms), (
            f"Business user help should contain workflow terms, got: {help_message.content}"
        )
    elif user_role == "Admin":
        # Admin help should mention system/management terms
        admin_terms = ["system", "configuration", "user", "security", "management"]
        assert any(term in content_lower for term in admin_terms), (
            f"Admin help should contain system management terms, got: {help_message.content}"
        )
    
    # Verify additional context for extended time
    if time_on_step > 300:  # More than 5 minutes
        assert "while" in content_lower or "time" in content_lower, (
            "Help should acknowledge extended time on step"
        )
    
    # Verify additional context for repeated interventions
    if previous_interventions > 0:
        assert "support" in content_lower or "help" in content_lower, (
            "Help should offer additional support for repeated interventions"
        )
    
    # Verify context metadata
    assert help_message.context["step_number"] == step_number, (
        "Context should include correct step number"
    )
    assert help_message.context["user_role"] == user_role, (
        "Context should include correct user role"
    )
    assert help_message.context["engagement_score"] == 25.0, (
        "Context should include engagement score"
    )


@pytest.mark.asyncio
async def test_property_intervention_threshold_boundary_conditions():
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.1**
    
    Verification test for exact threshold boundary conditions to ensure the 
    30.0 threshold is implemented correctly.
    """
    system = InterventionSystem()
    user_id = 1
    
    # Clear intervention history
    system.last_interventions.clear()
    
    # Test exact boundary values
    test_cases = [
        (30.0, False, "Exactly 30.0 should NOT trigger"),
        (30.1, False, "30.1 should NOT trigger"),
        (29.9, True, "29.9 should trigger"),
        (29.999999, True, "29.999999 should trigger"),
        (0.0, True, "0.0 should trigger"),
        (100.0, False, "100.0 should NOT trigger"),
    ]
    
    for score, expected_trigger, description in test_cases:
        # Clear history for each test
        system.last_interventions.clear()
        
        result = system._should_intervene(user_id, score)
        assert result == expected_trigger, f"{description}: score {score}, got {result}"
    
    print("✓ Intervention threshold boundary conditions verified")


@pytest.mark.asyncio
async def test_property_deduplication_window_boundary_conditions():
    """
    **Feature: customer-onboarding-agent, Property 6: Intervention Threshold Triggering**
    **Validates: Requirements 4.4**
    
    Verification test for exact deduplication window boundary conditions to 
    ensure the 5-minute window is implemented correctly.
    """
    system = InterventionSystem()
    user_id = 1
    low_score = 25.0  # Below threshold
    
    # Test exact boundary values for deduplication window
    test_cases = [
        (timedelta(minutes=5, seconds=1), True, "5 minutes 1 second should allow"),
        (timedelta(minutes=5), True, "Exactly 5 minutes should allow"),
        (timedelta(minutes=4, seconds=59), False, "4 minutes 59 seconds should block"),
        (timedelta(minutes=0), False, "0 minutes should block"),
        (timedelta(minutes=10), True, "10 minutes should allow"),
    ]
    
    for time_delta, expected_trigger, description in test_cases:
        # Set last intervention time
        system.last_interventions[user_id] = datetime.utcnow() - time_delta
        
        result = system._should_intervene(user_id, low_score)
        assert result == expected_trigger, f"{description}: delta {time_delta}, got {result}"
    
    print("✓ Deduplication window boundary conditions verified")