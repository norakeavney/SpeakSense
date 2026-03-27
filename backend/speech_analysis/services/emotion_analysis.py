"""
Emotion Analysis Service
Performs emotion detection from transcript and audio features using DistilBERT and Wav2Vec2
Combines text-based and audio-based emotion analysis
"""

import logging
from typing import Dict, List, Any, Tuple
from collections import Counter, defaultdict
import re
import torch
import torchaudio
import numpy as np
from transformers import (
    pipeline, 
    AutoModelForSequenceClassification, 
    AutoTokenizer,
    Wav2Vec2Processor,
    Wav2Vec2ForSequenceClassification
)
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

logger = logging.getLogger(__name__)

# Initialize emotion classifier with DistilBERT (for text)
_emotion_classifier = None

# Initialize Wav2Vec2 model (for audio)
_audio_emotion_model = None
_audio_emotion_processor = None

def get_emotion_classifier():
    """Lazy load the emotion classifier model"""
    global _emotion_classifier
    if _emotion_classifier is None:
        try:
            logger.info("Loading DistilBERT emotion classifier...")
            model_name = "SamLowe/roberta-base-go_emotions"
            _emotion_classifier = pipeline(
                "text-classification",
                model=model_name,
                top_k=None,
                device=-1,  # Force CPU to avoid GPU issues
            )
            logger.info("✓ DistilBERT loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load DistilBERT: {str(e)}")
            logger.warning("Using keyword-based fallback")
            _emotion_classifier = "fallback"
    return _emotion_classifier


# Emotion keyword mapping for text-based analysis
EMOTION_KEYWORDS = {
    'happy': [
        'happy', 'joy', 'excited', 'great', 'wonderful', 'amazing', 'fantastic',
        'excellent', 'love', 'glad', 'delighted', 'pleased', 'thrilled', 'awesome',
        'perfect', 'beautiful', 'fun', 'haha', 'lol', '😊', '😄', '😁'
    ],
    'sad': [
        'sad', 'unhappy', 'depressed', 'disappointed', 'unfortunate', 'sorry',
        'regret', 'miss', 'lonely', 'cry', 'tears', 'hurt', 'pain', 'terrible',
        'awful', 'bad', 'worse', 'worst', '😢', '😭'
    ],
    'angry': [
        'angry', 'mad', 'furious', 'hate', 'irritated', 'annoyed', 'frustrated',
        'outraged', 'rage', 'damn', 'stupid', 'idiot', 'ridiculous', 'disgusting',
        'unacceptable', '😠', '😡', '🤬'
    ],
    'fear': [
        'afraid', 'scared', 'fear', 'worry', 'anxious', 'nervous', 'concerned',
        'terrified', 'panic', 'frightened', 'alarmed', 'tense', 'stress', 'threat',
        '😨', '😰'
    ],
    'surprise': [
        'surprise', 'shocked', 'amazing', 'unexpected', 'wow', 'omg', 'incredible',
        'unbelievable', 'astonishing', 'sudden', '😮', '😲'
    ],
    'disgust': [
        'disgusting', 'gross', 'nasty', 'revolting', 'repulsive', 'sick', 'vile',
        'awful', 'terrible', 'yuck', '🤢', '🤮'
    ],
    'neutral': [
        'okay', 'fine', 'alright', 'normal', 'regular', 'standard', 'average',
        'usual', 'typical'
    ]
}


