# SpeakSense 3-Container Deployment Architecture

## Overview
SpeakSense is deployed across **two separate EC2 instances** with **3 total containers**:

### CPU Instance (Primary)
Host application server and frontend UI
- **Port 3000**: Frontend (Next.js)
- **Port 8000**: Backend API (Django REST)
- **Port 9000**: Portainer (container management)

### GPU Instance (Compute)
Host ML inference engine
- **Port 8001**: GPU Worker (FastAPI)

---

## Deployment Setup

### 1. CPU EC2 Instance Setup

**Prerequisites:**
- Docker & Docker Compose installed
- Python 3.9+ (for local development)
- 4GB+ RAM recommended

**Deployment:**
```bash
# Clone repository to CPU instance
git clone <repo-url> /opt/speaksense
cd /opt/speaksense

# Create .env file with configuration
cp .env.example .env

# Edit .env with:
MONGODB_URI=<your-mongodb-connection-string>
GPU_WORKER_URL=http://<GPU_INSTANCE_PRIVATE_IP>:8001/process
DJANGO_SECRET_KEY=<generate-new-key>

# Deploy with docker-compose (runs frontend + backend)
docker-compose up -d

# Verify services
docker ps
curl http://localhost:8000/api/health
curl http://localhost:3000
```

**Environment Variables (.env):**
```
# MongoDB - for job tracking and results storage
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/speaksense_db

# GPU Worker - backend communicates with this endpoint
GPU_WORKER_URL=http://10.0.1.100:8001/process

# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,*.compute.amazonaws.com

# Frontend (optional override)
NEXT_PUBLIC_API_URL=https://api.your-domain.com
```

---

### 2. GPU EC2 Instance Setup

**Prerequisites:**
- GPU EC2 instance type: `g4dn.xlarge` or better (NVIDIA GPU)
- NVIDIA CUDA drivers installed
- Docker with NVIDIA Container Runtime
- At least 40GB disk space (for models)

**Installation Steps:**

```bash
# 1. Install NVIDIA drivers and CUDA support
sudo apt-get update
sudo apt-get install -y nvidia-docker2 nvidia-container-runtime
sudo systemctl restart docker

# 2. Clone repository
git clone <repo-url> /opt/speaksense-gpu
cd /opt/speaksense-gpu/gpu_worker

# 3. Create environment file
cat > .env << EOF
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/speaksense_db
EOF

# 4. Deploy GPU worker container
docker-compose -f docker-compose.yml up -d

# 5. Verify GPU access
docker exec ss-gpu-worker nvidia-smi
```

**GPU Worker Docker Compose** (in gpu_worker/docker-compose.yml):
- Runs only the GPU worker FastAPI server
- Exposes port 8001 to backend
- Uses nvidia/cuda base image
- Requires NVIDIA Docker runtime

---

## Communication Flow

### Job Processing Pipeline:

```
Frontend (3000)
  ↓
Backend API (8000)
  ├─ Validates upload
  ├─ Creates MongoDB job record
  ├─ Returns job_id immediately
  │
  └─→ HTTP POST to GPU Worker (8001)
        ↓
        GPU Worker Processing:
        1. Speech-to-Text (Whisper)
        2. Speaker Diarization (Pyannote)
        3. Speaker Metrics (VADER/TextBlob)
        4. Emotion Analysis (DistilBERT)
        5. Topic Extraction (KeyBERT)
        6. Political Analysis (BART MNLI)
        ↓
        Results → MongoDB
        ↓
      Frontend polls Backend for results
        ↓
      Display complete analysis
```

### Cross-Instance Communication:

**Backend → GPU Worker:**
```
POST http://{GPU_INSTANCE_PRIVATE_IP}:8001/process
Content-Type: application/json

{
  "job_id": "job_abc123",
  "file_ref": "/path/to/audio.wav"
}

Response (202 Accepted):
{
  "status": "accepted",
  "job_id": "job_abc123"
}
```

**Status Polling (Frontend → Backend):**
```
GET http://backend:8000/api/jobs/{job_id}/status

Returns:
{
  "job_id": "job_abc123",
  "status": "processing",  // or "done", "failed"
  "steps": {
    "transcription": "completed",
    "diarization": "completed",
    "speaker_metrics": "processing",
    "emotion": "pending",
    "topics": "pending",
    "political_analysis": "pending"
  },
  "results": {
    "transcription": {...},
    "speaker_metrics": {...},
    ...
  }
}
```

