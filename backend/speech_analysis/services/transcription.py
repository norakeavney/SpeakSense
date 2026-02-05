import whisper
import os

# Global model cache (loaded once, reused)
_whisper_model = None

def get_whisper_model():
    """Load Whisper model (CPU-optimized 'base' model)."""
    global _whisper_model
    if _whisper_model is None:
        print("Loading Whisper 'base' model")
        _whisper_model = whisper.load_model("base")
        print("✅ Whisper model loaded and cached")
    return _whisper_model

def transcribe_audio(audio_path):
    """
    Transcribe audio file using Whisper.
    
    Args:
        audio_path: Path to audio file (string or Path object)
        
    Returns:
        dict: {
            'text': str,
            'segments': [{'start': float, 'end': float, 'text': str}, ...],
            'language': str
        }
    """
    # Convert Path object to string if needed
    audio_path = str(audio_path)
    
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")
    
    print(f"🎤 Transcribing: {audio_path}")
    
    model = get_whisper_model()
    
    # Transcribe with CPU-optimized settings
    result = model.transcribe(
        audio_path,
        fp16=False,
        verbose=False
    )
    
    # Format output
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
    
    print(f"✅ Transcription complete: {len(formatted_result['segments'])} segments, {len(formatted_result['text'])} characters")
    return formatted_result