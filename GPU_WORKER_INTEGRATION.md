# GPU Worker Integration Summary

## Changes Made

### 1. **GPU Worker Now Runs Complete ML Pipeline**

The GPU worker (`gpu_worker/main.py`) now executes all 6 steps:

```
Step 1: Speech Analysis (Whisper + Pyannote)
  ↓
Step 2: Speaker Metrics (VADER sentiment + TextBlob analysis) ← NEW
  ↓
Step 3: Emotion Analysis (DistilBERT)
  ↓
Step 4: Topic Extraction (KeyBERT)
  ↓
Step 5: Political Analysis (BART MNLI)
  ↓
All results → MongoDB
```

### 2. **Files Created**

| File | Purpose |
|------|---------|
| `gpu_worker/ml/speaker_metrics.py` | Speaker metrics calculation (700+ lines) |
| `gpu_worker/requirements.txt` | Python dependencies for GPU worker |
| `gpu_worker/Dockerfile` | CUDA 12.1 container for GPU execution |
| `gpu_worker/docker-compose.yml` | Standalone compose for GPU instance |
| `DEPLOYMENT.md` | Complete deployment architecture guide |

### 3. **Files Modified**

| File | Changes |
|------|---------|
| `gpu_worker/main.py` | Added speaker_metrics import + processing step |
| | Improved error handling with per-step exceptions |
| | Added proper logging throughout pipeline |
| | MongoDB connection lifecycle management |

---

## Key Improvements

### Error Handling & Resilience
- ✅ Each pipeline step is independently wrapped in try/catch
- ✅ Step failures don't cascade to subsequent steps
- ✅ Specific error messages logged for debugging
- ✅ Failed steps are marked in MongoDB for visibility

### Logging & Observability
- ✅ Structured logging with timestamps and log levels
- ✅ Job start/completion/failure logged at INFO level
- ✅ Full tracebacks logged at ERROR level
- ✅ Step transitions tracked for monitoring

### Architecture
- ✅ Speaker metrics (CPU-bound) runs on GPU instance for load distribution
- ✅ Frontend + Backend on one CPU EC2 instance
- ✅ GPU Worker on separate GPU EC2 instance
- ✅ HTTP-based communication for scalability

### Dependencies
- ✅ TextBlob & VADER included for sentiment analysis
- ✅ All optional imports handled gracefully
- ✅ Clear warnings if libraries unavailable
- ✅ Fallback mechanisms for missing dependencies

---

## Speaker Metrics Functionality

The `calculate_speaker_metrics()` function analyzes:

### Per-Speaker Metrics:
- Speaking time (seconds) & words per minute (WPM)
- Turn count and average turn duration
- Vocabulary: unique words, lexical diversity, avg word length
- Filler words & filler rate
- Sentiment (positive/negative/neutral)
- Question/statement ratio and likely role (interviewer/moderator/interviewee)

### Comparative Metrics:
- Time distribution across speakers (%)
- Most/least talkative speakers
- Fastest/slowest speakers
- Balance score (0=balanced, 1=imbalanced)

### Deep Analysis:
- Agreement/disagreement detection
- Leading questions (bias indicators)
- Interruption patterns & dominance scores
- Comprehensive bias metrics (0-100 score)

### Bias Analysis:
- Identifies moderator vs candidates
- Evaluates fairness: time distribution, question balance
- Detects moderator sentiment bias
- Flags leading questions and communication style

---

## Database Schema (MongoDB)

Job document now includes speaker_metrics results:

```javascript
{
  job_id: "job_abc123",
  status: "done",
  steps: {
    transcription: "completed",
    diarization: "completed",
    speaker_metrics: "completed",  // NEW STEP
    emotion: "completed",
    topics: "completed",
    political_analysis: "completed"
  },
  results: {
    speaker_metrics: {
      speakers: {
        SPEAKER_00: {
          speaking_time_seconds: 125.45,
          words_per_minute: 185.3,
          total_words: 385,
          filler_words: 12,
          // ... more metrics
        }
      },
      comparative: {
        time_distribution: { SPEAKER_00: 45.2, SPEAKER_01: 54.8 },
        balance_score: 0.095,
        balance_interpretation: "Well balanced conversation"
        // ...
      },
      bias_analysis: {
        overall_bias_score: 23.4,
        bias_level: "LOW",
        moderator: { speaker: "SPEAKER_00", ... },
        candidates: { SPEAKER_01: {...} },
        // ...
      }
    }
  }
}
```

---

