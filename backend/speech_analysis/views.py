"""
API Views for SpeakSense
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter
from datetime import datetime
import os
from pathlib import Path

from speech_analysis.workers.real_processor import start_real_processing
from .serializers import AudioUploadSerializer
from speech_analysis.db.mongodb import mongodb
from speech_analysis.db.analysis_jobs import AnalysisJobManager


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint to verify API and database connectivity
    """
    try:
        # Test MongoDB connection
        db = mongodb.connect()
        
        return Response({
            'status': 'healthy',
            'message': 'SpeakSense API is running',
            'database': 'connected',
            'version': '1.0.0'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'message': str(e),
            'database': 'disconnected'
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


@api_view(['GET'])
def api_info(request):
    """
    API information endpoint
    """
    return Response({
        'name': 'SpeakSense API',
        'description': 'Speech Analysis & Transcription API',
        'version': '1.0.0',
        'endpoints': {
            'health': '/api/health/',
            'info': '/api/info/',
            'docs': '/api/docs/',
        }
    })


@api_view(['GET'])
def mongodb_test(request):
    """Test MongoDB connection"""
    try:
        db = mongodb.connect()
        # Try to list collections
        collections = db.list_collection_names()
        
        return Response({
            'status': 'success',
            'message': 'MongoDB connection successful!',
            'database': 'speaksense_db',
            'collections': collections
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'message': 'MongoDB connection failed',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    request=AudioUploadSerializer,
    responses={201: dict},
    description="Upload an audio file for speech analysis"
)

@api_view(['POST'])
def upload_audio(request):
    """
    Upload audio file endpoint
    
    Accepts audio files and saves them for processing
    """
    
    # Validate the uploaded file
    serializer = AudioUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid file',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the validated file
    audio_file = serializer.validated_data['audio_file']
    title = serializer.validated_data.get('title', audio_file.name)
    
    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    original_name = audio_file.name
    file_extension = original_name.split('.')[-1]
    unique_filename = f"{timestamp}_{original_name}"
    
    # Save file to disk
    file_path = Path('media/audio_uploads') / unique_filename
    
    with open(file_path, 'wb+') as destination:
        for chunk in audio_file.chunks():
            destination.write(chunk)
        destination.flush()  # Ensure file is written to disk
        os.fsync(destination.fileno())  # Force OS to write to disk
    
    # Verify file exists and has size
    if not file_path.exists() or file_path.stat().st_size == 0:
        return Response({
            'error': 'File upload failed - file not saved properly'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Save metadata to MongoDB
    db = mongodb.connect()
    audio_collection = db['audio_files']
    
    audio_document = {
        'title': title,
        'original_filename': original_name,
        'saved_filename': unique_filename,
        'file_path': str(file_path),
        'file_size': audio_file.size,
        'file_extension': file_extension,
        'uploaded_at': datetime.utcnow(),
        'status': 'uploaded',  # uploaded, processing, completed, failed
        'transcript': None,
        'speakers': None,
        'emotions': None
    }
    
    result = audio_collection.insert_one(audio_document)
    
    # Create analysis job
    job_id = AnalysisJobManager.create_job(
        audio_id=str(result.inserted_id),
        audio_path=str(file_path)
    )
    
    # Start background processing
    start_real_processing(job_id, str(file_path))
    
    # Return success response
    return Response({
        'message': 'Audio file uploaded successfully!',
        'file_id': str(result.inserted_id),
        'job_id': job_id,
        'status': 'queued',
        'filename': unique_filename,
        'size': f"{audio_file.size / (1024*1024):.2f} MB",
        'title': title
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def analysis_status(request, job_id):
    """
    Get analysis job status and results
    
    Args:
        job_id (str): UUID of the analysis job
        
    Returns:
        JSON with status, steps, and available results
    """
    try:
        # Fetch job from MongoDB
        job = AnalysisJobManager.get_job(job_id)
        
        if not job:
            return Response({
                'error': 'Job not found',
                'job_id': job_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Return job status and results
        return Response({
            'job_id': job['job_id'],
            'status': job['status'],
            'steps': job['steps'],
            'results': job.get('results', {}),
            'speaker_confirmations': job.get('speaker_confirmations', {}),
            'error': job.get('error'),
            'created_at': job['created_at'].isoformat() if job.get('created_at') else None,
            'updated_at': job['updated_at'].isoformat() if job.get('updated_at') else None
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch job status',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def confirm_speakers(request, job_id):
    """
    Confirm speaker identities with user-provided names
    
    Expects JSON body:
    {
        "speakers": {
            "SPEAKER_00": "John Doe",
            "SPEAKER_01": "Jane Smith"
        }
    }
    
    Args:
        job_id (str): UUID of the analysis job
        
    Returns:
        JSON confirmation response
    """
    try:
        # Validate job exists
        job = AnalysisJobManager.get_job(job_id)
        
        if not job:
            return Response({
                'error': 'Job not found',
                'job_id': job_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get speaker names from request
        speaker_names = request.data.get('speakers', {})
        
        if not speaker_names:
            return Response({
                'error': 'No speaker names provided',
                'details': 'Expected "speakers" field with speaker_id -> name mapping'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate that we have diarization results
        diarization = job.get('results', {}).get('diarization')
        if not diarization:
            return Response({
                'error': 'No diarization results found',
                'details': 'Diarization must be complete before confirming speakers'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Update speaker confirmations
        AnalysisJobManager.update_speaker_confirmations(job_id, speaker_names)
        
        # Update diarization results with confirmed names
        confirmed_diarization = diarization.copy()
        confirmed_diarization['confirmed_speakers'] = speaker_names
        confirmed_diarization['status'] = 'confirmed'
        AnalysisJobManager.update_result(job_id, 'diarization', confirmed_diarization)
        
        return Response({
            'message': 'Speaker identities confirmed successfully',
            'job_id': job_id,
            'confirmed_speakers': speaker_names,
            'num_speakers': len(speaker_names)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to confirm speakers',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_speaker_suggestions(request, job_id):
    """
    Get AI-generated speaker name suggestions for a job
    
    Args:
        job_id (str): UUID of the analysis job
        
    Returns:
        JSON with speaker suggestions and reasoning
    """
    try:
        # Fetch job from MongoDB
        job = AnalysisJobManager.get_job(job_id)
        
        if not job:
            return Response({
                'error': 'Job not found',
                'job_id': job_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get diarization results
        diarization = job.get('results', {}).get('diarization')
        
        if not diarization:
            return Response({
                'error': 'Diarization not yet complete',
                'job_id': job_id
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Return suggestions
        suggestions = diarization.get('suggestions', {})
        
        return Response({
            'job_id': job_id,
            'suggestions': suggestions,
            'num_speakers': len(suggestions),
            'requires_confirmation': diarization.get('requires_user_confirmation', True)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch speaker suggestions',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
