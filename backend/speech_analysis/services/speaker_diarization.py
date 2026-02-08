"""
Speaker Diarization Service
Uses pyannote.audio to identify who speaks when
Combines with Whisper transcript to create speaker-labeled text
"""
import torch
from pyannote.audio import Pipeline
import os
from pathlib import Path


class SpeakerDiarizationService:
    """
    Service for diarizing audio and aligning with transcripts
    """
    
    def __init__(self):
        """Initialize diarization pipeline"""
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.pipeline = None
        
    def _load_pipeline(self):
        """Lazy load the diarization pipeline"""
        if self.pipeline is None:
            try:
                # Get HuggingFace token from environment
                hf_token = os.getenv('HF_TOKEN')
                
                if not hf_token:
                    raise ValueError(
                        "HUGGINGFACE_TOKEN not found in .env file. "
                        "Please run 'python setup_diarization.py' to configure."
                    )
                
                print(f"Loading pyannote speaker-diarization pipeline on {self.device}...")
                
                # Load the pipeline
                self.pipeline = Pipeline.from_pretrained(
                    "pyannote/speaker-diarization-3.1",
                    use_auth_token=hf_token
                )
                
                # Move to appropriate device
                self.pipeline.to(torch.device(self.device))
                
                print(f"Diarization pipeline loaded successfully!")
                
            except Exception as e:
                print(f"Failed to load diarization pipeline: {e}")
                raise
    
    def diarize_audio(self, audio_path):
        """
        Perform speaker diarization on audio file
        
        Args:
            audio_path (str): Path to audio file
            
        Returns:
            dict: Diarization results with speaker segments
        """
        try:
            self._load_pipeline()
            
            # Verify file exists
            if not Path(audio_path).exists():
                raise FileNotFoundError(f"Audio file not found: {audio_path}")
            
            print(f"\nStarting speaker diarization...")
            print(f"   Audio: {Path(audio_path).name}")
            
            # Run diarization
            diarization = self.pipeline(audio_path)
            
            # Extract speaker segments
            segments = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                segments.append({
                    'speaker': speaker,
                    'start': round(float(turn.start), 2),
                    'end': round(float(turn.end), 2),
                    'duration': round(float(turn.end - turn.start), 2)
                })
            
            # Get unique speakers
            unique_speakers = sorted(list(set([seg['speaker'] for seg in segments])))
            
            print(f"Diarization complete!")
            print(f"   - Segments detected: {len(segments)}")
            print(f"   - Unique speakers: {len(unique_speakers)}")
            for speaker in unique_speakers:
                speaker_segs = [s for s in segments if s['speaker'] == speaker]
                total_time = sum([s['duration'] for s in speaker_segs])
                print(f"   - {speaker}: {len(speaker_segs)} turns, {total_time:.1f}s total")
            
            return {
                'segments': segments,
                'speakers': unique_speakers,
                'num_speakers': len(unique_speakers),
                'status': 'completed'
            }
            
        except Exception as e:
            print(f"Diarization failed: {e}")
            return {
                'segments': [],
                'speakers': [],
                'num_speakers': 0,
                'status': 'failed',
                'error': str(e)
            }
    
    def align_transcript_with_speakers(self, whisper_result, diarization_segments):
        """
        Align Whisper transcription with speaker diarization
        Creates a combined transcript: SPEAKER_00: "text" → SPEAKER_01: "text"
        
        Args:
            whisper_result (dict): Whisper result with word-level timestamps
            diarization_segments (list): Speaker segments from diarization
            
        Returns:
            list: Combined transcript segments with speaker labels
        """
        try:
            # Get segments from Whisper (these have timestamps)
            if 'segments' not in whisper_result:
                print("Whisper result missing 'segments' field, using full text")
                return [{
                    'speaker': 'SPEAKER_00',
                    'text': whisper_result.get('text', ''),
                    'start': 0.0,
                    'end': 0.0
                }]
            
            combined_transcript = []
            
            # Process each Whisper segment
            for segment in whisper_result['segments']:
                segment_start = segment['start']
                segment_end = segment['end']
                segment_text = segment['text'].strip()
                
                # Find which speaker is talking at the midpoint of this segment
                midpoint = (segment_start + segment_end) / 2
                speaker = self._find_speaker_at_time(midpoint, diarization_segments)
                
                # Check if we can merge with previous segment (same speaker)
                if combined_transcript and combined_transcript[-1]['speaker'] == speaker:
                    # Merge with previous
                    combined_transcript[-1]['text'] += ' ' + segment_text
                    combined_transcript[-1]['end'] = segment_end
                else:
                    # New speaker segment
                    combined_transcript.append({
                        'speaker': speaker,
                        'text': segment_text,
                        'start': segment_start,
                        'end': segment_end
                    })
            
            print(f"Aligned transcript with speakers")
            print(f"   - Created {len(combined_transcript)} speaker turns")
            
            return combined_transcript
            
        except Exception as e:
            print(f"Transcript alignment failed: {e}")
            # Fallback: return transcript without speaker labels
            return [{
                'speaker': 'SPEAKER_00',
                'text': whisper_result.get('text', ''),
                'start': 0.0,
                'end': 0.0
            }]
    
    def _find_speaker_at_time(self, timestamp, diarization_segments):
        """
        Find which speaker is talking at a given timestamp
        
        Args:
            timestamp (float): Time in seconds
            diarization_segments (list): Speaker segments
            
        Returns:
            str: Speaker ID (e.g., 'SPEAKER_00')
        """
        # Find segment that contains this timestamp
        for segment in diarization_segments:
            if segment['start'] <= timestamp <= segment['end']:
                return segment['speaker']
        
        # If no exact match, find closest segment
        if diarization_segments:
            closest = min(
                diarization_segments, 
                key=lambda s: min(abs(s['start'] - timestamp), abs(s['end'] - timestamp))
            )
            return closest['speaker']
        
        return 'SPEAKER_00'


# Singleton instance
_diarization_service = None

def get_diarization_service():
    """Get or create singleton diarization service"""
    global _diarization_service
    if _diarization_service is None:
        _diarization_service = SpeakerDiarizationService()
    return _diarization_service


def diarize_and_align(audio_path, whisper_result):
    """
    Main function: Diarize audio + align with Whisper transcript
    
    Args:
        audio_path (str): Path to audio file
        whisper_result (dict): Whisper transcription result with timestamps
        
    Returns:
        dict: Combined result with speaker-labeled transcript
    """
    service = get_diarization_service()
    
    # Step 1: Diarize audio (find who speaks when)
    print("\nDiarizing audio...")
    diarization_result = service.diarize_audio(audio_path)
    
    if diarization_result['status'] == 'failed':
        print("Diarization failed, returning transcript without speakers")
        return {
            'status': 'failed',
            'error': diarization_result.get('error', 'Diarization failed'),
            'transcript': [{
                'speaker': 'SPEAKER_00',
                'text': whisper_result.get('text', ''),
                'start': 0.0,
                'end': 0.0
            }],
            'num_speakers': 1
        }
    
    # Step 2: Align transcript with speakers
    print("\nAligning transcript with speakers...")
    aligned_transcript = service.align_transcript_with_speakers(
        whisper_result,
        diarization_result['segments']
    )
    
    print("\nDiarization complete!")
    print(f"   - Speakers: {diarization_result['num_speakers']}")
    print(f"   - Speaker turns: {len(aligned_transcript)}")
    
    return {
        'status': 'completed',
        'transcript': aligned_transcript,
        'num_speakers': diarization_result['num_speakers'],
        'speakers': diarization_result['speakers']
    }