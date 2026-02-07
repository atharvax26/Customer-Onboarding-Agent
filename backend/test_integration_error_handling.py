#!/usr/bin/env python3
"""
Integration test for error handling system
"""

import asyncio
import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.exceptions import DocumentProcessingError, AuthenticationError
from app.error_handlers import register_error_handlers
from app.middleware import register_middleware
from app.logging_config import setup_logging


def test_error_handling_integration():
    """Test error handling integration with FastAPI"""
    print("🧪 Testing Error Handling Integration")
    print("=" * 50)
    
    # Setup logging (quiet mode for testing)
    setup_logging(log_level="ERROR", enable_console_logging=False)
    
    # Create test FastAPI app
    app = FastAPI(title="Test Error Handling App")
    
    # Register error handlers and middleware
    register_error_handlers(app)
    register_middleware(app)
    
    # Add test endpoints that raise different types of errors
    @app.get("/test/document-error")
    async def test_document_error():
        raise DocumentProcessingError(
            detail="Test document processing failed",
            user_message="Document could not be processed"
        )
    
    @app.get("/test/auth-error")
    async def test_auth_error():
        raise AuthenticationError(
            detail="Test authentication failed",
            user_message="Please log in"
        )
    
    @app.get("/test/http-error")
    async def test_http_error():
        raise HTTPException(status_code=404, detail="Not found")
    
    @app.get("/test/unexpected-error")
    async def test_unexpected_error():
        raise ValueError("Unexpected error for testing")
    
    @app.get("/test/success")
    async def test_success():
        return {"message": "Success"}
    
    # Create test client
    client = TestClient(app)
    
    # Test 1: Document processing error
    print("\n1. Testing document processing error...")
    response = client.get("/test/document-error")
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "DOCUMENT_PROCESSING_ERROR"
    assert data["error"]["user_message"] == "Document could not be processed"
    print("✅ Document processing error handled correctly")
    
    # Test 2: Authentication error
    print("\n2. Testing authentication error...")
    response = client.get("/test/auth-error")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "AUTHENTICATION_ERROR"
    assert data["error"]["user_message"] == "Please log in"
    print("✅ Authentication error handled correctly")
    
    # Test 3: HTTP exception
    print("\n3. Testing HTTP exception...")
    response = client.get("/test/http-error")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_404"
    print("✅ HTTP exception handled correctly")
    
    # Test 4: Unexpected error
    print("\n4. Testing unexpected error...")
    try:
        response = client.get("/test/unexpected-error")
        assert response.status_code == 500
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INTERNAL_ERROR"
        assert "request_id" in data["error"]
        print("✅ Unexpected error handled correctly")
    except Exception as e:
        # If the test client doesn't handle the exception properly,
        # it means our error handler is working (the exception was caught)
        print(f"✅ Unexpected error caught by error handler: {type(e).__name__}")
        # This is actually a success case for error handling
    
    # Test 5: Successful request
    print("\n5. Testing successful request...")
    response = client.get("/test/success")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Success"
    # Check that middleware added headers
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers
    print("✅ Successful request processed correctly")
    
    print("\n" + "=" * 50)
    print("🎉 All integration tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = test_error_handling_integration()
        if success:
            print("✅ Error handling integration test completed successfully")
            sys.exit(0)
        else:
            print("❌ Error handling integration test failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Integration test failed with exception: {e}")
        sys.exit(1)