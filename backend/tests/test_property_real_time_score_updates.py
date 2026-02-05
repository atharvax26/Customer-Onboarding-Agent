"""
Property-based tests for Real-Time Score Updates
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.engagement_service import EngagementScoringService
from app.database import EngagementLog, OnboardingSession, StepCompletion, User, UserRole, SessionStatus
from app.schemas import InteractionEvent


# Hypothesis strategies for generating test data
user_id_strategy = st.integers(min_value=1, max_value=1000)
session_id_strategy = st.integers(min_value=1, max_value=1000)
step_number_strategy = st.integers(min_value=1, max_value=10)
time_spent_strategy = st.integers(min_value=1, max_value=3600)  # 1 second to 1 hour
duration_strategy = st.integers(min_value=11, max_value=300)  # Significant durations only

# Strategy for generating interaction events
interaction_event_strategy = st.builds(
    InteractionEvent,
    event_type=st.sampled_from(["click", "scroll", "focus", "input", "button_click"]),
    element_id=st.text(min_size=1, max_size=50),
    element_type=st.sampled_from(["button", "link", "input", "div"]),
    page_url=st.text(min_size=1, max_size=100),
    timestamp=st.datetimes(min_value=datetime(2024, 1, 1), max_value=datetime(2024, 12, 31)),
    additional_data=st.dictionaries(st.text(min_size=1, max_size=20), st.text(min_size=1, max_size=50))
)

# Strategy for activity types
activity_type_strategy = st.sampled_from(["page_view", "focus", "scroll", "hover"])


@pytest.fixture
def mock_db():
    """Create a mock database session"""
    db = AsyncMock(spec=AsyncSession)
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def engagement_service():
    """Create engagement service instance"""
    return EngagementScoringService()


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy,
    interaction_event=interaction_event_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_real_time_score_updates_interaction(
    user_id,
    session_id,
    interaction_event,
    mock_db,
    engagement_service
):
    """
    **Feature: customer-onboarding-agent, Property 5: Real-Time Score Updates**
    **Validates: Requirements 3.5**
    
    For any user activity event, the engagement score should be updated within 5 seconds 
    of the activity occurring.
    """
    # Mock the score calculation to return a predictable value
    mock_score = 75.0
    engagement_service.calculate_score = AsyncMock(return_value=mock_score)
    
    # Mock database operations
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # Mock the latest engagement log query
    mock_log = EngagementLog(
        id=1,
        user_id=user_id,
        session_id=session_id,
        event_type=interaction_event.event_type,
        event_data={},
        timestamp=datetime.utcnow(),
        engagement_score=None
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    # Record the start time
    start_time = datetime.utcnow()
    
    # Record interaction event
    await engagement_service.record_interaction(
        db=mock_db,
        user_id=user_id,
        interaction=interaction_event,
        session_id=session_id
    )
    
    # Record the end time
    end_time = datetime.utcnow()
    
    # Calculate elapsed time
    elapsed_time = (end_time - start_time).total_seconds()
    
    # Verify real-time update requirement (within 5 seconds)
    assert elapsed_time <= 5.0, (
        f"Score update took {elapsed_time} seconds, should be within 5 seconds"
    )
    
    # Verify that the interaction was recorded
    mock_db.add.assert_called()
    mock_db.commit.assert_called()
    
    # Verify that score calculation was triggered
    engagement_service.calculate_score.assert_called_once_with(mock_db, user_id, session_id)
    
    # Verify that last activity was updated
    assert user_id in engagement_service.last_activity
    activity_time = engagement_service.last_activity[user_id]
    activity_elapsed = (datetime.utcnow() - activity_time).total_seconds()
    assert activity_elapsed <= 5.0, (
        f"Last activity timestamp should be updated within 5 seconds, was {activity_elapsed} seconds ago"
    )
    
    # Verify that the score was cached
    assert user_id in engagement_service.score_cache
    assert engagement_service.score_cache[user_id] == mock_score


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy,
    step_number=step_number_strategy,
    time_spent=time_spent_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_real_time_score_updates_step_completion(
    user_id,
    session_id,
    step_number,
    time_spent,
    mock_db,
    engagement_service
):
    """
    **Feature: customer-onboarding-agent, Property 5: Real-Time Score Updates**
    **Validates: Requirements 3.5**
    
    For any step completion event, the engagement score should be updated within 5 seconds 
    of the completion occurring.
    """
    # Mock the score calculation to return a predictable value
    mock_score = 85.0
    engagement_service.calculate_score = AsyncMock(return_value=mock_score)
    
    # Mock database operations
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # Mock the latest engagement log query
    mock_log = EngagementLog(
        id=1,
        user_id=user_id,
        session_id=session_id,
        event_type="step_completion",
        event_data={"step_number": step_number, "time_spent_seconds": time_spent},
        timestamp=datetime.utcnow(),
        engagement_score=None
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    # Record the start time
    start_time = datetime.utcnow()
    
    # Record step completion event
    await engagement_service.record_step_completion(
        db=mock_db,
        user_id=user_id,
        session_id=session_id,
        step_number=step_number,
        time_spent_seconds=time_spent
    )
    
    # Record the end time
    end_time = datetime.utcnow()
    
    # Calculate elapsed time
    elapsed_time = (end_time - start_time).total_seconds()
    
    # Verify real-time update requirement (within 5 seconds)
    assert elapsed_time <= 5.0, (
        f"Score update took {elapsed_time} seconds, should be within 5 seconds"
    )
    
    # Verify that the step completion was recorded
    mock_db.add.assert_called()
    mock_db.commit.assert_called()
    
    # Verify that score calculation was triggered
    engagement_service.calculate_score.assert_called_once_with(mock_db, user_id, session_id)
    
    # Verify that last activity was updated
    assert user_id in engagement_service.last_activity
    activity_time = engagement_service.last_activity[user_id]
    activity_elapsed = (datetime.utcnow() - activity_time).total_seconds()
    assert activity_elapsed <= 5.0, (
        f"Last activity timestamp should be updated within 5 seconds, was {activity_elapsed} seconds ago"
    )
    
    # Verify that the score was cached
    assert user_id in engagement_service.score_cache
    assert engagement_service.score_cache[user_id] == mock_score


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy,
    activity_type=activity_type_strategy,
    duration=duration_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_real_time_score_updates_time_activity(
    user_id,
    session_id,
    activity_type,
    duration,
    mock_db,
    engagement_service
):
    """
    **Feature: customer-onboarding-agent, Property 5: Real-Time Score Updates**
    **Validates: Requirements 3.5**
    
    For any significant time activity event (>10 seconds), the engagement score should be 
    updated within 5 seconds of the activity being recorded.
    """
    # Mock the score calculation to return a predictable value
    mock_score = 65.0
    engagement_service.calculate_score = AsyncMock(return_value=mock_score)
    
    # Mock database operations
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # Mock the latest engagement log query
    mock_log = EngagementLog(
        id=1,
        user_id=user_id,
        session_id=session_id,
        event_type=activity_type,
        event_data={"duration_seconds": duration},
        timestamp=datetime.utcnow(),
        engagement_score=None
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    # Record the start time
    start_time = datetime.utcnow()
    
    # Record time activity event (only significant durations trigger score updates)
    await engagement_service.record_time_activity(
        db=mock_db,
        user_id=user_id,
        session_id=session_id,
        activity_type=activity_type,
        duration_seconds=duration
    )
    
    # Record the end time
    end_time = datetime.utcnow()
    
    # Calculate elapsed time
    elapsed_time = (end_time - start_time).total_seconds()
    
    # Verify real-time update requirement (within 5 seconds)
    assert elapsed_time <= 5.0, (
        f"Score update took {elapsed_time} seconds, should be within 5 seconds"
    )
    
    # Verify that the time activity was recorded
    mock_db.add.assert_called()
    mock_db.commit.assert_called()
    
    # Since duration > 10 seconds, score calculation should be triggered
    engagement_service.calculate_score.assert_called_once_with(mock_db, user_id, session_id)
    
    # Verify that last activity was updated
    assert user_id in engagement_service.last_activity
    activity_time = engagement_service.last_activity[user_id]
    activity_elapsed = (datetime.utcnow() - activity_time).total_seconds()
    assert activity_elapsed <= 5.0, (
        f"Last activity timestamp should be updated within 5 seconds, was {activity_elapsed} seconds ago"
    )
    
    # Verify that the score was cached
    assert user_id in engagement_service.score_cache
    assert engagement_service.score_cache[user_id] == mock_score


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_real_time_score_updates_inactivity_detection(
    user_id,
    session_id,
    mock_db,
    engagement_service
):
    """
    **Feature: customer-onboarding-agent, Property 5: Real-Time Score Updates**
    **Validates: Requirements 3.5**
    
    For any inactivity detection event, the engagement score should be updated within 5 seconds 
    of the inactivity being detected.
    """
    # Mock the score calculation to return a predictable value
    mock_score = 45.0
    engagement_service.calculate_score = AsyncMock(return_value=mock_score)
    
    # Mock database operations
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # Mock the latest engagement log query
    mock_log = EngagementLog(
        id=1,
        user_id=user_id,
        session_id=session_id,
        event_type="inactivity_detected",
        event_data={"inactive_duration_seconds": 600},
        timestamp=datetime.utcnow(),
        engagement_score=None
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    # Set old activity to trigger inactivity detection
    old_activity_time = datetime.utcnow() - timedelta(minutes=10)
    engagement_service.last_activity[user_id] = old_activity_time
    
    # Record the start time
    start_time = datetime.utcnow()
    
    # Detect inactivity
    inactivity_detected = await engagement_service.detect_inactivity(
        db=mock_db,
        user_id=user_id,
        session_id=session_id
    )
    
    # Record the end time
    end_time = datetime.utcnow()
    
    # Calculate elapsed time
    elapsed_time = (end_time - start_time).total_seconds()
    
    # Verify that inactivity was detected
    assert inactivity_detected is True, "Inactivity should be detected for old activity"
    
    # Verify real-time update requirement (within 5 seconds)
    assert elapsed_time <= 5.0, (
        f"Score update took {elapsed_time} seconds, should be within 5 seconds"
    )
    
    # Verify that the inactivity event was recorded
    mock_db.add.assert_called()
    mock_db.commit.assert_called()
    
    # Verify that score calculation was triggered
    engagement_service.calculate_score.assert_called_once_with(mock_db, user_id, session_id)
    
    # Verify that the score was cached
    assert user_id in engagement_service.score_cache
    assert engagement_service.score_cache[user_id] == mock_score


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy,
    num_events=st.integers(min_value=1, max_value=10)
)
@settings(max_examples=50, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_real_time_score_updates_multiple_events(
    user_id,
    session_id,
    num_events,
    mock_db,
    engagement_service
):
    """
    **Feature: customer-onboarding-agent, Property 5: Real-Time Score Updates**
    **Validates: Requirements 3.5**
    
    For any sequence of user activity events, each event should trigger a score update 
    within 5 seconds, and the final score should reflect all accumulated activities.
    """
    # Mock the score calculation to return incrementing values
    mock_scores = [50.0 + (i * 5.0) for i in range(num_events)]
    engagement_service.calculate_score = AsyncMock(side_effect=mock_scores)
    
    # Mock database operations
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # Mock the latest engagement log query
    mock_log = EngagementLog(
        id=1,
        user_id=user_id,
        session_id=session_id,
        event_type="click",
        event_data={},
        timestamp=datetime.utcnow(),
        engagement_score=None
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    # Record multiple events and measure timing
    event_times = []
    
    for i in range(num_events):
        start_time = datetime.utcnow()
        
        # Create a simple interaction event
        interaction = InteractionEvent(
            event_type="click",
            element_id=f"button-{i}",
            element_type="button",
            page_url=f"/step-{i}",
            timestamp=datetime.utcnow()
        )
        
        # Record interaction
        await engagement_service.record_interaction(
            db=mock_db,
            user_id=user_id,
            interaction=interaction,
            session_id=session_id
        )
        
        end_time = datetime.utcnow()
        elapsed_time = (end_time - start_time).total_seconds()
        event_times.append(elapsed_time)
        
        # Verify this event was processed within 5 seconds
        assert elapsed_time <= 5.0, (
            f"Event {i+1} took {elapsed_time} seconds, should be within 5 seconds"
        )
    
    # Verify all events were processed
    assert mock_db.add.call_count == num_events, (
        f"Expected {num_events} database adds, got {mock_db.add.call_count}"
    )
    # Each event triggers 2 commits: one in record_interaction and one in _update_engagement_score
    expected_commits = num_events * 2
    assert mock_db.commit.call_count == expected_commits, (
        f"Expected {expected_commits} database commits (2 per event), got {mock_db.commit.call_count}"
    )
    
    # Verify score calculation was called for each event
    assert engagement_service.calculate_score.call_count == num_events, (
        f"Expected {num_events} score calculations, got {engagement_service.calculate_score.call_count}"
    )
    
    # Verify final score reflects the last calculation
    expected_final_score = mock_scores[-1]
    assert user_id in engagement_service.score_cache
    assert engagement_service.score_cache[user_id] == expected_final_score, (
        f"Final cached score should be {expected_final_score}, got {engagement_service.score_cache[user_id]}"
    )
    
    # Verify average processing time is reasonable
    average_time = sum(event_times) / len(event_times)
    assert average_time <= 2.0, (
        f"Average event processing time {average_time} seconds should be well under 5 seconds"
    )
    
    # Verify last activity was updated
    assert user_id in engagement_service.last_activity
    activity_time = engagement_service.last_activity[user_id]
    activity_elapsed = (datetime.utcnow() - activity_time).total_seconds()
    assert activity_elapsed <= 5.0, (
        f"Last activity timestamp should be recent, was {activity_elapsed} seconds ago"
    )


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_real_time_score_updates_concurrent_activities(
    user_id,
    mock_db,
    engagement_service
):
    """
    **Feature: customer-onboarding-agent, Property 5: Real-Time Score Updates**
    **Validates: Requirements 3.5**
    
    For any concurrent user activities, each activity should still trigger score updates 
    within 5 seconds, maintaining data consistency.
    """
    # Mock the score calculation to return predictable values
    mock_score = 70.0
    engagement_service.calculate_score = AsyncMock(return_value=mock_score)
    
    # Mock database operations
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    
    # Mock the latest engagement log query
    mock_log = EngagementLog(
        id=1,
        user_id=user_id,
        session_id=1,
        event_type="click",
        event_data={},
        timestamp=datetime.utcnow(),
        engagement_score=None
    )
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_log
    mock_db.execute.return_value = mock_result
    
    # Create multiple concurrent activities
    async def record_interaction_activity():
        interaction = InteractionEvent(
            event_type="click",
            element_id="concurrent-button",
            element_type="button",
            page_url="/concurrent-test",
            timestamp=datetime.utcnow()
        )
        await engagement_service.record_interaction(
            db=mock_db,
            user_id=user_id,
            interaction=interaction,
            session_id=1
        )
    
    async def record_step_activity():
        await engagement_service.record_step_completion(
            db=mock_db,
            user_id=user_id,
            session_id=1,
            step_number=2,
            time_spent_seconds=120
        )
    
    async def record_time_activity():
        await engagement_service.record_time_activity(
            db=mock_db,
            user_id=user_id,
            session_id=1,
            activity_type="page_view",
            duration_seconds=30
        )
    
    # Record start time
    start_time = datetime.utcnow()
    
    # Execute concurrent activities
    await asyncio.gather(
        record_interaction_activity(),
        record_step_activity(),
        record_time_activity()
    )
    
    # Record end time
    end_time = datetime.utcnow()
    elapsed_time = (end_time - start_time).total_seconds()
    
    # Verify all concurrent activities completed within 5 seconds
    assert elapsed_time <= 5.0, (
        f"Concurrent activities took {elapsed_time} seconds, should be within 5 seconds"
    )
    
    # Verify all activities were recorded (3 database operations)
    assert mock_db.add.call_count == 3, (
        f"Expected 3 database adds for concurrent activities, got {mock_db.add.call_count}"
    )
    # Each activity triggers 2 commits: one in the main method and one in _update_engagement_score
    expected_commits = 3 * 2
    assert mock_db.commit.call_count == expected_commits, (
        f"Expected {expected_commits} database commits (2 per activity), got {mock_db.commit.call_count}"
    )
    
    # Verify score calculations were triggered (3 times)
    assert engagement_service.calculate_score.call_count == 3, (
        f"Expected 3 score calculations for concurrent activities, got {engagement_service.calculate_score.call_count}"
    )
    
    # Verify final state consistency
    assert user_id in engagement_service.last_activity
    assert user_id in engagement_service.score_cache
    assert engagement_service.score_cache[user_id] == mock_score
    
    # Verify last activity timestamp is recent
    activity_time = engagement_service.last_activity[user_id]
    activity_elapsed = (datetime.utcnow() - activity_time).total_seconds()
    assert activity_elapsed <= 5.0, (
        f"Last activity timestamp should be recent after concurrent activities, was {activity_elapsed} seconds ago"
    )