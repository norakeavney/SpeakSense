"""
Speaker Metrics Analysis Service
Calculates comprehensive speaking patterns and statistics
"""
import re
import numpy as np
from collections import Counter


def calculate_speaker_metrics(transcription_result, diarization_result):
    """
    Calculate comprehensive speaker metrics from transcription and diarization
    
    Args:
        transcription_result: Dict with 'segments' containing transcribed text
        diarization_result: Dict with speaker-labeled transcript
    
    Returns:
        Dict with detailed speaker metrics
    """
    if not diarization_result or not diarization_result.get('transcript'):
        return _generate_placeholder_metrics(transcription_result)
    
    transcript = diarization_result['transcript']
    speakers = diarization_result.get('speakers', [])
    
    # Aggregate metrics per speaker
    speaker_data = {}
    
    for speaker in speakers:
        speaker_turns = [turn for turn in transcript if turn.get('speaker') == speaker]
        
        if not speaker_turns:
            continue
        
        # Calculate metrics
        metrics = _calculate_single_speaker_metrics(speaker_turns)
        speaker_data[speaker] = metrics
    
    # Calculate comparative metrics
    comparative = _calculate_comparative_metrics(speaker_data)
    
    # TODO: Add interruption detection metrics
    # - Count overlapping speech segments
    # - Identify who interrupts whom most frequently
    # - Calculate interruption rate per speaker
    
    # TODO: Add pause/silence analysis
    # - Detect pauses between turns
    # - Calculate average pause duration per speaker
    # - Identify hesitation patterns
    
    # TODO: Add per-topic metrics (requires topic extraction first)
    # - WPM per topic
    # - Speaking time per topic
    # - Dominant speaker per topic
    
    return {
        'speakers': speaker_data,
        'comparative': comparative,
        'summary': _generate_summary(speaker_data, comparative)
    }


def _calculate_single_speaker_metrics(turns):
    """Calculate metrics for a single speaker"""
    
    # Collect all text
    all_text = " ".join([turn.get('text', '') for turn in turns])
    words = all_text.split()
    
    # Calculate time metrics
    total_time = sum([turn.get('end', 0) - turn.get('start', 0) for turn in turns])
    
    # Words per minute
    wpm = (len(words) / total_time * 60) if total_time > 0 else 0
    
    # Turn-taking metrics
    num_turns = len(turns)
    avg_turn_duration = total_time / num_turns if num_turns > 0 else 0
    
    # Word metrics
    total_words = len(words)
    unique_words = len(set(word.lower() for word in words))
    lexical_diversity = unique_words / total_words if total_words > 0 else 0
    
    # Vocabulary complexity
    avg_word_length = sum(len(word) for word in words) / total_words if total_words > 0 else 0
    long_words = sum(1 for word in words if len(word) > 6)
    long_word_percentage = (long_words / total_words * 100) if total_words > 0 else 0
    
    # Filler words
    filler_count = _count_filler_words(all_text)
    filler_rate = (filler_count / (total_time / 60)) if total_time > 0 else 0
    
    # TODO: Add sentiment analysis per speaker
    # - Use VADER or TextBlob for sentiment scoring
    # - Calculate positive/negative/neutral percentages
    # - Track sentiment changes over time
    
    # TODO: Add emotion detection per speaker (using your DistilBERT code)
    # - Emotion distribution (anger, joy, sadness, fear, surprise, neutral)
    # - Dominant emotion per speaker
    # - Emotional intensity tracking
    
    # TODO: Add utterance length analysis
    # - Average words per turn
    # - Shortest/longest utterances
    # - Utterance length distribution
    
    # TODO: Add question vs statement analysis
    # - Count questions asked
    # - Count statements made
    # - Calculate question/statement ratio
    # - Identify role (interviewer vs interviewee)
    
    # TODO: Add agreement/disagreement detection
    # - Detect agreement markers ("yes", "exactly", "I agree")
    # - Detect disagreement markers ("no", "actually", "I disagree")
    # - Calculate confrontation score
    
    # TODO: Add leading questions detection
    # - Identify biased question patterns
    # - Flag manipulative phrasing
    
    return {
        'speaking_time_seconds': round(total_time, 2),
        'words_per_minute': round(wpm, 1),
        'total_words': total_words,
        'unique_words': unique_words,
        'lexical_diversity': round(lexical_diversity, 3),
        'avg_word_length': round(avg_word_length, 2),
        'long_word_percentage': round(long_word_percentage, 1),
        'num_turns': num_turns,
        'avg_turn_duration': round(avg_turn_duration, 2),
        'filler_words': filler_count,
        'filler_rate_per_minute': round(filler_rate, 2)
    }


def _count_filler_words(text):
    """Count filler words in text"""
    filler_words = [
        'um', 'uh', 'like', 'you know', 'i mean', 
        'sort of', 'kind of', 'actually', 'basically', 
        'literally', 'right', 'okay', 'so', 'well'
    ]
    
    text_lower = text.lower()
    count = 0
    
    for filler in filler_words:
        count += len(re.findall(r'\b' + re.escape(filler) + r'\b', text_lower))
    
    return count


