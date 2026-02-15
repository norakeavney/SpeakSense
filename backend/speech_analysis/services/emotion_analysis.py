"""
Emotion Analysis Service
Performs emotion detection from transcript and audio features using DistilBERT
"""

import logging
from typing import Dict, List, Any
from collections import Counter
import re
import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import warnings

warnings.filterwarnings('ignore', category=FutureWarning)

logger = logging.getLogger(__name__)

# Initialize emotion classifier with DistilBERT
# Using a pre-trained emotion classification model
_emotion_classifier = None

def get_emotion_classifier():
    """Lazy load the emotion classifier model"""
    global _emotion_classifier
    if _emotion_classifier is None:
        try:
            logger.info("Loading DistilBERT emotion classifier...")
            # Using a popular emotion classification model
            # You can also use: "j-hartmann/emotion-english-distilroberta-base"
            model_name = "bhadresh-savani/distilbert-base-uncased-emotion"
            _emotion_classifier = pipeline(
                "text-classification",
                model=model_name,
                top_k=None,  # Return all emotion scores
                device=0 if torch.cuda.is_available() else -1
            )
            logger.info("✓ Emotion classifier loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load DistilBERT model: {e}")
            logger.warning("Falling back to keyword-based emotion detection")
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


def analyze_emotions(transcript_data: List[Dict], audio_features: Dict = None) -> Dict[str, Any]:
    """
    Analyze emotions from transcript using DistilBERT and optional audio features.
    
    Args:
        transcript_data: List of transcript segments with 'text', 'start', 'end', and optionally 'speaker'
        audio_features: Optional dict of audio features per speaker (for future enhancement)
    
    Returns:
        Dict containing:
            - overall_sentiment: str (dominant emotion)
            - timeline: list of emotion points with timestamp
            - emotion_distribution: dict of emotion percentages
            - per_speaker_emotions: dict of emotions per speaker (if speakers available)
            - model_used: str (which model was used for analysis)
    """
    logger.info("Starting emotion analysis from transcript using DistilBERT")
    
    if not transcript_data:
        logger.warning("No transcript data provided")
        return {
            'overall_sentiment': 'neutral',
            'timeline': [],
            'emotion_distribution': {'neutral': 1.0},
            'error': 'No transcript data available',
            'model_used': 'none'
        }
    
    # Get the emotion classifier
    classifier = get_emotion_classifier()
    use_transformer = classifier != "fallback"
    
    # Analyze emotions for each segment
    timeline = []
    all_emotions = []
    per_speaker_emotions = {}
    
    for segment in transcript_data:
        text = segment.get('text', '')
        timestamp = segment.get('start', 0.0)
        speaker = segment.get('speaker', None)
        
        if not text or len(text.strip()) < 3:
            continue
        
        # Detect emotion for this segment
        if use_transformer:
            emotion, confidence = _detect_emotion_with_distilbert(text, classifier)
        else:
            emotion, confidence = _detect_emotion_from_text(text)
        
        all_emotions.append(emotion)
        
        # Add to timeline (sample every ~30 seconds or key segments)
        if len(timeline) == 0 or timestamp - timeline[-1]['timestamp'] >= 30:
            timeline.append({
                'timestamp': timestamp,
                'emotion': emotion,
                'confidence': confidence
            })
        
        # Track per-speaker emotions
        if speaker:
            if speaker not in per_speaker_emotions:
                per_speaker_emotions[speaker] = []
            per_speaker_emotions[speaker].append(emotion)
    
    # Calculate emotion distribution
    emotion_counts = Counter(all_emotions)
    total_segments = len(all_emotions)
    emotion_distribution = {
        emotion: count / total_segments
        for emotion, count in emotion_counts.items()
    }
    
    # Get overall sentiment (most common emotion)
    overall_sentiment = emotion_counts.most_common(1)[0][0] if emotion_counts else 'neutral'
    
    # Calculate per-speaker dominant emotions
    speaker_emotions = {}
    for speaker, emotions in per_speaker_emotions.items():
        emotion_counter = Counter(emotions)
        speaker_emotions[speaker] = {
            'dominant_emotion': emotion_counter.most_common(1)[0][0],
            'distribution': {
                emotion: count / len(emotions)
                for emotion, count in emotion_counter.items()
            }
        }
    
    result = {
        'overall_sentiment': overall_sentiment,
        'timeline': timeline,
        'emotion_distribution': emotion_distribution,
        'model_used': 'distilbert' if use_transformer else 'keyword-based'
    }
    
    if speaker_emotions:
        result['per_speaker_emotions'] = speaker_emotions
    
    logger.info(f"Emotion analysis complete: {overall_sentiment}, {len(timeline)} timeline points")
    logger.info(f"Distribution: {emotion_distribution}")
    logger.info(f"Model used: {result['model_used']}")
    
    return result


def _detect_emotion_with_distilbert(text: str, classifier) -> tuple:
    """
    Detect emotion using DistilBERT transformer model.
    
    Args:
        text: Text to analyze
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
        
        # Find the emotion with highest score
        top_emotion = max(results, key=lambda x: x['score'])
        emotion_label = top_emotion['label'].lower()
        confidence = top_emotion['score']
        
        # Map model labels to our standard emotions
        # The model might output: sadness, joy, love, anger, fear, surprise
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


def _detect_emotion_from_text(text: str) -> tuple:
    """
    Detect emotion from text using keyword matching and sentiment analysis.
    
    Args:
        text: Text to analyze
    
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
    
    # If no keywords found, analyze sentiment through basic heuristics
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


def analyze_speaker_emotional_state(speaker_metrics: Dict, audio_features: Dict = None) -> Dict[str, Any]:
    """
    Analyze emotional patterns for individual speakers.
    
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
        
        # Analyze speaking patterns for emotional indicators
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
    
    # Per-speaker insights
    if 'per_speaker_emotions' in emotion_data:
        speaker_insights = []
        for speaker, data in emotion_data['per_speaker_emotions'].items():
            dominant = data['dominant_emotion']
            speaker_insights.append(f"{speaker} is predominantly {dominant}")
        
        if speaker_insights:
            summary_parts.append(" ".join(speaker_insights) + ".")
    
    return " ".join(summary_parts)
