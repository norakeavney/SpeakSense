import re
from collections import Counter

try:
    from keybert import KeyBERT
    from sklearn.feature_extraction.text import CountVectorizer
    _KEYBERT_AVAILABLE = True
except ImportError:
    _KEYBERT_AVAILABLE = False

_kw_model = None

_FILLER_WORDS = ["um", "uh", "like", "you know", "yeah", "ok", "right", "oh"]

_BAD_PHRASE_KEYWORDS = [
    "really", "talked", "run", "long", "given", "make", "exception"
]

_BASIC_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has", "have",
    "he", "in", "is", "it", "its", "of", "on", "that", "the", "to", "was", "were",
    "will", "with", "we", "you", "they", "this", "those", "these", "i", "me", "my",
}

def _clean_text(text: str) -> str:
    text = (text or "").lower()
    for fw in _FILLER_WORDS:
        text = re.sub(rf'\b{re.escape(fw)}\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _filter_topics(topics: list) -> list:
    cleaned = []
    for phrase, score in topics:
        if any(bad in phrase for bad in _BAD_PHRASE_KEYWORDS):
            continue
        if len(phrase.split()) == 1 and score < 0.30:
            continue
        cleaned.append((phrase, score))
    return cleaned

def _fallback_topics(text: str, max_topics: int, max_keywords: int) -> dict:
    tokens = [
        t for t in re.findall(r"[a-zA-Z][a-zA-Z']{1,}", text)
        if t.lower() not in _BASIC_STOPWORDS and len(t) > 2
    ]
    if not tokens:
        return {"main_topics": [], "keywords": [], "method": "fallback"}
    freq = Counter(tokens)
    keywords = [w for w, _ in freq.most_common(max_keywords)]
    return {
        "main_topics": keywords[:max_topics],
        "keywords": keywords,
        "method": "fallback"
    }

def extract_topics(text: str, max_topics: int = 5, max_keywords: int = 10) -> dict:
    text = _clean_text(text)
    if not text:
        return {"main_topics": [], "keywords": [], "method": "none"}

    if not _KEYBERT_AVAILABLE:
        return _fallback_topics(text, max_topics, max_keywords)

    global _kw_model
    try:
        if _kw_model is None:
            print("  → Loading KeyBERT model...")
            _kw_model = KeyBERT(model="all-MiniLM-L6-v2")

        vectorizer = CountVectorizer(
            ngram_range=(1, 3),
            stop_words="english",
            min_df=1
        )

        raw_topics = _kw_model.extract_keywords(
            text,
            vectorizer=vectorizer,
            use_mmr=True,
            diversity=0.6,
            top_n=max_keywords
        )

        cleaned = _filter_topics(raw_topics)
        keywords = [phrase for phrase, _ in cleaned]

        return {
            "main_topics": keywords[:max_topics],
            "keywords": keywords,
            "scores": {phrase: round(score, 3) for phrase, score in cleaned},
            "method": "keybert"
        }

    except Exception as e:
        print(f"  KeyBERT failed: {e}, falling back to frequency method")
        return _fallback_topics(text, max_topics, max_keywords)