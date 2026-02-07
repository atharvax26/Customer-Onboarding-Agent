"""
Test the flexible ScaleDown.ai client (currently in mock mode)
"""

import asyncio
import os
from app.services.scaledown_ai_flexible_client import ScaleDownAIFlexibleClient

async def test_flexible_client():
    """Test the flexible ScaleDown.ai client"""
    
    api_key = os.getenv("SCALEDOWN_API_KEY")
    if not api_key:
        print("❌ SCALEDOWN_API_KEY not found")
        return False
    
    try:
        print("🔄 Initializing flexible ScaleDown.ai client...")
        client = ScaleDownAIFlexibleClient()
        
        print("🔄 Testing health check...")
        health = await client.health_check()
        
        if health["status"] == "healthy":
            print(f"✅ Health check passed! Response time: {health['response_time']:.2f}s")
            if "note" in health:
                print(f"📝 Note: {health['note']}")
        else:
            print(f"❌ Health check failed: {health.get('error', 'Unknown error')}")
            return False
        
        print("🔄 Testing document processing (mock mode)...")
        test_content = """
        Welcome to our Customer Onboarding System
        
        This comprehensive guide will help you get started with our platform and understand all the key features.
        
        Getting Started Steps:
        1. Create your account and verify your email address
        2. Complete your profile with business information
        3. Set up your first project and configure settings
        4. Invite team members and assign appropriate roles
        5. Upload your first documents for processing
        
        Key Features:
        - AI-powered document processing and summarization
        - Role-based onboarding flows for different user types
        - Real-time engagement tracking and analytics
        - Automated intervention system for struggling users
        - Comprehensive reporting and insights dashboard
        
        Best Practices:
        - Start with smaller documents to test the system
        - Review generated summaries for accuracy
        - Customize onboarding flows for your specific needs
        - Monitor user engagement and adjust content accordingly
        - Use analytics to identify areas for improvement
        """
        
        result = await client.process_document_single_call(
            content=test_content,
            filename="onboarding_guide.txt"
        )
        
        print("✅ Document processing successful!")
        print(f"📄 Summary length: {len(result['summary'])} characters")
        print(f"📋 Tasks generated: {len(result['tasks'])}")
        print(f"⏱️  Processing time: {result['processing_time']:.2f}s")
        print(f"🤖 Model used: {result['model_used']}")
        
        print("\n📄 Generated Summary:")
        print("-" * 50)
        print(result['summary'])
        
        print("\n📋 Generated Tasks:")
        print("-" * 50)
        for i, task in enumerate(result['tasks'], 1):
            print(f"{i}. {task}")
        
        print("\n📝 Integration Status:")
        print("-" * 50)
        print("✅ Client initialized successfully")
        print("✅ Mock processing working correctly")
        print("⚠️  Ready for actual API integration when endpoints are available")
        print("📞 Contact ScaleDown.ai for API documentation and correct endpoints")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing flexible client: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Testing Flexible ScaleDown.ai Integration")
    print("=" * 60)
    
    success = asyncio.run(test_flexible_client())
    
    if success:
        print("\n🎉 Flexible client test passed!")
        print("Your system is ready to work with ScaleDown.ai once API details are confirmed.")
        print("\nNext steps:")
        print("1. Contact ScaleDown.ai support for API documentation")
        print("2. Get the correct API endpoints and request format")
        print("3. Update the flexible client with actual API calls")
        print("4. Your document upload interface will work seamlessly!")
    else:
        print("\n💥 Tests failed. Please check your configuration.")