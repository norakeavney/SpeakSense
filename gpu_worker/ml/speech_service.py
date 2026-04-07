"""
Speech Analysis Service - Whisper + Pyannote (No WhisperX!)
Clean separation: Whisper for transcription, Pyannote for diarization
"""
import logging
import whisper
import torch
import os
from pathlib import Path

logger = logging.getLogger(__name__)



def analyse_audio(file_ref, include_diarization=True):
    """
    Transcribe with Whisper, diarize with Pyannote
    """
    if not Path(file_ref).exists():
        raise FileNotFoundError(f"Audio not found: {file_ref}")
    
    logger.info("Speech analysis pipeline started")
    
    # ============================================================
    # STEP 1: TRANSCRIBE WITH WHISPER
    # ============================================================
    logger.info("[1/3] Transcribing with Whisper...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    whisper_model = whisper.load_model("base", device=device)
    
    result = whisper_model.transcribe(file_ref, word_timestamps=True)
    
    text = result['text'].strip()
    segments = result.get('segments', [])
    
    logger.info(f"Transcription complete! {len(segments)} segments")
    
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
        from pyannote.audio import Pipeline
        
        hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
        if not hf_token:
            raise ValueError("HF_TOKEN not found in .env")
        
        # Load diarization pipeline with use_auth_token (older huggingface_hub)
        diarization_pipeline = Pipeline.from_pretrained(
            "pyannote/speaker-diarization-3.1",
            use_auth_token=hf_token
        )
        
        # Move to GPU if available
        if torch.cuda.is_available():
            diarization_pipeline.to("cuda")
            logger.info("Pyannote moved to GPU")
        
        # Run diarization
        diarization = diarization_pipeline(file_ref)
        
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
        logger.info("Returning transcription without speaker labels...")
        
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
            'speakers': ['SPEAKER_00'],
            'diarization_error': str(e)
        }
    
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
        
        segment['speaker'] = assigned_speaker
    
    # Build transcript with speaker labels
    transcript = []
    for segment in segments:
        speaker = segment.get('speaker', 'SPEAKER_00')
        seg_text = segment['text'].strip()
        start = segment['start']
        end = segment['end']
        
        # Merge consecutive segments from same speaker
        if transcript and transcript[-1]['speaker'] == speaker:
            transcript[-1]['text'] += ' ' + seg_text
            transcript[-1]['end'] = end
        else:
            transcript.append({
                'speaker': speaker,
                'text': seg_text,
                'start': start,
                'end': end
            })
    
    speakers = sorted(list(set([seg.get('speaker', 'SPEAKER_00') for seg in segments])))
    
    logger.info(f"Pipeline complete - {num_speakers} speakers, {len(transcript)} turns")
    
    return {
        'status': 'completed',
        'text': text,
        'segments': segments,
        'transcript': transcript,
        'num_speakers': num_speakers,
        'speakers': speakers,
        'language': result.get('language', 'unknown')
    }