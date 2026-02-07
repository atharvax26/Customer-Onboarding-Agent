"""
Test script to discover the correct ScaleDown.ai API endpoints
"""

import asyncio
import httpx
import os

async def test_endpoints():
    """Test different possible API endpoints"""
    
    api_key = os.getenv("SCALEDOWN_API_KEY")
    if not api_key:
        print("❌ SCALEDOWN_API_KEY not found")
        return
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test different possible endpoints
    endpoints_to_test = [
        "https://scaledown.ai/api",
        "https://api.scaledown.ai",
        "https://app.scaledown.ai/api",
        "https://scaledown.ai/api/v1",
        "https://api.scaledown.ai/v1",
        "https://scaledown.ai",
    ]
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        for endpoint in endpoints_to_test:
            try:
                print(f"🔄 Testing: {endpoint}")
                
                # Try health check
                response = await client.get(f"{endpoint}/health", headers=headers)
                print(f"   Health check: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ Health check successful!")
                    try:
                        data = response.json()
                        print(f"   Response: {data}")
                    except:
                        print(f"   Response: {response.text[:100]}")
                
                # Try root endpoint
                response = await client.get(endpoint, headers=headers)
                print(f"   Root endpoint: {response.status_code}")
                
                if response.status_code == 200:
                    print(f"   ✅ Root endpoint accessible!")
                    try:
                        data = response.json()
                        print(f"   Response: {data}")
                    except:
                        print(f"   Response: {response.text[:100]}")
                
                print()
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                print()

if __name__ == "__main__":
    print("🔍 Discovering ScaleDown.ai API endpoints...")
    print("=" * 50)
    asyncio.run(test_endpoints())