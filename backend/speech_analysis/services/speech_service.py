"""
Complete Speech Analysis Service
Combines transcription + speaker diarization in one place
"""
import torch
import whisper
import os
from pathlib import Path
from pyannote.audio import Pipeline
import pandas as pd


class SpeechAnalysisService:
    """
    All-in-one service for speech analysis:
    - Transcription (Whisper)
    - Speaker diarization (Pyannote)
    - Alignment (combine them)
    """
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.whisper_model = None
        self.diarization_pipeline = None
        
    def _load_whisper(self):
        """Lazy load Whisper model"""
        if self.whisper_model is None:
            print(f"Loading Whisper model on {self.device}...")
            self.whisper_model = whisper.load_model("base", device=self.device)
            print("✓ Whisper model loaded")
    
    def _load_diarization(self):
        """Lazy load pyannote diarization pipeline"""
        if self.diarization_pipeline is None:
            hf_token = os.getenv('HF_TOKEN') or os.getenv('HUGGINGFACE_TOKEN')
            
            if not hf_token:
                raise ValueError("HF_TOKEN not found in .env file")
            
            print(f"Loading pyannote diarization pipeline on {self.device}...")
            self.diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
            self.diarization_pipeline.to(torch.device(self.device))
            print("✓ Diarization pipeline loaded")
    
    def analyze_audio(self, audio_path, include_diarization=True):
        """
        Complete audio analysis: transcribe + diarize
        
        Args:
            audio_path (str): Path to audio file
            include_diarization (bool): Whether to include speaker diarization
            
        Returns:
            dict: Complete analysis with transcript and speakers
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        print("\n" + "="*70)
        print("🎤 SPEECH ANALYSIS")
        print("="*70)
        
        # Step 1: Transcribe with Whisper
        print("\n📝 Step 1: Transcribing audio...")
        self._load_whisper()
        
        whisper_result = self.whisper_model.transcribe(
            audio_path,
            word_timestamps=True,
            language='en'
        )
        
        print(f"✓ Transcription complete!")
        print(f"   - Duration: {whisper_result.get('duration', 0):.1f}s")
        print(f"   - Segments: {len(whisper_result.get('segments', []))}")
        
        # If diarization not needed, return just transcript
        if not include_diarization:
            return {
                'status': 'completed',
                'text': whisper_result['text'],
                'segments': whisper_result.get('segments', []),
                'transcript': [{
                    'speaker': 'SPEAKER_00',
                    'text': whisper_result['text'],
                    'start': 0.0,
                    'end': whisper_result.get('duration', 0)
                }],
                'num_speakers': 1,
                'speakers': ['SPEAKER_00']
            }
        
        # Step 2: Diarize speakers
        print("\n🎙️ Step 2: Identifying speakers...")
        try:
            self._load_diarization()
            
            diarization = self.diarization_pipeline(audio_path)
            
            # Convert to DataFrame
            diarize_list = []
            for turn, _, speaker in diarization.itertracks(yield_label=True):
                diarize_list.append({
                    'start': float(turn.start),
                    'end': float(turn.end),
                    'speaker': speaker,
                    'duration': float(turn.end - turn.start)
                })
            
            diarize_df = pd.DataFrame(diarize_list)
            num_speakers = len(diarize_df['speaker'].unique())
            
            print(f"✓ Diarization complete!")
            print(f"   - Speakers detected: {num_speakers}")
            
            for speaker in sorted(diarize_df['speaker'].unique()):
                speaker_time = diarize_df[diarize_df['speaker'] == speaker]['duration'].sum()
                speaker_turns = len(diarize_df[diarize_df['speaker'] == speaker])
                print(f"   - {speaker}: {speaker_turns} turns, {speaker_time:.1f}s")
            
        except Exception as e:
            print(f"⚠ Diarization failed: {e}")
            # Return without diarization
            return {
                'status': 'completed',
                'text': whisper_result['text'],
                'segments': whisper_result.get('segments', []),
                'transcript': [{
                    'speaker': 'SPEAKER_00',
                    'text': whisper_result['text'],
                    'start': 0.0,
                    'end': whisper_result.get('duration', 0)
                }],
                'num_speakers': 1,
                'speakers': ['SPEAKER_00'],
                'diarization_error': str(e)
            }
        
        # Step 3: Align transcript with speakers
        print("\n🔗 Step 3: Aligning transcript with speakers...")
        aligned_transcript = self._align_transcript(whisper_result, diarize_df)
        
        print(f"✓ Alignment complete!")
        print(f"   - Speaker turns: {len(aligned_transcript)}")
        
        print("\n" + "="*70)
        print("✅ ANALYSIS COMPLETE")
        print("="*70 + "\n")
        
        return {
            'status': 'completed',
            'text': whisper_result['text'],
            'segments': whisper_result.get('segments', []),
            'transcript': aligned_transcript,
            'num_speakers': num_speakers,
            'speakers': sorted(diarize_df['speaker'].unique())
        }
    
    def _align_transcript(self, whisper_result, diarize_df):
        """
        Align Whisper segments with speaker diarization
        
        Returns:
            list: Transcript segments with speaker labels
        """
        aligned = []
        current_speaker = None
        current_text = []
        current_start = None
        
        for segment in whisper_result.get('segments', []):
            seg_start = segment['start']
            seg_end = segment['end']
            seg_text = segment['text'].strip()
            
            # Find speaker at midpoint
            midpoint = (seg_start + seg_end) / 2
            matching = diarize_df[
                (diarize_df['start'] <= midpoint) & 
                (diarize_df['end'] >= midpoint)
            ]
            
            if not matching.empty:
                speaker = matching.iloc[0]['speaker']
            else:
                # Find closest
                diarize_df['distance'] = diarize_df.apply(
                    lambda x: min(abs(x['start'] - midpoint), abs(x['end'] - midpoint)),
                    axis=1
                )
                speaker = diarize_df.loc[diarize_df['distance'].idxmin()]['speaker']
            
            # If speaker changed, save previous and start new
            if speaker != current_speaker and current_text:
                aligned.append({
                    'speaker': current_speaker,
                    'text': ' '.join(current_text),
                    'start': current_start,
                    'end': seg_start
                })
                current_text = []
                current_start = None
            
            current_speaker = speaker
            if current_start is None:
                current_start = seg_start
            current_text.append(seg_text)
        
        # Don't forget last segment
        if current_text:
            aligned.append({
                'speaker': current_speaker,
                'text': ' '.join(current_text),
                'start': current_start,
                'end': whisper_result['segments'][-1]['end']
            })
        
        return aligned


# Singleton instance
_speech_service = None

def get_speech_service():
    """Get or create singleton speech analysis service"""
    global _speech_service
    if _speech_service is None:
        _speech_service = SpeechAnalysisService()
    return _speech_service


def analyze_audio(audio_path, include_diarization=True):
    """
    Main function: Complete speech analysis
    
    Args:
        audio_path (str): Path to audio file
        include_diarization (bool): Whether to include speaker diarization
        
    Returns:
        dict: Complete analysis results
    """
    service = get_speech_service()
    return service.analyze_audio(audio_path, include_diarization)
