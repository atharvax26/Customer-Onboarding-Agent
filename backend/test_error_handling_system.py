"""
Comprehensive test for the enhanced error handling system
Tests all components of the error handling infrastructure
"""

import asyncio
import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
import json

from app.main import app
from app.services.error_tracking_service import (
    error_tracking_service, 
    ErrorSeverity, 
    ErrorCategory
)
from app.services.system_monitor import system_monitor
from app.exceptions import (
    DocumentProcessingError,
    AuthenticationError,
    ValidationError
)


class TestErrorHandlingSystem:
    """Test suite for comprehensive error handling system"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.client = TestClient(app)
    
    def test_custom_exception_handling(self):
        """Test custom exception handling with enhanced error responses"""
        
        # Test DocumentProcessingError
        with patch('app.routers.scaledown.process_document') as mock_process:
            mock_process.side_effect = DocumentProcessingError(
                "Invalid document format",
                "Please upload a valid PDF or text file"
            )
            
            response = self.client.post(
                "/api/scaledown/process",
                files={"file": ("test.txt", "invalid content", "text/plain")}
            )
            
            assert response.status_code == 422
            error_data = response.json()
            
            # Check enhanced error response structure
            assert "error" in error_data
            assert error_data["error"]["code"] == "DOCUMENT_PROCESSING_ERROR"
            assert error_data["error"]["user_message"] == "Please upload a valid PDF or text file"
            assert "suggestions" in error_data["error"]
            assert "recovery_actions" in error_data["error"]
            assert "request_id" in error_data["error"]
            assert "timestamp" in error_data["error"]
    
    def test_validation_error_handling(self):
        """Test validation error handling with field-specific guidance"""
        
        # Test invalid login data
        response = self.client.post(
            "/api/auth/login",
            json={"email": "invalid-email", "password": ""}
        )
        
        assert response.status_code == 422
        error_data = response.json()
        
        # Check validation error structure
        assert error_data["error"]["code"] == "VALIDATION_ERROR"
        assert "validation_errors" in error_data["error"]["details"]
        assert "suggestions" in error_data["error"]
        assert "recovery_actions" in error_data["error"]
    
    def test_authentication_error_handling(self):
        """Test authentication error handling"""
        
        # Test invalid credentials
        response = self.client.post(
            "/api/auth/login",
            json={"email": "test@example.com", "password": "wrongpassword"}
        )
        
        assert response.status_code == 401
        error_data = response.json()
        
        # Check authentication error guidance
        assert error_data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert "suggestions" in error_data["error"]
        assert "recovery_actions" in error_data["error"]
        
        # Check for helpful suggestions
        suggestions = error_data["error"]["suggestions"]
        assert any("session may have expired" in s.lower() for s in suggestions)
    
    def test_rate_limiting_error_handling(self):
        """Test rate limiting with helpful guidance"""
        
        # Make multiple rapid requests to trigger rate limiting
        for _ in range(150):  # Exceed the 120 requests per minute limit
            response = self.client.get("/")
        
        # The last request should be rate limited
        assert response.status_code == 429
        error_data = response.json()
        
        # Check rate limit error guidance
        assert error_data["error"]["code"] == "HTTP_429"
        assert "suggestions" in error_data["error"]
        assert "recovery_actions" in error_data["error"]
        
        # Check for helpful recovery actions
        recovery_actions = error_data["error"]["recovery_actions"]
        assert any("wait" in action.lower() for action in recovery_actions)
    
    @pytest.mark.asyncio
    async def test_error_tracking_service(self):
        """Test the error tracking service functionality"""
        
        # Start error tracking
        await error_tracking_service.start_monitoring()
        
        try:
            # Track various types of errors
            error_id_1 = await error_tracking_service.track_error(
                message="Database connection failed",
                severity=ErrorSeverity.HIGH,
                category=ErrorCategory.DATABASE,
                component="database",
                user_id=1,
                context={"connection_pool": "primary"}
            )
            
            error_id_2 = await error_tracking_service.track_error(
                message="Authentication failed for user",
                severity=ErrorSeverity.MEDIUM,
                category=ErrorCategory.AUTHENTICATION,
                component="auth",
                user_id=2,
                context={"login_attempt": 3}
            )
            
            error_id_3 = await error_tracking_service.track_error(
                message="Critical system failure",
                severity=ErrorSeverity.CRITICAL,
                category=ErrorCategory.SYSTEM,
                component="system",
                context={"memory_usage": "95%"}
            )
            
            # Verify errors were tracked
            assert error_id_1 is not None
            assert error_id_2 is not None
            assert error_id_3 is not None
            
            # Get error summary
            summary = error_tracking_service.get_error_summary(hours=1)
            assert summary["total_errors"] >= 3
            assert summary["severity_distribution"]["high"] >= 1
            assert summary["severity_distribution"]["medium"] >= 1
            assert summary["severity_distribution"]["critical"] >= 1
            
            # Get recent errors
            recent_errors = error_tracking_service.get_recent_errors(limit=10)
            assert len(recent_errors) >= 3
            
            # Verify error structure
            for error in recent_errors:
                assert "id" in error
                assert "timestamp" in error
                assert "severity" in error
                assert "category" in error
                assert "component" in error
                assert "message" in error
        
        finally:
            await error_tracking_service.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_system_monitoring_integration(self):
        """Test integration between error handling and system monitoring"""
        
        # Start system monitoring
        await system_monitor.start_monitoring()
        
        try:
            # Simulate multiple errors to trigger alerts
            for i in range(5):
                await error_tracking_service.track_error(
                    message=f"Repeated error {i}",
                    severity=ErrorSeverity.HIGH,
                    category=ErrorCategory.SYSTEM,
                    component="test_component",
                    context={"iteration": i}
                )
            
            # Wait for monitoring to process
            await asyncio.sleep(2)
            
            # Check if alerts were generated
            active_alerts = system_monitor.get_active_alerts()
            assert len(active_alerts) > 0
            
            # Check system status
            status = system_monitor.get_system_status()
            assert status["monitoring_active"] is True
            assert status["active_alerts"] > 0
        
        finally:
            await system_monitor.stop_monitoring()
    
    def test_error_response_consistency(self):
        """Test that all error responses follow the same format"""
        
        test_endpoints = [
            ("/api/auth/login", "post", {"email": "invalid", "password": ""}),
            ("/api/nonexistent", "get", None),
            ("/api/scaledown/process", "post", None),  # Missing file
        ]
        
        for endpoint, method, data in test_endpoints:
            if method == "post":
                if data:
                    response = self.client.post(endpoint, json=data)
                else:
                    response = self.client.post(endpoint)
            else:
                response = self.client.get(endpoint)
            
            # All error responses should have the same structure
            if response.status_code >= 400:
                error_data = response.json()
                
                # Check required fields
                assert "error" in error_data
                assert "code" in error_data["error"]
                assert "message" in error_data["error"]
                assert "user_message" in error_data["error"]
                assert "request_id" in error_data["error"]
                assert "timestamp" in error_data["error"]
    
    def test_error_logging_context(self):
        """Test that errors are logged with proper context"""
        
        with patch('app.error_handlers.logger') as mock_logger:
            # Trigger an error
            response = self.client.post(
                "/api/auth/login",
                json={"email": "test@example.com", "password": "wrongpassword"}
            )
            
            # Verify logging was called with context
            assert mock_logger.error.called
            
            # Check that the log call included context information
            call_args = mock_logger.error.call_args
            assert "extra" in call_args.kwargs
            
            extra_data = call_args.kwargs["extra"]
            assert "request_id" in extra_data
            assert "path" in extra_data
            assert "method" in extra_data
            assert "user_agent" in extra_data
            assert "client_ip" in extra_data
    
    def test_health_monitoring_endpoints(self):
        """Test health monitoring endpoints"""
        
        # Test basic health check
        response = self.client.get("/health")
        assert response.status_code == 200
        
        health_data = response.json()
        assert "status" in health_data
        assert "timestamp" in health_data
        assert "components" in health_data
    
    def test_error_boundary_integration(self):
        """Test that backend errors integrate properly with frontend error boundaries"""
        
        # Test that error responses include all necessary information for frontend
        response = self.client.post(
            "/api/auth/login",
            json={"email": "invalid-email", "password": ""}
        )
        
        error_data = response.json()
        
        # Check that response includes frontend-friendly information
        assert "suggestions" in error_data["error"]
        assert "recovery_actions" in error_data["error"]
        assert error_data["error"]["user_message"] is not None
        
        # Verify suggestions are actionable
        suggestions = error_data["error"]["suggestions"]
        assert len(suggestions) > 0
        assert all(isinstance(s, str) for s in suggestions)
        
        # Verify recovery actions are actionable
        recovery_actions = error_data["error"]["recovery_actions"]
        assert len(recovery_actions) > 0
        assert all(isinstance(a, str) for a in recovery_actions)


def test_error_handling_performance():
    """Test that error handling doesn't significantly impact performance"""
    import time
    
    client = TestClient(app)
    
    # Measure response time for successful request
    start_time = time.time()
    response = client.get("/")
    success_time = time.time() - start_time
    
    # Measure response time for error request
    start_time = time.time()
    response = client.get("/nonexistent")
    error_time = time.time() - start_time
    
    # Error handling should not add significant overhead
    assert error_time < success_time * 3  # Allow 3x overhead for error handling
    assert error_time < 1.0  # Should complete within 1 second


if __name__ == "__main__":
    # Run basic tests
    test_client = TestClient(app)
    
    print("Testing error handling system...")
    
    # Test basic error response
    response = test_client.post("/api/auth/login", json={"email": "invalid"})
    print(f"Validation error response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    # Test health endpoint
    response = test_client.get("/health")
    print(f"Health check response: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    
    print("Error handling system test completed!")