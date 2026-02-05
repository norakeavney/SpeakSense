import whisper
import os

# Global model cache (loaded once, reused)
_whisper_model = None

def get_whisper_model():
    """Load Whisper model (CPU-optimized 'tiny' model for speed)."""
    global _whisper_model
    if _whisper_model is None:
        print("Loading Whisper 'base' model")
        _whisper_model = whisper.load_model("base")  
        print(" Whisper model loaded and cached")
    return _whisper_model

def transcribe_audio(audio_path):
    """
    Transcribe audio file using Whisper.
    
    Args:
        audio_path: Full path to audio file
        
    Returns:
        dict: {
            'text': str,           # Full transcription
            'segments': [          # Timestamped segments
                {'start': float, 'end': float, 'text': str},
                ...
            ],
            'language': str        # Detected language
        }
    """
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    print(f"Transcribing: {audio_path}")
    
    model = get_whisper_model()
    
    # Transcribe with CPU-optimized settings
    result = model.transcribe(
        audio_path,
        fp16=False, 
        verbose=False
    )
    
    # Format output to match our job schema
    formatted_result = {
        'text': result['text'].strip(),
        'segments': [
            {
                'start': seg['start'],
                'end': seg['end'],
                'text': seg['text'].strip()
            }
            for seg in result['segments']
        ],
        'language': result.get('language', 'en')
    }
    
    print(f"Transcription complete: {len(formatted_result['segments'])} segments")
    return formatted_result