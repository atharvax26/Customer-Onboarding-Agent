"""
Test script to follow redirects and find the actual ScaleDown.ai API
"""

import asyncio
import httpx
import os

async def test_with_redirects():
    """Test endpoints following redirects"""
    
    api_key = os.getenv("SCALEDOWN_API_KEY")
    if not api_key:
        print("❌ SCALEDOWN_API_KEY not found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            print("🔄 Testing with redirect following...")
            
            # Test the main API endpoint with redirects
            response = await client.get("https://scaledown.ai/api/health", headers=headers)
            print(f"Final URL: {response.url}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ Success!")
                try:
                    data = response.json()
                    print(f"Response: {data}")
                except:
                    print(f"Response: {response.text[:200]}")
            else:
                print(f"Response: {response.text[:200]}")
            
            # Try a simple POST to see if we can process documents
            print("\n🔄 Testing document processing endpoint...")
            
            test_payload = {
                "text": "This is a test document for processing.",
                "options": {
                    "extract_summary": True,
                    "extract_tasks": True
                }
            }
            
            response = await client.post("https://scaledown.ai/api/process", 
                                       json=test_payload, 
                                       headers=headers)
            
            print(f"Process endpoint - Status: {response.status_code}")
            print(f"Final URL: {response.url}")
            
            if response.status_code == 200:
                print("✅ Processing successful!")
                try:
                    data = response.json()
                    print(f"Response: {data}")
                except:
                    print(f"Response: {response.text[:200]}")
            else:
                print(f"Response: {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Testing ScaleDown.ai API with redirects...")
    print("=" * 50)
    asyncio.run(test_with_redirects())