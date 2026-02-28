"""
Speaker Diarization Flow Visualization
Run this to see the complete workflow
"""

def print_workflow():
    """Print ASCII art workflow diagram"""
    
    workflow = """
╔═══════════════════════════════════════════════════════════════════════╗
║                   🎭 SPEAKER IDENTIFICATION WORKFLOW                  ║
╚═══════════════════════════════════════════════════════════════════════╝

┌─────────────────────────────────────────────────────────────────────┐
│  STEP 1: Upload Audio                                               │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Audio File     │
                    │  Saved to Disk  │
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 2: Transcription (Whisper)                                    │
│  ✓ Generate text transcript                                         │
│  ✓ Extract audio features                                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 3: Speaker Diarization (Pyannote)                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  1. Voice Activity Detection (VAD)                         │    │
│  │     - Detect speech segments                               │    │
│  │     - Remove silence                                       │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  2. Speaker Embedding Extraction                           │    │
│  │     - Extract voice features                               │    │
│  │     - Create speaker signatures                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  3. Speaker Clustering                                     │    │
│  │     - Group similar voices                                 │    │
│  │     - Assign SPEAKER_00, SPEAKER_01, etc.                  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  4. Timeline Generation                                    │    │
│  │     - [00:00-00:15] SPEAKER_00                             │    │
│  │     - [00:15-00:32] SPEAKER_01                             │    │
│  │     - [00:32-00:45] SPEAKER_00                             │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 4: AI Analysis & Suggestion Generation                        │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  🧠 analyse Speaking Patterns                              │    │
│  │     - Count turns per speaker                              │    │
│  │     - Calculate speaking time                              │    │
│  │     - Average turn duration                                │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  🎯 Detect Communication Roles                             │    │
│  │     - Interviewer vs Interviewee                           │    │
│  │     - Host vs Guest                                        │    │
│  │     - Moderator vs Participants                            │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  📝 Extract Context from Transcript                        │    │
│  │     - Look for "My name is..."                             │    │
│  │     - Identify job titles                                  │    │
│  │     - analyse self-references                              │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  ⭐ Calculate Confidence Scores                            │    │
│  │     - Pattern strength                                     │    │
│  │     - Data availability                                    │    │
│  │     - Consistency metrics                                  │    │
│  └────────────────────────────────────────────────────────────┘    │
│                            │                                         │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  💡 Generate Suggestions                                   │    │
│  │     SPEAKER_00:                                            │    │
│  │       Name: "Host"                                         │    │
│  │       Role: "Interviewer/Host"                             │    │
│  │       Confidence: 70%                                      │    │
│  │       Alternatives: ["Speaker 1", "Person A"]              │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 5: User Interface Display                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  ╔═══════════════════════════════════════════════════╗     │    │
│  │  ║  🎭 Identify Speakers                             ║     │    │
│  │  ╚═══════════════════════════════════════════════════╝     │    │
│  │                                                             │    │
│  │  ┌─────────────────────────────────────────────────┐       │    │
│  │  │ 👤 SPEAKER_00                                   │       │    │
│  │  │    Role: Interviewer/Host                       │       │    │
│  │  │    Confidence: ⭐⭐⭐⭐ 70%                        │       │    │
│  │  │                                                  │       │    │
│  │  │    🧠 AI Reasoning:                             │       │    │
│  │  │    • More frequent turns                        │       │    │
│  │  │    • 23 turns, 145.3s total                     │       │    │
│  │  │                                                  │       │    │
│  │  │    Speaker Name: [Host____________]  ⚡ Host    │       │    │
│  │  │                                      Speaker 1  │       │    │
│  │  └─────────────────────────────────────────────────┘       │    │
│  │                                                             │    │
│  │  ┌─────────────────────────────────────────────────┐       │    │
│  │  │ 👤 SPEAKER_01                                   │       │    │
│  │  │    Role: Guest/Interviewee                      │       │    │
│  │  │    Confidence: ⭐⭐⭐⭐ 70%                        │       │    │
│  │  │                                                  │       │    │
│  │  │    🧠 AI Reasoning:                             │       │    │
│  │  │    • Longer responses                           │       │    │
│  │  │    • 18 turns, 234.7s total                     │       │    │
│  │  │                                                  │       │    │
│  │  │    Speaker Name: [Guest___________]  ⚡ Guest   │       │    │
│  │  │                                      Speaker 2  │       │    │
│  │  └─────────────────────────────────────────────────┘       │    │
│  │                                                             │    │
│  │  [  ✓ Confirm Speakers  ]                                  │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 6: User Interaction                                           │
│  User reviews suggestions and:                                      │
│  ✓ Accepts AI suggestions (click quick-fill)                        │
│  ✓ Modifies names (type custom names)                               │
│  ✓ Confirms all speakers                                            │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 7: Save Confirmations                                         │
│  POST /api/analysis/{job_id}/speakers/confirm/                      │
│  {                                                                   │
│    "speakers": {                                                     │
│      "SPEAKER_00": "Sarah Johnson",                                 │
│      "SPEAKER_01": "Dr. Mike Chen"                                  │
│    }                                                                 │
│  }                                                                   │
│  ✓ Saved to MongoDB                                                 │
│  ✓ Diarization status → "confirmed"                                 │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 8: Continue Analysis Pipeline                                 │
│  ✓ Speaker Metrics (with names)                                     │
│  ✓ Emotion Analysis (per speaker)                                   │
│  ✓ Topic Extraction (speaker attribution)                           │
└─────────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│  STEP 9: Final Results                                              │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │  📊 Complete Analysis with Named Speakers                  │    │
│  │                                                             │    │
│  │  Sarah Johnson:                                            │    │
│  │    • Total time: 145.3s (38%)                              │    │
│  │    • Turns: 23                                             │    │
│  │    • Emotions: Professional (65%), Curious (20%)           │    │
│  │    • Topics: Introduction, Technology, Future              │    │
│  │                                                             │    │
│  │  Dr. Mike Chen:                                            │    │
│  │    • Total time: 234.7s (62%)                              │    │
│  │    • Turns: 18                                             │    │
│  │    • Emotions: Enthusiastic (45%), Confident (40%)         │    │
│  │    • Topics: Research, Innovation, Applications            │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘

╔═══════════════════════════════════════════════════════════════════════╗
║                         KEY TECHNOLOGIES USED                         ║
╠═══════════════════════════════════════════════════════════════════════╣
║  🎙️  Pyannote.audio 3.1  → Speaker diarization                       ║
║  🎯  Whisper             → Transcription                              ║
║  🧠  Custom AI           → Intelligent suggestions                    ║
║  💾  MongoDB             → Data persistence                           ║
║  ⚛️  React/Next.js       → Interactive UI                             ║
║  🐍  Django REST         → API endpoints                              ║
╚═══════════════════════════════════════════════════════════════════════╝
"""
    
    print(workflow)


if __name__ == '__main__':
    print_workflow()
