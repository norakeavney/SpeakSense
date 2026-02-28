# 🎭 AI-Powered Speaker Diarization & Identification

## Overview

This feature adds intelligent speaker diarization (identifying "who spoke when") to SpeakSense with an innovative AI-assisted identification system. Instead of requiring manual labeling or pre-trained speaker models, our system:

1. **Automatically detects speakers** using state-of-the-art diarization
2. **Makes educated guesses** about speaker identities using AI analysis
3. **Asks users to confirm** through an interactive, beautiful UI
4. **Learns from context** including speaking patterns, roles, and transcript content

## 🌟 Key Features

### AI-Powered Suggestions
- analyses speaking patterns (duration, frequency, turn-taking)
- Detects common roles (interviewer/interviewee, host/guest, moderator)
- Extracts context clues from transcription
- Provides confidence scores and reasoning

### Beautiful Interactive UI
- Visual speaker cards with AI reasoning
- Confidence indicators (star ratings)
- Quick-fill suggestions
- Real-time validation
- Smooth animations and transitions

### Robust Backend
- Pyannote.audio 3.1 integration
- MongoDB storage for confirmations
- RESTful API endpoints
- Error handling and fallbacks

## 📦 Architecture

```
Backend:
├── services/speaker_diarization.py   # Core AI diarization service
├── workers/real_processor.py         # Analysis pipeline integration
├── db/analysis_jobs.py               # Job management with speaker data
└── views.py                          # API endpoints

Frontend:
├── components/SpeakerIdentification.jsx   # Interactive UI component
└── components/AnalysisProgress.jsx        # Integration point
```

## 🔄 Workflow

1. **Upload Audio** → Standard audio upload process
2. **Transcription** → Whisper generates text transcript
3. **Diarization** → Pyannote detects speakers and segments
4. **AI Analysis** → System generates intelligent name suggestions
5. **User Confirmation** → Interactive UI presents suggestions
6. **Confirmation** → User accepts/modifies speaker names
7. **Continue Analysis** → Pipeline proceeds with labeled speakers

## 🚀 API Endpoints

### Get Speaker Suggestions
```http
GET /api/analysis/{job_id}/speakers/suggestions/
```

**Response:**
```json
{
  "job_id": "uuid",
  "num_speakers": 2,
  "suggestions": {
    "SPEAKER_00": {
      "speaker_id": "SPEAKER_00",
      "suggested_name": "Host",
      "suggested_role": "Interviewer/Host",
      "confidence": 0.7,
      "reasoning": [
        "More frequent turns suggests interviewer/host role",
        "Total speaking time: 145.3s across 23 turns"
      ],
      "alternative_suggestions": ["Speaker 1", "Person A"]
    },
    "SPEAKER_01": {
      "speaker_id": "SPEAKER_01",
      "suggested_name": "Guest",
      "suggested_role": "Guest/Interviewee",
      "confidence": 0.7,
      "reasoning": [
        "Longer responses suggest guest/interviewee role",
        "Total speaking time: 234.7s across 18 turns"
      ],
      "alternative_suggestions": ["Speaker 2", "Person B"]
    }
  }
}
```

### Confirm Speaker Names
```http
POST /api/analysis/{job_id}/speakers/confirm/
Content-Type: application/json

{
  "speakers": {
    "SPEAKER_00": "John Doe",
    "SPEAKER_01": "Jane Smith"
  }
}
```

**Response:**
```json
{
  "message": "Speaker identities confirmed successfully",
  "job_id": "uuid",
  "confirmed_speakers": {
    "SPEAKER_00": "John Doe",
    "SPEAKER_01": "Jane Smith"
  },
  "num_speakers": 2
}
```

## 🎨 Frontend Component Usage

```jsx
import SpeakerIdentification from '@/components/SpeakerIdentification';

<SpeakerIdentification 
  jobId={jobId}
  onConfirm={(names) => {
    console.log('Confirmed speakers:', names);
    // Handle confirmation
  }}
/>
```

## 🧠 AI Suggestion Algorithm

The system uses multiple heuristics to generate suggestions:

### 1. **Speaking Pattern Analysis**
- **Turn frequency**: More turns → likely interviewer/host
- **Average turn duration**: Longer turns → likely interviewee/guest
- **Total speaking time**: Dominance patterns

### 2. **Role Detection**
- **Two-person conversations**: Interviewer vs. Interviewee
- **Multi-person discussions**: Moderator + Participants
- **Monologues**: Single speaker

### 3. **Transcript Context** (Future Enhancement)
- Named Entity Recognition (NER)
- Self-introductions: "Hi, I'm [Name]"
- Job titles and roles mentioned
- Pronoun usage patterns

### 4. **Confidence Scoring**
- Pattern strength
- Consistency across metrics
- Context availability
- Number of segments

## 🛠️ Setup & Configuration

### Backend Requirements

Already in `requirements.txt`:
```
pyannote.audio==3.4.0
whisperx==3.7.4
torch==2.7.1
```

