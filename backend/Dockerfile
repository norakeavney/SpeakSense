# Use a more complete base image for ML/audio dependencies
FROM python:3.12

WORKDIR /app

# Install system dependencies for audio processing and ML libraries
RUN apt-get update && apt-get install -y \
    build-essential \
    ffmpeg \
    libsndfile1-dev \
    libasound2-dev \
    libffi-dev \
    git \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install gunicorn for serving
RUN pip install --no-cache-dir gunicorn

# Copy application code
COPY . .

# Create media directory for uploads
RUN mkdir -p media/audio_uploads

EXPOSE 8000

# Use gunicorn to serve the Django application
CMD ["gunicorn", "speaksense_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120"]