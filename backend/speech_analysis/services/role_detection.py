import re

def _count_questions(segments: list, speaker: str) -> dict:
    question_words = ["who", "what", "when", "where", "why", "how", "would", "could", "should", "do you", "can you", "will you", "is it", "are you"]
    total_segments = 0
    question_segments = 0

    for seg in segments:
        if seg.get("speaker") != speaker:
            continue
        text = seg.get("text", "").strip().lower()
        total_segments += 1
        if text.endswith("?") or any(text.startswith(qw) for qw in question_words):
            question_segments += 1

    question_ratio = question_segments / total_segments if total_segments > 0 else 0
    return {
        "total_segments": total_segments,
        "question_segments": question_segments,
        "question_ratio": round(question_ratio, 3)
    }


def _speaking_time_signal(segments: list, speaker: str) -> dict:
    total_words = 0
    segment_lengths = []

    for seg in segments:
        if seg.get("speaker") != speaker:
            continue
        text = seg.get("text", "").strip()
        word_count = len(text.split())
        total_words += word_count
        segment_lengths.append(word_count)

    avg_segment_length = sum(segment_lengths) / len(segment_lengths) if segment_lengths else 0
    return {
        "total_words": total_words,
        "avg_segment_length": round(avg_segment_length, 1)
    }


def _score_role(speaker_data: dict, all_speakers_data: dict) -> str:
    """
    Compare each speaker's signals against ALL other speakers.
    Whoever asks the most questions + speaks least = Moderator.
    Everyone else = Candidate.
    """
    # Get values across all speakers for comparison
    all_question_ratios = [d["question_ratio"] for d in all_speakers_data.values()]
    all_word_counts = [d["total_words"] for d in all_speakers_data.values()]
    all_avg_lengths = [d["avg_segment_length"] for d in all_speakers_data.values()]

    # Score moderator likelihood (0-3 points)
    score = 0

    # Signal 1 - Highest question ratio of all speakers
    if speaker_data["question_ratio"] == max(all_question_ratios):
        score += 1

    # Signal 2 - Lowest total word count of all speakers
    if speaker_data["total_words"] == min(all_word_counts):
        score += 1

    # Signal 3 - Shortest average segment length of all speakers
    if speaker_data["avg_segment_length"] == min(all_avg_lengths):
        score += 1

    # Need at least 2/3 signals to be called Moderator
    if score >= 2:
        return "Moderator"
    else:
        return "Candidate"


def detect_speaker_roles(segments: list) -> dict:
    """
    Full pipeline:
    1. Collect signals per speaker
    2. Compare signals across all speakers
    3. Assign role label
    Returns: { "SPEAKER_00": { "role": "Moderator", ...signals } }
    """
    speakers = list({seg.get("speaker") for seg in segments if seg.get("speaker")})

    # Step 1 - Collect all signals first
    raw_data = {}
    for speaker in speakers:
        q_data = _count_questions(segments, speaker)
        s_data = _speaking_time_signal(segments, speaker)
        raw_data[speaker] = {
            "question_ratio": q_data["question_ratio"],
            "question_segments": q_data["question_segments"],
            "total_segments": q_data["total_segments"],
            "total_words": s_data["total_words"],
            "avg_segment_length": s_data["avg_segment_length"],
        }

    # Step 2 - Score and assign roles (needs all speakers data for comparison)
    results = {}
    for speaker in speakers:
        role = _score_role(raw_data[speaker], raw_data)
        results[speaker] = {**raw_data[speaker], "role": role}

    # Step 3 - Print summary
    print("\n" + "=" * 50)
    print("SPEAKER ROLE DETECTION")
    print("=" * 50)
    for speaker, data in results.items():
        print(f"\n{speaker} → {data['role']}")
        print(f"  Question ratio:   {data['question_ratio']}")
        print(f"  Total words:      {data['total_words']}")
        print(f"  Avg seg length:   {data['avg_segment_length']} words")

    return results