def analyse_emotions(transcript_data: List[Dict], audio_features: Dict = None) -> Dict[str, Any]:
    """
    analyse emotions from transcript using DistilBERT and optional audio features.
    
    Args:
        transcript_data: List of transcript segments with 'text', 'start', 'end', and optionally 'speaker'
        audio_features: Optional dict of audio features per speaker (for future enhancement)
    
    Returns:
        Dict containing:
            - overall_sentiment: str (dominant emotion)
            - timeline: list of emotion points with timestamp and confidence
            - emotion_distribution: dict of emotion percentages (confidence-weighted)
            - per_speaker_emotions: dict of emotions per speaker (if speakers available)
            - intensity_timeline: list of intensity values over time
            - volatility_score: float (emotional stability metric)
            - model_used: str (which model was used for analysis)
            - avg_confidence: float (average confidence across all predictions)
    """
    logger.info("Starting emotion analysis from transcript using DistilBERT")
    
    if not transcript_data:
        logger.warning("No transcript data provided")
        return {
            'overall_sentiment': 'neutral',
            'timeline': [],
            'emotion_distribution': {'neutral': 1.0},
            'error': 'No transcript data available',
            'model_used': 'none',
            'avg_confidence': 0.0
        }
    
    # Get the emotion classifier
    classifier = get_emotion_classifier()
    use_transformer = classifier != "fallback"
    
    # FIX 4: Use confidence-weighted emotion accumulation
    emotion_scores = defaultdict(float)  # Changed from list to weighted scores
    all_confidences = []  # FIX 1: Track text confidences for dynamic weighting
    timeline = []
    per_speaker_emotions = {}
    per_speaker_timeline = defaultdict(list)  # For per-speaker emotion over time
    
    for segment in transcript_data:
        text = segment.get('text', '')
        timestamp = segment.get('start', 0.0)
        speaker = segment.get('speaker', None)
        
        if not text or len(text.strip()) < 3:
            continue
        
        # Step 1: Get raw emotion prediction
        if use_transformer:
            raw_emotion, raw_confidence = _predict_emotion(text, classifier)
        else:
            raw_emotion, raw_confidence = _detect_emotion_from_text(text)
        
        # Step 2: Apply context-aware correction (FIX 3: Separate layer)
        emotion, confidence = _apply_context_rules(text, raw_emotion, raw_confidence)
        
        # FIX 4: Weighted accumulation
        emotion_scores[emotion] += confidence
        all_confidences.append(confidence)
        
        # Add to timeline (sample every ~30 seconds or key segments)
        if len(timeline) == 0 or timestamp - timeline[-1]['timestamp'] >= 30:
            timeline.append({
                'timestamp': timestamp,
                'emotion': emotion,
                'confidence': confidence,
                'intensity': confidence  # For intensity graph
            })
        
        # Track per-speaker emotions with timeline
        if speaker:
            if speaker not in per_speaker_emotions:
                per_speaker_emotions[speaker] = defaultdict(float)
            per_speaker_emotions[speaker][emotion] += confidence
            
            # Per-speaker timeline for emotional shifts
            per_speaker_timeline[speaker].append({
                'timestamp': timestamp,
                'emotion': emotion,
                'confidence': confidence
            })
    
    # FIX 4: Calculate confidence-weighted distribution
    total_weight = sum(emotion_scores.values())
    emotion_distribution = {
        emotion: score / total_weight
        for emotion, score in emotion_scores.items()
    } if total_weight > 0 else {'neutral': 1.0}
    
    # Get overall sentiment (highest weighted emotion)
    overall_sentiment = max(emotion_distribution, key=emotion_distribution.get)
    
    # FIX 1: Calculate average confidence for dynamic weighting
    avg_confidence = np.mean(all_confidences) if all_confidences else 0.0
    
    # Calculate emotional volatility (FIX: Advanced metric)
    volatility_score = _calculate_volatility(timeline)
    
    # Calculate per-speaker dominant emotions
    speaker_emotions = {}
    for speaker, emotions in per_speaker_emotions.items():
        total = sum(emotions.values())
        speaker_emotions[speaker] = {
            'dominant_emotion': max(emotions, key=emotions.get),
            'distribution': {
                emotion: score / total
                for emotion, score in emotions.items()
            },
            'timeline': per_speaker_timeline[speaker]  # Per-speaker emotion over time
        }
    
    # Calculate emotional asymmetry if multiple speakers
    asymmetry_score = None
    if len(speaker_emotions) == 2:
        asymmetry_score = _calculate_emotional_asymmetry(speaker_emotions)
    
    result = {
        'overall_sentiment': overall_sentiment,
        'timeline': timeline,
        'emotion_distribution': emotion_distribution,
        'model_used': 'distilbert' if use_transformer else 'keyword-based',
        'avg_confidence': round(avg_confidence, 2),  # FIX 1: Added for dynamic weighting
        'volatility_score': volatility_score,
        'intensity_timeline': [{'timestamp': p['timestamp'], 'intensity': p['confidence']} for p in timeline]
    }
    
    if speaker_emotions:
        result['per_speaker_emotions'] = speaker_emotions
    
    if asymmetry_score is not None:
        result['emotional_asymmetry'] = asymmetry_score
    
    logger.info(f"Emotion analysis complete: {overall_sentiment}, {len(timeline)} timeline points")
    logger.info(f"Distribution: {emotion_distribution}")
    logger.info(f"Average confidence: {avg_confidence:.2f}, Volatility: {volatility_score:.2f}")
    logger.info(f"Model used: {result['model_used']}")
    
    return result


