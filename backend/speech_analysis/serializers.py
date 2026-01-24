from rest_framework import serializers

class AudioUploadSerializer(serializers.Serializer):
    """Validates audio file uploads"""
    
    audio_file = serializers.FileField(
        help_text="Audio file (MP3, WAV, M4A, etc.)",
        required=True
    )
    
    title = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text="Optional title for the audio file"
    )
    
    def validate_audio_file(self, file):
        """Check if file is actually audio"""
        
        # Check file size (max 100MB)
        max_size = 100 * 1024 * 1024  # 100MB in bytes
        if file.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Max size is 100MB. Your file: {file.size / (1024*1024):.1f}MB"
            )
        
        # Check file extension
        allowed_extensions = ['.mp3', '.wav', '.m4a', '.ogg', '.flac', '.aac', '.wma']
        file_extension = file.name.lower().split('.')[-1]
        
        if f'.{file_extension}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type '.{file_extension}' not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        return file