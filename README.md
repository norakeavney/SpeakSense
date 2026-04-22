# SpeakSense – Multi-Speaker Audio Analysis Platform

SpeakSense is an AI-powered system designed to analyse multi-speaker conversational audio and transform it into structured, interpretable insights.

The platform processes raw audio inputs such as debates, interviews, and discussions, automatically extracting transcription, speaker identities, emotional tone, topics, and conversational behaviour metrics.

All outputs are presented through an interactive dashboard, enabling users to explore and understand complex conversations in a clear and meaningful way.

## Live Demo

🚧 **TODO: Add deployed demo link here**

## Getting Started

### Prerequisites

Make sure you have the following installed:

- Python 3.10+
- Node.js (v18+)
- npm or yarn
- MongoDB (local or MongoDB Atlas)
- Git

Optional (recommended for full performance):
- NVIDIA GPU with CUDA support
- Docker & Docker Compose

---

### 1. Clone the Repository

```bash
git clone https://github.com/norakeavney/SpeakSense.git
cd SpeakSense
```

### 2. Backend Setup (Django API)

```bash
cd backend
pip install -r requirements.txt
```

Create a .env file in the backend directory:

```bash
MONGO_URI=your_mongodb_connection_string
GPU_WORKER_URL=http://localhost:8001
```

2. Run the backend server:

```bash
python manage.py runserver
```

Backend will run on:
http://localhost:8000

### 3. Frontend Setup (Next.js)

```bash
cd frontend
npm install
npm run dev
```

Frontend will run on: http://localhost:3000

### 4. GPU Worker Setup (FastAPI + ML Pipeline)

```bash
cd speechlab
pip install -r requirements.txt
```

Create a .env file in the speechlab directory:

```bash
BACKEND_URL=http://localhost:8000
HF_TOKEN=your_huggingface_token
```

Run the GPU worker:

```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

GPU worker runs on: http://localhost:8001

### 5. Running the Full System

Start all components in this order:

- Backend (Django)
- GPU Worker (FastAPI)
- Frontend (Next.js)

Then:

- Open http://localhost:3000
- Upload an audio file or provide a YouTube link
- Wait for processing to complete
- View results in the dashboard

### 6. (Optional) Run with Docker

If Docker is configured:

```bash
docker-compose up --build
```

This will start:

- Backend
- Frontend
- GPU Worker

Notes
- First run may take time due to model downloads (Whisper, pyannote, etc.)
- GPU is strongly recommended for faster processing
- Ensure environment variables are correctly set before running

## Features

- Automatic Speech Recognition (ASR) using OpenAI Whisper  
- Speaker Diarization (multi-speaker identification)  
- Speaker Metrics (speaking time, word count, speaking rate)  
- Emotion Analysis (text-based and audio-based)  
- Topic Extraction using KeyBERT  
- Political Alignment Analysis (zero-shot classification)  
- Interactive Dashboard with visualisations  
- Support for real-world audio (uploaded files or YouTube links (locally))  

## System Architecture

SpeakSense follows a distributed architecture consisting of a frontend, backend API, GPU processing worker, and database.

### High-Level Architecture

![High-Level Architecture](images/sysarchitecture.svg)

### Deployment Architecture (AWS)

![Deployment Architecture](images/DeploymentSysDesign.png)

## Speech Processing Pipeline

The system processes raw audio through a multi-stage pipeline:

1. Audio preprocessing  
2. Speech-to-text transcription (Whisper)  
3. Speaker diarization (pyannote)  
4. Speaker-attributed transcript generation  
5. Feature extraction and analysis:
   - Speaker metrics
   - Emotion detection
   - Topic modelling
   - Political alignment  
6. Structured analytical output generation  

### Pipeline Overview

![Pipeline](images/SSPipeline.png)

## Backend Job Processing Flow

The system uses an asynchronous job-based architecture:

1. User uploads audio  
2. Backend creates an analysis job  
3. Job is dispatched to GPU worker  
4. Worker downloads audio and processes pipeline  
5. Results are stored and returned  
6. Frontend polls for status updates  

![Job Flow](images/BackendSysDesign.png)

## Data Storage Structure

SpeakSense uses MongoDB to store audio metadata and analysis results.

- **Audio Files Collection** – stores uploaded audio references  
- **Analysis Jobs Collection** – tracks processing status and results  

## Dashboard & Outputs

Results are presented through an interactive dashboard, providing both high-level summaries and detailed insights.

### Example Dashboard

![Dashboard](images/Dashboard-SS.png)

### Key Outputs

- Speaker distribution and speaking time  
- Emotion distribution and timeline  
- Topic summaries  
- Bias and conversational balance metrics  
- Word counts and speaking pace  

## Evaluation Summary

SpeakSense successfully demonstrates the transformation of raw conversational audio into structured analytical outputs.

- Accurate multi-speaker transcription and segmentation  
- Meaningful extraction of emotional and topical insights  
- Effective visualisation of conversational dynamics  
- Robust handling of real-world, unstructured audio  

## Future Work

- Improve diarization accuracy for overlapping speech  
- Real-time streaming analysis  
- Enhanced emotion detection using multimodal fusion  
- Expanded political and bias analysis models  
- Mobile and production deployment  

## License

This project is developed as part of a Final Year Project (FYP) in Software Development.
