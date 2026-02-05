"""
Tests for Analytics Service
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

from app.services.analytics_service import AnalyticsService
from app.schemas import AnalyticsFilters, UserRole
from app.database import User, OnboardingSession, SessionStatus, EngagementLog


class TestAnalyticsService:
    """Test analytics service functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return AsyncMock()
    
    @pytest.fixture
    def analytics_service(self, mock_db):
        """Analytics service instance with mocked database"""
        return AnalyticsService(mock_db)
    
    def test_analytics_service_initialization(self, mock_db):
        """Test analytics service can be initialized"""
        service = AnalyticsService(mock_db)
        assert service.db == mock_db
    
    @pytest.mark.asyncio
    async def test_calculate_activation_rates_no_filters(self, analytics_service, mock_db):
        """Test activation rate calculation without filters"""
        # Mock users with onboarding sessions
        mock_users = [
            MagicMock(
                role=UserRole.DEVELOPER,
                onboarding_sessions=[
                    MagicMock(status=SessionStatus.COMPLETED)
                ]
            ),
            MagicMock(
                role=UserRole.BUSINESS_USER,
                onboarding_sessions=[
                    MagicMock(status=SessionStatus.ACTIVE)
                ]
            )
        ]
        
        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result
        
        # Test activation rate calculation
        result = await analytics_service.calculate_activation_rates()
        
        assert result.total_users == 2
        assert result.activated_users == 1
        assert result.activation_rate == 50.0
        assert "Developer" in result.role_breakdown
        assert "Business_User" in result.role_breakdown
    
    @pytest.mark.asyncio
    async def test_calculate_activation_rates_with_role_filter(self, analytics_service, mock_db):
        """Test activation rate calculation with role filter"""
        # Mock users with specific role
        mock_users = [
            MagicMock(
                role=UserRole.DEVELOPER,
                onboarding_sessions=[
                    MagicMock(status=SessionStatus.COMPLETED)
                ]
            )
        ]
        
        # Mock database query result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_users
        mock_db.execute.return_value = mock_result
        
        # Test with role filter
        filters = AnalyticsFilters(role=UserRole.DEVELOPER)
        result = await analytics_service.calculate_activation_rates(filters)
        
        assert result.total_users == 1
        assert result.activated_users == 1
        assert result.activation_rate == 100.0
    
    @pytest.mark.asyncio
    async def test_get_dropoff_analysis_empty_sessions(self, analytics_service, mock_db):
        """Test dropoff analysis with no sessions"""
        # Mock empty result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        result = await analytics_service.get_dropoff_analysis()
        
        assert result.overall_completion_rate == 0.0
        assert result.steps == []
    
    @pytest.mark.asyncio
    async def test_get_real_time_metrics(self, analytics_service, mock_db):
        """Test real-time metrics calculation"""
        # Mock database query results - need to mock the execute calls properly
        mock_results = [
            MagicMock(scalar=MagicMock(return_value=10)),  # active_sessions
            MagicMock(scalar=MagicMock(return_value=50)),  # total_sessions  
            MagicMock(scalar=MagicMock(return_value=5)),   # recent_interventions
            MagicMock(scalar=MagicMock(return_value=75.5)) # avg_engagement
        ]
        mock_db.execute.side_effect = mock_results
        
        result = await analytics_service.get_real_time_metrics()
        
        assert result["active_sessions"] == 10
        assert result["total_sessions"] == 50
        assert result["recent_interventions"] == 5
        assert result["average_engagement_24h"] == 75.5
        assert "last_updated" in result
        assert isinstance(result["last_updated"], datetime)
    
    @pytest.mark.asyncio
    async def test_export_analytics_data(self, analytics_service, mock_db):
        """Test analytics data export"""
        # Mock all the service methods
        analytics_service.calculate_activation_rates = AsyncMock(return_value=MagicMock(dict=lambda: {"test": "data"}))
        analytics_service.get_dropoff_analysis = AsyncMock(return_value=MagicMock(dict=lambda: {"test": "data"}))
        analytics_service.get_engagement_trends = AsyncMock(return_value=MagicMock(dict=lambda: {"test": "data"}))
        analytics_service.get_real_time_metrics = AsyncMock(return_value={"test": "data"})
        
        result = await analytics_service.export_analytics_data()
        
        assert "export_timestamp" in result
        assert "activation_metrics" in result
        assert "dropoff_analysis" in result
        assert "engagement_trends" in result
        assert "real_time_metrics" in result
        assert result["filters_applied"] is None


class TestAnalyticsFilters:
    """Test analytics filters functionality"""
    
    def test_analytics_filters_creation(self):
        """Test creating analytics filters"""
        filters = AnalyticsFilters(
            role=UserRole.DEVELOPER,
            start_date=datetime.now(),
            end_date=datetime.now()
        )
        
        assert filters.role == UserRole.DEVELOPER
        assert filters.start_date is not None
        assert filters.end_date is not None
    
    def test_analytics_filters_optional_fields(self):
        """Test analytics filters with optional fields"""
        filters = AnalyticsFilters()
        
        assert filters.role is None
        assert filters.start_date is None
        assert filters.end_date is None
        assert filters.user_id is None