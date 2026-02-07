"""
System monitoring service for Customer Onboarding Agent
Provides real-time system metrics and alerting capabilities
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json

from app.logging_config import get_context_logger
from app.health_monitor import health_monitor, HealthStatus
from app.exceptions import SystemHealthError


logger = get_context_logger(__name__, component="system_monitor")


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class SystemAlert:
    """System alert data structure"""
    id: str
    level: AlertLevel
    component: str
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SystemMonitor:
    """System monitoring and alerting service"""
    
    def __init__(self):
        self.is_monitoring = False
        self.monitor_task: Optional[asyncio.Task] = None
        self.alerts: List[SystemAlert] = []
        self.alert_handlers: List[Callable[[SystemAlert], None]] = []
        self.metrics_history: List[Dict[str, Any]] = []
        self._start_time = time.time()
        self._error_counts = {}  # Track error rates by component
        self._last_error_reset = time.time()
        
        # Configuration
        self.check_interval = 30  # seconds
        self.max_alerts = 100
        self.max_metrics_history = 1000
        self.error_rate_window = 300  # 5 minutes for error rate calculation
        
        # Thresholds
        self.thresholds = {
            "response_time": 2.0,  # seconds
            "error_rate": 0.05,    # 5%
            "memory_usage": 85,    # percent
            "disk_usage": 90,      # percent
            "unhealthy_components": 1,  # count
            "cpu_usage": 90,       # percent
            "consecutive_failures": 3  # consecutive health check failures
        }
        
        # Enhanced monitoring state
        self._consecutive_failures = {}
        self._last_successful_check = {}
        
        # Add default alert handlers
        self.add_alert_handler(self._default_alert_handler)
    
    async def start_monitoring(self) -> None:
        """Start system monitoring"""
        if self.is_monitoring:
            logger.warning("System monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitoring_loop())
        
        logger.info("System monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop system monitoring"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("System monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop with enhanced error tracking"""
        logger.info("Starting enhanced system monitoring loop")
        
        while self.is_monitoring:
            try:
                await self._perform_health_check()
                await self._collect_metrics()
                await self._check_thresholds()
                await self._check_error_rates()
                await self._cleanup_old_data()
                
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    "Error in monitoring loop",
                    extra={"error": str(e)},
                    exc_info=True
                )
                
                # Track monitoring loop errors
                await self._record_error("monitoring_loop", str(e))
                await asyncio.sleep(self.check_interval)
    
    async def _perform_health_check(self) -> None:
        """Perform system health check"""
        try:
            health_status = await health_monitor.check_system_health()
            
            # Check for unhealthy components
            unhealthy_components = []
            for component_name, component_data in health_status.get("components", {}).items():
                if component_data.get("status") == "unhealthy":
                    unhealthy_components.append({
                        "name": component_name,
                        "error": component_data.get("error"),
                        "response_time": component_data.get("response_time")
                    })
            
            # Generate alerts for unhealthy components
            if unhealthy_components:
                await self._create_alert(
                    level=AlertLevel.ERROR,
                    component="health_check",
                    message=f"{len(unhealthy_components)} component(s) are unhealthy",
                    details={
                        "unhealthy_components": unhealthy_components,
                        "overall_status": health_status.get("status")
                    }
                )
            
            # Check overall system status
            overall_status = health_status.get("status")
            if overall_status == "unhealthy":
                await self._create_alert(
                    level=AlertLevel.CRITICAL,
                    component="system",
                    message="System is unhealthy",
                    details=health_status
                )
            elif overall_status == "degraded":
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    component="system",
                    message="System performance is degraded",
                    details=health_status
                )
            
        except Exception as e:
            logger.error(
                "Failed to perform health check",
                extra={"error": str(e)},
                exc_info=True
            )
    
    async def _collect_metrics(self) -> None:
        """Collect system metrics"""
        try:
            metrics = {
                "timestamp": datetime.utcnow().isoformat(),
                "system": await self._get_system_metrics(),
                "application": await self._get_application_metrics()
            }
            
            # Store metrics
            self.metrics_history.append(metrics)
            
            # Limit history size
            if len(self.metrics_history) > self.max_metrics_history:
                self.metrics_history = self.metrics_history[-self.max_metrics_history:]
            
        except Exception as e:
            logger.error(
                "Failed to collect metrics",
                extra={"error": str(e)},
                exc_info=True
            )
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics"""
        metrics = {}
        
        try:
            import psutil
            
            # CPU usage
            metrics["cpu_percent"] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            metrics["memory"] = {
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            }
            
            # Disk usage
            disk = psutil.disk_usage('.')
            metrics["disk"] = {
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total) * 100
            }
            
            # Network I/O
            network = psutil.net_io_counters()
            metrics["network"] = {
                "bytes_sent": network.bytes_sent,
                "bytes_recv": network.bytes_recv,
                "packets_sent": network.packets_sent,
                "packets_recv": network.packets_recv
            }
            
        except ImportError:
            metrics["note"] = "psutil not available for system metrics"
        except Exception as e:
            metrics["error"] = str(e)
        
        return metrics
    
    async def _get_application_metrics(self) -> Dict[str, Any]:
        """Get application-level metrics"""
        metrics = {
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "total_alerts": len(self.alerts),
            "monitoring_uptime": time.time() - getattr(self, '_start_time', time.time())
        }
        
        # Add health check metrics
        try:
            health_status = await health_monitor.check_system_health()
            metrics["health_check_duration"] = health_status.get("check_duration", 0)
            metrics["healthy_components"] = len([
                c for c in health_status.get("components", {}).values()
                if c.get("status") == "healthy"
            ])
            metrics["total_components"] = len(health_status.get("components", {}))
        except Exception as e:
            metrics["health_check_error"] = str(e)
        
        return metrics
    
    async def _check_thresholds(self) -> None:
        """Check metrics against thresholds and generate alerts"""
        if not self.metrics_history:
            return
        
        latest_metrics = self.metrics_history[-1]
        system_metrics = latest_metrics.get("system", {})
        app_metrics = latest_metrics.get("application", {})
        
        # Check memory usage
        memory_percent = system_metrics.get("memory", {}).get("percent", 0)
        if memory_percent > self.thresholds["memory_usage"]:
            await self._create_alert(
                level=AlertLevel.WARNING,
                component="memory",
                message=f"High memory usage: {memory_percent:.1f}%",
                details={"memory_percent": memory_percent, "threshold": self.thresholds["memory_usage"]}
            )
        
        # Check disk usage
        disk_percent = system_metrics.get("disk", {}).get("percent", 0)
        if disk_percent > self.thresholds["disk_usage"]:
            await self._create_alert(
                level=AlertLevel.ERROR,
                component="disk",
                message=f"High disk usage: {disk_percent:.1f}%",
                details={"disk_percent": disk_percent, "threshold": self.thresholds["disk_usage"]}
            )
        
        # Check health check duration
        health_duration = app_metrics.get("health_check_duration", 0)
        if health_duration > self.thresholds["response_time"]:
            await self._create_alert(
                level=AlertLevel.WARNING,
                component="health_check",
                message=f"Slow health check: {health_duration:.2f}s",
                details={"duration": health_duration, "threshold": self.thresholds["response_time"]}
            )
    
    async def _create_alert(
        self,
        level: AlertLevel,
        component: str,
        message: str,
        details: Dict[str, Any]
    ) -> SystemAlert:
        """Create and process a system alert"""
        
        # Check for duplicate alerts (same component and message within last 5 minutes)
        cutoff_time = datetime.utcnow() - timedelta(minutes=5)
        duplicate_alert = next((
            alert for alert in self.alerts
            if (alert.component == component and 
                alert.message == message and 
                alert.timestamp > cutoff_time and 
                not alert.resolved)
        ), None)
        
        if duplicate_alert:
            logger.debug(f"Skipping duplicate alert: {message}")
            return duplicate_alert
        
        # Create new alert
        alert = SystemAlert(
            id=f"alert_{int(time.time())}_{hash(f'{component}_{message}') % 10000}",
            level=level,
            component=component,
            message=message,
            details=details,
            timestamp=datetime.utcnow()
        )
        
        # Store alert
        self.alerts.append(alert)
        
        # Limit alerts history
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # Log alert
        log_level = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }.get(level, logger.info)
        
        log_level(
            f"System alert: {message}",
            extra={
                "alert_id": alert.id,
                "alert_level": level.value,
                "component": component,
                "details": details
            }
        )
        
        # Notify alert handlers
        for handler in self.alert_handlers:
            try:
                await self._call_alert_handler(handler, alert)
            except Exception as e:
                logger.error(
                    f"Alert handler failed: {e}",
                    extra={"alert_id": alert.id, "handler": str(handler)},
                    exc_info=True
                )
        
        return alert
    
    async def _call_alert_handler(self, handler: Callable, alert: SystemAlert) -> None:
        """Call alert handler (sync or async)"""
        if asyncio.iscoroutinefunction(handler):
            await handler(alert)
        else:
            handler(alert)
    
    async def _cleanup_old_data(self) -> None:
        """Clean up old alerts and metrics"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Remove old resolved alerts
        self.alerts = [
            alert for alert in self.alerts
            if not alert.resolved or alert.timestamp > cutoff_time
        ]
        
        # Keep only recent metrics (last 24 hours)
        cutoff_timestamp = cutoff_time.isoformat()
        self.metrics_history = [
            metrics for metrics in self.metrics_history
            if metrics.get("timestamp", "") > cutoff_timestamp
        ]
    
    def add_alert_handler(self, handler: Callable[[SystemAlert], None]) -> None:
        """Add alert handler"""
        self.alert_handlers.append(handler)
        logger.info(f"Added alert handler: {handler.__name__}")
    
    def remove_alert_handler(self, handler: Callable[[SystemAlert], None]) -> None:
        """Remove alert handler"""
        if handler in self.alert_handlers:
            self.alert_handlers.remove(handler)
            logger.info(f"Removed alert handler: {handler.__name__}")
    
    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        alert = next((a for a in self.alerts if a.id == alert_id), None)
        if alert and not alert.resolved:
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()
            
            logger.info(
                f"Alert resolved: {alert.message}",
                extra={"alert_id": alert_id, "component": alert.component}
            )
            return True
        
        return False
    
    def get_active_alerts(self) -> List[SystemAlert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.alerts if not alert.resolved]
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[SystemAlert]:
        """Get alerts by severity level"""
        return [alert for alert in self.alerts if alert.level == level]
    
    def get_recent_metrics(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent system metrics"""
        return self.metrics_history[-limit:]
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get current system status summary"""
        active_alerts = self.get_active_alerts()
        
        return {
            "monitoring_active": self.is_monitoring,
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == AlertLevel.CRITICAL]),
            "error_alerts": len([a for a in active_alerts if a.level == AlertLevel.ERROR]),
            "warning_alerts": len([a for a in active_alerts if a.level == AlertLevel.WARNING]),
            "last_check": self.metrics_history[-1]["timestamp"] if self.metrics_history else None,
            "uptime": time.time() - getattr(self, '_start_time', time.time())
        }
    
    def _default_alert_handler(self, alert: SystemAlert) -> None:
        """Default alert handler that logs alerts and performs basic actions"""
        
        # Log based on alert level
        log_methods = {
            AlertLevel.INFO: logger.info,
            AlertLevel.WARNING: logger.warning,
            AlertLevel.ERROR: logger.error,
            AlertLevel.CRITICAL: logger.critical
        }
        
        log_method = log_methods.get(alert.level, logger.info)
        log_method(
            f"System Alert: {alert.message}",
            extra={
                "alert_id": alert.id,
                "component": alert.component,
                "level": alert.level.value,
                "details": alert.details
            }
        )
        
        # For critical alerts, attempt immediate notification
        if alert.level == AlertLevel.CRITICAL:
            asyncio.create_task(self._handle_critical_alert(alert))
    
    async def _handle_critical_alert(self, alert: SystemAlert) -> None:
        """Handle critical alerts with immediate actions"""
        try:
            # Log critical alert with maximum detail
            logger.critical(
                f"CRITICAL SYSTEM ALERT: {alert.message}",
                extra={
                    "alert_id": alert.id,
                    "component": alert.component,
                    "details": alert.details,
                    "timestamp": alert.timestamp.isoformat(),
                    "requires_immediate_attention": True,
                    "system_status": self.get_system_status()
                }
            )
            
            # Attempt to send notification (email, Slack, etc.)
            await self._send_critical_alert_notification(alert)
            
            # If it's a system-wide issue, consider emergency actions
            if alert.component == "system" and "unhealthy" in alert.message.lower():
                await self._initiate_emergency_procedures(alert)
                
        except Exception as e:
            logger.error(f"Failed to handle critical alert {alert.id}: {e}")
    
    async def _send_critical_alert_notification(self, alert: SystemAlert) -> None:
        """Send critical alert notifications to external systems"""
        try:
            # This would integrate with notification services
            # For now, we'll log the notification attempt
            logger.info(
                f"Sending critical alert notification for {alert.id}",
                extra={
                    "alert_id": alert.id,
                    "notification_channels": ["email", "slack", "sms"],
                    "alert_details": {
                        "component": alert.component,
                        "message": alert.message,
                        "level": alert.level.value,
                        "timestamp": alert.timestamp.isoformat()
                    }
                }
            )
            
            # TODO: Implement actual notification sending
            # - Email notifications
            # - Slack/Teams integration
            # - SMS alerts for critical issues
            # - PagerDuty integration
            
        except Exception as e:
            logger.error(f"Failed to send critical alert notification: {e}")
    
    async def _initiate_emergency_procedures(self, alert: SystemAlert) -> None:
        """Initiate emergency procedures for system-wide critical issues"""
        try:
            logger.critical(
                "Initiating emergency procedures",
                extra={
                    "alert_id": alert.id,
                    "trigger": alert.message,
                    "procedures": [
                        "health_check_intensification",
                        "resource_monitoring_increase",
                        "error_rate_tracking"
                    ]
                }
            )
            
            # Increase monitoring frequency
            original_interval = self.check_interval
            self.check_interval = min(10, original_interval)  # Check every 10 seconds
            
            # Schedule return to normal monitoring after 10 minutes
            asyncio.create_task(self._restore_normal_monitoring(original_interval, 600))
            
        except Exception as e:
            logger.error(f"Failed to initiate emergency procedures: {e}")
    
    async def _restore_normal_monitoring(self, original_interval: int, delay: int) -> None:
        """Restore normal monitoring interval after emergency period"""
        try:
            await asyncio.sleep(delay)
            self.check_interval = original_interval
            
            logger.info(
                "Restored normal monitoring interval",
                extra={
                    "interval": original_interval,
                    "emergency_duration": delay
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to restore normal monitoring: {e}")
    
    async def _record_error(self, component: str, error_message: str) -> None:
        """Record error for rate tracking"""
        current_time = time.time()
        
        # Initialize component error tracking
        if component not in self._error_counts:
            self._error_counts[component] = []
        
        # Add error timestamp
        self._error_counts[component].append(current_time)
        
        # Clean old errors (outside the window)
        cutoff_time = current_time - self.error_rate_window
        self._error_counts[component] = [
            timestamp for timestamp in self._error_counts[component]
            if timestamp > cutoff_time
        ]
    
    async def _check_error_rates(self) -> None:
        """Check error rates and generate alerts if thresholds are exceeded"""
        current_time = time.time()
        cutoff_time = current_time - self.error_rate_window
        
        for component, error_timestamps in self._error_counts.items():
            # Clean old errors
            recent_errors = [ts for ts in error_timestamps if ts > cutoff_time]
            self._error_counts[component] = recent_errors
            
            # Calculate error rate (errors per minute)
            error_rate = len(recent_errors) / (self.error_rate_window / 60)
            
            # Check if error rate exceeds threshold
            if error_rate > self.thresholds.get("error_rate_per_minute", 5):
                await self._create_alert(
                    level=AlertLevel.ERROR,
                    component=component,
                    message=f"High error rate detected: {error_rate:.2f} errors/minute",
                    details={
                        "error_rate": error_rate,
                        "threshold": self.thresholds.get("error_rate_per_minute", 5),
                        "window_minutes": self.error_rate_window / 60,
                        "recent_error_count": len(recent_errors)
                    }
                )


# Global system monitor instance
system_monitor = SystemMonitor()


# Example alert handler
async def log_critical_alerts(alert: SystemAlert) -> None:
    """Example alert handler that logs critical alerts"""
    if alert.level == AlertLevel.CRITICAL:
        logger.critical(
            f"CRITICAL ALERT: {alert.message}",
            extra={
                "alert_id": alert.id,
                "component": alert.component,
                "details": alert.details
            }
        )