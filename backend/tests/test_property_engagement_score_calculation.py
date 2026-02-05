"""
Property-based tests for Engagement Score Calculation Accuracy
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.engagement_service import EngagementScoringService, EngagementMetrics
from app.database import EngagementLog, OnboardingSession, StepCompletion, User, UserRole, SessionStatus
from app.schemas import InteractionEvent


# Hypothesis strategies for generating test data
step_completion_rate_strategy = st.floats(min_value=0.0, max_value=100.0)
normalized_time_spent_strategy = st.floats(min_value=0.0, max_value=100.0)
interaction_frequency_strategy = st.floats(min_value=0.0, max_value=100.0)
inactivity_penalty_strategy = st.floats(min_value=0.0, max_value=100.0)

user_id_strategy = st.integers(min_value=1, max_value=1000)
session_id_strategy = st.integers(min_value=1, max_value=1000)

# Strategy for generating realistic engagement metrics
engagement_metrics_strategy = st.builds(
    EngagementMetrics,
    step_completion_rate=step_completion_rate_strategy,
    normalized_time_spent=normalized_time_spent_strategy,
    interaction_frequency=interaction_frequency_strategy,
    inactivity_penalty=inactivity_penalty_strategy,
    total_score=st.floats(min_value=0.0, max_value=100.0)
)

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
    step_completion_rate=step_completion_rate_strategy,
    normalized_time_spent=normalized_time_spent_strategy,
    interaction_frequency=interaction_frequency_strategy,
    inactivity_penalty=inactivity_penalty_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_engagement_score_calculation_accuracy(
    step_completion_rate,
    normalized_time_spent,
    interaction_frequency,
    inactivity_penalty
):
    """
    **Feature: customer-onboarding-agent, Property 4: Engagement Score Calculation Accuracy**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4, 3.6**
    
    For any user activity data, the Engagement_Scoring_Service should calculate scores using 
    the exact weighted formula: step_completion(40%) + time_spent(30%) + interactions(20%) - 
    inactivity_penalty(10%), with results always between 0-100 inclusive.
    """
    # Create engagement service
    service = EngagementScoringService()
    
    # Create mock engagement metrics
    metrics = EngagementMetrics(
        step_completion_rate=step_completion_rate,
        normalized_time_spent=normalized_time_spent,
        interaction_frequency=interaction_frequency,
        inactivity_penalty=inactivity_penalty,
        total_score=0.0  # Will be calculated
    )
    
    # Calculate expected score using the exact weighted formula
    expected_score = (
        step_completion_rate * 0.40 +
        normalized_time_spent * 0.30 +
        interaction_frequency * 0.20 -
        inactivity_penalty * 0.10
    )
    
    # Ensure expected score is within bounds (0-100)
    expected_score_bounded = max(0.0, min(100.0, expected_score))
    
    # Mock the _calculate_engagement_metrics method to return our test metrics
    async def mock_calculate_metrics(db, user_id, session_id=None):
        return metrics
    
    service._calculate_engagement_metrics = mock_calculate_metrics
    
    # Create mock database
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Calculate score using the service
    calculated_score = await service.calculate_score(mock_db, user_id=1, session_id=1)
    
    # Verify the score calculation accuracy
    assert isinstance(calculated_score, float), "Score should be a float"
    assert 0.0 <= calculated_score <= 100.0, f"Score {calculated_score} should be between 0-100 inclusive"
    
    # Verify the exact weighted formula is applied correctly
    # Allow for small floating point precision differences
    assert abs(calculated_score - expected_score_bounded) < 0.0001, (
        f"Calculated score {calculated_score} should match expected {expected_score_bounded} "
        f"using formula: ({step_completion_rate} * 0.40) + ({normalized_time_spent} * 0.30) + "
        f"({interaction_frequency} * 0.20) - ({inactivity_penalty} * 0.10) = {expected_score}"
    )
    
    # Verify individual weight components
    step_component = step_completion_rate * 0.40
    time_component = normalized_time_spent * 0.30
    interaction_component = interaction_frequency * 0.20
    penalty_component = inactivity_penalty * 0.10
    
    # Verify weights sum to 1.0 (40% + 30% + 20% + 10% = 100%)
    total_weights = 0.40 + 0.30 + 0.20 + 0.10
    assert abs(total_weights - 1.0) < 0.0001, "Weights should sum to 1.0"
    
    # Verify each component contributes correctly
    manual_calculation = step_component + time_component + interaction_component - penalty_component
    manual_bounded = max(0.0, min(100.0, manual_calculation))
    
    assert abs(calculated_score - manual_bounded) < 0.0001, (
        f"Manual calculation {manual_bounded} should match service calculation {calculated_score}"
    )


@pytest.mark.asyncio
@given(
    user_id=user_id_strategy,
    session_id=session_id_strategy,
    interaction_events=st.lists(interaction_event_strategy, min_size=0, max_size=10)
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_engagement_score_bounds_consistency(
    user_id,
    session_id,
    interaction_events
):
    """
    **Feature: customer-onboarding-agent, Property 4: Engagement Score Calculation Accuracy**
    **Validates: Requirements 3.6**
    
    For any sequence of user interactions, the calculated engagement score should always 
    remain within the bounds of 0-100 inclusive, regardless of input values.
    """
    service = EngagementScoringService()
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Mock database responses for engagement logs
    mock_logs = []
    for i, event in enumerate(interaction_events):
        log = EngagementLog(
            id=i + 1,
            user_id=user_id,
            session_id=session_id,
            event_type=event.event_type,
            event_data={
                "element_id": event.element_id,
                "element_type": event.element_type,
                "duration_seconds": 30  # Add some time data
            },
            timestamp=event.timestamp,
            engagement_score=None
        )
        mock_logs.append(log)
    
    # Mock database query results
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_logs
    mock_db.execute.return_value = mock_result
    
    # Mock onboarding session
    mock_session = OnboardingSession(
        id=session_id,
        user_id=user_id,
        document_id=1,
        status=SessionStatus.ACTIVE,
        current_step=1,
        total_steps=5,
        step_completions=[]
    )
    
    mock_session_result = MagicMock()
    mock_session_result.scalar_one_or_none.return_value = mock_session
    mock_db.execute.return_value = mock_session_result
    
    # Calculate engagement score
    score = await service.calculate_score(mock_db, user_id, session_id)
    
    # Verify score bounds
    assert isinstance(score, (int, float)), "Score should be numeric"
    assert 0.0 <= score <= 100.0, f"Score {score} should be between 0-100 inclusive"
    
    # Verify score is not NaN or infinite
    assert not (score != score), "Score should not be NaN"  # NaN != NaN is True
    assert score != float('inf'), "Score should not be infinite"
    assert score != float('-inf'), "Score should not be negative infinite"


@pytest.mark.asyncio
@given(
    metrics=engagement_metrics_strategy
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_weighted_formula_components(metrics):
    """
    **Feature: customer-onboarding-agent, Property 4: Engagement Score Calculation Accuracy**
    **Validates: Requirements 3.1, 3.2, 3.3, 3.4**
    
    For any engagement metrics, verify that each component of the weighted formula 
    contributes the correct percentage to the final score.
    """
    service = EngagementScoringService()
    
    # Mock the metrics calculation
    async def mock_calculate_metrics(db, user_id, session_id=None):
        return metrics
    
    service._calculate_engagement_metrics = mock_calculate_metrics
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Calculate score
    calculated_score = await service.calculate_score(mock_db, user_id=1)
    
    # Verify individual component weights
    step_contribution = metrics.step_completion_rate * 0.40
    time_contribution = metrics.normalized_time_spent * 0.30
    interaction_contribution = metrics.interaction_frequency * 0.20
    penalty_contribution = metrics.inactivity_penalty * 0.10
    
    # Calculate expected total
    expected_total = step_contribution + time_contribution + interaction_contribution - penalty_contribution
    expected_bounded = max(0.0, min(100.0, expected_total))
    
    # Verify the calculation matches
    assert abs(calculated_score - expected_bounded) < 0.0001, (
        f"Score calculation mismatch: expected {expected_bounded}, got {calculated_score}"
    )
    
    # Verify absolute weight contributions (not relative percentages)
    # Each component should contribute exactly its weight * its value to the total
    expected_step_contribution = metrics.step_completion_rate * 0.40
    expected_time_contribution = metrics.normalized_time_spent * 0.30
    expected_interaction_contribution = metrics.interaction_frequency * 0.20
    expected_penalty_contribution = metrics.inactivity_penalty * 0.10
    
    # Verify the weighted formula components are applied correctly
    manual_score = (
        expected_step_contribution + 
        expected_time_contribution + 
        expected_interaction_contribution - 
        expected_penalty_contribution
    )
    manual_bounded = max(0.0, min(100.0, manual_score))
    
    assert abs(calculated_score - manual_bounded) < 0.0001, (
        f"Manual weighted calculation {manual_bounded} should match service calculation {calculated_score}"
    )
    
    # Verify weight coefficients sum to 1.0 (excluding penalty which is subtracted)
    positive_weights = 0.40 + 0.30 + 0.20  # Step + Time + Interaction
    penalty_weight = 0.10
    total_weight_magnitude = positive_weights + penalty_weight
    assert abs(total_weight_magnitude - 1.0) < 0.0001, "Weight magnitudes should sum to 1.0"


@pytest.mark.asyncio
@given(
    penalty_value=st.floats(min_value=0.0, max_value=200.0)  # Allow values above 100 to test bounds
)
@settings(max_examples=100, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_inactivity_penalty_application(penalty_value):
    """
    **Feature: customer-onboarding-agent, Property 4: Engagement Score Calculation Accuracy**
    **Validates: Requirements 3.4**
    
    For any inactivity penalty value, verify that it reduces the engagement score 
    by exactly 10% of the penalty value, and the final score remains bounded.
    """
    service = EngagementScoringService()
    
    # Create metrics with fixed positive components and variable penalty
    base_metrics = EngagementMetrics(
        step_completion_rate=80.0,  # Fixed high value
        normalized_time_spent=60.0,  # Fixed medium value
        interaction_frequency=40.0,  # Fixed low value
        inactivity_penalty=penalty_value,
        total_score=0.0
    )
    
    # Mock the metrics calculation
    async def mock_calculate_metrics(db, user_id, session_id=None):
        return base_metrics
    
    service._calculate_engagement_metrics = mock_calculate_metrics
    mock_db = AsyncMock(spec=AsyncSession)
    
    # Calculate score with penalty
    score_with_penalty = await service.calculate_score(mock_db, user_id=1)
    
    # Calculate expected score without penalty
    base_score = (80.0 * 0.40) + (60.0 * 0.30) + (40.0 * 0.20)  # 32 + 18 + 8 = 58
    expected_penalty_reduction = penalty_value * 0.10
    expected_score = base_score - expected_penalty_reduction
    expected_bounded = max(0.0, min(100.0, expected_score))
    
    # Verify penalty application
    assert abs(score_with_penalty - expected_bounded) < 0.0001, (
        f"Penalty application incorrect: expected {expected_bounded}, got {score_with_penalty}"
    )
    
    # Verify penalty reduces score (unless already at 0)
    if expected_score > 0 and penalty_value > 0:
        assert score_with_penalty <= base_score, (
            f"Penalty should reduce or maintain score: {score_with_penalty} <= {base_score}"
        )
    
    # Verify bounds are maintained
    assert 0.0 <= score_with_penalty <= 100.0, (
        f"Score with penalty {score_with_penalty} should be within bounds 0-100"
    )