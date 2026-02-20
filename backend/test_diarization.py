"""Test where pkg_resources fails"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent / '.env'
load_dotenv(env_path)

print("1. Testing pkg_resources import...")
try:
    import pkg_resources
    print("   ✓ pkg_resources imported successfully")
except Exception as e:
    print(f"   ✗ pkg_resources failed: {e}")

print("\n2. Testing pyannote.audio import...")
try:
    from pyannote.audio import Pipeline
    print("   ✓ pyannote.audio imported successfully")
except Exception as e:
    print(f"   ✗ pyannote.audio failed: {e}")
    import traceback
    traceback.print_exc()

print("\n3. Testing Pipeline.from_pretrained...")
try:
    hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
    print(f"   Token found: {bool(hf_token)}")
    if hf_token:
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
        print("   ✓ Pipeline loaded successfully")
    else:
        print("   ⚠ No token - skipping pipeline test")
except Exception as e:
    print(f"   ✗ Pipeline failed: {e}")
    import traceback
    traceback.print_exc()