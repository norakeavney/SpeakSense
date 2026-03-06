"""
Speaker Metrics Analysis Service
Calculates comprehensive speaking patterns and statistics
"""
import re
import numpy as np
from collections import Counter

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False


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
    
    # Add enhanced analysis features
    questions_analysis = analyse_questions_vs_statements(transcript)
    agreement_analysis = detect_agreement_disagreement(transcript)
    leading_questions = detect_leading_questions(transcript)
    interruptions = detect_interruptions(transcript)
    
    # Add sentiment analysis per speaker
    sentiment_analysis = {}
    for speaker in speakers:
        speaker_turns = [turn for turn in transcript if turn.get('speaker') == speaker]
        if speaker_turns:
            sentiment_analysis[speaker] = calculate_sentiment_per_speaker(speaker_turns)
    
    return {
        'speakers': speaker_data,
        'comparative': comparative,
        'questions_analysis': questions_analysis,
        'agreement_analysis': agreement_analysis,
        'sentiment_analysis': sentiment_analysis,
        'leading_questions': leading_questions,
        'interruptions': interruptions,
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

def analyse_questions_vs_statements(transcript):
    """
    Classify segments as questions or statements
    
    Args:
        transcript: List of turn dictionaries with 'text' and 'speaker' keys
    
    Returns:
        Dict with question/statement analysis per speaker
    """
    speakers_analysis = {}
    
    # Question patterns (more comprehensive)
    question_patterns = [
        r'\?',  # Direct question mark
        r'^(what|when|where|why|how|who|which|whose|whom)\b',  # Wh- questions
        r'^(is|are|was|were|do|does|did|can|could|will|would|should|shall|may|might|have|has|had)\b',  # Yes/no questions
        r'^(don\'t you|wouldn\'t you|isn\'t it|aren\'t you|didn\'t you)\b',  # Tag questions
        r'\b(right|correct|true)\?$',  # Confirmation questions
    ]
    
    for turn in transcript:
        speaker = turn.get('speaker', 'unknown')
        text = turn.get('text', '').strip().lower()
        
        if not text:
            continue
            
        if speaker not in speakers_analysis:
            speakers_analysis[speaker] = {
                'questions': 0,
                'statements': 0,
                'question_examples': [],
                'statement_examples': []
            }
        
        # Check if it's a question
        is_question = False
        for pattern in question_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                is_question = True
                break
        
        if is_question:
            speakers_analysis[speaker]['questions'] += 1
            if len(speakers_analysis[speaker]['question_examples']) < 3:
                speakers_analysis[speaker]['question_examples'].append(turn.get('text', '')[:100])
        else:
            speakers_analysis[speaker]['statements'] += 1
            if len(speakers_analysis[speaker]['statement_examples']) < 3:
                speakers_analysis[speaker]['statement_examples'].append(turn.get('text', '')[:100])
    
    # Calculate ratios
    for speaker in speakers_analysis:
        total = speakers_analysis[speaker]['questions'] + speakers_analysis[speaker]['statements']
        if total > 0:
            speakers_analysis[speaker]['question_ratio'] = round(
                speakers_analysis[speaker]['questions'] / total, 3
            )
            speakers_analysis[speaker]['likely_role'] = (
                'interviewer' if speakers_analysis[speaker]['question_ratio'] > 0.3 
                else 'interviewee'
            )
    
    return speakers_analysis


def detect_agreement_disagreement(transcript):
    """
    Detect agreement and disagreement patterns
    
    Args:
        transcript: List of turn dictionaries with 'text' and 'speaker' keys
    
    Returns:
        Dict with agreement/disagreement analysis per speaker
    """
    speakers_analysis = {}
    
    agreement_patterns = [
        r'\b(yes|yeah|yep|absolutely|exactly|right|correct|true|agreed?|definitely)\b',
        r'\b(i agree|that\'s right|you\'re right|exactly right|spot on)\b',
        r'\b(good point|makes sense|i think so too|no doubt)\b'
    ]
    
    disagreement_patterns = [
        r'\b(no|nope|not really|i disagree|actually)\b',
        r'\b(that\'s wrong|i don\'t think|i doubt|but)\b',
        r'\b(however|on the contrary|i\'d argue|not necessarily)\b'
    ]
    
    for turn in transcript:
        speaker = turn.get('speaker', 'unknown')
        text = turn.get('text', '').lower()
        
        if not text:
            continue
            
        if speaker not in speakers_analysis:
            speakers_analysis[speaker] = {
                'agreements': 0,
                'disagreements': 0,
                'agreement_examples': [],
                'disagreement_examples': []
            }
        
        # Check for agreement
        for pattern in agreement_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                speakers_analysis[speaker]['agreements'] += 1
                if len(speakers_analysis[speaker]['agreement_examples']) < 3:
                    speakers_analysis[speaker]['agreement_examples'].append(turn.get('text', '')[:100])
                break
        
        # Check for disagreement
        for pattern in disagreement_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                speakers_analysis[speaker]['disagreements'] += 1
                if len(speakers_analysis[speaker]['disagreement_examples']) < 3:
                    speakers_analysis[speaker]['disagreement_examples'].append(turn.get('text', '')[:100])
                break
    
    # Calculate confrontation scores
    for speaker in speakers_analysis:
        total = speakers_analysis[speaker]['agreements'] + speakers_analysis[speaker]['disagreements']
        if total > 0:
            speakers_analysis[speaker]['confrontation_score'] = round(
                speakers_analysis[speaker]['disagreements'] / total, 3
            )
            if speakers_analysis[speaker]['confrontation_score'] > 0.6:
                speakers_analysis[speaker]['communication_style'] = 'confrontational'
            elif speakers_analysis[speaker]['confrontation_score'] > 0.3:
                speakers_analysis[speaker]['communication_style'] = 'questioning'
            else:
                speakers_analysis[speaker]['communication_style'] = 'agreeable'
    
    return speakers_analysis


def calculate_sentiment_per_speaker(speaker_turns):
    """
    Calculate sentiment scores using VADER/TextBlob
    
    Args:
        speaker_turns: List of turn dictionaries for a single speaker
    
    Returns:
        Dict with sentiment analysis results
    """
    if not speaker_turns:
        return {}
    
    all_text = " ".join([turn.get('text', '') for turn in speaker_turns])
    
    results = {
        'total_turns': len(speaker_turns),
        'sentiment_scores': []
    }
    
    # Use VADER if available (better for short texts and social media)
    if VADER_AVAILABLE:
        analyzer = SentimentIntensityAnalyzer()
        
        for turn in speaker_turns:
            text = turn.get('text', '')
            if text.strip():
                scores = analyzer.polarity_scores(text)
                results['sentiment_scores'].append({
                    'text': text[:100],
                    'positive': scores['pos'],
                    'negative': scores['neg'],
                    'neutral': scores['neu'],
                    'compound': scores['compound']
                })
        
        # Overall sentiment
        overall = analyzer.polarity_scores(all_text)
        results['overall_sentiment'] = {
            'positive': round(overall['pos'], 3),
            'negative': round(overall['neg'], 3),
            'neutral': round(overall['neu'], 3),
            'compound': round(overall['compound'], 3)
        }
        
        # Interpret compound score
        if overall['compound'] >= 0.05:
            results['sentiment_label'] = 'positive'
        elif overall['compound'] <= -0.05:
            results['sentiment_label'] = 'negative'
        else:
            results['sentiment_label'] = 'neutral'
            
    # Fallback to TextBlob if VADER not available
    elif TEXTBLOB_AVAILABLE:
        blob = TextBlob(all_text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        results['overall_sentiment'] = {
            'polarity': round(polarity, 3),  # -1 (negative) to 1 (positive)
            'subjectivity': round(subjectivity, 3)  # 0 (objective) to 1 (subjective)
        }
        
        if polarity > 0.1:
            results['sentiment_label'] = 'positive'
        elif polarity < -0.1:
            results['sentiment_label'] = 'negative'
        else:
            results['sentiment_label'] = 'neutral'
    
    else:
        results['error'] = 'No sentiment analysis library available (install textblob or vaderSentiment)'
    
    return results


def detect_leading_questions(transcript):
    """
    Identify biased or leading questions
    
    Args:
        transcript: List of turn dictionaries with 'text' and 'speaker' keys
    
    Returns:
        Dict with leading question analysis per speaker
    """
    speakers_analysis = {}
    
    # Patterns that suggest leading questions
    leading_patterns = [
        r'don\'t you think',
        r'wouldn\'t you agree',
        r'isn\'t it true that',
        r'wouldn\'t you say',
        r'don\'t you believe',
        r'surely you must',
        r'obviously',
        r'clearly',
        r'undoubtedly',
        r'wouldn\'t it be fair to say',
        r'isn\'t it obvious',
        r'you must admit',
        r'certainly you',
        r'of course you'
    ]
    
    for turn in transcript:
        speaker = turn.get('speaker', 'unknown')
        text = turn.get('text', '').lower()
        
        if not text or '?' not in turn.get('text', ''):
            continue  # Only analyze questions
            
        if speaker not in speakers_analysis:
            speakers_analysis[speaker] = {
                'total_questions': 0,
                'leading_questions': 0,
                'leading_examples': [],
                'bias_indicators': []
            }
        
        speakers_analysis[speaker]['total_questions'] += 1
        
        # Check for leading patterns
        leading_found = False
        for pattern in leading_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                leading_found = True
                speakers_analysis[speaker]['bias_indicators'].append(pattern)
                break
        
        if leading_found:
            speakers_analysis[speaker]['leading_questions'] += 1
            if len(speakers_analysis[speaker]['leading_examples']) < 3:
                speakers_analysis[speaker]['leading_examples'].append(turn.get('text', ''))
    
    # Calculate bias score
    for speaker in speakers_analysis:
        total_q = speakers_analysis[speaker]['total_questions']
        leading_q = speakers_analysis[speaker]['leading_questions']
        
        if total_q > 0:
            speakers_analysis[speaker]['bias_score'] = round(leading_q / total_q, 3)
            
            if speakers_analysis[speaker]['bias_score'] > 0.3:
                speakers_analysis[speaker]['bias_level'] = 'high'
            elif speakers_analysis[speaker]['bias_score'] > 0.1:
                speakers_analysis[speaker]['bias_level'] = 'moderate'
            else:
                speakers_analysis[speaker]['bias_level'] = 'low'
    
    return speakers_analysis


def detect_interruptions(transcript):
    """
    Detect when speakers interrupt each other based on timestamps
    
    Args:
        transcript: List of turn dictionaries with 'start', 'end', 'speaker', 'text'
    
    Returns:
        Dict with interruption analysis
    """
    if len(transcript) < 2:
        return {}
    
    interruptions = []
    speakers_stats = {}
    
    for i in range(len(transcript) - 1):
        current_turn = transcript[i]
        next_turn = transcript[i + 1]
        
        current_speaker = current_turn.get('speaker')
        next_speaker = next_turn.get('speaker')
        
        if current_speaker == next_speaker:
            continue
            
        current_end = current_turn.get('end', 0)
        next_start = next_turn.get('start', 0)
        
        # Initialize speaker stats
        for speaker in [current_speaker, next_speaker]:
            if speaker not in speakers_stats:
                speakers_stats[speaker] = {
                    'interruptions_made': 0,
                    'interrupted_by_others': 0,
                    'interruption_examples': []
                }
        
        # Check for interruption (next speaker starts before current ends)
        if next_start < current_end:
            overlap_duration = current_end - next_start
            
            interruption = {
                'interrupted_speaker': current_speaker,
                'interrupting_speaker': next_speaker,
                'overlap_duration': round(overlap_duration, 2),
                'interrupted_text': current_turn.get('text', '')[:100],
                'interrupting_text': next_turn.get('text', '')[:100]
            }
            
            interruptions.append(interruption)
            speakers_stats[next_speaker]['interruptions_made'] += 1
            speakers_stats[current_speaker]['interrupted_by_others'] += 1
            
            # Store examples
            if len(speakers_stats[next_speaker]['interruption_examples']) < 3:
                speakers_stats[next_speaker]['interruption_examples'].append(
                    f"Interrupted: '{current_turn.get('text', '')[:50]}...' with '{next_turn.get('text', '')[:50]}...'"
                )
    
    # Calculate interruption rates
    for speaker in speakers_stats:
        total_interruptions = speakers_stats[speaker]['interruptions_made'] + speakers_stats[speaker]['interrupted_by_others']
        if total_interruptions > 0:
            speakers_stats[speaker]['dominance_score'] = round(
                speakers_stats[speaker]['interruptions_made'] / total_interruptions, 3
            )
    
    return {
        'total_interruptions': len(interruptions),
        'interruption_details': interruptions[:10],  # Limit to first 10
        'speaker_stats': speakers_stats
    }


# TODO: def analyse_pauses(transcript, audio_path):
#     """analyse silence/pause patterns between turns"""
#     pass

# TODO: def detect_emotions_per_speaker(speaker_turns):
#     """Detect emotions using DistilBERT model"""
#     pass

# TODO: def extract_topics_per_speaker(speaker_turns):
#     """Extract main topics discussed by each speaker using KeyBERT"""
#     pass

# TODO: def analyse_loudness_per_speaker(audio_path, transcript):
#     """analyse audio loudness and tone per speaker"""
#     pass