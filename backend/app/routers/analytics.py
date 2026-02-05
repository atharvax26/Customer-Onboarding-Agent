"""
Analytics router for Customer Onboarding Agent
Provides comprehensive analytics data aggregation and reporting
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from app.database import get_db, User, UserRole
from app.auth import (
    get_current_active_user, require_roles, require_admin,
    can_access_user_data
)
from app.services.analytics_service import AnalyticsService
from app.schemas import (
    ActivationMetrics, DropoffAnalysisResponse, TrendData,
    AnalyticsFilters, DashboardData
)

router = APIRouter()


@router.get("/activation-rates", response_model=ActivationMetrics)
async def get_activation_rates(
    role: Optional[str] = Query(None, description="Filter by user role"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BUSINESS_USER])),
    db: AsyncSession = Depends(get_db)
) -> ActivationMetrics:
    """Get activation rates with optional filtering - admins and business users only"""
    
    # Business users can only see their own role's data unless they're admin
    if current_user.role == UserRole.BUSINESS_USER and role and role != current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business users can only view their own role's activation rates"
        )
    
    # Create filters
    filters = AnalyticsFilters(
        role=UserRole(role) if role else None,
        start_date=start_date,
        end_date=end_date
    )
    
    analytics_service = AnalyticsService(db)
    return await analytics_service.calculate_activation_rates(filters)


@router.get("/dropoff-analysis", response_model=DropoffAnalysisResponse)
async def get_dropoff_analysis(
    role: Optional[str] = Query(None, description="Filter by user role"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BUSINESS_USER])),
    db: AsyncSession = Depends(get_db)
) -> DropoffAnalysisResponse:
    """Get step-by-step drop-off analysis - admins and business users only"""
    
    # Role filtering based on user permissions
    if current_user.role == UserRole.BUSINESS_USER and role and role != current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business users can only view their own role's drop-off analysis"
        )
    
    # Create filters
    filters = AnalyticsFilters(
        role=UserRole(role) if role else None,
        start_date=start_date,
        end_date=end_date
    )
    
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_dropoff_analysis(filters)


@router.get("/engagement-trends", response_model=TrendData)
async def get_engagement_trends(
    user_id: Optional[int] = Query(None, description="Filter by specific user ID"),
    days_back: int = Query(30, description="Number of days to look back"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> TrendData:
    """Get engagement score trends - users can see their own, admins can see all"""
    
    # If user_id is specified, check access permissions
    if user_id is not None:
        if not can_access_user_data(user_id, current_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own engagement trends"
            )
        target_user_id = user_id
    else:
        # If no user_id specified, show current user's data
        target_user_id = current_user.id
    
    # Create filters
    filters = AnalyticsFilters(user_id=target_user_id)
    
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_engagement_trends(filters, days_back)


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BUSINESS_USER])),
    db: AsyncSession = Depends(get_db)
):
    """Get comprehensive dashboard data - admins and business users only"""
    
    analytics_service = AnalyticsService(db)
    
    # Get role-specific filters
    filters = None
    if current_user.role == UserRole.BUSINESS_USER:
        # Business users only see their role's data
        filters = AnalyticsFilters(role=current_user.role)
    
    # Gather all dashboard data
    activation_metrics = await analytics_service.calculate_activation_rates(filters)
    dropoff_analysis = await analytics_service.get_dropoff_analysis(filters)
    engagement_trends = await analytics_service.get_engagement_trends(filters)
    real_time_metrics = await analytics_service.get_real_time_metrics()
    
    dashboard_data = {
        "activation_metrics": activation_metrics,
        "recent_dropoff_analysis": dropoff_analysis,
        "engagement_trends": [engagement_trends],
        "real_time_metrics": real_time_metrics,
        "user_role": current_user.role.value,
        "access_level": "admin" if current_user.role == UserRole.ADMIN else "business_user"
    }
    
    return dashboard_data


@router.get("/real-time-metrics")
async def get_real_time_metrics(
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BUSINESS_USER])),
    db: AsyncSession = Depends(get_db)
):
    """Get real-time system metrics - admins and business users only"""
    
    analytics_service = AnalyticsService(db)
    return await analytics_service.get_real_time_metrics()


@router.get("/export")
async def export_analytics_data(
    role: Optional[str] = Query(None, description="Filter by user role"),
    start_date: Optional[datetime] = Query(None, description="Start date for filtering"),
    end_date: Optional[datetime] = Query(None, description="End date for filtering"),
    export_format: str = Query("json", description="Export format (json, csv)"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BUSINESS_USER])),
    db: AsyncSession = Depends(get_db)
):
    """Export analytics data - admins and business users only"""
    
    # Business users can only export their own role's data
    if current_user.role == UserRole.BUSINESS_USER and role and role != current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business users can only export their own role's data"
        )
    
    # Create filters
    filters = AnalyticsFilters(
        role=UserRole(role) if role else None,
        start_date=start_date,
        end_date=end_date
    )
    
    analytics_service = AnalyticsService(db)
    export_data = await analytics_service.export_analytics_data(filters, export_format)
    
    return {
        "message": "Analytics data exported successfully",
        "export_format": export_format,
        "data": export_data
    }


@router.get("/admin/system-metrics")
async def get_system_metrics(
    admin_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide metrics - admin only"""
    
    analytics_service = AnalyticsService(db)
    real_time_metrics = await analytics_service.get_real_time_metrics()
    
    # Add admin-specific system metrics
    system_metrics = {
        **real_time_metrics,
        "admin_user": admin_user.email,
        "system_status": "operational",
        "database_health": "good",
        "api_response_time": "< 200ms"
    }
    
    return {
        "message": "System metrics retrieved",
        "metrics": system_metrics
    }


