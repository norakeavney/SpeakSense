"""
Speaker Metrics Analysis Service
Calculates comprehensive speaking patterns and statistics
Optimized for GPU worker deployment with proper error handling
"""
import re
import logging
import numpy as np
from collections import Counter
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    logger.warning("TextBlob not available - sentiment analysis limited")
    
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    logger.warning("VADER not available - sentiment analysis limited")


def calculate_speaker_metrics(
    transcription_result: Dict[str, Any], 
    diarization_result: Dict[str, Any]
) -> Dict[str, Any]:
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
    
    # Calculate bias analysis
    bias_analysis = calculate_bias_metrics(
        speaker_data, 
        questions_analysis, 
        sentiment_analysis, 
        leading_questions, 
        interruptions, 
        speakers
    )
    
    return {
        'speakers': speaker_data,
        'comparative': comparative,
        'questions_analysis': questions_analysis,
        'agreement_analysis': agreement_analysis,
        'sentiment_analysis': sentiment_analysis,
        'leading_questions': leading_questions,
        'interruptions': interruptions,
        'bias_analysis': bias_analysis,
        'summary': _generate_summary(speaker_data, comparative)
    }


def _calculate_single_speaker_metrics(turns: List[Dict]) -> Dict[str, Any]:
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


def _count_filler_words(text: str) -> int:
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


def _calculate_comparative_metrics(speaker_data: Dict[str, Any]) -> Dict[str, Any]:
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
    
    return {
        'time_distribution': time_percentages,
        'most_talkative_speaker': most_talkative,
        'least_talkative_speaker': least_talkative,
        'fastest_speaker': fastest_speaker,
        'slowest_speaker': slowest_speaker,
        'balance_score': round(balance_score, 3),
        'balance_interpretation': _interpret_balance(balance_score)
    }


def _interpret_balance(score: float) -> str:
    """Interpret balance score"""
    if score < 0.15:
        return "Well balanced conversation"
    elif score < 0.30:
        return "Slightly imbalanced"
    elif score < 0.50:
        return "Moderately imbalanced"
    else:
        return "Highly imbalanced - one speaker dominates"


def _generate_summary(speaker_data: Dict[str, Any], comparative: Dict[str, Any]) -> str:
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


def _generate_placeholder_metrics(transcription_result: Dict[str, Any]) -> Dict[str, Any]:
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


def analyse_questions_vs_statements(transcript: List[Dict]) -> Dict[str, Any]:
    """
    Classify segments as questions or statements
    
    Args:
        transcript: List of turn dictionaries with 'text' and 'speaker' keys
    
    Returns:
        Dict with question/statement analysis per speaker
    """
    speakers_analysis = {}
    
    # Question patterns (comprehensive)
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
    
    # Calculate ratios and detect roles
    for speaker in speakers_analysis:
        total = speakers_analysis[speaker]['questions'] + speakers_analysis[speaker]['statements']
        if total > 0:
            speakers_analysis[speaker]['question_ratio'] = round(
                speakers_analysis[speaker]['questions'] / total, 3
            )
            # Role detection with clear thresholds
            q_ratio = speakers_analysis[speaker]['question_ratio']
            if q_ratio >= 0.60:
                speakers_analysis[speaker]['likely_role'] = 'interviewer'
            elif q_ratio >= 0.30:
                speakers_analysis[speaker]['likely_role'] = 'moderator'
            else:
                speakers_analysis[speaker]['likely_role'] = 'interviewee'
    
    return speakers_analysis


def detect_agreement_disagreement(transcript: List[Dict]) -> Dict[str, Any]:
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


