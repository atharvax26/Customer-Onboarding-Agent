"""
Simple test script to verify ScaleDown.ai API integration
Run this to test if your SCALEDOWN_API_KEY is working correctly
"""

import asyncio
import os
from app.services.scaledown_ai_client import ScaleDownAIClient

async def test_scaledown_ai_integration():
    """Test basic ScaleDown.ai API functionality"""
    
    # Check if API key is available
    api_key = os.getenv("SCALEDOWN_API_KEY")
    if not api_key:
        print("❌ SCALEDOWN_API_KEY environment variable not found")
        print("Please set your ScaleDown.ai API key:")
        print("export SCALEDOWN_API_KEY=your_api_key_here")
        return False
    
    try:
        print("🔄 Initializing ScaleDown.ai client...")
        client = ScaleDownAIClient()
        
        print("🔄 Testing health check...")
        health = await client.health_check()
        
        if health["status"] == "healthy":
            print(f"✅ Health check passed! Response time: {health['response_time']:.2f}s")
        else:
            print(f"❌ Health check failed: {health.get('error', 'Unknown error')}")
            return False
        
        print("🔄 Testing document processing...")
        test_content = """
        Welcome to our API Documentation
        
        This comprehensive guide will help you get started with our REST API and integrate it into your applications.
        
        Getting Started:
        1. Sign up for an API key at our developer portal
        2. Make your first authenticated request
        3. Handle responses and error codes properly
        4. Implement rate limiting in your application
        
        Authentication:
        All requests require an API key in the Authorization header.
        Use Bearer token authentication for secure access.
        
        Rate Limits:
        - Free tier: 1000 requests per hour
        - Pro tier: 10000 requests per hour
        - Enterprise: Custom limits available
        
        Best Practices:
        - Cache responses when possible
        - Use webhooks for real-time updates
        - Implement proper error handling
        - Monitor your usage and quotas
        """
        
        result = await client.process_document_single_call(
            content=test_content,
            filename="test_api_docs.txt"
        )
        
        print("✅ Document processing successful!")
        print(f"📄 Summary length: {len(result['summary'])} characters")
        print(f"📋 Tasks generated: {len(result['tasks'])}")
        print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
        
        print("\n📄 Generated Summary:")
        print("-" * 50)
        print(result['summary'])
        
        print("\n📋 Generated Tasks:")
        print("-" * 50)
        for i, task in enumerate(result['tasks'], 1):
            print(f"{i}. {task}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing ScaleDown.ai integration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing ScaleDown.ai API Integration")
    print("=" * 50)
    
    success = asyncio.run(test_scaledown_ai_integration())
    
    if success:
        print("\n🎉 All tests passed! ScaleDown.ai integration is working correctly.")
        print("You can now use the Customer Onboarding Agent with ScaleDown.ai API.")
    else:
        print("\n💥 Tests failed. Please check your configuration and try again.")