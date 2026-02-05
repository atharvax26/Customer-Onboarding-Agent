"""
Tests for Engagement Scoring Service
"""

import pytest
import pytest_asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.engagement_service import EngagementScoringService, EngagementMetrics
from app.schemas import InteractionEvent
from app.database import EngagementLog, User, OnboardingSession, UserRole, SessionStatus


class TestEngagementScoringService:
    """Test suite for EngagementScoringService"""
    
    @pytest.fixture
    def engagement_service(self):
        """Create engagement service instance"""
        return EngagementScoringService()
    
    @pytest.fixture
    def mock_db(self):
        """Create mock database session"""
        return AsyncMock(spec=AsyncSession)
    
    @pytest.fixture
    def sample_interaction(self):
        """Create sample interaction event"""
        return InteractionEvent(
            event_type="click",
            element_id="submit-button",
            element_type="button",
            page_url="/onboarding/step-1",
            timestamp=datetime.utcnow(),
            additional_data={"step": 1}
        )
    
    @pytest.mark.asyncio
    async def test_record_interaction_success(self, engagement_service, mock_db, sample_interaction):
        """Test successful interaction recording"""
        user_id = 1
        session_id = 1
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # Mock score calculation
        engagement_service.calculate_score = AsyncMock(return_value=75.0)
        engagement_service._update_engagement_score = AsyncMock()
        
        # Record interaction
        await engagement_service.record_interaction(
            db=mock_db,
            user_id=user_id,
            interaction=sample_interaction,
            session_id=session_id
        )
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify last activity updated
        assert user_id in engagement_service.last_activity
        
    @pytest.mark.asyncio
    async def test_record_step_completion_success(self, engagement_service, mock_db):
        """Test successful step completion recording"""
        user_id = 1
        session_id = 1
        step_number = 2
        time_spent = 120
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        
        # Mock score update
        engagement_service._update_engagement_score = AsyncMock()
        
        # Record step completion
        await engagement_service.record_step_completion(
            db=mock_db,
            user_id=user_id,
            session_id=session_id,
            step_number=step_number,
            time_spent_seconds=time_spent
        )
        
        # Verify database operations
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Verify last activity updated
        assert user_id in engagement_service.last_activity
        
    @pytest.mark.asyncio
    async def test_calculate_score_bounds(self, engagement_service, mock_db):
        """Test engagement score calculation stays within bounds (0-100)"""
        user_id = 1
        
        # Mock metrics calculation
        engagement_service._calculate_engagement_metrics = AsyncMock(
            return_value=EngagementMetrics(
                step_completion_rate=100.0,
                normalized_time_spent=100.0,
                interaction_frequency=100.0,
                inactivity_penalty=0.0,
                total_score=100.0
            )
        )
        
        # Calculate score
        score = await engagement_service.calculate_score(mock_db, user_id)
        
        # Verify score is within bounds
        assert 0.0 <= score <= 100.0
        # Expected: (100*0.4) + (100*0.3) + (100*0.2) - (0*0.1) = 40 + 30 + 20 - 0 = 90
        assert score == 90.0
        
    @pytest.mark.asyncio
    async def test_calculate_score_with_penalty(self, engagement_service, mock_db):
        """Test engagement score calculation with inactivity penalty"""
        user_id = 1
        
        # Mock metrics with high penalty
        engagement_service._calculate_engagement_metrics = AsyncMock(
            return_value=EngagementMetrics(
                step_completion_rate=50.0,
                normalized_time_spent=30.0,
                interaction_frequency=20.0,
                inactivity_penalty=50.0,  # High penalty
                total_score=25.0
            )
        )
        
        # Calculate score
        score = await engagement_service.calculate_score(mock_db, user_id)
        
        # Verify score reflects penalty
        assert score < 50.0
        assert score >= 0.0
        
    @pytest.mark.asyncio
    async def test_weighted_scoring_algorithm(self, engagement_service, mock_db):
        """Test the weighted scoring algorithm implementation"""
        user_id = 1
        
        # Mock metrics with known values
        engagement_service._calculate_engagement_metrics = AsyncMock(
            return_value=EngagementMetrics(
                step_completion_rate=80.0,  # 40% weight
                normalized_time_spent=60.0,  # 30% weight
                interaction_frequency=40.0,  # 20% weight
                inactivity_penalty=10.0,     # 10% weight (penalty)
                total_score=0.0  # Will be calculated
            )
        )
        
        # Calculate score
        score = await engagement_service.calculate_score(mock_db, user_id)
        
        # Expected: (80*0.4) + (60*0.3) + (40*0.2) - (10*0.1) = 32 + 18 + 8 - 1 = 57
        expected_score = 57.0
        assert abs(score - expected_score) < 0.1
        
    @pytest.mark.asyncio
    async def test_detect_inactivity_no_activity(self, engagement_service, mock_db):
        """Test inactivity detection when no activity recorded"""
        user_id = 1
        
        # Mock database query returning no results
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.execute = AsyncMock(return_value=mock_result)
        
        # Detect inactivity
        inactivity_detected = await engagement_service.detect_inactivity(
            db=mock_db,
            user_id=user_id
        )
        
        # Should return False when no activity found
        assert inactivity_detected is False
        
    @pytest.mark.asyncio
    async def test_detect_inactivity_recent_activity(self, engagement_service, mock_db):
        """Test inactivity detection with recent activity"""
        user_id = 1
        
        # Set recent activity
        engagement_service.last_activity[user_id] = datetime.utcnow() - timedelta(minutes=2)
        
        # Detect inactivity
        inactivity_detected = await engagement_service.detect_inactivity(
            db=mock_db,
            user_id=user_id
        )
        
        # Should return False for recent activity
        assert inactivity_detected is False
        
    @pytest.mark.asyncio
    async def test_detect_inactivity_old_activity(self, engagement_service, mock_db):
        """Test inactivity detection with old activity"""
        user_id = 1
        session_id = 1
        
        # Set old activity (more than 5 minutes ago)
        engagement_service.last_activity[user_id] = datetime.utcnow() - timedelta(minutes=10)
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        engagement_service._update_engagement_score = AsyncMock()
        
        # Detect inactivity
        inactivity_detected = await engagement_service.detect_inactivity(
            db=mock_db,
            user_id=user_id,
            session_id=session_id
        )
        
        # Should return True for old activity
        assert inactivity_detected is True
        
        # Verify inactivity event was logged
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_get_current_score_from_cache(self, engagement_service, mock_db):
        """Test getting current score from cache"""
        user_id = 1
        cached_score = 85.0
        
        # Set cached score
        engagement_service.score_cache[user_id] = cached_score
        
        # Get current score
        score = await engagement_service.get_current_score(mock_db, user_id)
        
        # Should return cached score
        assert score == cached_score
        
    @pytest.mark.asyncio
    async def test_get_current_score_calculate_fresh(self, engagement_service, mock_db):
        """Test getting current score when not cached"""
        user_id = 1
        calculated_score = 65.0
        
        # Mock score calculation
        engagement_service.calculate_score = AsyncMock(return_value=calculated_score)
        
        # Get current score
        score = await engagement_service.get_current_score(mock_db, user_id)
        
        # Should calculate and cache score
        assert score == calculated_score
        assert engagement_service.score_cache[user_id] == calculated_score
        
    def test_calculate_interaction_frequency(self, engagement_service):
        """Test interaction frequency calculation"""
        # Create mock engagement logs with interactive events
        logs = [
            MagicMock(event_type="click"),
            MagicMock(event_type="scroll"),
            MagicMock(event_type="focus"),
            MagicMock(event_type="page_view"),  # Not interactive
            MagicMock(event_type="button_click"),
        ]
        
        # Calculate frequency
        frequency = engagement_service._calculate_interaction_frequency(logs)
        
        # Should count only interactive events (4 out of 5)
        # Expected interactions per hour = 60, so 4/60 * 100 = 6.67%
        expected_frequency = (4 / 60) * 100
        assert abs(frequency - expected_frequency) < 0.1
        
    def test_calculate_inactivity_penalty(self, engagement_service):
        """Test inactivity penalty calculation"""
        # Create mock engagement logs with inactivity events
        logs = [
            MagicMock(
                event_type="inactivity_detected",
                event_data={"inactive_duration_seconds": 300}  # 5 minutes
            ),
            MagicMock(
                event_type="inactivity_detected", 
                event_data={"inactive_duration_seconds": 600}  # 10 minutes
            ),
            MagicMock(event_type="click"),  # Not inactivity
        ]
        
        # Calculate penalty
        penalty = engagement_service._calculate_inactivity_penalty(logs)
        
        # 5 minutes = 10 penalty points, 10 minutes = 20 penalty points
        # Total = 30 penalty points
        expected_penalty = 30.0
        assert abs(penalty - expected_penalty) < 0.1
        
    @pytest.mark.asyncio
    async def test_record_time_activity_significant_duration(self, engagement_service, mock_db):
        """Test recording time activity with significant duration triggers score update"""
        user_id = 1
        session_id = 1
        activity_type = "page_view"
        duration = 30  # Significant duration (> 10 seconds)
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        engagement_service._update_engagement_score = AsyncMock()
        
        # Record time activity
        await engagement_service.record_time_activity(
            db=mock_db,
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            duration_seconds=duration
        )
        
        # Verify score update was triggered
        engagement_service._update_engagement_score.assert_called_once()
        
    @pytest.mark.asyncio
    async def test_record_time_activity_short_duration(self, engagement_service, mock_db):
        """Test recording time activity with short duration doesn't trigger score update"""
        user_id = 1
        session_id = 1
        activity_type = "focus"
        duration = 5  # Short duration (<= 10 seconds)
        
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        engagement_service._update_engagement_score = AsyncMock()
        
        # Record time activity
        await engagement_service.record_time_activity(
            db=mock_db,
            user_id=user_id,
            session_id=session_id,
            activity_type=activity_type,
            duration_seconds=duration
        )
        
        # Verify score update was NOT triggered
        engagement_service._update_engagement_score.assert_not_called()


class TestEngagementMetrics:
    """Test suite for EngagementMetrics dataclass"""
    
    def test_engagement_metrics_creation(self):
        """Test EngagementMetrics creation with all fields"""
        metrics = EngagementMetrics(
            step_completion_rate=80.0,
            normalized_time_spent=60.0,
            interaction_frequency=40.0,
            inactivity_penalty=10.0,
            total_score=67.0
        )
        
        assert metrics.step_completion_rate == 80.0
        assert metrics.normalized_time_spent == 60.0
        assert metrics.interaction_frequency == 40.0
        assert metrics.inactivity_penalty == 10.0
        assert metrics.total_score == 67.0