def calculate_sentiment_per_speaker(speaker_turns: List[Dict]) -> Dict[str, Any]:
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
    
    # Use VADER if available (better for short texts)
    if VADER_AVAILABLE:
        try:
            analyzer = SentimentIntensityAnalyzer()
            
            for turn in speaker_turns:
                text = turn.get('text', '')
                if text.strip():
                    scores = analyzer.polarity_scores(text)
                    results['sentiment_scores'].append({
                        'text': text[:100],
                        'positive': round(scores['pos'], 3),
                        'negative': round(scores['neg'], 3),
                        'neutral': round(scores['neu'], 3),
                        'compound': round(scores['compound'], 3)
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
                
        except Exception as e:
            logger.error(f"VADER sentiment analysis failed: {e}")
            results['error'] = 'Sentiment analysis failed'
    
    # Fallback to TextBlob if VADER not available
    elif TEXTBLOB_AVAILABLE:
        try:
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
        except Exception as e:
            logger.error(f"TextBlob sentiment analysis failed: {e}")
            results['error'] = 'Sentiment analysis failed'
    
    else:
        results['error'] = 'No sentiment analysis library available'
    
    return results


def detect_leading_questions(transcript: List[Dict]) -> Dict[str, Any]:
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
                if pattern not in speakers_analysis[speaker]['bias_indicators']:
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


def detect_interruptions(transcript: List[Dict]) -> Dict[str, Any]:
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


def calculate_bias_metrics(
    speaker_data: Dict[str, Any], 
    questions_analysis: Dict[str, Any], 
    sentiment_analysis: Dict[str, Any], 
    leading_questions: Dict[str, Any], 
    interruptions: Dict[str, Any], 
    speakers_list: List[str]
) -> Dict[str, Any]:
    """
    Calculate comprehensive bias metrics across all speakers.
    Identifies moderator, fairness indicators, and bias scores.
    
    Args:
        speaker_data: Dict of speaker metrics
        questions_analysis: Dict of questions/statements per speaker
        sentiment_analysis: Dict of sentiment per speaker
        leading_questions: Dict of leading questions per speaker
        interruptions: Dict of interruption data
        speakers_list: List of speaker names
    
    Returns:
        Dict with bias analysis including moderator profile and fairness metrics
    """
    if not speakers_list or len(speakers_list) < 2:
        return {'error': 'Need at least 2 speakers for bias analysis'}
    
    # Identify moderator (most questions, least speaking time)
    moderator = None
    moderator_score = -1
    
    for speaker in speakers_list:
        q_ratio = questions_analysis.get(speaker, {}).get('question_ratio', 0)
        speaking_time = speaker_data.get(speaker, {}).get('speaking_time_seconds', float('inf'))
        
        # Score: high question ratio + low speaking time = likely moderator
        mod_score = (q_ratio * 100) - (speaking_time / 10)
        
        if mod_score > moderator_score:
            moderator_score = mod_score
            moderator = speaker
    
    # Separate candidates from moderator
    candidates = [s for s in speakers_list if s != moderator]
    
    # Build candidate fairness analysis
    candidate_analysis = {}
    
    for candidate in candidates:
        cand_data = {
            'speaker': candidate,
            'role': 'candidate',
            'speaking_time': speaker_data.get(candidate, {}).get('speaking_time_seconds', 0),
            'words': speaker_data.get(candidate, {}).get('total_words', 0),
            'turns': speaker_data.get(candidate, {}).get('num_turns', 0),
            'questions_asked': questions_analysis.get(candidate, {}).get('questions', 0),
            'question_ratio': questions_analysis.get(candidate, {}).get('question_ratio', 0),
        }
        
        # Sentiment received (indicator of bias toward candidate)
        sentiment_data = sentiment_analysis.get(candidate, {}).get('overall_sentiment', {})
        if isinstance(sentiment_data, dict):
            cand_data['sentiment_score'] = sentiment_data.get('compound', 0)
            cand_data['sentiment_label'] = sentiment_analysis.get(candidate, {}).get('sentiment_label', 'neutral')
        else:
            cand_data['sentiment_score'] = sentiment_data.get('polarity', 0) if isinstance(sentiment_data, dict) else 0
            cand_data['sentiment_label'] = 'neutral'
        
        # Leading questions directed at this candidate
        lq_data = leading_questions.get(moderator if moderator else candidates[0], {})
        cand_data['leading_questions_toward_candidate'] = lq_data.get('leading_questions', 0)
        
        # Interruptions made by candidate
        int_stats = interruptions.get('speaker_stats', {}).get(candidate, {})
        cand_data['interruptions_made'] = int_stats.get('interruptions_made', 0)
        cand_data['interrupted_count'] = int_stats.get('interrupted_by_others', 0)
        cand_data['dominance_score'] = int_stats.get('dominance_score', 0)
        
        candidate_analysis[candidate] = cand_data
    
    # Calculate fairness metrics
    speaking_times = [cand_data['speaking_time'] for cand_data in candidate_analysis.values()]
    
    if speaking_times and sum(speaking_times) > 0:
        time_distribution = {
            speaker: round((candidate_analysis[speaker]['speaking_time'] / sum(speaking_times)) * 100, 1)
            for speaker in candidate_analysis
        }
    else:
        time_distribution = {speaker: 0 for speaker in candidate_analysis}
    
    # Calculate imbalance score (0 = fair, 1 = completely unfair)
    if speaking_times:
        max_time = max(speaking_times)
        min_time = min(speaking_times)
        time_variance = (max_time - min_time) / (max_time + min_time) if (max_time + min_time) > 0 else 0
    else:
        time_variance = 0
    
    # Calculate sentiment bias (how consistently positive/negative moderator was)
    moderator_sentiment = sentiment_analysis.get(moderator, {}).get('overall_sentiment', {})
    if isinstance(moderator_sentiment, dict):
        moderator_sentiment_score = moderator_sentiment.get('compound', 0)
    else:
        moderator_sentiment_score = moderator_sentiment.get('polarity', 0) if isinstance(moderator_sentiment, dict) else 0
    
    # Calculate question distribution fairness
    questions_per_candidate = {
        speaker: questions_analysis.get(speaker, {}).get('questions', 0)
        for speaker in candidate_analysis
    }
    
    if questions_per_candidate and sum(questions_per_candidate.values()) > 0:
        total_q = sum(questions_per_candidate.values())
        question_distribution = {
            speaker: round((q / total_q) * 100, 1) if total_q > 0 else 0
            for speaker, q in questions_per_candidate.items()
        }
    else:
        question_distribution = {}
    
    # Calculate overall bias score (0-100, higher = more biased)
    bias_factors = []
    
    # Factor 1: Unequal speaking time (0-30 points)
    if len(speaking_times) >= 2:
        bias_factors.append(min(time_variance * 30, 30))
    
    # Factor 2: Unequal questions asked (0-30 points)
    if len(question_distribution) >= 2:
        questions_values = list(question_distribution.values())
        question_variance = (max(questions_values) - min(questions_values)) / 100 if len(questions_values) >= 2 else 0
        bias_factors.append(min(question_variance * 30, 30))
    
    # Factor 3: Moderator sentiment bias (0-20 points)
    moderator_bias = abs(moderator_sentiment_score) * 20
    bias_factors.append(min(moderator_bias, 20))
    
    # Factor 4: Leading questions (0-20 points)
    lq_count = leading_questions.get(moderator if moderator else '', {}).get('leading_questions', 0)
    lq_ratio = leading_questions.get(moderator if moderator else '', {}).get('bias_score', 0)
    bias_factors.append(min(lq_ratio * 20, 20))
    
    overall_bias_score = round(sum(bias_factors) / len(bias_factors) if bias_factors else 0, 1)
    
    # Interpret bias level
    if overall_bias_score >= 70:
        bias_level = 'SEVERE'
        bias_description = 'Significant bias detected. Moderator severely favored one or more candidates.'
    elif overall_bias_score >= 50:
        bias_level = 'HIGH'
        bias_description = 'High bias detected. Noticeable favoritism toward certain candidates.'
    elif overall_bias_score >= 30:
        bias_level = 'MODERATE'
        bias_description = 'Moderate bias detected. Some fairness issues present.'
    elif overall_bias_score >= 15:
        bias_level = 'LOW'
        bias_description = 'Low bias detected. Generally fair but minor inconsistencies.'
    else:
        bias_level = 'MINIMAL'
        bias_description = 'Minimal bias detected. Conversation appears well-balanced and fair.'
    
    question_variance = (max(questions_values) - min(questions_values)) / 100 if len(question_distribution) >= 2 else 0
    
    return {
        'overall_bias_score': overall_bias_score,
        'bias_level': bias_level,
        'bias_description': bias_description,
        'bias_factors': {
            'speaking_time_variance': round(time_variance, 3),
            'question_distribution_variance': round(question_variance, 3),
            'moderator_sentiment_bias': round(abs(moderator_sentiment_score), 3),
            'leading_questions_ratio': round(lq_ratio, 3)
        },
        'moderator': {
            'speaker': moderator,
            'role': 'moderator',
            'speaking_time': speaker_data.get(moderator, {}).get('speaking_time_seconds', 0) if moderator else 0,
            'sentiment_score': moderator_sentiment_score,
            'sentiment_label': sentiment_analysis.get(moderator, {}).get('sentiment_label', 'neutral') if moderator else 'neutral',
            'questions_asked': questions_analysis.get(moderator, {}).get('questions', 0) if moderator else 0,
            'leading_questions_count': lq_count,
            'leading_questions_ratio': lq_ratio
        },
        'candidates': candidate_analysis,
        'time_distribution': time_distribution,
        'question_distribution': question_distribution,
        'fairness_metrics': {
            'time_balance': round(1 - time_variance, 3),  # Higher = more balanced
            'time_most_given_to': max(time_distribution, key=time_distribution.get) if time_distribution else None,
            'time_least_given_to': min(time_distribution, key=time_distribution.get) if time_distribution else None,
            'time_spread_percent': round((max(time_distribution.values()) - min(time_distribution.values())) if time_distribution else 0, 1),
        }
    }


def extract_topics_per_speaker(transcript: List[Dict], topics_data: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Extract main topics discussed by each speaker using topic extraction.
    
    Args:
        transcript: List of turn dictionaries with 'text' and 'speaker' keys
        topics_data: Global topics data (optional, for reference scoring)
    
    Returns:
        Dict with topic analysis per speaker
    """
    if not transcript:
        logger.warning("Empty transcript provided to extract_topics_per_speaker")
        return {}
    
    speaker_topics: Dict[str, Any] = {}
    global_scores: Dict[str, float] = {}
    
    # Get global topic scores for reference
    if topics_data and topics_data.get('scores'):
        global_scores = topics_data['scores']
    
    # Group turns by speaker
    speakers_turns: Dict[str, List[Dict]] = {}
    for turn in transcript:
        speaker = turn.get('speaker', 'unknown')
        if speaker not in speakers_turns:
            speakers_turns[speaker] = []
        speakers_turns[speaker].append(turn)
    
    # Extract topics/keywords for each speaker using regex-based keyword extraction
    for speaker, turns in speakers_turns.items():
        speaker_text = " ".join([turn.get('text', '') for turn in turns])
        
        if not speaker_text.strip():
            speaker_topics[speaker] = {
                'topics': [],
                'keywords': [],
                'scores': {}
            }
            continue
        
        try:
            # Extract keywords using simple frequency analysis
            words = speaker_text.lower().split()
            # Filter out common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'is',
                'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
                'do', 'does', 'did', 'will', 'would', 'should', 'could', 'i', 'you',
                'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'where',
                'when', 'why', 'how', 'that', 'this', 'these', 'those', 'very',
                'too', 'so', 'just', 'only', 'then', 'now', 'here', 'there'
            }
            
            keywords = [w for w in words if w not in stop_words and len(w) > 2]
            keyword_freq = Counter(keywords)
            top_keywords = [kw for kw, _ in keyword_freq.most_common(15)]
            
            # Derive topics from keyword frequency
            topics = top_keywords[:6] if top_keywords else []
            
            # Create keyword scores (frequency-based)
            scores = {
                kw: round(keyword_freq[kw] / len(keywords), 3) if keywords else 0
                for kw in top_keywords
            }
            
            speaker_topics[speaker] = {
                'topics': topics,
                'keywords': top_keywords,
                'scores': scores,
                'turn_count': len(turns)
            }
            logger.debug(f"Extracted {len(topics)} topics for speaker {speaker}")
            
        except Exception as e:
            logger.error(f"Topic extraction for {speaker} failed: {e}")
            speaker_topics[speaker] = {
                'topics': [],
                'keywords': [],
                'scores': {},
                'error': str(e)
            }
    
    return speaker_topics


def analyze_topic_sentiment(transcript: List[Dict], topics_list: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Analyze sentiment of specific topics mentioned by speakers.
    
    Args:
        transcript: List of turn dictionaries with 'text' and 'speaker' keys
        topics_list: List of topics to analyze (None = use all keywords from all turns)
    
    Returns:
        Dict with sentiment analysis per topic and speaker
    """
    if not transcript:
        logger.warning("Empty transcript provided to analyze_topic_sentiment")
        return {}
    
    if not topics_list:
        logger.warning("No topics provided to analyze_topic_sentiment")
        return {}
    
    sentiment_per_topic: Dict[str, Any] = {}
    
    # Use VADER for sentiment analysis
    if not VADER_AVAILABLE:
        logger.error("VADER sentiment analyzer not available")
        return {'error': 'VADER sentiment analyzer not available'}
    
    try:
        analyzer = SentimentIntensityAnalyzer()
    except Exception as e:
        logger.error(f"Failed to initialize VADER analyzer: {e}")
        return {'error': f'Failed to initialize sentiment analyzer: {e}'}
    
    # For each topic, find relevant segments and analyze sentiment
    for topic in topics_list:
        topic_lower = topic.lower()
        sentiment_per_topic[topic] = {
            'mentions': 0,
            'positive_mentions': 0,
            'negative_mentions': 0,
            'neutral_mentions': 0,
            'average_sentiment': 0,
            'per_speaker': {},
            'example_passages': []
        }
        
        topic_sentiments: List[float] = []
        
        try:
            for turn in transcript:
                text = turn.get('text', '')
                speaker = turn.get('speaker', 'unknown')
                
                # Check if topic is mentioned in this turn
                if topic_lower in text.lower():
                    sentiment_per_topic[topic]['mentions'] += 1
                    
                    # Analyze sentiment of this turn
                    scores = analyzer.polarity_scores(text)
                    compound = scores['compound']
                    
                    topic_sentiments.append(compound)
                    
                    # Categorize sentiment
                    if compound >= 0.05:
                        sentiment_per_topic[topic]['positive_mentions'] += 1
                        category = 'positive'
                    elif compound <= -0.05:
                        sentiment_per_topic[topic]['negative_mentions'] += 1
                        category = 'negative'
                    else:
                        sentiment_per_topic[topic]['neutral_mentions'] += 1
                        category = 'neutral'
                    
                    # Track per-speaker sentiment
                    if speaker not in sentiment_per_topic[topic]['per_speaker']:
                        sentiment_per_topic[topic]['per_speaker'][speaker] = {
                            'mentions': 0,
                            'positive': 0,
                            'negative': 0,
                            'neutral': 0,
                            'compounds': []
                        }
                    
                    sentiment_per_topic[topic]['per_speaker'][speaker]['mentions'] += 1
                    sentiment_per_topic[topic]['per_speaker'][speaker]['compounds'].append(compound)
                    
                    if category == 'positive':
                        sentiment_per_topic[topic]['per_speaker'][speaker]['positive'] += 1
                    elif category == 'negative':
                        sentiment_per_topic[topic]['per_speaker'][speaker]['negative'] += 1
                    else:
                        sentiment_per_topic[topic]['per_speaker'][speaker]['neutral'] += 1
                    
                    # Store example passages
                    if len(sentiment_per_topic[topic]['example_passages']) < 3:
                        sentiment_per_topic[topic]['example_passages'].append({
                            'text': text[:150],
                            'speaker': speaker,
                            'sentiment': category,
                            'score': round(compound, 3)
                        })
            
            # Calculate average sentiment
            if topic_sentiments:
                sentiment_per_topic[topic]['average_sentiment'] = round(
                    sum(topic_sentiments) / len(topic_sentiments), 3
                )
                
                # Calculate percentages per speaker
                for speaker in sentiment_per_topic[topic]['per_speaker']:
                    data = sentiment_per_topic[topic]['per_speaker'][speaker]
                    if data['mentions'] > 0:
                        data['avg_compound'] = round(
                            sum(data['compounds']) / len(data['compounds']), 3
                        )
                        data['positive_pct'] = round(
                            (data['positive'] / data['mentions']) * 100, 1
                        )
                        data['negative_pct'] = round(
                            (data['negative'] / data['mentions']) * 100, 1
                        )
                        data['neutral_pct'] = round(
                            (data['neutral'] / data['mentions']) * 100, 1
                        )
                        # Remove the raw compounds list from final output
                        del data['compounds']
                
                logger.debug(f"Analyzed sentiment for topic '{topic}': {sentiment_per_topic[topic]['average_sentiment']}")
        
        except Exception as e:
            logger.error(f"Topic sentiment analysis failed for topic '{topic}': {e}")
            sentiment_per_topic[topic]['error'] = str(e)
    
    return sentiment_per_topic