def _is_formal_analytical_speech(text: str) -> bool:
    """
    Detect if text is formal/analytical speech (debates, legal, policy discussion).
    These contexts often use emotional words without emotional intent.
    """
    analytical_markers = [
        "evidence", "policy", "law", "public interest", "emergency",
        "prosecution", "report", "inquiry", "crisis", "threat",
        "I think", "I would argue", "in practice", "the fact is",
        "parliament", "government", "minister", "debate", "question",
        "according to", "statistics", "data shows", "research"
    ]
    
    # Count analytical markers
    score = sum(1 for marker in analytical_markers if marker.lower() in text.lower())
    
    # Formal speech tends to:
    # 1. Use analytical markers
    # 2. Avoid exclamation marks
    # 3. Have longer, complex sentences
    if score >= 2 and "!" not in text:
        return True
    
    # Also detect by structure (long, formal sentences)
    if len(text) > 80 and "." in text and text.count(",") >= 2:
        return True
    
    return False


def _predict_emotion(text: str, classifier) -> Tuple[str, float]:
    """
    FIX 3: Base model inference (raw prediction without context rules).
    Separated from context-aware correction for cleaner architecture.
    
    Args:
        text: Text to analyse
        classifier: HuggingFace pipeline for emotion classification
    
    Returns:
        Tuple of (emotion, confidence)
    """
    try:
        # Truncate text if too long (DistilBERT has 512 token limit)
        if len(text) > 500:
            text = text[:500]
        
        # Get predictions
        results = classifier(text)[0]
        
        # FIX 2: Boost existing neutral score for analytical speech
        is_analytical = _is_formal_analytical_speech(text)
        if is_analytical:
            neutral_boost = 0.15
            for r in results:
                if r['label'].lower() == 'neutral':
                    r['score'] = min(1.0, r['score'] + neutral_boost)
        
        # If no neutral in results at all, add it
        if not any(r['label'].lower() == 'neutral' for r in results):
            results.append({'label': 'neutral', 'score': 0.25})
        
        # Find the emotion with highest score
        top_emotion = max(results, key=lambda x: x['score'])
        emotion_label = top_emotion['label'].lower()
        confidence = top_emotion['score']
        
        # Map model labels to our standard emotions
        emotion_mapping = {
            'joy': 'happy',
            'love': 'happy',
            'sadness': 'sad',
            'anger': 'angry',
            'fear': 'fear',
            'surprise': 'surprise',
            'disgust': 'disgust',
            'neutral': 'neutral'
        }
        
        emotion = emotion_mapping.get(emotion_label, emotion_label)
        
        return emotion, round(confidence, 2)
        
    except Exception as e:
        logger.warning(f"DistilBERT emotion detection failed: {e}, falling back to keywords")
        return _detect_emotion_from_text(text)


