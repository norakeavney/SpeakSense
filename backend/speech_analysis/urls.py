"""
URL patterns for speech_analysis app
"""
from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('info/', views.api_info, name='api_info'),
    path('mongodb-test/', views.mongodb_test, name='mongodb_test'),
    
    # Audio upload endpoint
    path('upload/', views.upload_audio, name='upload_audio'),
    
    # Analysis job status endpoint
    path('analysis/<str:job_id>/status/', views.analysis_status, name='analysis_status'),
]
