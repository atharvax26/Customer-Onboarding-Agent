"""
Simple test to verify enhanced error handling system
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.error_tracking_service import (
    error_tracking_service, 
    ErrorSeverity, 
    ErrorCategory
)
from app.services.system_monitor import system_monitor
from app.error_handlers import ErrorResponse


async def test_error_tracking():
    """Test error tracking service"""
    print("Testing Error Tracking Service...")
    
    # Start error tracking
    await error_tracking_service.start_monitoring()
    
    try:
        # Track some test errors
        error_id_1 = await error_tracking_service.track_error(
            message="Test database connection failed",
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            component="database",
            user_id=1,
            context={"connection_pool": "primary"}
        )
        print(f"✓ Tracked error 1: {error_id_1}")
        
        error_id_2 = await error_tracking_service.track_error(
            message="Test authentication failed",
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AUTHENTICATION,
            component="auth",
            user_id=2,
            context={"login_attempt": 3}
        )
        print(f"✓ Tracked error 2: {error_id_2}")
        
        error_id_3 = await error_tracking_service.track_error(
            message="Test critical system failure",
            severity=ErrorSeverity.CRITICAL,
            category=ErrorCategory.SYSTEM,
            component="system",
            context={"memory_usage": "95%"}
        )
        print(f"✓ Tracked error 3: {error_id_3}")
        
        # Get error summary
        summary = error_tracking_service.get_error_summary(hours=1)
        print(f"✓ Error summary: {summary['total_errors']} total errors")
        print(f"  - Critical: {summary['severity_distribution'].get('critical', 0)}")
        print(f"  - High: {summary['severity_distribution'].get('high', 0)}")
        print(f"  - Medium: {summary['severity_distribution'].get('medium', 0)}")
        
        # Get recent errors
        recent_errors = error_tracking_service.get_recent_errors(limit=5)
        print(f"✓ Retrieved {len(recent_errors)} recent errors")
        
        print("✓ Error Tracking Service test completed successfully!")
        
    finally:
        await error_tracking_service.stop_monitoring()


async def test_system_monitoring():
    """Test system monitoring"""
    print("\nTesting System Monitoring...")
    
    # Start system monitoring
    await system_monitor.start_monitoring()
    
    try:
        # Wait a moment for monitoring to start
        await asyncio.sleep(2)
        
        # Check system status
        status = system_monitor.get_system_status()
        print(f"✓ System monitoring active: {status['monitoring_active']}")
        print(f"✓ Active alerts: {status['active_alerts']}")
        
        # Get recent metrics
        metrics = system_monitor.get_recent_metrics(limit=1)
        print(f"✓ Retrieved {len(metrics)} metrics")
        
        print("✓ System Monitoring test completed successfully!")
        
    finally:
        await system_monitor.stop_monitoring()


def test_error_response():
    """Test error response formatting"""
    print("\nTesting Error Response Formatting...")
    
    # Test basic error response
    error_response = ErrorResponse(
        error_code="TEST_ERROR",
        message="This is a test error",
        user_message="Something went wrong during testing",
        suggestions=["Try again", "Check your input"],
        recovery_actions=["Refresh the page", "Contact support"]
    )
    
    response_dict = error_response.to_dict()
    
    # Verify structure
    assert "error" in response_dict
    assert "code" in response_dict["error"]
    assert "message" in response_dict["error"]
    assert "user_message" in response_dict["error"]
    assert "suggestions" in response_dict["error"]
    assert "recovery_actions" in response_dict["error"]
    assert "request_id" in response_dict["error"]
    assert "timestamp" in response_dict["error"]
    
    print("✓ Error response structure is correct")
    print(f"✓ Error code: {response_dict['error']['code']}")
    print(f"✓ User message: {response_dict['error']['user_message']}")
    print(f"✓ Suggestions: {len(response_dict['error']['suggestions'])}")
    print(f"✓ Recovery actions: {len(response_dict['error']['recovery_actions'])}")
    
    print("✓ Error Response Formatting test completed successfully!")


async def main():
    """Run all tests"""
    print("🚀 Starting Enhanced Error Handling System Tests\n")
    
    try:
        # Test error response formatting
        test_error_response()
        
        # Test error tracking service
        await test_error_tracking()
        
        # Test system monitoring
        await test_system_monitoring()
        
        print("\n🎉 All tests completed successfully!")
        print("✅ Enhanced Error Handling System is working correctly!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)