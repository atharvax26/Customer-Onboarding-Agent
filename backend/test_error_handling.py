#!/usr/bin/env python3
"""
Simple test script for error handling components
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.exceptions import DocumentProcessingError, AuthenticationError, SystemHealthError
from app.logging_config import setup_logging, get_context_logger
from app.error_handlers import ErrorResponse
from app.health_monitor import health_monitor
from app.services.system_monitor import system_monitor


async def test_error_handling():
    """Test error handling components"""
    print("🧪 Testing Customer Onboarding Agent Error Handling")
    print("=" * 60)
    
    # Test 1: Setup logging
    print("\n1. Testing logging setup...")
    try:
        setup_logging(log_level="INFO", enable_console_logging=True)
        logger = get_context_logger("test", component="error_test")
        logger.info("Logging setup successful")
        print("✅ Logging setup works")
    except Exception as e:
        print(f"❌ Logging setup failed: {e}")
        return False
    
    # Test 2: Custom exceptions
    print("\n2. Testing custom exceptions...")
    try:
        # Test DocumentProcessingError
        doc_error = DocumentProcessingError(
            detail="Test document processing error",
            user_message="Document could not be processed"
        )
        assert doc_error.status_code == 422
        assert doc_error.error_code == "DOCUMENT_PROCESSING_ERROR"
        
        # Test AuthenticationError
        auth_error = AuthenticationError(
            detail="Test authentication error",
            user_message="Invalid credentials"
        )
        assert auth_error.status_code == 401
        assert auth_error.error_code == "AUTHENTICATION_ERROR"
        
        print("✅ Custom exceptions work correctly")
    except Exception as e:
        print(f"❌ Custom exceptions failed: {e}")
        return False
    
    # Test 3: Error response formatting
    print("\n3. Testing error response formatting...")
    try:
        error_response = ErrorResponse(
            error_code="TEST_ERROR",
            message="Test error message",
            user_message="User-friendly test message",
            details={"test": "data"}
        )
        
        response_dict = error_response.to_dict()
        assert "error" in response_dict
        assert response_dict["error"]["code"] == "TEST_ERROR"
        assert response_dict["error"]["user_message"] == "User-friendly test message"
        
        print("✅ Error response formatting works")
    except Exception as e:
        print(f"❌ Error response formatting failed: {e}")
        return False
    
    # Test 4: Health monitor
    print("\n4. Testing health monitor...")
    try:
        # This will test basic health check functionality
        health_status = await health_monitor.check_system_health()
        assert "status" in health_status
        assert "components" in health_status
        assert "timestamp" in health_status
        
        print(f"✅ Health monitor works - Status: {health_status['status']}")
    except Exception as e:
        print(f"❌ Health monitor failed: {e}")
        return False
    
    # Test 5: System monitor
    print("\n5. Testing system monitor...")
    try:
        # Test system monitor status
        status = system_monitor.get_system_status()
        assert "monitoring_active" in status
        assert "active_alerts" in status
        
        print("✅ System monitor works")
    except Exception as e:
        print(f"❌ System monitor failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 All error handling tests passed!")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_error_handling())
    sys.exit(0 if success else 1)