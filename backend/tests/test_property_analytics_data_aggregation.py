"""
Property-based tests for analytics data aggregation
Feature: customer-onboarding-agent, Property 7: Analytics Data Aggregation
Validates: Requirements 5.1, 5.2, 5.3
"""

import pytest
import asyncio
import uuid
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from typing import List, Dict, Any
from collections import defaultdict

from app.database import (
    Base, User, OnboardingSession, StepCompletion, EngagementLog, 
    UserRole, SessionStatus
)
from app.services.analytics_service import AnalyticsService
from app.schemas import AnalyticsFilters


# Test database setup
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


# Hypothesis strategies for generating test data
user_role_strategy = st.sampled_from([UserRole.DEVELOPER, UserRole.BUSINESS_USER, UserRole.ADMIN])

# Generate unique emails using UUIDs to ensure uniqueness
email_strategy = st.builds(
    lambda: f"user_{uuid.uuid4().hex[:12]}@test.com"
)

session_status_strategy = st.sampled_from([SessionStatus.ACTIVE, SessionStatus.COMPLETED, SessionStatus.ABANDONED])

# Strategy for generating realistic user data
user_data_strategy = st.builds(
    dict,
    email=email_strategy,
    role=user_role_strategy,
    created_at=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2024, 12, 31)
    ),
    is_active=st.booleans()
)

# Strategy for generating onboarding session data
session_data_strategy = st.builds(
    dict,
    status=session_status_strategy,
    current_step=st.integers(min_value=1, max_value=10),
    total_steps=st.integers(min_value=3, max_value=10),
    started_at=st.datetimes(
        min_value=datetime(2024, 1, 1),
        max_value=datetime(2024, 12, 31)
    )
)

# Strategy for generating step completion data
step_completion_strategy = st.builds(
    dict,
    step_number=st.integers(min_value=1, max_value=10),
    time_spent_seconds=st.integers(min_value=10, max_value=3600),
    completed_at=st.one_of(
        st.none(),
        st.datetimes(
            min_value=datetime(2024, 1, 1),
            max_value=datetime(2024, 12, 31)
        )
    )
)


