import re
from collections import Counter

try:
    from keybert import KeyBERT
    from sklearn.feature_extraction.text import CountVectorizer
    import torch
    _KEYBERT_AVAILABLE = True
except ImportError:
    _KEYBERT_AVAILABLE = False


# ─────────────────────────────────────────────
# GLOBAL KEYBERT MODEL (LOAD ONCE)
# ─────────────────────────────────────────────
_kw_model = None


# ─────────────────────────────────────────────
# STOPWORDS & FILLER WORDS 
# ─────────────────────────────────────────────
_FILLER_WORDS = {
    "um", "uh", "like", "you know", "yeah", "ok", "okay", "right", "oh",
    "sort of", "kind of", "i mean", "you see"
}

_BASIC_STOPWORDS = {
    "a","an","and","are","as","at","be","by","for","from","has","have",
    "he","she","it","they","them","we","you","i","me","my",
    "in","is","of","on","that","this","those","these","to","was","were","will","with",
    "what","which","who","whom","why","how",
    "yeah","okay","ok","right","well","just","like","know",
    "our","their","his","her","its","not","so","if","then","than"
}

_EXTRA_STOPWORDS = {
    "one","say","said","look","going","done","into","back",
    "because","when","people","thing","things","way","time","make","made",
    "really","want","think","know","see","come","even",
    "well","just","like","yeah","okay","right"
}

ALL_STOPWORDS = _BASIC_STOPWORDS.union(_EXTRA_STOPWORDS)


# ─────────────────────────────────────────────
# CLEAN TEXT (LOWERCASE, REMOVE FILLERS, NON-LETTERS, SHORT WORDS, STOPWORDS)
# ─────────────────────────────────────────────
def _clean_text(text: str) -> str:
    text = (text or "").lower()

    # Remove filler phrases
    for fw in _FILLER_WORDS:
        text = re.sub(rf"\b{re.escape(fw)}\b", " ", text)

    # Remove non-letters
    text = re.sub(r"[^a-z\s]", " ", text)

    # Collapse spaces
    text = re.sub(r"\s+", " ", text).strip()

    words = text.split()

    cleaned = []
    for w in words:
        if len(w) < 4:
            continue
        if w in ALL_STOPWORDS:
            continue
        if len(set(w)) == 1:  # skip words like "aaaa" or "hhhh"
            continue
        cleaned.append(w)

    return " ".join(cleaned)


# ─────────────────────────────────────────────
# CLEAN SEGMENTS (EXTRACT + CLEAN TEXT FROM ALL SEGMENTS)
# ─────────────────────────────────────────────
def _clean_segments(segments: list) -> str:
    if not segments:
        return ""

    cleaned_segments = []

    for seg in segments:
        raw = (seg or {}).get("text", "")
        cleaned = _clean_text(raw)

        # keep only meaningful chunks
        if len(cleaned.split()) < 4:
            continue

        cleaned_segments.append(cleaned)

    return " ".join(cleaned_segments)


# ─────────────────────────────────────────────
# FALLBACK TOPIC EXTRACTION (SIMPLE FREQUENCY)
# ─────────────────────────────────────────────
def _fallback_topics(text: str, max_topics: int, max_keywords: int) -> dict:
    tokens = [
        t for t in re.findall(r"[a-zA-Z]{4,}", text)
        if t.lower() not in ALL_STOPWORDS
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


# ─────────────────────────────────────────────
# MAIN TOPIC EXTRACTION FUNCTION
# ─────────────────────────────────────────────
def extract_topics(
    text: str,
    segments: list = None,
    max_topics: int = 8,
    max_keywords: int = 20,
    min_score: float = 0.30,
    diversity: float = 0.7
) -> dict:

    source_text = _clean_segments(segments) if segments else _clean_text(text)

    if not source_text:
        return {"main_topics": [], "keywords": [], "method": "none"}

    if not _KEYBERT_AVAILABLE:
        return _fallback_topics(source_text, max_topics, max_keywords)

    global _kw_model

    try:
        if _kw_model is None:
            print("→ Loading KeyBERT model...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _kw_model = KeyBERT(model="all-MiniLM-L6-v2")
            print(f"✓ KeyBERT ready")

        # STEP 1: Extract candidates
        raw = _kw_model.extract_keywords(
            source_text,
            vectorizer=CountVectorizer(
                ngram_range=(1, 2),
                stop_words=list(ALL_STOPWORDS),
                token_pattern=r"(?u)\b[a-zA-Z]{4,}\b"
            ),
            use_mmr=True,
            diversity=diversity,
            top_n=max_keywords
        )

        # STEP 2: Clean results
        final = []
        seen = set()

        for phrase, score in raw:
            phrase = phrase.strip().lower()
            words = phrase.split()

            if score < min_score:
                continue

            if any(len(w) < 4 for w in words):
                continue

            if all(w in ALL_STOPWORDS for w in words):
                continue

            if phrase in seen:
                continue

            seen.add(phrase)
            final.append((phrase, score))

        keywords = [p for p, _ in final]

        # STEP 3: Link to segments (for frontend)
        sources = {}
        if segments:
            for phrase in keywords[:max_topics]:
                for seg in segments:
                    seg_text = (seg.get("text") or "").lower()
                    if phrase in seg_text:
                        sources[phrase] = {
                            "text": seg.get("text", "").strip(),
                            "start": seg.get("start", 0),
                            "speaker": seg.get("speaker", "UNKNOWN")
                        }
                        break

        return {
            "main_topics": keywords[:max_topics],
            "keywords": keywords,
            "scores": {p: round(s, 3) for p, s in final},
            "sources": sources,
            "method": "keybert_clean"
        }

    except Exception as e:
        print(f"KeyBERT failed: {e}")
        return _fallback_topics(source_text, max_topics, max_keywords)