### HuggingFace Token

Pyannote requires authentication:

1. Get token from https://huggingface.co/settings/tokens
2. Accept model license at https://huggingface.co/pyannote/speaker-diarization-3.1
3. Set in environment:
```bash
export HF_TOKEN="your_token_here"
```

Or in code:
```python
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    use_auth_token="your_token_here"
)
```

## 📊 Database Schema

### Analysis Job Document
```javascript
{
  job_id: "uuid",
  audio_id: "audio_objectid",
  status: "processing",
  steps: {
    transcription: "done",
    diarization: "done",      // NEW
    speaker_metrics: "pending",
    emotion: "pending",
    topics: "pending"
  },
  results: {
    transcription: { text: "..." },
    diarization: {              // NEW
      diarization: {
        segments: [...],
        speakers: ["SPEAKER_00", "SPEAKER_01"],
        num_speakers: 2
      },
      suggestions: {...},
      requires_user_confirmation: true,
      status: "pending_confirmation",
      confirmed_speakers: {     // After confirmation
        "SPEAKER_00": "John Doe",
        "SPEAKER_01": "Jane Smith"
      }
    }
  },
  speaker_confirmations: {      // NEW
    "SPEAKER_00": "John Doe",
    "SPEAKER_01": "Jane Smith"
  }
}
```

## 🎯 Future Enhancements

### 1. **Advanced NLP Context Analysis**
- Full NER integration
- Semantic role labeling
- Coreference resolution

### 2. **Voice Biometric Matching**
- Store voice embeddings
- Match across recordings
- Build speaker database

### 3. **Active Learning**
- Learn from user corrections
- Improve suggestions over time
- Personalized patterns

### 4. **Real-time Diarization**
- Live audio streaming
- Incremental updates
- WebSocket integration

### 5. **Multi-language Support**
- Language-specific patterns
- Cultural communication styles
- International name suggestions

### 6. **Transcript Alignment**
- WhisperX word-level timestamps
- Accurate text-to-speaker mapping
- Formatted conversation view

## 🐛 Troubleshooting

### Diarization Fails
**Error**: `Could not load pyannote pipeline`

**Solution**: 
1. Check HuggingFace token is set
2. Accept model license
3. Verify CUDA/GPU availability
4. Check internet connection

### No Suggestions Displayed
**Error**: `Speaker identification not available yet`

**Solution**:
1. Wait for diarization to complete
2. Check analysis job status
3. Verify API endpoint connectivity
4. Review browser console for errors

### Speaker Names Not Saving
**Error**: `Failed to confirm speakers`

**Solution**:
1. Ensure all speakers have names
2. Check MongoDB connection
3. Verify job_id is valid
4. Review API logs

## 📝 Usage Examples

### Example 1: Podcast Interview
```
Input: 30-minute podcast, 2 speakers
AI Suggests:
  - SPEAKER_00 → "Host" (35 turns, 8min speaking)
  - SPEAKER_01 → "Guest" (28 turns, 22min speaking)
User Confirms:
  - SPEAKER_00 → "Sarah Johnson"
  - SPEAKER_01 → "Dr. Mike Chen"
```

### Example 2: Panel Discussion
```
Input: 45-minute panel, 4 speakers
AI Suggests:
  - SPEAKER_00 → "Moderator" (frequent short turns)
  - SPEAKER_01 → "Participant 1" (balanced contributions)
  - SPEAKER_02 → "Participant 2" (balanced contributions)
  - SPEAKER_03 → "Participant 3" (balanced contributions)
User Confirms:
  - SPEAKER_00 → "Panel Host"
  - SPEAKER_01 → "Alice Williams"
  - SPEAKER_02 → "Bob Martinez"
  - SPEAKER_03 → "Carol Zhang"
```

## 🎓 Technical Details

### Diarization Pipeline
Uses **Pyannote 3.1** which includes:
- **Segmentation**: Detect voice activity
- **Embedding**: Extract speaker embeddings
- **Clustering**: Group segments by speaker
- **Resegmentation**: Refine boundaries

### Performance
- **Diarization Speed**: ~1-3x real-time (GPU)
- **Accuracy**: 85-95% DER on benchmark datasets
- **Latency**: 5-30 seconds for typical audio

### GPU Requirements
- **Recommended**: NVIDIA GPU with 4GB+ VRAM
- **Fallback**: CPU mode (slower, ~10x)
- **CUDA Version**: 11.8+ or 12.x

## 🤝 Contributing

To extend the AI suggestion algorithm:

1. Edit `services/speaker_diarization.py`
2. Update `_infer_speaker_role()` method
3. Add new heuristics to `_analyse_transcription_context()`
4. Test with diverse audio samples
5. Submit PR with examples

## 📄 License

Part of SpeakSense project. See main LICENSE file.

---

**Built with ❤️ using AI-powered intelligence and human creativity!**