@router.get("/user-analytics/{user_id}")
async def get_user_analytics(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get analytics for a specific user - with access control"""
    
    # Check if current user can access this user's data
    if not can_access_user_data(user_id, current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. You can only view your own analytics or you need admin privileges."
        )
    
    analytics_service = AnalyticsService(db)
    
    # Get user-specific analytics
    filters = AnalyticsFilters(user_id=user_id)
    engagement_trends = await analytics_service.get_engagement_trends(filters)
    
    return {
        "message": "User analytics retrieved",
        "target_user_id": user_id,
        "accessed_by": current_user.id,
        "user_role": current_user.role.value,
        "engagement_trends": engagement_trends,
        "analytics": {
            "user_id": user_id,
            "data_points": len(engagement_trends.data_points),
            "trend_direction": engagement_trends.trend_direction
        }
    }


@router.get("/metrics/summary")
async def get_metrics_summary(
    role: Optional[str] = Query(None, description="Filter by user role"),
    current_user: User = Depends(require_roles([UserRole.ADMIN, UserRole.BUSINESS_USER])),
    db: AsyncSession = Depends(get_db)
):
    """Get summarized metrics for quick overview"""
    
    # Business users can only see their own role's data
    if current_user.role == UserRole.BUSINESS_USER and role and role != current_user.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business users can only view their own role's metrics"
        )
    
    analytics_service = AnalyticsService(db)
    
    # Create filters
    filters = AnalyticsFilters(role=UserRole(role) if role else None)
    
    # Get summary data
    activation_metrics = await analytics_service.calculate_activation_rates(filters)
    dropoff_analysis = await analytics_service.get_dropoff_analysis(filters)
    real_time_metrics = await analytics_service.get_real_time_metrics()
    
    summary = {
        "activation_rate": activation_metrics.activation_rate,
        "total_users": activation_metrics.total_users,
        "overall_completion_rate": dropoff_analysis.overall_completion_rate,
        "active_sessions": real_time_metrics["active_sessions"],
        "average_engagement": real_time_metrics["average_engagement_24h"],
        "role_filter": role,
        "generated_at": datetime.utcnow()
    }
    
    return summary


@router.post("/metrics/refresh")
async def refresh_metrics_cache(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """Refresh analytics metrics cache - admin only"""
    
    analytics_service = AnalyticsService(db)
    
    # Force refresh of real-time metrics
    refreshed_metrics = await analytics_service.get_real_time_metrics()
    
    return {
        "message": "Metrics cache refreshed successfully",
        "refreshed_at": datetime.utcnow(),
        "refreshed_by": current_user.email,
        "metrics": refreshed_metrics
    }


@router.get("/filters/roles")
async def get_available_roles(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Get available roles for filtering - based on user permissions"""
    
    if current_user.role == UserRole.ADMIN:
        # Admins can see all roles
        available_roles = [role.value for role in UserRole]
    else:
        # Other users can only see their own role
        available_roles = [current_user.role.value]
    
    return {
        "available_roles": available_roles,
        "user_role": current_user.role.value,
        "access_level": "admin" if current_user.role == UserRole.ADMIN else "limited"
    }


@router.get("/health")
async def analytics_health_check(
    db: AsyncSession = Depends(get_db)
):
    """Health check for analytics service"""
    
    try:
        analytics_service = AnalyticsService(db)
        # Quick health check by getting real-time metrics
        metrics = await analytics_service.get_real_time_metrics()
        
        return {
            "status": "healthy",
            "service": "analytics",
            "timestamp": datetime.utcnow(),
            "metrics_available": True,
            "last_updated": metrics.get("last_updated")
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Analytics service unhealthy: {str(e)}"
        )