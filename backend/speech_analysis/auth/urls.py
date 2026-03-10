"""
URL patterns for authentication endpoints
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='auth_register'),
    path('login/', views.login, name='auth_login'),
    path('logout/', views.logout, name='auth_logout'),
    path('profile/', views.profile, name='auth_profile'),
    
    # JWT token refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]