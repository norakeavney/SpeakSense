"""Serializers for authentication and user profiles."""

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
        )
        extra_kwargs = {"email": {"required": True}}

    def validate(self, attrs):
        """Ensure password and confirmation match."""
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError("Password and password confirmation don't match.")
        return attrs

    def validate_email(self, value):
        """Ensure email is unique."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        """Create a user and remove confirmation field."""
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Authenticate by username or email."""
        username = attrs.get("username")
        password = attrs.get("password")

        if username and password:
            user = authenticate(username=username, password=password)

            if not user:
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    user = None

            if not user:
                raise serializers.ValidationError(
                    {"general": "Invalid username/email or password. Please try again."}
                )

            if not user.is_active:
                raise serializers.ValidationError({"general": "User account is disabled."})

            attrs["user"] = user
        else:
            raise serializers.ValidationError("Must include username/email and password.")

        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for displaying user profile info."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "date_joined",
            "last_login",
        )
        read_only_fields = ("id", "username", "date_joined", "last_login")