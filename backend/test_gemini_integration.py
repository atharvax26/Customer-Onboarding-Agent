"""
Simple test script to verify Gemini API integration
Run this to test if your GOOGLE_API_KEY is working correctly
"""

import asyncio
import os
from app.services.gemini_client import GeminiAPIClient

async def test_gemini_integration():
    """Test basic Gemini API functionality"""
    
    # Check if API key is available
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not found")
        print("Please set your Google Gemini API key:")
        print("export GOOGLE_API_KEY=your_api_key_here")
        return False
    
    try:
        print("🔄 Initializing Gemini client...")
        client = GeminiAPIClient()
        
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
        
        This guide will help you get started with our REST API.
        
        Getting Started:
        1. Sign up for an API key
        2. Make your first request
        3. Handle responses and errors
        
        Authentication:
        All requests require an API key in the header.
        
        Rate Limits:
        - 1000 requests per hour for free tier
        - 10000 requests per hour for paid tier
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
        print(f"❌ Error testing Gemini integration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Gemini API Integration")
    print("=" * 50)
    
    success = asyncio.run(test_gemini_integration())
    
    if success:
        print("\n🎉 All tests passed! Gemini integration is working correctly.")
        print("You can now use the Customer Onboarding Agent with Gemini API.")
    else:
        print("\n💥 Tests failed. Please check your configuration and try again.")