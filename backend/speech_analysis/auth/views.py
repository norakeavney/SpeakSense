"""
Authentication views for user registration, login, and profile management
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView
from drf_spectacular.utils import extend_schema

from django.contrib.auth.models import User
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer
from speech_analysis.db.mongodb import mongodb
from datetime import datetime


def get_tokens_for_user(user):
    """Generate JWT tokens for user"""
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


def create_user_profile_in_mongodb(user):
    """Create user profile in MongoDB"""
    try:
        db = mongodb.connect()
        users_collection = db['users']
        
        profile_document = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'profile': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'organization': '',
                'created_at': datetime.utcnow(),
                'last_login': None
            },
            'preferences': {
                'youtube_sharing_enabled': True,  # Default: allow YouTube sharing
                'notification_preferences': {
                    'email_on_completion': True
                }
            },
            'stats': {
                'total_analyses': 0,
                'total_audio_time': 0
            }
        }
        
        users_collection.insert_one(profile_document)
        # profile created (info)
        
    except Exception as e:
        print(f"Failed to create MongoDB profile: {e}")


@extend_schema(
    request=UserRegistrationSerializer,
    responses={201: dict, 400: dict},
    description="Register a new user account"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """User registration endpoint"""
    serializer = UserRegistrationSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.save()
        
        # Create MongoDB profile
        create_user_profile_in_mongodb(user)
        
        # Generate tokens
        tokens = get_tokens_for_user(user)
        
        return Response({
            'message': 'User created successfully',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=UserLoginSerializer,
    responses={200: dict, 401: dict},
    description="Login user and get JWT tokens"
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """User login endpoint"""
    serializer = UserLoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Update last login in MongoDB
        try:
            db = mongodb.connect()
            users_collection = db['users']
            users_collection.update_one(
                {'user_id': user.id},
                {'$set': {'profile.last_login': datetime.utcnow()}}
            )
        except Exception as e:
            print(f"Failed to update last login: {e}")
        
        # Generate tokens
        tokens = get_tokens_for_user(user)
        
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name
            },
            'tokens': tokens
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)


@extend_schema(
    responses={200: dict},
    description="Get current user profile information"
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile(request):
    """Get user profile endpoint"""
    user = request.user
    serializer = UserProfileSerializer(user)
    
    # Get additional profile data from MongoDB
    try:
        db = mongodb.connect()
        users_collection = db['users']
        mongodb_profile = users_collection.find_one({'user_id': user.id}, {'_id': 0})
        
        if mongodb_profile:
            profile_data = {
                **serializer.data,
                'preferences': mongodb_profile.get('preferences', {}),
                'stats': mongodb_profile.get('stats', {})
            }
        else:
            profile_data = serializer.data
            
    except Exception as e:
        print(f"Failed to fetch MongoDB profile: {e}")
        profile_data = serializer.data
    
    return Response(profile_data, status=status.HTTP_200_OK)


@extend_schema(
    responses={200: dict},
    description="Logout user (client-side token removal)"
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """Logout endpoint (mainly for consistency - JWT is stateless)"""
    return Response({
        'message': 'Logout successful. Please remove tokens from client storage.'
    }, status=status.HTTP_200_OK)