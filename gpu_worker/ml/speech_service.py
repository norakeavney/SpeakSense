"""Speech Analysis Service — Whisper + Pyannote.

Pipeline: transcription (Whisper) -> diarization (Pyannote) -> speaker matching.
"""
import logging
import whisper
import torch
import os
import tempfile
from pathlib import Path
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)

# ============================================================
# GLOBAL MODEL INITIALIZATION (loaded once at startup)
# ============================================================
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
logger.info(f"Initializing Whisper model on {DEVICE}...")
WHISPER_MODEL = whisper.load_model("large", device=DEVICE)
logger.info(f"Whisper model ready on {DEVICE}")

# Initialize Pyannote pipeline
logger.info("Initializing Pyannote diarization pipeline...")
HF_TOKEN = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
try:
    from pyannote.audio import Pipeline
    
    if not HF_TOKEN:
        logger.warning("HF_TOKEN not found in .env - diarization will fail")
        DIARIZATION_PIPELINE = None
    else:
        DIARIZATION_PIPELINE = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=HF_TOKEN
        )
        DIARIZATION_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        DIARIZATION_PIPELINE.to(DIARIZATION_DEVICE)
        logger.info(f"Pyannote ready on {DIARIZATION_DEVICE}")
except Exception as e:
    logger.error(f"Failed to load Pyannote: {e}")
    DIARIZATION_PIPELINE = None


def _convert_to_clean_wav(file_ref, target_sr=16000):
    """
    Convert any audio format to mono 16kHz WAV for consistent Whisper + Pyannote processing.
    
    Args:
        file_ref: Path to audio file (mp4, m4a, wav, etc.)
        target_sr: Target sample rate (default 16000 Hz)
    
    Returns:
        Path to converted WAV file (in temp directory)
    """
    try:
        logger.info(f"Converting audio to mono {target_sr}Hz WAV...")

        # Load audio (librosa handles formats like mp4, m4a, wav)
        y, sr = librosa.load(file_ref, sr=target_sr, mono=True)
        logger.debug(f"Loaded audio: {sr}Hz, shape={y.shape}")

        # Save to temp WAV file
        temp_wav = Path(tempfile.gettempdir()) / f"speaksense_clean_{Path(file_ref).stem}.wav"
        sf.write(str(temp_wav), y, target_sr)
        logger.debug(f"Converted audio saved to {temp_wav}")

        return str(temp_wav)
    except Exception as e:
        logger.error(f"Audio conversion failed: {e}")
        logger.warning("Falling back to original file (may cause diarization issues)")
        
        return file_ref



def analyse_audio(file_ref, include_diarization=True):
    """
    Transcribe with Whisper, diarize with Pyannote
    """
    if not Path(file_ref).exists():
        raise FileNotFoundError(f"Audio not found: {file_ref}")
    
    logger.info("Speech analysis pipeline started")
    
    # ============================================================
    # STEP 0: CONVERT AUDIO TO CLEAN WAV
    # ============================================================
    logger.info("[0/3] Converting audio to clean mono WAV...")
    audio_path = _convert_to_clean_wav(file_ref)
    
    # ============================================================
    # STEP 1: TRANSCRIBE WITH WHISPER
    # ============================================================
    logger.info("[1/3] Transcribing with Whisper...")

    result = WHISPER_MODEL.transcribe(
        audio_path,
        task="transcribe",
        word_timestamps=True,
        fp16=torch.cuda.is_available()
    )
    
    text = result['text'].strip()
    segments = result.get('segments', [])

    logger.info(f"Transcription complete: {len(segments)} segments")
    
    # If no diarization needed, return early
    if not include_diarization:
        return {
            'status': 'completed',
            'text': text,
            'segments': segments,
            'transcript': [{
                'speaker': 'SPEAKER_00',
                'text': text,
                'start': 0.0,
                'end': segments[-1]['end'] if segments else 0
            }],
            'num_speakers': 1,
            'speakers': ['SPEAKER_00']
        }
    
    # ============================================================
    # STEP 2: DIARIZE WITH PYANNOTE
    # ============================================================
    logger.info("[2/3] Running speaker diarization...")
    
    try:
        if DIARIZATION_PIPELINE is None:
            raise RuntimeError("Diarization pipeline not available")
        
        # Run diarization on clean WAV audio using global pipeline
        diarization = DIARIZATION_PIPELINE(audio_path)
        
        # Convert to list of speaker segments
        speaker_segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            speaker_segments.append({
                'start': turn.start,
                'end': turn.end,
                'speaker': speaker
            })
        
        num_speakers = len(set([seg['speaker'] for seg in speaker_segments]))
        logger.info(f"Diarization complete! Found {num_speakers} speakers")
        
    except Exception as e:
        logger.error(f"Diarization failed: {e}")
        logger.info("Continuing WITHOUT speaker labels...")
        
        # Fallback: create one speaker covering entire audio for consistency
        speaker_segments = [{
            'start': 0,
            'end': segments[-1]['end'] if segments else 0,
            'speaker': 'SPEAKER_00'
        }]
        num_speakers = 1
    
    # ============================================================
    # STEP 3: MATCH TRANSCRIPTION TO SPEAKERS
    # ============================================================
    logger.info("[3/3] Matching speakers to transcript...")
    
    # Assign speaker to each Whisper segment based on overlap
    for segment in segments:
        segment_start = segment['start']
        segment_end = segment['end']
        segment_mid = (segment_start + segment_end) / 2
        
        # Find which speaker was talking at the midpoint of this segment
        assigned_speaker = 'SPEAKER_00'
        for speaker_seg in speaker_segments:
            if speaker_seg['start'] <= segment_mid <= speaker_seg['end']:
                assigned_speaker = speaker_seg['speaker']
                break
        
        segment['speaker'] = assigned_speaker or 'SPEAKER_00'
    
    # Build transcript with speaker labels
    transcript = []
    for segment in segments:
        speaker = segment.get('speaker') or 'SPEAKER_00'
        seg_text = segment['text'].strip()
        start = segment['start']
        end = segment['end']
        
        # Merge consecutive segments from same speaker (only if gap < 1 second)
        if (
            transcript
            and transcript[-1]['speaker'] == speaker
            and (start - transcript[-1]['end']) < 1.0
        ):
            transcript[-1]['text'] += ' ' + seg_text
            transcript[-1]['end'] = end
        else:
            transcript.append({
                'speaker': speaker,
                'text': seg_text,
                'start': start,
                'end': end
            })
    
    speakers = sorted(list(set([
        seg.get('speaker') or 'SPEAKER_00'
        for seg in segments
    ])))
    
    logger.info(f"Pipeline complete: {num_speakers} speakers, {len(transcript)} turns")
    
    return {
        'status': 'completed',
        'text': text,
        'segments': segments,
        'transcript': transcript,
        'num_speakers': num_speakers,
        'speakers': speakers,
        'language': result.get('language', 'unknown')
    }