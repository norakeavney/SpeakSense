"""
Test the new speaker analysis functions
"""

def test_new_speaker_functions():
    """Test all the new speaker analysis functions with sample data"""
    
    # Sample transcript data
    sample_transcript = [
        {
            'speaker': 'SPEAKER_00',
            'text': "Thank you for joining me today. What are your thoughts on this topic?",
            'start': 0.0,
            'end': 5.5
        },
        {
            'speaker': 'SPEAKER_01', 
            'text': "I absolutely agree with your assessment. It's exactly what I was thinking.",
            'start': 6.0,
            'end': 10.0
        },
        {
            'speaker': 'SPEAKER_00',
            'text': "Don't you think this approach is clearly the most effective solution?",
            'start': 10.5,
            'end': 15.0
        },
        {
            'speaker': 'SPEAKER_01',
            'text': "Actually, I disagree. I think there might be better alternatives.",
            'start': 14.0,  # Overlapping - interruption
            'end': 18.0
        },
        {
            'speaker': 'SPEAKER_00',
            'text': "You make a valid point. How would you approach this differently?",
            'start': 18.5,
            'end': 23.0
        }
    ]

    # Import the functions
    from speech_analysis.services.speaker_metrics import (
        analyse_questions_vs_statements,
        detect_agreement_disagreement,
        detect_leading_questions,
        detect_interruptions,
        calculate_sentiment_per_speaker
    )
    
    print("Testing new speaker analysis functions...\n")
    print("="*60)
    
    # Test 1: Questions vs Statements
    print("1. QUESTIONS VS STATEMENTS ANALYSIS:")
    print("-" * 40)
    questions_result = analyse_questions_vs_statements(sample_transcript)
    for speaker, data in questions_result.items():
        print(f"  {speaker}: {data['questions']} questions, {data['statements']} statements")
        print(f"    Role: {data['likely_role']}, Question ratio: {data['question_ratio']}")
    print()
    
    # Test 2: Agreement/Disagreement
    print("2. AGREEMENT/DISAGREEMENT ANALYSIS:")
    print("-" * 40)
    agreement_result = detect_agreement_disagreement(sample_transcript)
    for speaker, data in agreement_result.items():
        print(f"  {speaker}: {data['agreements']} agreements, {data['disagreements']} disagreements")
        print(f"    Style: {data.get('communication_style', 'unknown')}")
    print()
    
    # Test 3: Leading Questions
    print("3. LEADING QUESTIONS DETECTION:")
    print("-" * 40)
    leading_result = detect_leading_questions(sample_transcript)
    for speaker, data in leading_result.items():
        if data['total_questions'] > 0:
            print(f"  {speaker}: {data['leading_questions']}/{data['total_questions']} leading questions")
            print(f"    Bias level: {data.get('bias_level', 'unknown')}")
    print()
    
    # Test 4: Interruptions
    print("4. INTERRUPTION DETECTION:")
    print("-" * 40)
    interruption_result = detect_interruptions(sample_transcript)
    print(f"  Total interruptions: {interruption_result.get('total_interruptions', 0)}")
    for speaker, stats in interruption_result.get('speaker_stats', {}).items():
        print(f"  {speaker}: Made {stats['interruptions_made']}, Interrupted {stats['interrupted_by_others']} times")
    print()
    
    # Test 5: Sentiment Analysis (will show fallback message if libraries not installed)
    print("5. SENTIMENT ANALYSIS:")
    print("-" * 40)
    speaker_01_turns = [turn for turn in sample_transcript if turn['speaker'] == 'SPEAKER_01']
    sentiment_result = calculate_sentiment_per_speaker(speaker_01_turns)
    print(f"  SPEAKER_01 sentiment: {sentiment_result}")
    print()
    
    print("="*60)
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    test_new_speaker_functions()