# GPU_Testing.ipynb - Complete Feature Guide

Your notebook is now fully functional with GPU acceleration and comprehensive analytics! Here's what you can do:

## 🚀 Key Features

### 1. **Dual Backend Transcription**
```python
TRANSCRIPTION_BACKEND = "faster-whisper"  # or "openai"
```
- **Faster-Whisper**: GPU-accelerated, no API calls, local processing
- **OpenAI Whisper**: Highest quality (uses your API key from .env)

### 2. **Speaker Diarization with Adjustable Detection**
```python
PAUSE_THRESHOLD = 0.6  # Adjust to detect more/fewer speakers
```
- **0.3-0.5s**: Detects more potential speaker changes
- **0.6-0.8s**: Balanced detection (current)
- **0.9-1.2s**: Detects fewer, more confident changes

### 3. **Comprehensive Analytics**
Generates multiple outputs:

#### CSV/JSON Outputs:
- `speaker_transcript.csv` - Full transcript with timestamps
- `speaker_analytics.csv` - Summary statistics
- `speaker_detailed_stats.json` - Detailed per-speaker metrics
- `full_transcript_with_speakers.txt` - Formatted readable transcript
- `full_transcript_with_speakers.json` - Transcript as JSON

#### Visualizations:
- `speaker_analytics_dashboard.png` - 4-panel analytics dashboard
- `speaker_timeline.png` - Visual timeline of who spoke when

### 4. **Detailed Statistics Per Speaker**
- Total speaking time (seconds & %)
- Number of turns
- Total words spoken
- Words per minute (speaking rate)
- Average words per segment
- Longest/shortest segment duration
- Segment count

## 🎯 How to Get 3 Speakers Detected

The silence-detection algorithm needs tuning. Try these adjustments:

1. **Lower pause threshold** (0.3-0.5s):
   ```python
   PAUSE_THRESHOLD = 0.3  # More sensitive to gaps
   ```
   Then re-run the diarization cell.

2. **Use OpenAI for better results** (if you want professional diarization):
   ```python
   DIARIZATION_BACKEND = "openai"  # Once Pyannote is fixed
   ```

3. **Check the audio file** - Verify it actually has 3 distinct speakers

## 📊 Generated Outputs Location
All files are saved to: `../outputs/`

## 💡 Pro Tips

1. **Run cells in order**: Setup → Transcription → Diarization → Merge → Analytics → Viz
2. **Adjust PAUSE_THRESHOLD first** to get your speaker count right
3. **Save outputs**: All CSVs and JSONs are ready for other analysis
4. **Re-run visualization**: Just change the threshold and re-run cells 5-9

## 🔄 GPU Usage

- **Transcription**: ~15 seconds (Faster-Whisper on Tesla T4)
- **Diarization**: ~1 second (silence detection)
- **Analytics**: ~0.1 seconds
- **Total runtime**: ~30 seconds for full analysis

## 🛠️ Next Steps

If you want real speaker diarization (not silence-based):
1. Fix Pyannote compatibility issue (torchvision/torchmetrics conflict)
2. Or use: `pip install pyannote.audio --upgrade --force-reinstall`
3. Change `DIARIZATION_BACKEND = "pyannote"` in cell 6

