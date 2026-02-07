"""
List available Gemini models
"""

import os
from dotenv import load_dotenv

load_dotenv()

from google import genai

api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

print("Available Gemini Models:")
print("=" * 60)

try:
    models = client.models.list()
    for model in models:
        print(f"\nModel: {model.name}")
        print(f"  Display Name: {model.display_name}")
        print(f"  Supported Methods: {', '.join(model.supported_generation_methods)}")
except Exception as e:
    print(f"Error listing models: {e}")