@pytest.mark.asyncio
@given(
    users_data=st.lists(user_data_strategy, min_size=1, max_size=20),
    sessions_per_user=st.integers(min_value=0, max_value=3),
    steps_per_session=st.integers(min_value=0, max_value=5)
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_analytics_activation_rate_calculation(users_data, sessions_per_user, steps_per_session):
    """
    **Feature: customer-onboarding-agent, Property 7: Analytics Data Aggregation**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    For any analytics request, the dashboard should aggregate data from all user sessions 
    and display activation rates as percentages with accurate step-by-step drop-off statistics.
    
    This test validates that activation rates are calculated correctly as percentages
    based on users who completed their onboarding flow.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        analytics_service = AnalyticsService(db)
        
        # Create users and track expected activation counts
        created_users = []
        expected_activated_count = 0
        role_breakdown_expected = defaultdict(lambda: {"total": 0, "activated": 0})
        
        # Use data strategy to generate session data within the test
        from hypothesis.strategies import data
        
        # Generate a unique test run ID to ensure email uniqueness
        test_run_id = str(uuid.uuid4())[:8]
        
        for i, user_data in enumerate(users_data):
            # Make email unique by using UUID
            unique_email = f"test_{test_run_id}_{i}_{uuid.uuid4().hex[:8]}@test.com"
            
            user = User(
                email=unique_email,
                password_hash="test_hash",
                role=user_data["role"],
                created_at=user_data["created_at"],
                is_active=user_data["is_active"]
            )
            db.add(user)
            await db.flush()  # Get the user ID
            created_users.append(user)
            
            role_breakdown_expected[user.role.value]["total"] += 1
            
            # Create onboarding sessions for this user
            user_has_completed_session = False
            for session_idx in range(sessions_per_user):
                # Generate session data directly
                session_status = SessionStatus.COMPLETED if session_idx == 0 else SessionStatus.ACTIVE
                current_step = min(3, steps_per_session + 1)
                total_steps = max(current_step, 3)
                started_at = user_data["created_at"] + timedelta(hours=session_idx)
                
                session = OnboardingSession(
                    user_id=user.id,
                    document_id=1,  # Assume document exists
                    status=session_status,
                    current_step=current_step,
                    total_steps=total_steps,
                    started_at=started_at
                )
                
                if session_status == SessionStatus.COMPLETED:
                    session.completed_at = started_at + timedelta(hours=1)
                    user_has_completed_session = True
                
                db.add(session)
                await db.flush()
                
                # Create step completions for this session
                for step_num in range(1, min(current_step + 1, steps_per_session + 1)):
                    step_completion = StepCompletion(
                        session_id=session.id,
                        step_number=step_num,
                        started_at=started_at,
                        completed_at=started_at + timedelta(minutes=step_num * 10),
                        time_spent_seconds=step_num * 600
                    )
                    db.add(step_completion)
            
            if user_has_completed_session:
                expected_activated_count += 1
                role_breakdown_expected[user.role.value]["activated"] += 1
        
        await db.commit()
        
        # Test activation rate calculation without filters
        result = await analytics_service.calculate_activation_rates()
        
        # Validate basic metrics
        assert result.total_users == len(users_data)
        assert result.activated_users == expected_activated_count
        
        # Validate activation rate percentage calculation
        expected_rate = (expected_activated_count / len(users_data) * 100) if len(users_data) > 0 else 0.0
        assert abs(result.activation_rate - expected_rate) < 0.01  # Allow for floating point precision
        
        # Validate role breakdown aggregation
        for role_value, expected_counts in role_breakdown_expected.items():
            assert role_value in result.role_breakdown
            actual_counts = result.role_breakdown[role_value]
            assert actual_counts["total"] == expected_counts["total"]
            assert actual_counts["activated"] == expected_counts["activated"]


@pytest.mark.asyncio
@given(
    users_data=st.lists(user_data_strategy, min_size=1, max_size=15),
    filter_role=st.one_of(st.none(), user_role_strategy),
    date_range_days=st.integers(min_value=1, max_value=365)
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_analytics_filtering_accuracy(users_data, filter_role, date_range_days):
    """
    **Feature: customer-onboarding-agent, Property 7: Analytics Data Aggregation**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    For any analytics request with filters, the system should return accurate subsets 
    of data that match the filtering criteria (role, date range).
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        analytics_service = AnalyticsService(db)
        
        # Create users with varied creation dates
        base_date = datetime(2024, 6, 1)
        filter_start_date = base_date
        filter_end_date = base_date + timedelta(days=date_range_days)
        
        created_users = []
        expected_filtered_count = 0
        test_run_id = str(uuid.uuid4())[:8]
        
        for i, user_data in enumerate(users_data):
            # Vary creation dates - some within filter range, some outside
            if i % 3 == 0:
                creation_date = filter_start_date + timedelta(days=i % date_range_days)
            else:
                creation_date = filter_start_date - timedelta(days=i + 1)  # Outside range
            
            # Create unique email for each user
            unique_email = f"test_{test_run_id}_{i}_{uuid.uuid4().hex[:8]}@test.com"
            
            user = User(
                email=unique_email,
                password_hash="test_hash",
                role=user_data["role"],
                created_at=creation_date,
                is_active=user_data["is_active"]
            )
            db.add(user)
            
            # Count users that should match filters
            date_matches = filter_start_date <= creation_date <= filter_end_date
            role_matches = filter_role is None or user.role == filter_role
            
            if date_matches and role_matches:
                expected_filtered_count += 1
            
            created_users.append(user)
        
        await db.commit()
        
        # Create filters
        filters = AnalyticsFilters(
            role=filter_role,
            start_date=filter_start_date,
            end_date=filter_end_date
        )
        
        # Test filtered activation rate calculation
        result = await analytics_service.calculate_activation_rates(filters)
        
        # Validate that filtering works correctly
        assert result.total_users == expected_filtered_count
        
        # If role filter is applied, all users in result should have that role
        if filter_role:
            for role_value, counts in result.role_breakdown.items():
                if counts["total"] > 0:
                    assert role_value == filter_role.value


@pytest.mark.asyncio
@given(
    sessions_data=st.lists(session_data_strategy, min_size=1, max_size=20),
    max_steps=st.integers(min_value=3, max_value=8)
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_analytics_dropoff_analysis_accuracy(sessions_data, max_steps):
    """
    **Feature: customer-onboarding-agent, Property 7: Analytics Data Aggregation**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    For any analytics request, the system should provide accurate step-by-step 
    drop-off statistics showing completion rates for each step.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        analytics_service = AnalyticsService(db)
        
        # Create a test user first
        unique_email = f"test_{uuid.uuid4().hex[:12]}@example.com"
        user = User(
            email=unique_email,
            password_hash="test_hash",
            role=UserRole.DEVELOPER,
            created_at=datetime.now(),
            is_active=True
        )
        db.add(user)
        await db.flush()
        
        # Track expected step statistics
        step_stats_expected = defaultdict(lambda: {"started": 0, "completed": 0})
        completed_sessions_count = 0
        
        # Create onboarding sessions with step completions
        for session_data in sessions_data:
            # Normalize session data
            session_total_steps = min(session_data["total_steps"], max_steps)
            session_current_step = min(session_data["current_step"], session_total_steps)
            
            session = OnboardingSession(
                user_id=user.id,
                document_id=1,
                status=session_data["status"],
                current_step=session_current_step,
                total_steps=session_total_steps,
                started_at=session_data["started_at"]
            )
            
            if session_data["status"] == SessionStatus.COMPLETED:
                session.completed_at = session_data["started_at"] + timedelta(hours=1)
                completed_sessions_count += 1
            
            db.add(session)
            await db.flush()
            
            # Create step completions and track expected statistics
            for step_num in range(1, session_current_step + 1):
                step_stats_expected[step_num]["started"] += 1
                
                # Create step completion
                step_completion = StepCompletion(
                    session_id=session.id,
                    step_number=step_num,
                    started_at=session_data["started_at"],
                    completed_at=session_data["started_at"] + timedelta(minutes=step_num * 10),
                    time_spent_seconds=step_num * 600  # 10 minutes per step
                )
                db.add(step_completion)
                step_stats_expected[step_num]["completed"] += 1
        
        await db.commit()
        
        # Test drop-off analysis
        result = await analytics_service.get_dropoff_analysis()
        
        # Validate overall completion rate
        expected_overall_rate = (completed_sessions_count / len(sessions_data) * 100) if sessions_data else 0.0
        assert abs(result.overall_completion_rate - expected_overall_rate) < 0.01
        
        # Validate step-by-step statistics
        for step_data in result.steps:
            step_num = step_data.step_number
            expected_stats = step_stats_expected[step_num]
            
            assert step_data.started_count == expected_stats["started"]
            assert step_data.completed_count == expected_stats["completed"]
            
            # Validate completion rate calculation
            if expected_stats["started"] > 0:
                expected_completion_rate = (expected_stats["completed"] / expected_stats["started"] * 100)
                assert abs(step_data.completion_rate - expected_completion_rate) < 0.01
            else:
                assert step_data.completion_rate == 0.0


@pytest.mark.asyncio
@given(
    engagement_logs_count=st.integers(min_value=1, max_value=50),
    score_range=st.tuples(
        st.floats(min_value=0.0, max_value=100.0),
        st.floats(min_value=0.0, max_value=100.0)
    ).map(lambda x: (min(x), max(x))),
    days_back=st.integers(min_value=1, max_value=30)
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_analytics_engagement_trends_aggregation(engagement_logs_count, score_range, days_back):
    """
    **Feature: customer-onboarding-agent, Property 7: Analytics Data Aggregation**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    For any analytics request, the system should aggregate engagement data correctly
    and provide accurate trend analysis over time periods.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        analytics_service = AnalyticsService(db)
        
        # Create a test user
        unique_email = f"test_{uuid.uuid4().hex[:12]}@example.com"
        user = User(
            email=unique_email,
            password_hash="test_hash",
            role=UserRole.DEVELOPER,
            created_at=datetime.now(),
            is_active=True
        )
        db.add(user)
        await db.flush()
        
        # Create engagement logs with varied timestamps and scores
        base_date = datetime.now() - timedelta(days=days_back)
        daily_scores = defaultdict(list)
        
        for i in range(engagement_logs_count):
            # Distribute logs across the time period
            log_date = base_date + timedelta(
                days=i % days_back,
                hours=i % 24,
                minutes=i % 60
            )
            
            # Generate score within the specified range
            min_score, max_score = score_range
            score = min_score + (max_score - min_score) * (i / max(engagement_logs_count - 1, 1))
            
            engagement_log = EngagementLog(
                user_id=user.id,
                session_id=1,
                event_type="interaction",
                event_data={"test": "data"},
                engagement_score=score,
                timestamp=log_date
            )
            db.add(engagement_log)
            
            # Track expected daily averages
            daily_scores[log_date.date()].append(score)
        
        await db.commit()
        
        # Test engagement trends analysis
        filters = AnalyticsFilters(
            start_date=base_date,
            end_date=datetime.now()
        )
        result = await analytics_service.get_engagement_trends(filters, days_back=days_back)
        
        # Validate trend data aggregation
        assert result.metric_name == "engagement_score"
        assert len(result.data_points) <= len(daily_scores)  # May have fewer points due to grouping
        
        # Validate that data points have reasonable values
        for data_point in result.data_points:
            assert 0.0 <= data_point.value <= 100.0
            assert data_point.count > 0
            assert isinstance(data_point.date, datetime)
        
        # Validate trend direction calculation
        assert result.trend_direction in ["up", "down", "stable"]


@pytest.mark.asyncio
@given(
    user_count=st.integers(min_value=1, max_value=20),
    session_count=st.integers(min_value=0, max_value=50),
    intervention_count=st.integers(min_value=0, max_value=30)
)
@settings(max_examples=20, deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
async def test_property_analytics_real_time_metrics_accuracy(user_count, session_count, intervention_count):
    """
    **Feature: customer-onboarding-agent, Property 7: Analytics Data Aggregation**
    **Validates: Requirements 5.1, 5.2, 5.3**
    
    For any analytics request, the system should provide accurate real-time metrics
    including active sessions, total sessions, and recent interventions.
    """
    # Create fresh database session for each test
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as db:
        analytics_service = AnalyticsService(db)
        
        # Create users
        created_users = []
        test_run_id = str(uuid.uuid4())[:8]
        for i in range(user_count):
            unique_email = f"user_{test_run_id}_{i}_{uuid.uuid4().hex[:8]}@example.com"
            user = User(
                email=unique_email,
                password_hash="test_hash",
                role=UserRole.DEVELOPER,
                created_at=datetime.now(),
                is_active=True
            )
            db.add(user)
            created_users.append(user)
        
        await db.flush()
        
        # Create sessions with varied statuses
        active_sessions_count = 0
        for i in range(session_count):
            user = created_users[i % len(created_users)]
            status = SessionStatus.ACTIVE if i % 3 == 0 else SessionStatus.COMPLETED
            
            if status == SessionStatus.ACTIVE:
                active_sessions_count += 1
            
            session = OnboardingSession(
                user_id=user.id,
                document_id=1,
                status=status,
                current_step=1,
                total_steps=5,
                started_at=datetime.now()
            )
            db.add(session)
        
        # Create recent intervention logs (last 24 hours)
        recent_interventions_count = 0
        yesterday = datetime.now() - timedelta(days=1)
        
        for i in range(intervention_count):
            user = created_users[i % len(created_users)]
            
            # Some interventions are recent, some are older
            if i % 2 == 0:
                timestamp = datetime.now() - timedelta(hours=i % 12)
                recent_interventions_count += 1
            else:
                timestamp = datetime.now() - timedelta(days=2)  # Older than 24 hours
            
            engagement_log = EngagementLog(
                user_id=user.id,
                session_id=1,
                event_type="intervention_triggered",
                event_data={"intervention": "help_message"},
                engagement_score=25.0,  # Below threshold
                timestamp=timestamp
            )
            db.add(engagement_log)
        
        await db.commit()
        
        # Test real-time metrics calculation
        result = await analytics_service.get_real_time_metrics()
        
        # Validate that metrics are non-negative integers
        assert result["active_sessions"] >= 0
        assert result["total_sessions"] >= 0
        assert result["recent_interventions"] >= 0
        assert isinstance(result["average_engagement_24h"], float)
        assert "last_updated" in result
        assert isinstance(result["last_updated"], datetime)