def _apply_context_rules(text: str, emotion: str, confidence: float) -> Tuple[str, float]:
    """
    FIX 3: Post-processing correction layer.
    Apply domain-aware adjustments based on context.
    
    Args:
        text: Original text
        emotion: Raw emotion prediction
        confidence: Raw confidence score
    
    Returns:
        Tuple of (corrected_emotion, corrected_confidence)
    """
    # Rule 1: Confidence threshold - low confidence defaults to neutral
    if confidence < 0.65:
        return "neutral", confidence
    
    # Rule 2: Context-aware emotion correction for analytical/debate speech
    if _is_formal_analytical_speech(text):
        # Don't misinterpret policy/emergency language as fear/anger
        if emotion in ["angry", "fear"]:
            return "neutral", 0.7
    
    return emotion, confidence


def _detect_emotion_from_text(text: str) -> Tuple[str, float]:
    """
    Detect emotion from text using keyword matching and sentiment analysis.
    
    Args:
        text: Text to analyse
    
    Returns:
        Tuple of (emotion, confidence)
    """
    text_lower = text.lower()
    
    # Count emotion keywords
    emotion_scores = {}
    for emotion, keywords in EMOTION_KEYWORDS.items():
        score = sum(1 for keyword in keywords if keyword in text_lower)
        if score > 0:
            emotion_scores[emotion] = score
    
    # If no keywords found, analyse sentiment through basic heuristics
    if not emotion_scores:
        # Check for punctuation and capitalization patterns
        if '!' in text or text.isupper():
            if any(word in text_lower for word in ['no', 'not', 'never', "don't", "can't", "won't"]):
                emotion_scores['angry'] = 1
            else:
                emotion_scores['excited'] = 1
                emotion_scores['happy'] = 1
        elif '?' in text:
            emotion_scores['neutral'] = 1
        else:
            emotion_scores['neutral'] = 2
    
    # Get the dominant emotion
    if emotion_scores:
        dominant_emotion = max(emotion_scores, key=emotion_scores.get)
        total_score = sum(emotion_scores.values())
        confidence = emotion_scores[dominant_emotion] / total_score
    else:
        dominant_emotion = 'neutral'
        confidence = 0.5
    
    # Normalize confidence to realistic range (0.6-0.95)
    confidence = min(0.95, max(0.6, 0.6 + (confidence * 0.35)))
    
    return dominant_emotion, round(confidence, 2)


def _calculate_volatility(timeline: List[Dict]) -> float:
    """
    Calculate emotional volatility score.
    
    Args:
        timeline: List of emotion points over time
    
    Returns:
        Volatility score (0-1, higher = more volatile)
    """
    if len(timeline) < 2:
        return 0.0
    
    # Count emotion changes
    changes = 0
    for i in range(1, len(timeline)):
        if timeline[i]['emotion'] != timeline[i-1]['emotion']:
            changes += 1
    
    volatility = changes / (len(timeline) - 1)
    return round(volatility, 2)


def _calculate_emotional_asymmetry(speaker_emotions: Dict) -> Dict[str, Any]:
    """
    Calculate emotional asymmetry between two speakers.
    
    Args:
        speaker_emotions: Dict of per-speaker emotion distributions
    
    Returns:
        Dict with asymmetry metrics
    """
    speakers = list(speaker_emotions.keys())
    if len(speakers) != 2:
        return None
    
    speaker1, speaker2 = speakers
    dist1 = speaker_emotions[speaker1]['distribution']
    dist2 = speaker_emotions[speaker2]['distribution']
    
    # Get all emotions
    all_emotions = set(list(dist1.keys()) + list(dist2.keys()))
    
    # Calculate distance
    distance = sum(
        abs(dist1.get(emotion, 0.0) - dist2.get(emotion, 0.0))
        for emotion in all_emotions
    )
    
    # Normalize to 0-1
    asymmetry_score = distance / 2.0  # Max distance is 2.0
    
    # Interpret
    if asymmetry_score < 0.3:
        interpretation = "emotionally aligned"
    elif asymmetry_score < 0.6:
        interpretation = "moderately different"
    else:
        interpretation = "emotionally oppositional"
    
    return {
        'score': round(asymmetry_score, 2),
        'interpretation': interpretation,
        'speakers': speakers
    }


