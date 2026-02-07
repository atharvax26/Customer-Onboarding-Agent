"""
Centralized error tracking service for Customer Onboarding Agent
Provides comprehensive error monitoring, analysis, and reporting
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from enum import Enum
import json
from collections import defaultdict, deque

from app.logging_config import get_context_logger
from app.services.system_monitor import system_monitor, AlertLevel


logger = get_context_logger(__name__, component="error_tracking")


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_API = "external_api"
    DOCUMENT_PROCESSING = "document_processing"
    SYSTEM = "system"
    NETWORK = "network"
    UNKNOWN = "unknown"


@dataclass
class ErrorEvent:
    """Represents a single error event"""
    id: str
    timestamp: datetime
    severity: ErrorSeverity
    category: ErrorCategory
    component: str
    message: str
    stack_trace: Optional[str] = None
    user_id: Optional[int] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    context: Dict[str, Any] = None
    resolved: bool = False
    resolution_notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        data['category'] = self.category.value
        return data


class ErrorPattern:
    """Represents a pattern of recurring errors"""
    
    def __init__(self, pattern_id: str, signature: str):
        self.pattern_id = pattern_id
        self.signature = signature  # Unique identifier for the error pattern
        self.occurrences: List[ErrorEvent] = []
        self.first_seen = datetime.utcnow()
        self.last_seen = datetime.utcnow()
        self.frequency = 0
        self.affected_users: Set[int] = set()
        self.affected_components: Set[str] = set()
    
    def add_occurrence(self, error_event: ErrorEvent):
        """Add an error occurrence to this pattern"""
        self.occurrences.append(error_event)
        self.last_seen = error_event.timestamp
        self.frequency += 1
        
        if error_event.user_id:
            self.affected_users.add(error_event.user_id)
        
        self.affected_components.add(error_event.component)
    
    def get_trend_data(self, hours: int = 24) -> Dict[str, Any]:
        """Get trend data for this error pattern"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_occurrences = [
            error for error in self.occurrences
            if error.timestamp > cutoff_time
        ]
        
        # Group by hour
        hourly_counts = defaultdict(int)
        for error in recent_occurrences:
            hour_key = error.timestamp.strftime('%Y-%m-%d %H:00')
            hourly_counts[hour_key] += 1
        
        return {
            "pattern_id": self.pattern_id,
            "signature": self.signature,
            "total_occurrences": len(recent_occurrences),
            "affected_users": len(self.affected_users),
            "affected_components": list(self.affected_components),
            "hourly_distribution": dict(hourly_counts),
            "first_seen": self.first_seen.isoformat(),
            "last_seen": self.last_seen.isoformat()
        }


