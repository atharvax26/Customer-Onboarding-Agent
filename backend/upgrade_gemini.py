"""
Upgrade from deprecated google-generativeai to new google-genai package
"""

import subprocess
import sys

print("=" * 60)
print("Upgrading Gemini AI Package")
print("=" * 60)

print("\n1. Uninstalling old package (google-generativeai)...")
try:
    subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "google-generativeai"], check=True)
    print("✓ Old package uninstalled")
except Exception as e:
    print(f"⚠️  Could not uninstall old package: {e}")

print("\n2. Installing new package (google-genai)...")
try:
    subprocess.run([sys.executable, "-m", "pip", "install", "google-genai>=0.2.0"], check=True)
    print("✓ New package installed")
except Exception as e:
    print(f"✗ Failed to install new package: {e}")
    sys.exit(1)

print("\n3. Verifying installation...")
try:
    from google import genai
    print("✓ google-genai imported successfully")
except ImportError as e:
    print(f"✗ Failed to import google-genai: {e}")
    sys.exit(1)

print("\n" + "=" * 60)
print("✓ Upgrade complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Restart your backend server")
print("2. Run: python check_gemini_status.py")
print("3. Test document upload and processing")
