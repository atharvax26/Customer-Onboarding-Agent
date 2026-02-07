"""
System monitoring and health router for Customer Onboarding Agent
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_active_user, User
from app.health_monitor import health_monitor
from app.services.system_monitor import system_monitor, AlertLevel
from app.services.background_tasks import get_background_task_status
from app.logging_config import get_context_logger
from app.exceptions import AuthorizationError, SystemHealthError


logger = get_context_logger(__name__, component="system_router")
router = APIRouter()


@router.get("/health")
async def get_system_health():
    """Get comprehensive system health status"""
    try:
        health_status = await health_monitor.check_system_health()
        return health_status
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Health check failed"
        )


@router.get("/health/{component}")
async def get_component_health(component: str):
    """Get health status of specific component"""
    try:
        component_health = await health_monitor.check_component_health(component)
        return component_health.to_dict()
    except SystemHealthError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Component health check failed for {component}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Component health check failed"
        )


@router.get("/health-history")
async def get_health_history(
    limit: int = Query(default=10, ge=1, le=100),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent health check history (Admin only)"""
    if current_user.role.value != "Admin":
        raise AuthorizationError("Admin access required")
    
    try:
        history = health_monitor.get_health_history(limit)
        return {"history": history}
    except Exception as e:
        logger.error(f"Failed to retrieve health history: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve health history"
        )


@router.get("/alerts")
async def get_system_alerts(
    level: Optional[AlertLevel] = Query(default=None),
    active_only: bool = Query(default=True),
    limit: int = Query(default=50, ge=1, le=200),
    current_user: User = Depends(get_current_active_user)
):
    """Get system alerts (Admin only)"""
    if current_user.role.value != "Admin":
        raise AuthorizationError("Admin access required")
    
    try:
        if level:
            alerts = system_monitor.get_alerts_by_level(level)
        else:
            alerts = system_monitor.get_active_alerts() if active_only else system_monitor.alerts
        
        # Convert alerts to dict format and limit results
        alert_dicts = []
        for alert in alerts[-limit:]:
            alert_dict = {
                "id": alert.id,
                "level": alert.level.value,
                "component": alert.component,
                "message": alert.message,
                "details": alert.details,
                "timestamp": alert.timestamp.isoformat() + "Z",
                "resolved": alert.resolved
            }
            if alert.resolved_at:
                alert_dict["resolved_at"] = alert.resolved_at.isoformat() + "Z"
            alert_dicts.append(alert_dict)
        
        return {
            "alerts": alert_dicts,
            "total_count": len(alerts),
            "active_count": len(system_monitor.get_active_alerts())
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve alerts: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system alerts"
        )


@router.post("/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    current_user: User = Depends(get_current_active_user)
):
    """Resolve a system alert (Admin only)"""
    if current_user.role.value != "Admin":
        raise AuthorizationError("Admin access required")
    
    try:
        resolved = await system_monitor.resolve_alert(alert_id)
        if not resolved:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found or already resolved"
            )
        
        return {"message": "Alert resolved successfully", "alert_id": alert_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resolve alert {alert_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )


@router.get("/metrics")
async def get_system_metrics(
    limit: int = Query(default=100, ge=1, le=1000),
    current_user: User = Depends(get_current_active_user)
):
    """Get recent system metrics (Admin only)"""
    if current_user.role.value != "Admin":
        raise AuthorizationError("Admin access required")
    
    try:
        metrics = system_monitor.get_recent_metrics(limit)
        return {
            "metrics": metrics,
            "count": len(metrics)
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve metrics: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )


@router.get("/status")
async def get_system_status(
    current_user: User = Depends(get_current_active_user)
):
    """Get overall system status summary (Admin only)"""
    if current_user.role.value != "Admin":
        raise AuthorizationError("Admin access required")
    
    try:
        # Get system monitor status
        monitor_status = system_monitor.get_system_status()
        
        # Get background task status
        task_status = get_background_task_status()
        
        # Get recent health check
        health_status = await health_monitor.check_system_health()
        
        return {
            "system_monitor": monitor_status,
            "background_tasks": task_status,
            "health_check": {
                "status": health_status.get("status"),
                "timestamp": health_status.get("timestamp"),
                "check_duration": health_status.get("check_duration"),
                "component_count": len(health_status.get("components", {}))
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve system status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.post("/monitoring/start")
async def start_system_monitoring(
    current_user: User = Depends(get_current_active_user)
):
    """Start system monitoring (Admin only)"""
    if current_user.role.value != "Admin":
        raise AuthorizationError("Admin access required")
    
    try:
        await system_monitor.start_monitoring()
        return {"message": "System monitoring started successfully"}
        
    except Exception as e:
        logger.error(f"Failed to start system monitoring: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start system monitoring"
        )


@router.post("/monitoring/stop")
async def stop_system_monitoring(
    current_user: User = Depends(get_current_active_user)
):
    """Stop system monitoring (Admin only)"""
    if current_user.role.value != "Admin":
        raise AuthorizationError("Admin access required")
    
    try:
        await system_monitor.stop_monitoring()
        return {"message": "System monitoring stopped successfully"}
        
    except Exception as e:
        logger.error(f"Failed to stop system monitoring: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop system monitoring"
        )