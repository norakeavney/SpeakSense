"""
Fake Processor - Simulates progressive analysis
This will be replaced with real analysis functions in Phase B
"""
import time
import threading
from pathlib import Path
from speech_analysis.db.analysis_jobs import AnalysisJobManager


class FakeProcessor:
    """Simulates progressive speech analysis"""
    
    @staticmethod
    def process_job(job_id, audio_path):
        """
        Process a job with fake analysis steps
        
        This runs in a background thread and simulates progressive analysis.
        Each step updates the job status and adds dummy results.
        
        Args:
            job_id (str): UUID of the job to process
            audio_path (str): Path to the audio file
        """
        try:
            # Validate inputs
            if not job_id:
                raise ValueError("job_id is required")
            
            # Validate file path exists (with retry for timing issues)
            if not audio_path:
                raise ValueError("audio_path is required")
            
            file_path = Path(audio_path)
            max_retries = 3
            for attempt in range(max_retries):
                if file_path.exists() and file_path.stat().st_size > 0:
                    break
                if attempt < max_retries - 1:
                    print(f"⏳ File not ready, waiting... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(0.5)
            else:
                raise ValueError(f"Audio file not found or empty after {max_retries} attempts: {audio_path}")
            
            print(f"✅ File validated: {audio_path} ({file_path.stat().st_size} bytes)")
            
            # Update job status to processing
            AnalysisJobManager.update_status(job_id, AnalysisJobManager.STATUS_PROCESSING)
            
            # Step 1: Transcription
            AnalysisJobManager.update_step(job_id, 'transcription', AnalysisJobManager.STEP_PROCESSING)
            time.sleep(2)  # Simulate processing time
            
            fake_transcription = {
                'text': 'This is a fake transcription. In Phase B, this will be replaced with real Whisper output.',
                'segments': [
                    {'start': 0.0, 'end': 3.5, 'text': 'This is a fake transcription.'},
                    {'start': 3.5, 'end': 7.2, 'text': 'In Phase B, this will be replaced with real Whisper output.'}
                ],
                'language': 'en'
            }
            AnalysisJobManager.update_result(job_id, 'transcription', fake_transcription)
            AnalysisJobManager.update_step(job_id, 'transcription', AnalysisJobManager.STEP_DONE)
            
            # Step 2: Speaker Metrics
            AnalysisJobManager.update_step(job_id, 'speaker_metrics', AnalysisJobManager.STEP_PROCESSING)
            time.sleep(2)  # Simulate processing time
            
            fake_speaker_metrics = {
                'total_duration_seconds': 123.4,
                'words_per_minute': 140,
                'speakers_detected': 2,
                'speaker_details': {
                    'SPEAKER_00': {
                        'total_time': 65.2,
                        'word_count': 152,
                        'percentage': 52.8
                    },
                    'SPEAKER_01': {
                        'total_time': 58.2,
                        'word_count': 135,
                        'percentage': 47.2
                    }
                }
            }
            AnalysisJobManager.update_result(job_id, 'speaker_metrics', fake_speaker_metrics)
            AnalysisJobManager.update_step(job_id, 'speaker_metrics', AnalysisJobManager.STEP_DONE)
            
            # Step 3: Emotion Analysis
            AnalysisJobManager.update_step(job_id, 'emotion', AnalysisJobManager.STEP_PROCESSING)
            time.sleep(2)  # Simulate processing time
            
            fake_emotion = {
                'overall_sentiment': 'neutral',
                'timeline': [
                    {'timestamp': 0.0, 'emotion': 'neutral', 'confidence': 0.82},
                    {'timestamp': 30.0, 'emotion': 'happy', 'confidence': 0.75},
                    {'timestamp': 60.0, 'emotion': 'neutral', 'confidence': 0.79},
                    {'timestamp': 90.0, 'emotion': 'sad', 'confidence': 0.68},
                    {'timestamp': 120.0, 'emotion': 'neutral', 'confidence': 0.81}
                ],
                'emotion_distribution': {
                    'neutral': 0.65,
                    'happy': 0.20,
                    'sad': 0.15
                }
            }
            AnalysisJobManager.update_result(job_id, 'emotion', fake_emotion)
            AnalysisJobManager.update_step(job_id, 'emotion', AnalysisJobManager.STEP_DONE)
            
            # Step 4: Topic Extraction
            AnalysisJobManager.update_step(job_id, 'topics', AnalysisJobManager.STEP_PROCESSING)
            time.sleep(2)  # Simulate processing time
            
            fake_topics = {
                'main_topics': [
                    {'topic': 'technology', 'confidence': 0.85, 'keywords': ['software', 'development', 'code']},
                    {'topic': 'business', 'confidence': 0.72, 'keywords': ['meeting', 'project', 'deadline']},
                    {'topic': 'communication', 'confidence': 0.68, 'keywords': ['discuss', 'talk', 'conversation']}
                ],
                'keywords': ['software', 'development', 'project', 'meeting', 'discussion']
            }
            AnalysisJobManager.update_result(job_id, 'topics', fake_topics)
            AnalysisJobManager.update_step(job_id, 'topics', AnalysisJobManager.STEP_DONE)
            
            # Mark job as complete
            AnalysisJobManager.update_status(job_id, AnalysisJobManager.STATUS_DONE)
            
            print(f"✅ Job {job_id} completed successfully")
            
        except Exception as e:
            # Handle any errors
            error_message = f"Processing failed: {str(e)}"
            print(f"❌ Job {job_id} failed: {error_message}")
            AnalysisJobManager.set_error(job_id, error_message)
    
    @staticmethod
    def start_processing(job_id, audio_path):
        """
        Start processing in a background thread
        
        Args:
            job_id (str): UUID of the job
            audio_path (str): Path to the audio file
        """
        thread = threading.Thread(
            target=FakeProcessor.process_job,
            args=(job_id, audio_path),
            daemon=True
        )
        thread.start()
        print(f"🚀 Started background processing for job {job_id}")
