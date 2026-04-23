"""URL patterns for the `speech_analysis` app."""

from django.urls import path
from . import views

urlpatterns = [
    # Health & info endpoints
    path('health/', views.health_check, name='health_check'),
    path('info/', views.api_info, name='api_info'),
    path('mongodb-test/', views.mongodb_test, name='mongodb_test'),

    # Upload audio endpoint
    path('upload/', views.upload_audio, name='upload_audio'),

    # Download audio for GPU worker
    path('download/<str:job_id>/', views.download_audio, name='download_audio'),

    # Analysis status endpoint
    path('analysis/<str:job_id>/status/', views.analysis_status, name='analysis_status'),

    # Speaker identification: suggestions & confirmations
    path('analysis/<str:job_id>/speakers/suggestions/', views.get_speaker_suggestions, name='get_speaker_suggestions'),
    path('analysis/<str:job_id>/speakers/confirm/', views.confirm_speakers, name='confirm_speakers'),

    # User report and audio management endpoints
    path('user/reports/', views.user_reports, name='user_reports'),
    path('user/reports/<str:job_id>/', views.user_report_detail, name='user_report_detail'),
    path('user/reports/<str:job_id>/download/', views.download_user_report_pdf, name='download_user_report_pdf'),
    path('user/reports/<str:job_id>/rename/', views.rename_user_report, name='rename_user_report'),
    path('user/reports/<str:job_id>/delete/', views.delete_user_report, name='delete_user_report'),
    path('user/audio/', views.user_audio_files, name='user_audio_files'),
]
