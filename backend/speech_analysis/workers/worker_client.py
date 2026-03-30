"""
Client for dispatching jobs to the external GPU worker.
"""
import requests
import os

GPU_WORKER_URL = os.environ.get("GPU_WORKER_URL", "http://localhost:8001/process")

def dispatch_to_worker(job_id: str, file_path: str):
    """
    Sends a job to the GPU worker for processing.

    Args:
        job_id (str): The ID of the job.
        file_path (str): The path to the audio file.
    
    Returns:
        bool: True if the job was dispatched successfully, False otherwise.
    """
    try:
        payload = {
            "job_id": job_id,
            "file_ref": file_path
        }
        response = requests.post(GPU_WORKER_URL, json=payload, timeout=5) # 5 second timeout

        if response.status_code == 202:
            print(f"Successfully dispatched job {job_id} to GPU worker.")
            return True
        else:
            print(f"Error dispatching job {job_id} to GPU worker. Status: {response.status_code}, Body: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to GPU worker: {e}")
        return False