def analyse_speaker_emotional_state(speaker_metrics: Dict, audio_features: Dict = None) -> Dict[str, Any]:
    """
    analyse emotional patterns for individual speakers.
    
    Args:
        speaker_metrics: Dict of speaker metrics (speaking time, WPM, etc.)
        audio_features: Optional audio features for more accurate analysis
    
    Returns:
        Dict of emotional insights per speaker
    """
    logger.info("Analyzing speaker emotional states")
    
    speaker_emotional_insights = {}
    
    for speaker, metrics in speaker_metrics.items():
        insights = {
            'energy_level': 'medium',
            'emotional_stability': 'stable',
            'engagement': 'moderate'
        }
        
        # analyse speaking patterns for emotional indicators
        wpm = metrics.get('words_per_minute', 120)
        
        # Fast speaking might indicate excitement or anxiety
        if wpm > 160:
            insights['energy_level'] = 'high'
            insights['engagement'] = 'high'
        elif wpm < 100:
            insights['energy_level'] = 'low'
            insights['engagement'] = 'low'
        
        # Filler words can indicate nervousness
        filler_words = metrics.get('filler_words', 0)
        if filler_words > 10:
            insights['emotional_stability'] = 'nervous'
        
        speaker_emotional_insights[speaker] = insights
    
    return speaker_emotional_insights


def generate_emotion_summary(emotion_data: Dict) -> str:
    """
    Generate a human-readable summary of the emotion analysis.
    
    Args:
        emotion_data: Emotion analysis results
    
    Returns:
        String summary
    """
    overall = emotion_data.get('overall_sentiment', 'neutral')
    distribution = emotion_data.get('emotion_distribution', {})
    volatility = emotion_data.get('volatility_score', 0.0)
    asymmetry = emotion_data.get('emotional_asymmetry')
    
    # Sort emotions by percentage
    sorted_emotions = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
    
    summary_parts = [
        f"The overall emotional tone is {overall}.",
    ]
    
    # Add top emotions
    if len(sorted_emotions) > 1:
        top_emotions = sorted_emotions[:3]
        emotion_list = ", ".join([f"{emotion} ({pct*100:.0f}%)" for emotion, pct in top_emotions])
        summary_parts.append(f"The conversation contains: {emotion_list}.")
    
    # Add volatility analysis
    if volatility < 0.3:
        summary_parts.append("The emotional tone is stable throughout.")
    elif volatility < 0.6:
        summary_parts.append("The emotional tone shows moderate variation.")
    else:
        summary_parts.append("The emotional tone is highly volatile with frequent shifts.")
    
    # Per-speaker insights
    if 'per_speaker_emotions' in emotion_data:
        speaker_insights = []
        for speaker, data in emotion_data['per_speaker_emotions'].items():
            dominant = data['dominant_emotion']
            speaker_insights.append(f"{speaker} is predominantly {dominant}")
        
        if speaker_insights:
            summary_parts.append(" ".join(speaker_insights) + ".")
    
    # Add asymmetry analysis
    if asymmetry:
        summary_parts.append(f"The speakers are {asymmetry['interpretation']} (asymmetry: {asymmetry['score']}).")
    
    return " ".join(summary_parts)


# ============================================================================
# AUDIO-BASED EMOTION ANALYSIS (Wav2Vec2)
# ============================================================================