---

## Network Configuration

### Security Group Rules (AWS)

**CPU Instance:**
- Inbound: 443 (HTTPS from anywhere)
- Inbound: 80 (HTTP from anywhere)
- Inbound: 3000 (Frontend, restrict to known IPs if possible)
- Inbound: 8000 (Backend, restrict to known IPs if possible)
- Outbound: All (to MongoDB, GPU worker)

**GPU Instance:**
- Inbound: 8001 (GPU Worker, only from CPU instance private IP)
- Outbound: MongoDB (for result storage)

### VPC Setup (Recommended):

```
VPC Internal Network:
├─ CPU Subnet (10.0.0.0/24)
│  ├─ Backend: 10.0.0.10:8000
│  ├─ Frontend: 10.0.0.11:3000
│  └─ Portainer: 10.0.0.12:9000
│
└─ GPU Subnet (10.0.1.0/24)
   └─ GPU Worker: 10.0.1.100:8001 (internal only)

NAT/ALB for external traffic to frontend/backend
```

---

## Monitoring & Logging

### CPU Instance Health Checks:

```bash
# Check all services
docker ps
docker logs ss-backend
docker logs ss-frontend
docker logs portainer

# Monitor GPU worker connectivity
curl http://{GPU_INSTANCE_PRIVATE_IP}:8001/docs
```

### GPU Instance Health Checks:

```bash
# Check GPU worker
docker logs ss-gpu-worker

# Verify GPU access
docker exec ss-gpu-worker nvidia-smi

# Check model loading
docker exec ss-gpu-worker curl http://localhost:8001/docs
```

### Logs Location:
- Backend: `docker logs ss-backend`
- GPU Worker: `docker logs ss-gpu-worker`
- Application logs: Check MongoDB for job status details

---

## MongoDB Schema

Jobs collection stores processing state and results:

```javascript
{
  job_id: "job_abc123",
  status: "done",  // processing, done, failed
  created_at: ISODate(),
  updated_at: ISODate(),
  error: null,
  steps: {
    transcription: "completed",
    diarization: "completed",
    speaker_metrics: "completed",
    emotion: "completed",
    topics: "completed",
    political_analysis: "completed"
  },
  results: {
    transcription: {...},
    diarization: {...},
    speaker_metrics: {...},
    emotion: {...},
    topics: {...},
    political_analysis: {...}
  }
}
```

---

## Troubleshooting

### GPU Worker Not Responding

```bash
# Check connectivity from CPU instance
ssh ec2-user@gpu-instance
curl http://localhost:8001/docs

# Check GPU availability
nvidia-smi

# Check logs
docker logs ss-gpu-worker

# Restart service
docker-compose restart gpu_worker
```

### Audio Processing Timeout

- Increase timeout in backend job queue (currently 5 seconds for submission)
- Check GPU instance disk space (models and audio files)
- Monitor GPU memory: `nvidia-smi`

### Memory Issues

- Increase GPU instance type (g4dn.12xlarge for larger files)
- Enable disk caching for models
- Consider model quantization for reduced memory usage

---

## Scaling Considerations

1. **Multiple GPUs on GPU Instance:**
   - Set `CUDA_VISIBLE_DEVICES=0,1,2` in environment
   - Run multiple GPU worker containers (one per GPU)

2. **Multiple GPU Instances:**
   - Create load balancer pointing to multiple GPU workers
   - Backend submits to round-robin URL

3. **Queue System:**
   - Add Redis/RabbitMQ for job queuing
   - GPU workers pull from queue instead of direct HTTP

---

## Deployment Checklist

- [ ] CPU EC2 instance provisioned (t3.large+ recommended)
- [ ] GPU EC2 instance provisioned (g4dn.xlarge+)
- [ ] Both instances in same VPC
- [ ] Security groups configured for cross-instance communication
- [ ] MongoDB instance or Atlas cluster created
- [ ] `.env` file configured on both instances
- [ ] Docker & nvidia-docker installed on GPU instance
- [ ] `docker-compose up -d` run on CPU instance
- [ ] `docker-compose -f gpu_worker/docker-compose.yml up -d` run on GPU instance
- [ ] Health checks passing: Frontend (3000), Backend (8000), GPU Worker (8001)
- [ ] Job submitted and tracked end-to-end
