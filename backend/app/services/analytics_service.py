"""
Analytics Service for Customer Onboarding Agent
Implements data aggregation, activation rate calculation, and drop-off analysis
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from sqlalchemy.orm import selectinload
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
from collections import defaultdict

from app.database import (
    User, OnboardingSession, StepCompletion, EngagementLog, 
    UserRole, SessionStatus
)
from app.schemas import (
    ActivationMetrics, DropoffData, DropoffAnalysisResponse,
    TrendDataPoint, TrendData, AnalyticsFilters
)


class AnalyticsService:
    """Service for analytics data aggregation and calculation"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_activation_rates(
        self, 
        filters: Optional[AnalyticsFilters] = None
    ) -> ActivationMetrics:
        """
        Calculate activation rates with optional filtering
        Activation = users who completed their onboarding flow
        """
        # Build base query
        query = select(User).options(selectinload(User.onboarding_sessions))
        
        # Apply role filter
        if filters and filters.role:
            query = query.where(User.role == filters.role)
        
        # Apply date filters to users created within the date range
        if filters and filters.start_date:
            query = query.where(User.created_at >= filters.start_date)
        if filters and filters.end_date:
            query = query.where(User.created_at <= filters.end_date)
        
        result = await self.db.execute(query)
        users = result.scalars().all()
        
        total_users = len(users)
        activated_users = 0
        role_breakdown = defaultdict(lambda: {"total": 0, "activated": 0})
        
        for user in users:
            role_breakdown[user.role.value]["total"] += 1
            
            # Check if user has completed any onboarding session
            completed_sessions = [
                session for session in user.onboarding_sessions 
                if session.status == SessionStatus.COMPLETED
            ]
            
            if completed_sessions:
                activated_users += 1
                role_breakdown[user.role.value]["activated"] += 1
        
        activation_rate = (activated_users / total_users * 100) if total_users > 0 else 0.0
        
        return ActivationMetrics(
            total_users=total_users,
            activated_users=activated_users,
            activation_rate=round(activation_rate, 2),
            role_breakdown=dict(role_breakdown)
        )
    
    async def get_dropoff_analysis(
        self, 
        filters: Optional[AnalyticsFilters] = None
    ) -> DropoffAnalysisResponse:
        """
        Analyze step-by-step drop-off rates
        """
        # Build query for onboarding sessions with step completions
        session_query = select(OnboardingSession).options(
            selectinload(OnboardingSession.step_completions),
            selectinload(OnboardingSession.user)
        )
        
        # Apply filters
        if filters:
            if filters.role:
                session_query = session_query.join(User).where(User.role == filters.role)
            if filters.start_date:
                session_query = session_query.where(OnboardingSession.started_at >= filters.start_date)
            if filters.end_date:
                session_query = session_query.where(OnboardingSession.started_at <= filters.end_date)
        
        result = await self.db.execute(session_query)
        sessions = result.scalars().all()
        
        if not sessions:
            return DropoffAnalysisResponse(
                overall_completion_rate=0.0,
                steps=[]
            )
        
        # Analyze step completion patterns
        step_stats = defaultdict(lambda: {
            "started": 0, 
            "completed": 0, 
            "total_time": 0, 
            "time_count": 0
        })
        
        max_steps = 0
        completed_sessions = 0
        
        for session in sessions:
            max_steps = max(max_steps, session.total_steps)
            
            if session.status == SessionStatus.COMPLETED:
                completed_sessions += 1
            
            # Track which steps were started and completed
            completed_step_numbers = set()
            for completion in session.step_completions:
                step_num = completion.step_number
                step_stats[step_num]["started"] += 1
                
                if completion.completed_at:
                    step_stats[step_num]["completed"] += 1
                    completed_step_numbers.add(step_num)
                    
                    if completion.time_spent_seconds:
                        step_stats[step_num]["total_time"] += completion.time_spent_seconds
                        step_stats[step_num]["time_count"] += 1
            
            # Mark steps as started if user progressed beyond them
            current_step = session.current_step
            for step_num in range(1, min(current_step + 1, session.total_steps + 1)):
                if step_num not in [c.step_number for c in session.step_completions]:
                    step_stats[step_num]["started"] += 1
        
        # Calculate overall completion rate
        overall_completion_rate = (completed_sessions / len(sessions) * 100) if sessions else 0.0
        
        # Build step-by-step analysis
        steps_analysis = []
        for step_num in range(1, max_steps + 1):
            stats = step_stats[step_num]
            started_count = stats["started"]
            completed_count = stats["completed"]
            
            completion_rate = (completed_count / started_count * 100) if started_count > 0 else 0.0
            
            avg_time = None
            if stats["time_count"] > 0:
                avg_time = stats["total_time"] / stats["time_count"]
            
            steps_analysis.append(DropoffData(
                step_number=step_num,
                step_title=f"Step {step_num}",
                started_count=started_count,
                completed_count=completed_count,
                completion_rate=round(completion_rate, 2),
                average_time_spent=round(avg_time, 2) if avg_time else None
            ))
        
        return DropoffAnalysisResponse(
            overall_completion_rate=round(overall_completion_rate, 2),
            steps=steps_analysis
        )
    
    async def get_engagement_trends(
        self, 
        filters: Optional[AnalyticsFilters] = None,
        days_back: int = 30
    ) -> TrendData:
        """
        Get engagement score trends over time
        """
        end_date = filters.end_date if filters and filters.end_date else datetime.utcnow()
        start_date = filters.start_date if filters and filters.start_date else end_date - timedelta(days=days_back)
        
        # Build query for engagement logs
        query = select(EngagementLog).where(
            and_(
                EngagementLog.timestamp >= start_date,
                EngagementLog.timestamp <= end_date,
                EngagementLog.engagement_score.isnot(None)
            )
        )
        
        # Apply role filter
        if filters and filters.role:
            query = query.join(User).where(User.role == filters.role)
        
        # Apply user filter
        if filters and filters.user_id:
            query = query.where(EngagementLog.user_id == filters.user_id)
        
        result = await self.db.execute(query)
        engagement_logs = result.scalars().all()
        
        # Group by date and calculate daily averages
        daily_scores = defaultdict(list)
        for log in engagement_logs:
            date_key = log.timestamp.date()
            daily_scores[date_key].append(log.engagement_score)
        
        # Calculate trend data points
        data_points = []
        for date, scores in sorted(daily_scores.items()):
            avg_score = sum(scores) / len(scores)
            data_points.append(TrendDataPoint(
                date=datetime.combine(date, datetime.min.time()),
                value=round(avg_score, 2),
                count=len(scores)
            ))
        
        # Determine trend direction
        trend_direction = "stable"
        if len(data_points) >= 2:
            first_half = data_points[:len(data_points)//2]
            second_half = data_points[len(data_points)//2:]
            
            first_avg = sum(dp.value for dp in first_half) / len(first_half)
            second_avg = sum(dp.value for dp in second_half) / len(second_half)
            
            if second_avg > first_avg + 5:
                trend_direction = "up"
            elif second_avg < first_avg - 5:
                trend_direction = "down"
        
        return TrendData(
            metric_name="engagement_score",
            data_points=data_points,
            trend_direction=trend_direction
        )
    
    async def get_real_time_metrics(self) -> Dict[str, Any]:
        """
        Get real-time system metrics
        """
        # Active sessions count
        active_sessions_query = select(func.count(OnboardingSession.id)).where(
            OnboardingSession.status == SessionStatus.ACTIVE
        )
        active_sessions_result = await self.db.execute(active_sessions_query)
        active_sessions = active_sessions_result.scalar() or 0
        
        # Total sessions count
        total_sessions_query = select(func.count(OnboardingSession.id))
        total_sessions_result = await self.db.execute(total_sessions_query)
        total_sessions = total_sessions_result.scalar() or 0
        
        # Recent interventions (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_interventions_query = select(func.count()).select_from(
            select(EngagementLog.user_id).where(
                and_(
                    EngagementLog.timestamp >= yesterday,
                    EngagementLog.event_type == "intervention_triggered"
                )
            ).distinct().subquery()
        )
        recent_interventions_result = await self.db.execute(recent_interventions_query)
        recent_interventions = recent_interventions_result.scalar() or 0
        
        # Average engagement score (last 24 hours)
        avg_engagement_query = select(func.avg(EngagementLog.engagement_score)).where(
            and_(
                EngagementLog.timestamp >= yesterday,
                EngagementLog.engagement_score.isnot(None)
            )
        )
        avg_engagement_result = await self.db.execute(avg_engagement_query)
        avg_engagement = avg_engagement_result.scalar() or 0.0
        
        return {
            "active_sessions": active_sessions,
            "total_sessions": total_sessions,
            "recent_interventions": recent_interventions,
            "average_engagement_24h": round(float(avg_engagement), 2),
            "last_updated": datetime.utcnow()
        }
    
    async def export_analytics_data(
        self, 
        filters: Optional[AnalyticsFilters] = None,
        export_format: str = "json"
    ) -> Dict[str, Any]:
        """
        Export comprehensive analytics data
        """
        activation_metrics = await self.calculate_activation_rates(filters)
        dropoff_analysis = await self.get_dropoff_analysis(filters)
        engagement_trends = await self.get_engagement_trends(filters)
        real_time_metrics = await self.get_real_time_metrics()
        
        export_data = {
            "export_timestamp": datetime.utcnow().isoformat(),
            "filters_applied": filters.dict() if filters else None,
            "activation_metrics": activation_metrics.dict(),
            "dropoff_analysis": dropoff_analysis.dict(),
            "engagement_trends": engagement_trends.dict(),
            "real_time_metrics": real_time_metrics
        }
        
        return export_data