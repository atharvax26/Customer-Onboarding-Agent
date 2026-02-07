"""
Check Gemini API status and configuration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 60)
print("Gemini API Configuration Check")
print("=" * 60)

# Check if API key is set
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("✗ GEMINI_API_KEY is NOT set in environment")
    print("\nTo fix this:")
    print("1. Add GEMINI_API_KEY to backend/.env file")
    print("2. Get your API key from: https://makersuite.google.com/app/apikey")
    print("3. Restart the backend server")
else:
    print(f"✓ GEMINI_API_KEY is set")
    print(f"  Key preview: {api_key[:10]}...{api_key[-4:]}")
    print(f"  Key length: {len(api_key)} characters")
    
    # Try to initialize Gemini client
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=api_key)
        print("\n✓ Gemini client initialized successfully with new API")
        print("✓ API key is valid")
        
        # Try a simple test
        print("\nTesting API connection...")
        try:
            config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=50
            )
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents="Say 'Hello'",
                config=config
            )
            print(f"✓ API test successful: {response.text[:50]}")
        except Exception as e:
            print(f"✗ API test failed: {str(e)}")
            
    except Exception as e:
        print(f"\n✗ Failed to initialize Gemini client: {str(e)}")

print("=" * 60)
