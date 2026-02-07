#!/usr/bin/env python3
"""
Demonstration of the comprehensive error handling system
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.exceptions import *
from app.logging_config import setup_logging, get_context_logger
from app.error_handlers import ErrorResponse
from app.health_monitor import health_monitor
from app.services.system_monitor import system_monitor, AlertLevel


async def demonstrate_error_handling():
    """Demonstrate the error handling system capabilities"""
    
    print("🚀 Customer Onboarding Agent - Error Handling System Demo")
    print("=" * 70)
    
    # Setup logging with JSON formatting for demo
    setup_logging(
        log_level="INFO",
        enable_json_logging=False,  # Keep it readable for demo
        enable_console_logging=True
    )
    
    logger = get_context_logger("demo", component="error_demo")
    
    print("\n1. 📝 STRUCTURED LOGGING DEMONSTRATION")
    print("-" * 40)
    logger.info("This is an info message with context", extra={
        "user_id": 123,
        "session_id": "abc-123",
        "operation": "demo"
    })
    logger.warning("This is a warning message")
    logger.error("This is an error message with details", extra={
        "error_code": "DEMO_ERROR",
        "details": {"key": "value"}
    })
    
    print("\n2. 🚨 CUSTOM EXCEPTION DEMONSTRATION")
    print("-" * 40)
    
    # Demonstrate different types of custom exceptions
    exceptions_to_demo = [
        DocumentProcessingError("Failed to process PDF document", "Document format not supported"),
        AuthenticationError("Invalid JWT token", "Please log in again"),
        ValidationError("Email format is invalid", "email", "Please enter a valid email address"),
        RateLimitError("API rate limit exceeded", "Too many requests. Please wait."),
        SystemHealthError("Database connection failed", "database", "System temporarily unavailable")
    ]
    
    for exc in exceptions_to_demo:
        print(f"  • {exc.__class__.__name__}: {exc.user_message}")
        print(f"    Status Code: {exc.status_code}, Error Code: {exc.error_code}")
    
    print("\n3. 📊 HEALTH MONITORING DEMONSTRATION")
    print("-" * 40)
    
    try:
        health_status = await health_monitor.check_system_health()
        print(f"  • Overall System Status: {health_status['status'].upper()}")
        print(f"  • Health Check Duration: {health_status.get('check_duration', 0):.3f}s")
        print(f"  • Components Checked: {len(health_status.get('components', {}))}")
        
        # Show component details
        for component_name, component_data in health_status.get('components', {}).items():
            status = component_data.get('status', 'unknown')
            response_time = component_data.get('response_time')
            print(f"    - {component_name}: {status.upper()}", end="")
            if response_time:
                print(f" ({response_time:.3f}s)")
            else:
                print()
                
    except Exception as e:
        print(f"  ❌ Health check failed: {e}")
    
    print("\n4. 🔍 SYSTEM MONITORING DEMONSTRATION")
    print("-" * 40)
    
    try:
        # Get system monitor status
        monitor_status = system_monitor.get_system_status()
        print(f"  • Monitoring Active: {monitor_status['monitoring_active']}")
        print(f"  • Active Alerts: {monitor_status['active_alerts']}")
        print(f"  • Critical Alerts: {monitor_status.get('critical_alerts', 0)}")
        print(f"  • Warning Alerts: {monitor_status.get('warning_alerts', 0)}")
        
        # Create a demo alert
        await system_monitor._create_alert(
            level=AlertLevel.INFO,
            component="demo",
            message="Demo alert for testing purposes",
            details={"demo": True, "timestamp": "2024-01-01T00:00:00Z"}
        )
        print("  • Demo alert created successfully")
        
    except Exception as e:
        print(f"  ❌ System monitoring demo failed: {e}")
    
    print("\n5. 📋 ERROR RESPONSE FORMATTING DEMONSTRATION")
    print("-" * 40)
    
    # Demonstrate error response formatting
    error_response = ErrorResponse(
        error_code="DEMO_ERROR",
        message="This is a demonstration error message",
        user_message="Something went wrong, but don't worry - this is just a demo!",
        details={
            "demo_mode": True,
            "error_category": "demonstration",
            "suggested_action": "No action needed - this is a demo"
        }
    )
    
    response_dict = error_response.to_dict()
    print("  • Structured Error Response:")
    print(f"    - Error Code: {response_dict['error']['code']}")
    print(f"    - User Message: {response_dict['error']['user_message']}")
    print(f"    - Request ID: {response_dict['error']['request_id']}")
    print(f"    - Timestamp: {response_dict['error']['timestamp']}")
    
    print("\n6. ✨ KEY FEATURES SUMMARY")
    print("-" * 40)
    print("  ✅ Structured JSON logging with context")
    print("  ✅ Custom exception hierarchy with user-friendly messages")
    print("  ✅ Comprehensive health monitoring")
    print("  ✅ Real-time system monitoring with alerts")
    print("  ✅ Request tracking middleware")
    print("  ✅ Security headers middleware")
    print("  ✅ Rate limiting middleware")
    print("  ✅ Standardized error response format")
    print("  ✅ Automatic error logging and tracking")
    print("  ✅ Performance monitoring")
    
    print("\n" + "=" * 70)
    print("🎉 Error Handling System Demo Complete!")
    print("   The system is ready to handle errors gracefully and provide")
    print("   comprehensive monitoring and alerting capabilities.")
    print("=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(demonstrate_error_handling())
    except KeyboardInterrupt:
        print("\n\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        sys.exit(1)