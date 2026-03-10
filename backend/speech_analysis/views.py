"""
API Views for SpeakSense
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema
from datetime import datetime, timezone
import os
from pathlib import Path
from django.conf import settings

from speech_analysis.workers.real_processor import start_real_processing
from .serializers import AudioUploadSerializer
from speech_analysis.db.mongodb import mongodb
from speech_analysis.db.analysis_jobs import AnalysisJobManager
from speech_analysis.utils.youtube import download_youtube_audio
from speech_analysis.utils.media import normalise_audio
from bson import ObjectId


@api_view(['GET'])
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
@permission_classes([AllowAny])
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
@permission_classes([IsAuthenticated])
def upload_audio(request):
    """
    Upload audio file endpoint
    
    Accepts audio files and saves them for processing
    Requires authentication - links files to user account
    """
    
    # Validate the uploaded file
    serializer = AudioUploadSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            'error': 'Invalid file',
            'details': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get the validated file
    audio_file = serializer.validated_data.get('audio_file')
    youtube_url = serializer.validated_data.get('youtube_url')
    title = serializer.validated_data.get('title')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # If YouTube link
    if youtube_url:
        audio_upload_dir = Path(settings.MEDIA_ROOT) / 'audio_uploads'
        audio_upload_dir.mkdir(parents=True, exist_ok=True)

        try:
            downloaded_file = download_youtube_audio(
                youtube_url,
                str(audio_upload_dir)
            )

            file_path = Path(downloaded_file)
            original_name = file_path.name
            file_extension = ".wav"

        except Exception as e:
            return Response({
                "error": "Failed to download YouTube audio",
                "details": str(e)
            }, status=400)

    # If normal audio upload
    else:
        original_name = audio_file.name
        file_extension = original_name.split('.')[-1]
        unique_filename = f"{timestamp}_{original_name}"
        file_path = Path(settings.MEDIA_ROOT) / 'audio_uploads' / unique_filename
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'wb+') as destination:
            for chunk in audio_file.chunks():
                destination.write(chunk)
            destination.flush()  # Ensure file is written to disk
            os.fsync(destination.fileno())  # Force OS to write to disk

    # Convert video if necessary
    video_extensions = ['mp4', 'mov', 'mkv', 'webm']

    if file_extension.lower() in video_extensions:
        file_path = Path(normalise_audio(file_path))
        file_extension = 'wav'

    # Verify file exists and has size
    if not file_path.exists() or file_path.stat().st_size == 0:
        return Response({
            'error': 'File upload failed - file not saved properly'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

    # Save metadata to MongoDB
    db = mongodb.connect()
    audio_collection = db['audio_files']
    
    audio_document = {
        'user_id': request.user.id,  # Link to authenticated user
        'title': title,
        'original_filename': original_name,
        'saved_filename': file_path.name,
        'file_path': str(file_path),
        'file_size': file_path.stat().st_size,
        'file_extension': file_extension,
        'uploaded_at': datetime.now(timezone.utc),
        'status': 'uploaded',  # uploaded, processing, completed, failed
        'transcript': None,
        'speakers': None,
        'emotions': None
    }
    
    result = audio_collection.insert_one(audio_document)

    
    # Create analysis job
    job_id = AnalysisJobManager.create_job(
        audio_id=str(result.inserted_id),
        audio_path=str(file_path),
        user_id=request.user.id  # Pass user ID to job
    )
    
    # Start background processing
    start_real_processing(job_id, str(file_path))
    
    # Return success response
    return Response({
        'message': 'Audio file uploaded successfully!',
        'file_id': str(result.inserted_id),
        'job_id': job_id,
        'status': 'queued',
        'filename': file_path.name,
        'size': f"{file_path.stat().st_size / (1024*1024):.2f} MB",
        'title': title
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
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
        
        # Check if job belongs to authenticated user
        if job.get('user_id') != request.user.id:
            return Response({
                'error': 'Access denied - not your job',
                'job_id': job_id
            }, status=status.HTTP_403_FORBIDDEN)
        
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
@permission_classes([IsAuthenticated])
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
        
        # Check if job belongs to authenticated user
        if job.get('user_id') != request.user.id:
            return Response({
                'error': 'Access denied - not your job',
                'job_id': job_id
            }, status=status.HTTP_403_FORBIDDEN)
        
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


# ============================================
# USER-SPECIFIC ENDPOINTS
# ============================================

@extend_schema(
    responses={200: dict},
    description="Get all analysis reports for the authenticated user"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_reports(request):
    """
    Get all analysis jobs/reports for the authenticated user
    """
    try:
        db = mongodb.connect()
        jobs_collection = db['analysis_jobs']
        
        # Get all jobs for this user
        user_jobs = list(jobs_collection.find(
            {'user_id': request.user.id},
            {'_id': 0}
        ).sort('created_at', -1))
        
        # Also get associated audio file info
        audio_collection = db['audio_files']
        
        # Enrich jobs with audio file details
        for job in user_jobs:
            try:
                audio_info = audio_collection.find_one(
                    {'_id': ObjectId(job['audio_id'])},
                    {'title': 1, 'original_filename': 1, 'file_size': 1, 'uploaded_at': 1}
                )
                if audio_info:
                    job['audio_info'] = {
                        'title': audio_info.get('title', 'Untitled'),
                        'filename': audio_info.get('original_filename', ''),
                        'size': audio_info.get('file_size', 0),
                        'uploaded_at': audio_info.get('uploaded_at')
                    }
            except Exception:
                # Handle invalid ObjectId gracefully
                job['audio_info'] = {'title': 'Unknown', 'filename': '', 'size': 0}
        
        return Response({
            'reports': user_jobs,
            'total_count': len(user_jobs)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch user reports',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={200: dict, 404: dict},
    description="Get a specific analysis report for the authenticated user"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_report_detail(request, job_id):
    """
    Get detailed information about a specific report/job
    """
    try:
        # Fetch job from MongoDB
        job = AnalysisJobManager.get_job(job_id)
        
        if not job:
            return Response({
                'error': 'Report not found',
                'job_id': job_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if job belongs to authenticated user
        if job.get('user_id') != request.user.id:
            return Response({
                'error': 'Access denied - not your report',
                'job_id': job_id
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Get associated audio file info
        db = mongodb.connect()
        audio_collection = db['audio_files']
        try:
            audio_info = audio_collection.find_one(
                {'_id': ObjectId(job['audio_id'])},
                {'_id': 0}
            )
        except Exception:
            audio_info = None
        
        return Response({
            'report': job,
            'audio_file': audio_info
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch report details',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={200: dict, 404: dict},
    description="Delete a specific analysis report for the authenticated user"
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user_report(request, job_id):
    """
    Delete a user's analysis report and associated audio file
    """
    try:
        # Fetch job from MongoDB
        job = AnalysisJobManager.get_job(job_id)
        
        if not job:
            return Response({
                'error': 'Report not found',
                'job_id': job_id
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if job belongs to authenticated user
        if job.get('user_id') != request.user.id:
            return Response({
                'error': 'Access denied - not your report',
                'job_id': job_id
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Delete from MongoDB
        db = mongodb.connect()
        
        # Delete analysis job
        jobs_collection = db['analysis_jobs']
        jobs_collection.delete_one({'job_id': job_id})
        
        # Delete associated audio file record
        audio_collection = db['audio_files']
        try:
            audio_info = audio_collection.find_one({'_id': ObjectId(job['audio_id'])})
            if audio_info:
                # Delete physical file
                audio_file_path = Path(audio_info.get('file_path', ''))
                if audio_file_path.exists():
                    audio_file_path.unlink()
                
                # Delete database record
                audio_collection.delete_one({'_id': ObjectId(job['audio_id'])})
        except Exception as e:
            print(f"Failed to delete audio file: {e}")
        
        return Response({
            'message': 'Report deleted successfully',
            'job_id': job_id
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to delete report',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@extend_schema(
    responses={200: dict},
    description="Get all uploaded audio files for the authenticated user"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_audio_files(request):
    """
    Get all uploaded audio files for the authenticated user
    """
    try:
        db = mongodb.connect()
        audio_collection = db['audio_files']
        
        # Get all audio files for this user
        user_files = list(audio_collection.find(
            {'user_id': request.user.id},
            {'_id': 0}
        ).sort('uploaded_at', -1))
        
        return Response({
            'audio_files': user_files,
            'total_count': len(user_files)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to fetch user audio files',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
