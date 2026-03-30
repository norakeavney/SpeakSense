# ============================================================
# GPU Worker Container - CUDA/GPU-optimized
# Runs on GPU EC2 instance for ML inference
# ============================================================

FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

# Install Python 3.11 and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    git \
    libsndfile1 \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Use Python 3.11 by default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
# Note: torch and related packages from requirements.txt will use CUDA wheels automatically
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/docs', timeout=5)" || exit 1

# Expose port for GPU worker API
EXPOSE 8001

# Run uvicorn server with GPU support
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]
