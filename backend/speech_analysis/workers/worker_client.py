"""
Client for dispatching jobs to the external GPU worker.
"""
import requests
import os

GPU_WORKER_URL = os.environ.get("GPU_WORKER_URL")
BACKEND_URL = os.environ.get("BACKEND_URL")

def dispatch_to_worker(job_id: str, file_path: str):
    """
    Sends a job to the GPU worker for processing.
    
    The GPU worker will download the audio file from Backend instead of
    receiving it locally, allowing it to work across separate instances.

    Args:
        job_id (str): The ID of the job.
        file_path (str): The local path to the audio file (unused, kept for compatibility).
    
    Returns:
        bool: True if the job was dispatched successfully, False otherwise.
    """

    try:
        # Construct download URL for GPU Worker to fetch the file
        download_url = f"{BACKEND_URL}/download/{job_id}/"
        
        payload = {
            "job_id": job_id,
            "file_url": download_url
        }
        response = requests.post(GPU_WORKER_URL, json=payload, timeout=10)

        if response.status_code == 202:
            print(f"Successfully dispatched job {job_id} to GPU worker.")
            return True
        else:
            print(f"Error dispatching job {job_id} to GPU worker. Status: {response.status_code}, Body: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to GPU worker: {e}")
        return False
