"""
Analysis Jobs Collection Manager
Handles job status tracking and progressive results storage
"""
from datetime import datetime
import uuid
from .mongodb import mongodb


class AnalysisJobManager:
    """Manager for analysis jobs stored in MongoDB"""
    
    COLLECTION_NAME = 'analysis_jobs'
    
    # Job statuses
    STATUS_QUEUED = 'queued'
    STATUS_PROCESSING = 'processing'
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'
    
    # Step statuses
    STEP_PENDING = 'pending'
    STEP_PROCESSING = 'processing'
    STEP_DONE = 'done'
    STEP_FAILED = 'failed'
    
    @staticmethod
    def get_collection():
        """Get the analysis_jobs collection"""
        db = mongodb.connect()
        return db[AnalysisJobManager.COLLECTION_NAME]
    
    @staticmethod
    def create_job(audio_id, audio_path, user_id):
        """
        Create a new analysis job
        
        Args:
            audio_id (str): MongoDB ObjectId of the audio file
            audio_path (str): Local file path to the audio file
            user_id (int): Django User ID who owns this job
            
        Returns:
            str: The job_id (UUID)
        """
        collection = AnalysisJobManager.get_collection()
        
        job_id = str(uuid.uuid4())
        
        job_document = {
            'job_id': job_id,
            'user_id': user_id,  # Track which user owns this job
            'audio_id': audio_id,
            'audio_path': audio_path,
            'status': AnalysisJobManager.STATUS_QUEUED,
            'steps': {
                'transcription': AnalysisJobManager.STEP_PENDING,
                'diarization': AnalysisJobManager.STEP_PENDING,
                'speaker_metrics': AnalysisJobManager.STEP_PENDING,
                'emotion': AnalysisJobManager.STEP_PENDING,
                'topics': AnalysisJobManager.STEP_PENDING,
                'political_analysis': AnalysisJobManager.STEP_PENDING
            },
            'results': {},
            'speaker_confirmations': {},  # Store user-confirmed speaker names
            'error': None,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        collection.insert_one(job_document)
        
        return job_id
    
    @staticmethod
    def get_job(job_id):
        """
        Get job by job_id
        
        Args:
            job_id (str): The job UUID
            
        Returns:
            dict: Job document or None if not found
        """
        collection = AnalysisJobManager.get_collection()
        return collection.find_one({'job_id': job_id}, {'_id': 0})
    
    @staticmethod
    def update_status(job_id, status):
        """
        Update job status
        
        Args:
            job_id (str): The job UUID
            status (str): New status (queued, processing, done, failed)
        """
        collection = AnalysisJobManager.get_collection()
        collection.update_one(
            {'job_id': job_id},
            {
                '$set': {
                    'status': status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    def update_step(job_id, step_name, step_status):
        """
        Update a specific step status
        
        Args:
            job_id (str): The job UUID
            step_name (str): Name of the step (transcription, speaker_metrics, emotion, topics)
            step_status (str): Status (pending, processing, done, failed)
        """
        collection = AnalysisJobManager.get_collection()
        collection.update_one(
            {'job_id': job_id},
            {
                '$set': {
                    f'steps.{step_name}': step_status,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    def update_result(job_id, result_key, result_data):
        """
        Update job results
        
        Args:
            job_id (str): The job UUID
            result_key (str): Key for the result (e.g., 'transcription', 'speaker_metrics')
            result_data: Data to store (dict, list, string, etc.)
        """
        collection = AnalysisJobManager.get_collection()
        collection.update_one(
            {'job_id': job_id},
            {
                '$set': {
                    f'results.{result_key}': result_data,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    def set_error(job_id, error_message):
        """
        Set job error and mark as failed
        
        Args:
            job_id (str): The job UUID
            error_message (str): Error description
        """
        collection = AnalysisJobManager.get_collection()
        collection.update_one(
            {'job_id': job_id},
            {
                '$set': {
                    'status': AnalysisJobManager.STATUS_FAILED,
                    'error': error_message,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    def update_speaker_confirmations(job_id, speaker_names):
        """
        Update confirmed speaker names
        
        Args:
            job_id (str): The job UUID
            speaker_names (dict): Map of speaker_id -> confirmed name
        """
        collection = AnalysisJobManager.get_collection()
        collection.update_one(
            {'job_id': job_id},
            {
                '$set': {
                    'speaker_confirmations': speaker_names,
                    'updated_at': datetime.utcnow()
                }
            }
        )
    
    @staticmethod
    def get_speaker_confirmations(job_id):
        """
        Get confirmed speaker names for a job
        
        Args:
            job_id (str): The job UUID
            
        Returns:
            dict: Map of speaker_id -> confirmed name, or empty dict
        """
        job = AnalysisJobManager.get_job(job_id)
        return job.get('speaker_confirmations', {}) if job else {}
