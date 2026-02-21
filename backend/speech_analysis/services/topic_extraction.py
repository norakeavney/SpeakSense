import re
from collections import Counter

_BASIC_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "he", "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "we", "you", "they", "this", "those", "these", "i", "me", "my",
    "our", "ours", "your", "yours", "their", "them", "or", "if", "but", "so", "not",
    "do", "does", "did", "can", "could", "should", "would", "just", "about", "into",
    "than", "then", "there", "here", "also", "very", "really"
}

def _tokenize(text: str):
    return re.findall(r"[a-zA-Z][a-zA-Z']{1,}", (text or "").lower())

def extract_topics(text: str, max_topics: int = 5, max_keywords: int = 12):
    tokens = [t for t in _tokenize(text) if t not in _BASIC_STOPWORDS and len(t) > 2]
    if not tokens:
        return {
            "main_topics": [],
            "keywords": [],
            "note": "No usable text for topic extraction (baseline)."
        }

    freq = Counter(tokens)
    keywords = [w for w, _ in freq.most_common(max_keywords)]
    main_topics = keywords[:max_topics]

    return {
        "main_topics": main_topics,
        "keywords": keywords,
        "note": "Baseline frequency-based topics (Step 1)."
    }