def get_audio_emotion_model():
    """Lazy load Wav2Vec2 emotion model for audio analysis"""
    global _audio_emotion_model, _audio_emotion_processor
    
    if _audio_emotion_model is None:
        try:
            logger.info("Loading Wav2Vec2 emotion model...")
            model_name = "superb/wav2vec2-base-superb-er"
            
            _audio_emotion_processor = Wav2Vec2Processor.from_pretrained(model_name)
            _audio_emotion_model = Wav2Vec2ForSequenceClassification.from_pretrained(model_name)
            
            device = torch.device('cpu')  # Force CPU for stability
            _audio_emotion_model.to(device)
            _audio_emotion_model.eval()
            
            logger.info(f"✓ Wav2Vec2 loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load Wav2Vec2: {str(e)}")
            _audio_emotion_model = "failed"
            _audio_emotion_processor = "failed"
    
    return _audio_emotion_model, _audio_emotion_processor


def analyse_audio_emotions(file_ref: str, transcript_data: List[Dict] = None) -> Dict[str, Any]:
    """
    analyse emotions from audio file using Wav2Vec2.
    
    Args:
        file_ref: Path to audio file
        transcript_data: Optional transcript with timestamps for alignment
    
    Returns:
        Dict containing:
            - overall_sentiment: str
            - timeline: list of emotion points
            - emotion_distribution: dict of emotion percentages
            - audio_confidence: average confidence score
            - model_used: 'wav2vec2' or 'failed'
            - avg_confidence: average confidence (for fusion)
    """
    logger.info(f"Starting audio emotion analysis for: {file_ref}")

    # FIX: Handle missing audio path gracefully
    if not file_ref:
        logger.warning("No audio path provided")
    return {
        'overall_sentiment': 'neutral',
        'timeline': [],
        'emotion_distribution': {'neutral': 1.0},
        'model_used': 'none',
        'avg_confidence': 0.0,
        'error': 'No audio path provided'
    }

    
    model, processor = get_audio_emotion_model()
    
    if model == "failed":
        logger.error("Audio emotion model not available")
        return {
            'overall_sentiment': 'neutral',
            'timeline': [],
            'emotion_distribution': {'neutral': 1.0},
            'model_used': 'failed',
            'avg_confidence': 0.0,
            'error': 'Wav2Vec2 model failed to load'
        }
    
    try:
        # Load audio
        waveform, sample_rate = torchaudio.load(file_ref)
        
        # Resample to 16kHz if needed (Wav2Vec2 expects 16kHz)
        if sample_rate != 16000:
            resampler = torchaudio.transforms.Resample(sample_rate, 16000)
            waveform = resampler(waveform)
            sample_rate = 16000
        
        # Convert to mono if stereo
        if waveform.shape[0] > 1:
            waveform = torch.mean(waveform, dim=0, keepdim=True)
        
        # analyse audio in chunks (30 second segments)
        chunk_duration = 30  # seconds
        chunk_samples = chunk_duration * sample_rate
        total_samples = waveform.shape[1]
        
        timeline = []
        emotion_scores = defaultdict(float)  # FIX 4: Weighted accumulation
        all_confidences = []
        
        for start_sample in range(0, total_samples, chunk_samples):
            end_sample = min(start_sample + chunk_samples, total_samples)
            chunk = waveform[:, start_sample:end_sample]
            
            timestamp = start_sample / sample_rate
            
            # Skip very short chunks
            if chunk.shape[1] < sample_rate * 2:  # Less than 2 seconds
                continue
            
            # analyse chunk
            emotion, confidence = _predict_emotion_from_audio(chunk.squeeze().numpy(), processor, model)
            
            # FIX 4: Weighted accumulation
            emotion_scores[emotion] += confidence
            all_confidences.append(confidence)
            
            timeline.append({
                'timestamp': round(timestamp, 1),
                'emotion': emotion,
                'confidence': round(confidence, 2),
                'source': 'audio'
            })
        
        # FIX 4: Calculate confidence-weighted distribution
        total_weight = sum(emotion_scores.values())
        emotion_distribution = {
            emotion: score / total_weight
            for emotion, score in emotion_scores.items()
        } if total_weight > 0 else {'neutral': 1.0}
        
        # Overall sentiment
        overall_sentiment = max(emotion_distribution, key=emotion_distribution.get)
        avg_confidence = np.mean(all_confidences) if all_confidences else 0.0
        
        result = {
            'overall_sentiment': overall_sentiment,
            'timeline': timeline,
            'emotion_distribution': emotion_distribution,
            'audio_confidence': round(avg_confidence, 2),
            'avg_confidence': round(avg_confidence, 2),  # For fusion
            'model_used': 'wav2vec2',
            'num_chunks_analysed': len(timeline)
        }
        
        logger.info(f"Audio emotion analysis complete: {overall_sentiment}, {len(timeline)} chunks")
        logger.info(f"Average confidence: {avg_confidence:.2f}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing audio emotions: {e}", exc_info=True)
        return {
            'overall_sentiment': 'neutral',
            'timeline': [],
            'emotion_distribution': {'neutral': 1.0},
            'model_used': 'failed',
            'avg_confidence': 0.0,
            'error': str(e)
        }


