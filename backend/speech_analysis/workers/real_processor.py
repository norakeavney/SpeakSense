import threading
import time
import os
from speech_analysis.db.analysis_jobs import AnalysisJobManager
from speech_analysis.services.speech_service import analyze_audio  # One simple import!
from speech_analysis.services.speaker_metrics import calculate_speaker_metrics  # NEW!
from speech_analysis.services.emotion_analysis import (
    analyze_emotions, 
    generate_emotion_summary,
    analyze_audio_emotions,  # Audio emotion analysis
    fuse_text_and_audio_emotions  # Fusion
)
import librosa  


def start_real_processing(job_id, audio_path):
    """Start background processing for a job."""
    thread = threading.Thread(
        target=_process_job,
        args=(job_id, audio_path),
        daemon=True
    )
    thread.start()
    print(f"Real processing started for job {job_id}")

def _process_job(job_id, audio_path):
    """Background worker that processes the audio file."""
    
    try:
        print(f"\n{'='*60}")
        print(f"Starting real analysis for job: {job_id}")
        print(f"Audio file: {audio_path}")
        print(f"{'='*60}\n")
        
        # Verify file exists
        max_retries = 3
        for attempt in range(max_retries):
            if os.path.exists(audio_path):
                break
            print(f"Waiting for file... (attempt {attempt + 1}/{max_retries})")
            time.sleep(0.5)
        
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found after {max_retries} retries")
        
        # Update job status to processing
        AnalysisJobManager.update_status(job_id, AnalysisJobManager.STATUS_PROCESSING)
        
        # ========================================
        # STEP 1: COMPLETE SPEECH ANALYSIS
        # (Transcription + Speaker Diarization combined!)
        # ========================================
        print("\nSTEP 1/4: Complete Speech Analysis (Transcription + Diarization)")
        AnalysisJobManager.update_step(job_id, "transcription", AnalysisJobManager.STEP_PROCESSING)
        AnalysisJobManager.update_step(job_id, "diarization", AnalysisJobManager.STEP_PROCESSING)
        
        # Run complete analysis - does BOTH transcription + diarization!
        analysis_result = analyze_audio(audio_path, include_diarization=True)
        
        # Store transcription
        AnalysisJobManager.update_result(job_id, "transcription", {
            'text': analysis_result['text'],
            'segments': analysis_result.get('segments', [])
        })
        AnalysisJobManager.update_step(job_id, "transcription", AnalysisJobManager.STEP_DONE)
        
        # Store diarization
        if analysis_result.get('diarization_error'):
            print(f"⚠ Diarization failed: {analysis_result['diarization_error']}")
            AnalysisJobManager.update_result(job_id, "diarization", {
                "status": "failed",
                "error": analysis_result['diarization_error'],
                "num_speakers": analysis_result.get('num_speakers', 1)
            })
            AnalysisJobManager.update_step(job_id, "diarization", AnalysisJobManager.STEP_FAILED)
        else:
            AnalysisJobManager.update_result(job_id, "diarization", {
                'status': 'completed',
                'transcript': analysis_result['transcript'],
                'num_speakers': analysis_result['num_speakers'],
                'speakers': analysis_result['speakers']
            })
            AnalysisJobManager.update_step(job_id, "diarization", AnalysisJobManager.STEP_DONE)
            print(f"✓ Complete analysis done! {analysis_result['num_speakers']} speakers detected.")
        
        # ========================================
        # STEP 2: SPEAKER METRICS (REAL!)
        # ========================================
        print("\nSTEP 2/4: Speaker Metrics")
        AnalysisJobManager.update_step(job_id, "speaker_metrics", AnalysisJobManager.STEP_PROCESSING)
        
        # Get audio duration
        try:
            audio, sr = librosa.load(audio_path, sr=None)
            audio_duration = len(audio) / sr
            print(f"✓ Audio duration: {audio_duration:.2f} seconds")
        except Exception as e:
            print(f"Could not load audio for duration: {e}")
            audio_duration = 0
        
        # Calculate real speaker metrics
        speaker_metrics_result = calculate_speaker_metrics(
            transcription_result=analysis_result,
            diarization_result=analysis_result
        )

        # DEBUG: Print what we got
        print("\n" + "="*60)
        print("📊 SPEAKER METRICS RESULT:")
        print("="*60)
        import json
        print(json.dumps(speaker_metrics_result, indent=2))
        print("="*60 + "\n")
        
        AnalysisJobManager.update_result(job_id, "speaker_metrics", speaker_metrics_result)
        AnalysisJobManager.update_step(job_id, "speaker_metrics", AnalysisJobManager.STEP_DONE)
        print("✓ Speaker metrics complete.")
        
        # ========================================
        # STEP 3: EMOTION ANALYSIS (Text + Audio Fusion)
        # ========================================
        print("\nSTEP 3/4: Emotion Analysis (Text + Audio)")
        AnalysisJobManager.update_step(job_id, "emotion", AnalysisJobManager.STEP_PROCESSING)
        
        try:
            # Analyze emotions from TEXT (DistilBERT)
            print("  → Analyzing text emotions with DistilBERT...")
            transcript_segments = []
            if analysis_result.get('transcript'):
                transcript_segments = analysis_result['transcript']
            elif analysis_result.get('text'):
                # Fallback: use plain transcription if no diarization
                transcript_segments = [{
                    'text': analysis_result['text'],
                    'start': 0.0,
                    'end': analysis_result.get('duration', 0.0)
                }]
            
            text_emotions = analyze_emotions(transcript_segments)
            print(f"  ✓ Text emotions: {text_emotions.get('overall_sentiment')}")
            
            # Analyze emotions from AUDIO (Wav2Vec2)
            print("  → Analyzing audio emotions with Wav2Vec2...")
            audio_emotions = analyze_audio_emotions(audio_path, transcript_segments)
            print(f"  ✓ Audio emotions: {audio_emotions.get('overall_sentiment')}")
            
            # FUSE both analyses
            print("  → Fusing text and audio predictions...")
            emotion_result = fuse_text_and_audio_emotions(text_emotions, audio_emotions)
            
            # Generate human-readable summary
            emotion_result['summary'] = generate_emotion_summary(emotion_result)
            
            AnalysisJobManager.update_result(job_id, "emotion", emotion_result)
            AnalysisJobManager.update_step(job_id, "emotion", AnalysisJobManager.STEP_DONE)
            print("✓ Emotion analysis complete (fused).")
            print(f"  Overall sentiment: {emotion_result['overall_sentiment']}")
            print(f"  Timeline points: {len(emotion_result.get('timeline', []))}")
            
            # Print fusion info
            if isinstance(emotion_result.get('fusion_info'), dict):
                fusion = emotion_result['fusion_info']
                print(f"  Models used: Text={fusion.get('text_model')}, Audio={fusion.get('audio_model')}")
        
        except Exception as e:
            error_msg = f"Emotion analysis failed: {str(e)}"
            print(f"✗ {error_msg}")
            import traceback
            traceback.print_exc()
            AnalysisJobManager.update_result(job_id, "emotion", {
                'error': error_msg,
                'overall_sentiment': 'neutral'
            })
            AnalysisJobManager.update_step(job_id, "emotion", AnalysisJobManager.STEP_DONE)
        
        # ========================================
        # STEP 4: TOPICS (Fake for now)
        # ========================================
        print("\nSTEP 4/4: Topic Extraction (placeholder)")
        AnalysisJobManager.update_step(job_id, "topics", AnalysisJobManager.STEP_PROCESSING)
        time.sleep(2)
        
        topics_result = {
            "main_topics": [],
            "keywords": [],
            "note": "Real implementation coming in Step B4"
        }
        
        AnalysisJobManager.update_result(job_id, "topics", topics_result)
        AnalysisJobManager.update_step(job_id, "topics", AnalysisJobManager.STEP_DONE)
        print("Topic extraction complete.")
        
        # ========================================
        # MARK JOB AS COMPLETE
        # ========================================
        AnalysisJobManager.update_status(job_id, AnalysisJobManager.STATUS_DONE)
        
        print(f"\n{'='*60}")
        print(f"Analysis complete for job: {job_id}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nError processing job {job_id}: {str(e)}")
        import traceback
        traceback.print_exc()
        AnalysisJobManager.set_error(job_id, str(e))