def _calculate_comparative_metrics(speaker_data):
    """Calculate metrics comparing speakers"""
    
    if len(speaker_data) < 2:
        return {}
    
    speakers = list(speaker_data.keys())
    
    # Speaking time comparison
    times = {s: speaker_data[s]['speaking_time_seconds'] for s in speakers}
    total_time = sum(times.values())
    time_percentages = {s: round(t / total_time * 100, 1) for s, t in times.items()}
    
    # WPM comparison
    wpms = {s: speaker_data[s]['words_per_minute'] for s in speakers}
    
    # Dominance metrics
    most_talkative = max(times.keys(), key=lambda k: times[k])
    least_talkative = min(times.keys(), key=lambda k: times[k])
    
    fastest_speaker = max(wpms.keys(), key=lambda k: wpms[k])
    slowest_speaker = min(wpms.keys(), key=lambda k: wpms[k])
    
    # Balance score (0 = perfectly balanced, 1 = completely imbalanced)
    time_values = list(times.values())
    balance_score = (max(time_values) - min(time_values)) / sum(time_values) if sum(time_values) > 0 else 0
    
    # TODO: Add turn-taking frequency analysis
    # - Calculate speaker switches per minute
    # - Identify who controls conversation flow
    # - analyse turn-taking patterns (who follows whom)
    
    # TODO: Add dominance ratio calculation
    # - Calculate speaking time ratio
    # - Identify conversational dominance patterns
    
    # TODO: Add loudness/tone comparison (requires audio feature extraction)
    # - Compare average loudness between speakers
    # - analyse pitch/tone variations
    # - Detect aggressive vs calm speaking patterns
    
    return {
        'time_distribution': time_percentages,
        'most_talkative_speaker': most_talkative,
        'least_talkative_speaker': least_talkative,
        'fastest_speaker': fastest_speaker,
        'slowest_speaker': slowest_speaker,
        'balance_score': round(balance_score, 3),
        'balance_interpretation': _interpret_balance(balance_score)
    }


def _interpret_balance(score):
    """Interpret balance score"""
    if score < 0.15:
        return "Well balanced conversation"
    elif score < 0.30:
        return "Slightly imbalanced"
    elif score < 0.50:
        return "Moderately imbalanced"
    else:
        return "Highly imbalanced - one speaker dominates"


def _generate_summary(speaker_data, comparative):
    """Generate human-readable summary"""
    num_speakers = len(speaker_data)
    
    summary_lines = [
        f"Detected {num_speakers} speaker(s)"
    ]
    
    if comparative:
        summary_lines.append(
            f"Speaking time: {comparative.get('balance_interpretation', 'Unknown balance')}"
        )
        summary_lines.append(
            f"Most talkative: {comparative.get('most_talkative_speaker', 'Unknown')}"
        )
    
    return "\n".join(summary_lines)


def _generate_placeholder_metrics(transcription_result):
    """Generate placeholder metrics when diarization is unavailable"""
    
    segments = transcription_result.get('segments', [])
    all_text = " ".join([seg.get('text', '') for seg in segments])
    words = all_text.split()
    
    total_time = segments[-1].get('end', 0) - segments[0].get('start', 0) if segments else 0
    wpm = (len(words) / total_time * 60) if total_time > 0 else 0
    
    return {
        'speakers': {
            'SPEAKER_00': {
                'speaking_time_seconds': round(total_time, 2),
                'words_per_minute': round(wpm, 1),
                'total_words': len(words),
                'unique_words': len(set(word.lower() for word in words)),
                'num_turns': len(segments),
                'note': 'Single speaker detected - no diarization performed'
            }
        },
        'comparative': {},
        'summary': f"Single speaker detected. Duration: {round(total_time, 1)}s, WPM: {round(wpm, 1)}"
    }


# ============================================================
# TODO: FUTURE METRIC FUNCTIONS TO IMPLEMENT
# ============================================================

# TODO: def detect_interruptions(transcript):
#     """Detect when speakers interrupt each other"""
#     pass

# TODO: def analyse_pauses(transcript, audio_path):
#     """analyse silence/pause patterns between turns"""
#     pass

# TODO: def calculate_sentiment_per_speaker(speaker_turns):
#     """Calculate sentiment scores using VADER/TextBlob"""
#     pass

# TODO: def detect_emotions_per_speaker(speaker_turns):
#     """Detect emotions using DistilBERT model"""
#     pass

# TODO: def analyse_questions_vs_statements(transcript):
#     """Classify segments as questions or statements"""
#     pass

# TODO: def detect_agreement_disagreement(transcript):
#     """Detect agreement and disagreement patterns"""
#     pass

# TODO: def detect_leading_questions(transcript):
#     """Identify biased or leading questions"""
#     pass

# TODO: def extract_topics_per_speaker(speaker_turns):
#     """Extract main topics discussed by each speaker using KeyBERT"""
#     pass

# TODO: def analyse_loudness_per_speaker(audio_path, transcript):
#     """analyse audio loudness and tone per speaker"""
#     pass