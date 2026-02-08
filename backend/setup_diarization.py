"""
Setup script for Speaker Diarization
Helps configure HuggingFace authentication for pyannote.audio
"""
import os
from pathlib import Path


def setup_huggingface_token():
    """
    Guide user through HuggingFace token setup
    """
    print("=" * 60)
    print("🎭 Speaker Diarization Setup")
    print("=" * 60)
    print()
    
    # Check if token already exists in environment
    existing_token = os.getenv('HF_TOKEN') or os.getenv('HUGGING_FACE_HUB_TOKEN')
    
    if existing_token:
        print("✅ HuggingFace token found in environment!")
        print(f"   Token: {existing_token[:10]}...{existing_token[-4:]}")
        print()
        response = input("Do you want to update it? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Keeping existing token.")
            return
    else:
        print("⚠️  No HuggingFace token found.")
        print()
    
    print("To use speaker diarization, you need a HuggingFace token:")
    print()
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Create a new token (or use existing)")
    print("3. Accept model license: https://huggingface.co/pyannote/speaker-diarization-3.1")
    print("4. Copy your token")
    print()
    
    token = input("Enter your HuggingFace token: ").strip()
    
    if not token:
        print("❌ No token provided. Exiting.")
        return
    
    # Save to .env file
    env_path = Path(__file__).parent / '.env'
    
    # Read existing .env content
    env_content = ""
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
    
    # Check if HF_TOKEN already in .env
    if 'HF_TOKEN=' in env_content or 'HUGGING_FACE_HUB_TOKEN=' in env_content:
        # Replace existing
        lines = env_content.split('\n')
        new_lines = []
        for line in lines:
            if line.startswith('HF_TOKEN=') or line.startswith('HUGGING_FACE_HUB_TOKEN='):
                continue  # Skip old tokens
            new_lines.append(line)
        env_content = '\n'.join(new_lines)
    
    # Add new token
    if env_content and not env_content.endswith('\n'):
        env_content += '\n'
    
    env_content += f'\n# HuggingFace token for pyannote.audio\n'
    env_content += f'HF_TOKEN={token}\n'
    env_content += f'HUGGING_FACE_HUB_TOKEN={token}\n'
    
    # Write back to .env
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print()
    print("✅ Token saved to .env file!")
    print()
    print("Next steps:")
    print("1. Restart your Django server to load the new token")
    print("2. Upload an audio file to test speaker diarization")
    print()


def test_diarization():
    """
    Test if diarization pipeline can be loaded
    """
    print("=" * 60)
    print("🧪 Testing Diarization Pipeline")
    print("=" * 60)
    print()
    
    try:
        import torch
        from pyannote.audio import Pipeline
        
        print("📦 Loading pyannote pipeline...")
        
        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"   Using device: {device}")
        
        pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=True
        )
        
        print("✅ Pipeline loaded successfully!")
        print()
        print("Your speaker diarization setup is complete! 🎉")
        
    except Exception as e:
        print("❌ Failed to load pipeline")
        print(f"   Error: {str(e)}")
        print()
        print("Troubleshooting:")
        print("1. Make sure you accepted the model license")
        print("2. Check your HuggingFace token is valid")
        print("3. Verify internet connection")
        print("4. Try: pip install --upgrade pyannote.audio")


def main():
    """Main setup flow"""
    print()
    print("Welcome to SpeakSense Speaker Diarization Setup! 🎙️")
    print()
    
    # Step 1: Configure token
    setup_huggingface_token()
    
    # Step 2: Test setup
    print()
    response = input("Would you like to test the setup now? (y/N): ").strip().lower()
    if response in ['y', 'yes']:
        print()
        test_diarization()
    else:
        print()
        print("Setup complete! Run this script again with --test to test later.")
        print()


if __name__ == '__main__':
    import sys
    
    if '--test' in sys.argv:
        test_diarization()
    else:
        main()
