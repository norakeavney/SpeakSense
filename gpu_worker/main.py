from fastapi import FastAPI, BackgroundTasks, status
from pydantic import BaseModel
from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime, timezone
import os
import logging
import traceback
from pathlib import Path
from typing import Any, Optional

from ml.speech_service import analyse_audio
from ml.emotion_analysis import analyse_emotions
from ml.topic_extraction import extract_topics
from ml.speaker_metrics import calculate_speaker_metrics
from ml.political_analysis import (
    analyse_speaker_politics,
    build_speaker_texts_from_diarized_transcript,
)

# Configure logging for production
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

mongo_uri = os.getenv("MONGODB_URI")
client = MongoClient(mongo_uri)

# Get database - use default if available, otherwise fallback to speaksense_db
try:
    db = client.get_default_database()
except Exception:
    db = client["speaksense_db"]

jobs_collection = db["analysis_jobs"]


class JobRequest(BaseModel):
    job_id: str
    file_ref: str


def now_utc() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def update_job(job_id: str, updates: dict) -> None:
    """Update job document with new data and timestamp."""
    updates["updated_at"] = now_utc()
    jobs_collection.update_one({"job_id": job_id}, {"$set": updates})


def fail_job(job_id: str, error: str, failed_step: Optional[str] = None) -> None:
    """Mark job as failed with error message and optional failed step."""
    updates = {
        "status": "failed",
        "error": error,
    }
    if failed_step:
        updates[f"steps.{failed_step}"] = "failed"
    update_job(job_id, updates)


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Cleanup MongoDB connection on shutdown."""
    logger.info("Closing MongoDB connection")
    client.close()


def process_job(job_id: str, file_ref: str) -> None:
    """
    Process audio analysis job with all pipeline steps.
    Handles transcription, diarization, emotion, topics, and political analysis.
    """
    logger.info(f"🚀 [JOB {job_id}] BACKGROUND TASK STARTED!")
    logger.info(f"🚀 [JOB {job_id}] File: {file_ref}")
    logger.info(f"[JOB {job_id}] Processing started for file: {file_ref}")

    # Validate file exists before processing
    if not Path(file_ref).exists():
        error_msg = f"Audio file not found: {file_ref}"
        logger.error(f"[JOB {job_id}] {error_msg}")
        fail_job(job_id, error_msg)
        return

    try:
        # ============ STEP 1: TRANSCRIPTION & DIARIZATION ============
        logger.info(f"[JOB {job_id}] Starting speech pipeline")
        update_job(job_id, {
            "status": "processing",
            "steps.transcription": "processing",
        })

        try:
            speech_result = analyse_audio(file_ref, include_diarization=True)
            transcript = speech_result.get("transcript", [])
            full_text = speech_result.get("text", "")

            logger.info(f"[JOB {job_id}] Speech analysis completed: {len(transcript)} turns, {len(full_text)} chars")
            
            update_job(job_id, {
                "results.transcription": {
                    "status": "done",
                    "text": speech_result.get("text", ""),
                    "segments": speech_result.get("segments", []),
                    "transcript": transcript,
                    "language": speech_result.get("language", "unknown"),
                },
                "results.diarization": {
                    "status": "done",
                    "transcript": transcript,
                    "num_speakers": speech_result.get("num_speakers", 0),
                    "speakers": speech_result.get("speakers", []),
                    "diarization_error": speech_result.get("diarization_error"),
                },
                "steps.transcription": "done",
                "steps.diarization": "done",
                "steps.speaker_metrics": "processing",
            })
        except Exception as e:
            error_msg = f"Speech analysis failed: {str(e)}"
            logger.error(f"[JOB {job_id}] {error_msg}", exc_info=True)
            fail_job(job_id, error_msg, "transcription")
            return

        # ============ STEP 2: SPEAKER METRICS ============
        try:
            logger.info(f"[JOB {job_id}] Computing speaker metrics")
            speaker_metrics = calculate_speaker_metrics(speech_result, speech_result)
            logger.info(f"[JOB {job_id}] Speaker metrics completed")

            update_job(job_id, {
                "results.speaker_metrics": speaker_metrics,
                "steps.speaker_metrics": "done",
                "steps.emotion": "processing",
            })
        except Exception as e:
            error_msg = f"Speaker metrics failed: {str(e)}"
            logger.error(f"[JOB {job_id}] {error_msg}", exc_info=True)
            fail_job(job_id, error_msg, "speaker_metrics")
            return

        # ============ STEP 3: EMOTION ANALYSIS ============
        try:
            logger.info(f"[JOB {job_id}] Running emotion analysis")
            emotion_result = analyse_emotions(transcript)
            logger.info(f"[JOB {job_id}] Emotion analysis completed")

            update_job(job_id, {
                "results.emotion": emotion_result,
                "steps.emotion": "done",
                "steps.topics": "processing",
            })
        except Exception as e:
            error_msg = f"Emotion analysis failed: {str(e)}"
            logger.error(f"[JOB {job_id}] {error_msg}", exc_info=True)
            fail_job(job_id, error_msg, "emotion")
            return

        # ============ STEP 4: TOPIC EXTRACTION ============
        try:
            logger.info(f"[JOB {job_id}] Extracting topics")
            topics_result = extract_topics(full_text, segments=transcript)
            logger.info(f"[JOB {job_id}] Topic extraction completed")

            update_job(job_id, {
                "results.topics": topics_result,
                "steps.topics": "done",
                "steps.political_analysis": "processing",
            })
        except Exception as e:
            error_msg = f"Topic extraction failed: {str(e)}"
            logger.error(f"[JOB {job_id}] {error_msg}", exc_info=True)
            fail_job(job_id, error_msg, "topics")
            return

        # ============ STEP 5: POLITICAL ANALYSIS ============
        try:
            logger.info(f"[JOB {job_id}] Running political analysis")
            speaker_texts = build_speaker_texts_from_diarized_transcript(transcript)
            political_result = analyse_speaker_politics(speaker_texts)
            logger.info(f"[JOB {job_id}] Political analysis completed")

            update_job(job_id, {
                "results.political_analysis": political_result,
                "steps.political_analysis": "done",
                "status": "done",
                "error": None,
            })
        except Exception as e:
            error_msg = f"Political analysis failed: {str(e)}"
            logger.error(f"[JOB {job_id}] {error_msg}", exc_info=True)
            fail_job(job_id, error_msg, "political_analysis")
            return

        logger.info(f"[JOB {job_id}] Processing completed successfully")

    except Exception as e:
        # Catch-all for unexpected errors
        error_msg = f"Unexpected error during processing: {str(e)}"
        logger.error(f"[JOB {job_id}] {error_msg}", exc_info=True)
        fail_job(job_id, error_msg)


@app.post("/process", status_code=status.HTTP_202_ACCEPTED)
def process(request: JobRequest, background_tasks: BackgroundTasks) -> dict[str, Any]:
    """
    Queue an audio analysis job for processing.
    Returns immediately with job_id; processing happens in background.
    """
    logger.info(f"🎬 JOB RECEIVED: {request.job_id}")
    logger.info(f"📁 File: {request.file_ref}")
    logger.info(f"⏳ Queueing background task...")
    background_tasks.add_task(process_job, request.job_id, request.file_ref)
    logger.info(f"✅ Background task queued!")
    return {"status": "accepted", "job_id": request.job_id}