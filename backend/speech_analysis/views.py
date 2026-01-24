"""
API Views for SpeakSense
"""
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
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

