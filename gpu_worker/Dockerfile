FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

WORKDIR /app

# Install system + Python dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    python3.11 \
    python3.11-venv \
    python3-pip \
    libsndfile1 \
    libsndfile1-dev \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1 && \
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

# Upgrade pip
RUN python -m pip install --upgrade pip setuptools wheel

# Install PyTorch with CUDA 12.1 support
RUN pip install torch --index-url https://download.pytorch.org/whl/cu121

# Copy requirements first
COPY requirements.txt .

# Install Python deps
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8001/docs', timeout=5)" || exit 1

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "1"]