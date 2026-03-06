from rest_framework import serializers

class AudioUploadSerializer(serializers.Serializer):
    """Validates audio uploads OR YouTube URLs"""

    audio_file = serializers.FileField(
        help_text="Audio file (MP3, WAV, M4A, etc.)",
        required=False
    )

    youtube_url = serializers.URLField(
        required=False,
        help_text="Optional YouTube URL"
    )

    title = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional title for the audio file"
    )

    def validate(self, data):
        """
        Ensure either audio_file OR youtube_url is provided
        """
        if not data.get("audio_file") and not data.get("youtube_url"):
            raise serializers.ValidationError(
                "You must provide either an audio file or a YouTube URL"
            )

        return data


    def validate_audio_file(self, file):
        """Check if file is actually audio"""

        if file is None:
            return file

        # Check file size (max 100MB)
        max_size = 100 * 1024 * 1024
        if file.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Max size is 100MB. Your file: {file.size / (1024*1024):.1f}MB"
            )

        # Allowed extensions
        allowed_extensions = [
        '.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma',
        '.mp4', '.mov', '.mkv', '.webm'
        ]

        file_extension = file.name.lower().split('.')[-1]

        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_extension}' not supported. Allowed: {', '.join(allowed_extensions)}"
            )

        return file