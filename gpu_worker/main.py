from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
from pymongo import MongoClient
import time
import os
from dotenv import load_dotenv
from ml.emotion_analysis import analyse_emotions
from ml.speech_service import analyse_audio
from ml.topic_extraction import extract_topics
from ml.political_analysis import run_political

load_dotenv()

app = FastAPI()

# Mongo connection (use same URI as Django)
client = MongoClient(os.getenv("MONGODB_URI"))
db = client["speaksense_db"]
jobs_collection = db["analysis_jobs"]


class JobRequest(BaseModel):
    job_id: str
    file_ref: str


def process_job(job_id: str, file_ref: str):
    print(f"Processing job: {job_id}")

    # Step 1: mark as processing
    jobs_collection.update_one(
        {"job_id": job_id},
        {"$set": {"status": "processing"}}
    )

    # Simulate ML work
    transcription = analyse_audio(file_ref, include_diarization=False)
    diarization = analyse_audio(file_ref, include_diarization=True)
    metrics = compute_metrics(transcription, diarization)
    emotion = analyse_emotions(transcription)
    topics = extract_topics(transcription)
    politics = run_political(transcription) 

    # Step 2: mark as done
    jobs_collection.update_one(
    {"job_id": job_id},
    {
        "$set": {
            "status": "done",

            # RESULTS
            "results.transcription": transcription,
            "results.diarization": diarization,

            # STEPS (THIS IS WHY UI IS STUCK)
            "steps.transcription": "completed",
            "steps.diarization": "completed",
            "steps.speaker_metrics": "completed",
            "steps.emotion": "completed",
            "steps.topics": "completed",
            "steps.political_analysis": "completed"
        }
    }
)
    print(f"Finished job: {job_id}")


@app.post("/process")
def process(request: JobRequest, background_tasks: BackgroundTasks):
    background_tasks.add_task(process_job, request.job_id, request.file_ref)

    return {"status": "accepted"}