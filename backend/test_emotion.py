"""
Test script for emotion analysis with DistilBERT
Run this to verify the emotion detection is working
"""

from speech_analysis.services.emotion_analysis import analyse_emotions, generate_emotion_summary


def test_emotion_analysis():
    """Test the emotion analysis with sample transcript data"""
    
    print("=" * 60)
    print("Testing Emotion Analysis with DistilBERT")
    print("=" * 60)
    
    # Sample transcript with different emotions
    test_transcript = [
        {
            'text': 'I am so happy about this project! It is going great!',
            'start': 0.0,
            'end': 3.5,
            'speaker': 'SPEAKER_00'
        },
        {
            'text': 'Yeah, I agree. This is wonderful work. I love it!',
            'start': 4.0,
            'end': 6.5,
            'speaker': 'SPEAKER_01'
        },
        {
            'text': 'Unfortunately, we have some bad news to discuss. I am really sad about this.',
            'start': 7.0,
            'end': 10.0,
            'speaker': 'SPEAKER_00'
        },
        {
            'text': 'Oh no, that is terrible news. I am very disappointed and upset.',
            'start': 10.5,
            'end': 13.0,
            'speaker': 'SPEAKER_01'
        },
        {
            'text': 'I am so angry about how this situation was handled!',
            'start': 14.0,
            'end': 16.5,
            'speaker': 'SPEAKER_00'
        },
        {
            'text': 'But do not worry too much. We can fix this and move forward.',
            'start': 17.0,
            'end': 20.0,
            'speaker': 'SPEAKER_01'
        },
        {
            'text': 'You are right. Let us work together on this.',
            'start': 21.0,
            'end': 23.0,
            'speaker': 'SPEAKER_00'
        },
        {
            'text': 'This is surprising! I did not expect this outcome at all!',
            'start': 24.0,
            'end': 27.0,
            'speaker': 'SPEAKER_01'
        },
    ]
    
    # analyse emotions
    print("\nAnalyzing emotions...")
    result = analyse_emotions(test_transcript)
    
    # Print results
    print("\n✓ Emotion Analysis Complete")
    print("-" * 60)
    print(f"Model Used: {result.get('model_used', 'unknown')}")
    print(f"Overall Sentiment: {result['overall_sentiment']}")
    print(f"\nEmotion Distribution:")
    for emotion, percentage in sorted(result['emotion_distribution'].items(), key=lambda x: x[1], reverse=True):
        bar = '█' * int(percentage * 50)
        emoji_map = {
            'happy': '😊', 'sad': '😢', 'angry': '😠',
            'neutral': '😐', 'fear': '😨', 'surprise': '😮', 'disgust': '🤢'
        }
        emoji = emoji_map.get(emotion, '🎭')
        print(f"  {emoji} {emotion:10s}: {bar} {percentage*100:.1f}%")
    
    print(f"\nTimeline ({len(result['timeline'])} points):")
    for point in result['timeline']:
        emotion = point['emotion']
        emoji_map = {
            'happy': '😊', 'sad': '😢', 'angry': '😠',
            'neutral': '😐', 'fear': '😨', 'surprise': '😮', 'disgust': '🤢'
        }
        emoji = emoji_map.get(emotion, '🎭')
        print(f"  {point['timestamp']:5.1f}s: {emoji} {emotion:10s} (confidence: {point['confidence']:.2f})")
    
    if 'per_speaker_emotions' in result:
        print(f"\nPer-Speaker Emotions:")
        for speaker, data in result['per_speaker_emotions'].items():
            print(f"  {speaker}: {data['dominant_emotion']}")
            print(f"    Distribution: {data['distribution']}")
    
    # Generate summary
    summary = generate_emotion_summary(result)
    print(f"\nSummary:")
    print(f"  {summary}")
    
    print("\n" + "=" * 60)
    print("Test Complete!")
    print("=" * 60)


if __name__ == '__main__':
    test_emotion_analysis()
