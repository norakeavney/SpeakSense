"""Test script for emotion analysis with DistilBERT."""

import logging

from gpu_worker.ml.emotion_analysis import analyse_emotions, generate_emotion_summary


logger = logging.getLogger(__name__)


def test_emotion_analysis():
    """Test the emotion analysis with sample transcript data."""

    logger.info("%s", "=" * 60)
    logger.info("Testing Emotion Analysis with DistilBERT")
    logger.info("%s", "=" * 60)

    # Sample transcript with different emotions
    test_transcript = [
        {"text": "I am so happy about this project! It is going great!", "start": 0.0, "end": 3.5, "speaker": "SPEAKER_00"},
        {"text": "Yeah, I agree. This is wonderful work. I love it!", "start": 4.0, "end": 6.5, "speaker": "SPEAKER_01"},
        {"text": "Unfortunately, we have some bad news to discuss. I am really sad about this.", "start": 7.0, "end": 10.0, "speaker": "SPEAKER_00"},
        {"text": "Oh no, that is terrible news. I am very disappointed and upset.", "start": 10.5, "end": 13.0, "speaker": "SPEAKER_01"},
        {"text": "I am so angry about how this situation was handled!", "start": 14.0, "end": 16.5, "speaker": "SPEAKER_00"},
        {"text": "But do not worry too much. We can fix this and move forward.", "start": 17.0, "end": 20.0, "speaker": "SPEAKER_01"},
        {"text": "You are right. Let us work together on this.", "start": 21.0, "end": 23.0, "speaker": "SPEAKER_00"},
        {"text": "This is surprising! I did not expect this outcome at all!", "start": 24.0, "end": 27.0, "speaker": "SPEAKER_01"},
    ]

    # analyse emotions
    logger.info("Analyzing emotions...")
    result = analyse_emotions(test_transcript)

    # Print results (logged)
    logger.info("%s", "\n✓ Emotion Analysis Complete")
    logger.info("%s", "-" * 60)
    logger.info("Model Used: %s", result.get("model_used", "unknown"))
    logger.info("Overall Sentiment: %s", result["overall_sentiment"])
    logger.info("Emotion Distribution:")
    for emotion, percentage in sorted(result["emotion_distribution"].items(), key=lambda x: x[1], reverse=True):
        bar = "█" * int(percentage * 50)
        emoji_map = {"happy": "😊", "sad": "😢", "angry": "😠", "neutral": "😐", "fear": "😨", "surprise": "😮", "disgust": "🤢"}
        emoji = emoji_map.get(emotion, "🎭")
        logger.info("  %s %s: %s %0.1f%%", emoji, f"{emotion:10s}", bar, percentage * 100)

    logger.info("Timeline (%d points):", len(result["timeline"]))
    for point in result["timeline"]:
        emotion = point["emotion"]
        emoji_map = {"happy": "😊", "sad": "😢", "angry": "😠", "neutral": "😐", "fear": "😨", "surprise": "😮", "disgust": "🤢"}
        emoji = emoji_map.get(emotion, "🎭")
        logger.info("  %5.1fs: %s %s (confidence: %0.2f)", point["timestamp"], emoji, f"{emotion:10s}", point["confidence"])

    if "per_speaker_emotions" in result:
        logger.info("Per-Speaker Emotions:")
        for speaker, data in result["per_speaker_emotions"].items():
            logger.info("  %s: %s", speaker, data["dominant_emotion"])
            logger.info("    Distribution: %s", data["distribution"])

    # Generate summary
    summary = generate_emotion_summary(result)
    logger.info("Summary:")
    logger.info("  %s", summary)

    logger.info("%s", "\n" + "=" * 60)
    logger.info("Test Complete!")
    logger.info("%s", "=" * 60)


if __name__ == '__main__':
    test_emotion_analysis()