def _predict_emotion_from_audio(audio_array: np.ndarray, processor, model) -> Tuple[str, float]:
    """
    Predict emotion from audio chunk using Wav2Vec2.
    
    Args:
        audio_array: Audio waveform as numpy array
        processor: Wav2Vec2 processor
        model: Wav2Vec2 model
    
    Returns:
        Tuple of (emotion, confidence)
    """
    try:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Process audio
        inputs = processor(audio_array, sampling_rate=16000, return_tensors="pt", padding=True)
        inputs = {key: val.to(device) for key, val in inputs.items()}
        
        # Get predictions
        with torch.no_grad():
            logits = model(**inputs).logits
        
        # Get probabilities
        probabilities = torch.nn.functional.softmax(logits, dim=-1)
        predicted_id = torch.argmax(probabilities, dim=-1).item()
        confidence = probabilities[0][predicted_id].item()
        
        # Map model output based on which model is loaded
        model_type = getattr(model, 'model_type', 'ehcalabres')
        
        if model_type == 'superb':
            # SUPERB model outputs: ['neu', 'hap', 'ang', 'sad']
            emotion_mapping = {
                0: 'neutral',
                1: 'happy',
                2: 'angry',
                3: 'sad'
            }
        else:
            # ehcalabres model outputs: ['angry', 'calm', 'disgust', 'fearful', 'happy', 'neutral', 'sad', 'surprised']
            emotion_labels = ['angry', 'calm', 'disgust', 'fear', 'happy', 'neutral', 'sad', 'surprise']
            emotion_mapping = {i: label for i, label in enumerate(emotion_labels)}
        
        emotion = emotion_mapping.get(predicted_id, 'neutral')
        
        # Map 'calm' to 'neutral' for consistency
        if emotion == 'calm':
            emotion = 'neutral'
        
        return emotion, confidence
        
    except Exception as e:
        logger.error(f"Error predicting emotion from audio: {e}", exc_info=True)
        return 'neutral', 0.5


# ============================================================================
# FUSION: TEXT + AUDIO EMOTION ANALYSIS
# ============================================================================

