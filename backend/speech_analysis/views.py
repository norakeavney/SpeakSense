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
from .serializers import AudioUploadSerializer
from speech_analysis.db.mongodb import mongodb


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
    
    # Return success response
    return Response({
        'message': 'Audio file uploaded successfully!',
        'file_id': str(result.inserted_id),
        'filename': unique_filename,
        'size': f"{audio_file.size / (1024*1024):.2f} MB",
        'title': title
    }, status=status.HTTP_201_CREATED)