class ErrorTrackingService:
    """Centralized error tracking and analysis service"""
    
    def __init__(self):
        self.error_events: deque = deque(maxlen=10000)  # Keep last 10k errors
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.is_monitoring = False
        self.analysis_task: Optional[asyncio.Task] = None
        
        # Configuration
        self.pattern_detection_window = 3600  # 1 hour
        self.rate_limit_window = 300  # 5 minutes
        self.max_error_rate = 10  # errors per minute
        self.pattern_threshold = 5  # minimum occurrences to form a pattern
        
        # Severity thresholds
        self.severity_thresholds = {
            ErrorSeverity.CRITICAL: 1,  # 1 critical error triggers alert
            ErrorSeverity.HIGH: 3,      # 3 high errors in 5 minutes
            ErrorSeverity.MEDIUM: 10,   # 10 medium errors in 5 minutes
            ErrorSeverity.LOW: 50       # 50 low errors in 5 minutes
        }
    
    async def start_monitoring(self):
        """Start error tracking and analysis"""
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        self.analysis_task = asyncio.create_task(self._analysis_loop())
        
        logger.info("Error tracking service started")
    
    async def stop_monitoring(self):
        """Stop error tracking and analysis"""
        if not self.is_monitoring:
            return
        
        self.is_monitoring = False
        
        if self.analysis_task:
            self.analysis_task.cancel()
            try:
                await self.analysis_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Error tracking service stopped")
    
    async def track_error(
        self,
        message: str,
        severity: ErrorSeverity,
        category: ErrorCategory,
        component: str,
        stack_trace: Optional[str] = None,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track a new error event"""
        
        error_id = f"error_{int(time.time())}_{hash(message) % 10000}"
        
        error_event = ErrorEvent(
            id=error_id,
            timestamp=datetime.utcnow(),
            severity=severity,
            category=category,
            component=component,
            message=message,
            stack_trace=stack_trace,
            user_id=user_id,
            session_id=session_id,
            request_id=request_id,
            context=context or {}
        )
        
        # Store the error event
        self.error_events.append(error_event)
        
        # Update error rates
        self.error_rates[component].append(time.time())
        self.error_rates['global'].append(time.time())
        
        # Log the error
        logger.error(
            f"Error tracked: {message}",
            extra={
                "error_id": error_id,
                "severity": severity.value,
                "category": category.value,
                "component": component,
                "user_id": user_id,
                "session_id": session_id,
                "request_id": request_id
            }
        )
        
        # Immediate analysis for critical errors
        if severity == ErrorSeverity.CRITICAL:
            await self._handle_critical_error(error_event)
        
        # Check for pattern formation
        await self._check_error_patterns(error_event)
        
        # Check error rate thresholds
        await self._check_error_rates(component)
        
        return error_id
    
    async def _analysis_loop(self):
        """Main analysis loop for error patterns and trends"""
        while self.is_monitoring:
            try:
                await self._analyze_error_patterns()
                await self._analyze_error_trends()
                await self._cleanup_old_data()
                
                # Run analysis every 5 minutes
                await asyncio.sleep(300)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in analysis loop: {e}", exc_info=True)
                await asyncio.sleep(60)
    
    async def _handle_critical_error(self, error_event: ErrorEvent):
        """Handle critical errors immediately"""
        try:
            # Create system alert
            await system_monitor._create_alert(
                level=AlertLevel.CRITICAL,
                component=error_event.component,
                message=f"Critical error: {error_event.message}",
                details={
                    "error_id": error_event.id,
                    "category": error_event.category.value,
                    "user_id": error_event.user_id,
                    "session_id": error_event.session_id,
                    "request_id": error_event.request_id,
                    "context": error_event.context
                }
            )
            
            logger.critical(
                f"CRITICAL ERROR DETECTED: {error_event.message}",
                extra={
                    "error_id": error_event.id,
                    "component": error_event.component,
                    "category": error_event.category.value,
                    "immediate_action_required": True
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to handle critical error: {e}")
    
    async def _check_error_patterns(self, error_event: ErrorEvent):
        """Check if error forms part of a pattern"""
        try:
            # Create signature for pattern matching
            signature = self._create_error_signature(error_event)
            
            if signature in self.error_patterns:
                # Add to existing pattern
                pattern = self.error_patterns[signature]
                pattern.add_occurrence(error_event)
                
                # Check if pattern frequency warrants an alert
                if pattern.frequency >= self.pattern_threshold:
                    await self._alert_error_pattern(pattern)
            else:
                # Create new pattern
                pattern_id = f"pattern_{len(self.error_patterns)}_{int(time.time())}"
                pattern = ErrorPattern(pattern_id, signature)
                pattern.add_occurrence(error_event)
                self.error_patterns[signature] = pattern
            
        except Exception as e:
            logger.error(f"Failed to check error patterns: {e}")
    
    def _create_error_signature(self, error_event: ErrorEvent) -> str:
        """Create a signature for error pattern matching"""
        # Normalize the error message for pattern matching
        normalized_message = error_event.message.lower()
        
        # Remove dynamic parts (numbers, IDs, timestamps)
        import re
        normalized_message = re.sub(r'\d+', 'N', normalized_message)
        normalized_message = re.sub(r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', 'UUID', normalized_message)
        
        return f"{error_event.category.value}:{error_event.component}:{normalized_message[:100]}"
    
    async def _alert_error_pattern(self, pattern: ErrorPattern):
        """Alert about recurring error pattern"""
        try:
            recent_occurrences = len([
                error for error in pattern.occurrences
                if error.timestamp > datetime.utcnow() - timedelta(hours=1)
            ])
            
            if recent_occurrences >= self.pattern_threshold:
                await system_monitor._create_alert(
                    level=AlertLevel.WARNING,
                    component="error_pattern",
                    message=f"Recurring error pattern detected: {recent_occurrences} occurrences",
                    details={
                        "pattern_id": pattern.pattern_id,
                        "signature": pattern.signature,
                        "total_occurrences": pattern.frequency,
                        "recent_occurrences": recent_occurrences,
                        "affected_users": len(pattern.affected_users),
                        "affected_components": list(pattern.affected_components)
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed to alert error pattern: {e}")
    
    async def _check_error_rates(self, component: str):
        """Check error rates and alert if thresholds exceeded"""
        try:
            current_time = time.time()
            cutoff_time = current_time - self.rate_limit_window
            
            # Clean old error timestamps
            component_errors = self.error_rates[component]
            while component_errors and component_errors[0] < cutoff_time:
                component_errors.popleft()
            
            # Calculate error rate (errors per minute)
            error_count = len(component_errors)
            error_rate = error_count / (self.rate_limit_window / 60)
            
            if error_rate > self.max_error_rate:
                await system_monitor._create_alert(
                    level=AlertLevel.ERROR,
                    component=component,
                    message=f"High error rate: {error_rate:.2f} errors/minute",
                    details={
                        "error_rate": error_rate,
                        "threshold": self.max_error_rate,
                        "window_minutes": self.rate_limit_window / 60,
                        "error_count": error_count
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed to check error rates: {e}")
    
    async def _analyze_error_patterns(self):
        """Analyze error patterns for trends and insights"""
        try:
            for pattern in self.error_patterns.values():
                trend_data = pattern.get_trend_data()
                
                # Log pattern analysis
                logger.info(
                    f"Error pattern analysis: {pattern.signature}",
                    extra={
                        "pattern_analysis": trend_data,
                        "requires_attention": trend_data["total_occurrences"] > 10
                    }
                )
        
        except Exception as e:
            logger.error(f"Failed to analyze error patterns: {e}")
    
    async def _analyze_error_trends(self):
        """Analyze overall error trends"""
        try:
            # Analyze last 24 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            recent_errors = [
                error for error in self.error_events
                if error.timestamp > cutoff_time
            ]
            
            # Group by severity
            severity_counts = defaultdict(int)
            category_counts = defaultdict(int)
            component_counts = defaultdict(int)
            
            for error in recent_errors:
                severity_counts[error.severity.value] += 1
                category_counts[error.category.value] += 1
                component_counts[error.component] += 1
            
            # Log trend analysis
            logger.info(
                "Error trend analysis (24h)",
                extra={
                    "total_errors": len(recent_errors),
                    "severity_distribution": dict(severity_counts),
                    "category_distribution": dict(category_counts),
                    "component_distribution": dict(component_counts)
                }
            )
        
        except Exception as e:
            logger.error(f"Failed to analyze error trends: {e}")
    
    async def _cleanup_old_data(self):
        """Clean up old error data"""
        try:
            # Remove old error patterns (older than 7 days)
            cutoff_time = datetime.utcnow() - timedelta(days=7)
            
            patterns_to_remove = []
            for signature, pattern in self.error_patterns.items():
                if pattern.last_seen < cutoff_time:
                    patterns_to_remove.append(signature)
            
            for signature in patterns_to_remove:
                del self.error_patterns[signature]
            
            if patterns_to_remove:
                logger.info(f"Cleaned up {len(patterns_to_remove)} old error patterns")
        
        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get error summary for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_events
            if error.timestamp > cutoff_time
        ]
        
        # Calculate statistics
        severity_counts = defaultdict(int)
        category_counts = defaultdict(int)
        component_counts = defaultdict(int)
        
        for error in recent_errors:
            severity_counts[error.severity.value] += 1
            category_counts[error.category.value] += 1
            component_counts[error.component] += 1
        
        return {
            "time_period_hours": hours,
            "total_errors": len(recent_errors),
            "severity_distribution": dict(severity_counts),
            "category_distribution": dict(category_counts),
            "component_distribution": dict(component_counts),
            "active_patterns": len(self.error_patterns),
            "monitoring_active": self.is_monitoring
        }
    
    def get_error_patterns(self) -> List[Dict[str, Any]]:
        """Get all active error patterns"""
        return [
            pattern.get_trend_data()
            for pattern in self.error_patterns.values()
        ]
    
    def get_recent_errors(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent error events"""
        recent_errors = list(self.error_events)[-limit:]
        return [error.to_dict() for error in recent_errors]


# Global error tracking service instance
error_tracking_service = ErrorTrackingService()