## Deployment Architecture

### CPU Instance (t3.large+)
```
Frontend (Next.js)          :3000
Backend API (Django)        :8000  → POST /api/jobs/
Portainer (Management)      :9000

Background: Worker polls GPU instance
```

### GPU Instance (g4dn.xlarge+)
```
GPU Worker (FastAPI)        :8001  ← POST /process
  Runs: Speech → Diarization → Metrics → Emotion → Topics → Politics
  Stores results in MongoDB
```

### Communication
```
Frontend → Backend (HTTP)
  Submit job → Returns job_id immediately
  Poll status ← Backend queries MongoDB
  
Backend → GPU Worker (HTTP)
  background_tasks.add_task(process_job, job_id, file_ref)
  Submits: POST /process with job_id + file_ref
  
GPU Worker → MongoDB
  Stores all results and step statuses
```

---

## Verification Checklist

### Local Testing (Before Deployment)

```bash
# 1. Verify GPU worker imports
cd gpu_worker
python -c "from ml.speaker_metrics import calculate_speaker_metrics; print('✓ Import OK')"

# 2. Check syntax
python -m py_compile main.py ml/speaker_metrics.py

# 3. Verify requirements
pip install -r requirements.txt  # Should complete without errors

# 4. Build Dockerfile
docker build -t speaksense-gpu-worker .

# 5. Run test
docker run --rm speaksense-gpu-worker python -c "from ml.speaker_metrics import calculate_speaker_metrics; print('✓ Container OK')"
```

### Deployment Verification

```bash
# On GPU Instance
docker-compose -f gpu_worker/docker-compose.yml up -d
docker logs ss-gpu-worker
# Should see: "Application startup complete"

# Verify endpoint
curl http://localhost:8001/docs

# Check GPU access
docker exec ss-gpu-worker nvidia-smi

# On CPU Instance
curl -X POST http://{GPU_IP}:8001/process \
  -H "Content-Type: application/json" \
  -d '{"job_id": "test_123", "file_ref": "/path/to/test.wav"}'
# Should return: {"status": "accepted", "job_id": "test_123"}
```

---

## Performance Characteristics

### GPU Worker Step Timing (Estimates)

| Step | GPU Time | CPU Time | Input |
|------|----------|----------|-------|
| Transcription | 0.3x* | 2-3x | 60s audio = 30s |
| Diarization | 0.4x* | 4-5x | 60s audio = 40s |
| Speaker Metrics | - | 1-2s | transcript |
| Emotion | 0.2x* | 3-4x | 60 segments |
| Topics | - | 2-3s | full text |
| Political | 0.1x* | 5-10s | speaker texts |
| **Total (60s audio)** | **~15s** | **~20-30s** | - |

*GPU speedup factor vs CPU

### Resource Requirements

- **GPU Memory**: 8GB+ (for Whisper + Pyannote + DistilBERT)
- **CPU**: 4 cores dedicated to GPU worker
- **Disk**: 40GB+ for model cache
- **Network**: 100Mbps sufficient

---

## Troubleshooting

### "Module not found: speaker_metrics"
```bash
# Ensure file exists
ls -la gpu_worker/ml/speaker_metrics.py

# Check Python path
docker exec ss-gpu-worker python -c "import sys; print(sys.path)"
```

### Speaker metrics missing from results
```bash
# Check step status in MongoDB
db.analysis_jobs.findOne({ job_id: "job_abc" })
# Look for steps.speaker_metrics status
```

### VADER/TextBlob errors
```bash
# These are optional - check logs
docker logs ss-gpu-worker | grep -i "vader\|textblob"

# Should fallback gracefully if not installed
```

---

## Migration Path (Backend Integration)

If running speaker metrics on backend instead of GPU worker:

```python
# In backend/speech_analysis/workers/real_processor.py
from gpu_worker.ml.speaker_metrics import calculate_speaker_metrics

# After getting diarization results:
speaker_metrics = calculate_speaker_metrics(
    transcription_result=speech_result,
    diarization_result=speech_result
)

# Store: analysis_job.results.speaker_metrics = speaker_metrics
```

---

## Next Steps

1. **Deploy GPU instance** with Dockerfile + docker-compose
2. **Configure networking** (security groups, VPC)
3. **Test end-to-end** with sample audio file
4. **Monitor performance** (GPU utilization, latency)
5. **Scale** if needed (more GPUs or additional GPU instances)

---

## Questions?

See `DEPLOYMENT.md` for complete deployment guide.
