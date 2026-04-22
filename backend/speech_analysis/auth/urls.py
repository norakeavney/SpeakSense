"""Auth URL patterns for the `speech_analysis.auth` app."""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

# API endpoints for user registration, login, logout, profile, and token refresh
urlpatterns = [
    path("register/", views.register, name="auth_register"),
    path("login/", views.login, name="auth_login"),
    path("logout/", views.logout, name="auth_logout"),
    path("profile/", views.profile, name="auth_profile"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]