def fuse_text_and_audio_emotions(
    text_emotions: Dict[str, Any],
    audio_emotions: Dict[str, Any],
    text_weight: float = 0.3,
    audio_weight: float = 0.7
) -> Dict[str, Any]:
    """
    Fuse text-based and audio-based emotion predictions.
    Optimized for debate/analytical speech where audio prosody is more reliable.
    
    Args:
        text_emotions: Results from text emotion analysis (DistilBERT)
        audio_emotions: Results from audio emotion analysis (Wav2Vec2)
        text_weight: Weight for text predictions (default 0.3)
        audio_weight: Weight for audio predictions (default 0.7)
    
    Returns:
        Fused emotion analysis results
    """
    logger.info("Fusing text and audio emotion predictions")
    
    # FIX 1: Dynamic weighting based on text confidence (now correctly pulling from text)
    text_avg_confidence = text_emotions.get('avg_confidence', 0.5)
    if text_avg_confidence < 0.65:
        logger.info(f"Low text confidence ({text_avg_confidence:.2f}), increasing audio weight")
        text_weight = 0.2
        audio_weight = 0.8
    
    # Check if both analyses succeeded
    text_available = text_emotions.get('model_used') in ['distilbert', 'keyword-based']
    audio_available = audio_emotions.get('model_used') == 'wav2vec2'
    
    # If only one available, return that one
    if not audio_available and text_available:
        logger.info("Using text emotions only (audio unavailable)")
        text_emotions['fusion_info'] = 'text_only'
        return text_emotions
    
    if not text_available and audio_available:
        logger.info("Using audio emotions only (text unavailable)")
        audio_emotions['fusion_info'] = 'audio_only'
        return audio_emotions
    
    if not text_available and not audio_available:
        logger.warning("Neither text nor audio emotions available")
        return {
            'overall_sentiment': 'neutral',
            'timeline': [],
            'emotion_distribution': {'neutral': 1.0},
            'fusion_info': 'none_available'
        }
    
    # Fuse emotion distributions
    text_dist = text_emotions.get('emotion_distribution', {})
    audio_dist = audio_emotions.get('emotion_distribution', {})
    
    all_emotions = set(list(text_dist.keys()) + list(audio_dist.keys()))
    fused_distribution = {}
    
    for emotion in all_emotions:
        text_score = text_dist.get(emotion, 0.0)
        audio_score = audio_dist.get(emotion, 0.0)
        fused_score = (text_score * text_weight) + (audio_score * audio_weight)
        fused_distribution[emotion] = fused_score
    
    # Normalize
    total = sum(fused_distribution.values())
    if total > 0:
        fused_distribution = {k: v/total for k, v in fused_distribution.items()}
    
    # Get overall sentiment
    overall_sentiment = max(fused_distribution, key=fused_distribution.get)
    
    # Merge timelines (prefer audio timeline as it's more detailed)
    timeline = audio_emotions.get('timeline', [])
    
    # Add text timeline points if they don't conflict
    for text_point in text_emotions.get('timeline', []):
        text_time = text_point['timestamp']
        # Check if there's an audio point nearby (within 5 seconds)
        nearby = any(abs(audio_point['timestamp'] - text_time) < 5 for audio_point in timeline)
        if not nearby:
            text_point['source'] = 'text'
            timeline.append(text_point)
    
    # Sort by timestamp
    timeline.sort(key=lambda x: x['timestamp'])
    
    # Combine metrics from both
    result = {
        'overall_sentiment': overall_sentiment,
        'timeline': timeline,
        'emotion_distribution': fused_distribution,
        'fusion_info': {
            'method': 'weighted_average',
            'text_weight': text_weight,
            'audio_weight': audio_weight,
            'text_model': text_emotions.get('model_used'),
            'audio_model': audio_emotions.get('model_used'),
            'text_confidence': text_avg_confidence,
            'audio_confidence': audio_emotions.get('avg_confidence', 0.0)
        },
        'volatility_score': text_emotions.get('volatility_score', 0.0),
        'emotional_asymmetry': text_emotions.get('emotional_asymmetry'),
        'per_speaker_emotions': text_emotions.get('per_speaker_emotions'),
        'separate_results': {
            'text': text_emotions,
            'audio': audio_emotions
        }
    }
    
    logger.info(f"Fused emotion analysis: {overall_sentiment}")
    logger.info(f"Timeline: {len(timeline)} points from both sources")
    logger.info(f"Dynamic weights used - Text: {text_weight}, Audio: {audio_weight}")
    
    return result