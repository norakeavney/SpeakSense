import re
import os
from collections import Counter

try:
    from keybert import KeyBERT
    from sklearn.feature_extraction.text import CountVectorizer
    from sentence_transformers import SentenceTransformer, util
    _KEYBERT_AVAILABLE = True
except ImportError:
    _KEYBERT_AVAILABLE = False

try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    _OPENAI_AVAILABLE = False

# ── Models loaded once, reused ──────────────────────────────
_kw_model = None
_embed_model = None
_openai_client = None

_FILLER_WORDS = ["um", "uh", "like", "you know", "yeah", "ok", "right", "oh"]

_BASIC_STOPWORDS = {
    "a","an","and","are","as","at","be","by","for","from","has","have",
    "he","she","it","they","them","we","you","i","me","my",
    "in","is","of","on","that","this","those","these","to","was","were","will","with",
    "what","which","who","whom","why","how",
    "yeah","okay","ok","right","well","just","like","know",
    "our","their","his","her","its",
    "not","so","if","then","than"
}

_EXTRA_STOPWORDS = {
    "one","say","said","look","going","done","into","back",
    "because","when","that's","they're","she's","he's",
    "people","thing","things","way","time","make","made",
    "really","want","think","know","see","come","even",
    "well","just","like","yeah","okay","right"
}

def _clean_text(text: str) -> str:
    """Remove filler words and extra whitespace."""
    text = (text or "").lower()
    for fw in _FILLER_WORDS:
        text = re.sub(rf'\b{re.escape(fw)}\b', '', text)
    return re.sub(r'\s+', ' ', text).strip()


def _structural_filter(topics: list, min_score: float = 0.35) -> list:
    """
    Balanced filtering:
    - Keeps meaningful phrases
    - Allows strong single-word topics
    - Removes conversational noise
    """
    kept = []

    for phrase, score in topics:
        words = phrase.split()

        # Minimum relevance
        if score < min_score:
            continue

        # Remove digits
        if any(w.isdigit() for w in words):
            continue

        # HANDLE SINGLE WORDS 
        if len(words) == 1:
            word = words[0]

            # Too short = junk
            if len(word) < 5:
                continue

            # Stopwords = junk
            if word in _BASIC_STOPWORDS or word in _EXTRA_STOPWORDS:
                continue

            # Must be stronger than phrases
            if score < (min_score + 0.1):
                continue

        # HANDLE PHRASES
        else:
            # Remove phrases dominated by stopwords
            if sum(1 for w in words if w in _BASIC_STOPWORDS or w in _EXTRA_STOPWORDS) >= len(words) / 2:
                continue

            # Avoid very short meaningless phrases
            if sum(len(w) for w in words) / len(words) < 3:
                continue

        kept.append((phrase, score))

    return kept

def _generate_summary(text: str) -> str:
    """
    Ask OpenAI to summarize the debate transcript.
    This summary becomes our 'anchor' - topics are compared against it
    so only relevant ones survive.
    """
    global _openai_client
    try:
        if not _OPENAI_AVAILABLE:
            return ""
        if _openai_client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                return ""
            _openai_client = OpenAI(api_key=api_key)

        # First 3000 words is enough context for a summary
        truncated = " ".join(text.split()[:3000])

        response = _openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": (
                    "Summarize the main topics and arguments in this debate transcript "
                    "in 3-4 sentences. Focus only on the key issues debated:\n\n"
                    + truncated
                )
            }],
            max_tokens=150,
            temperature=0.3
        )
        summary = response.choices[0].message.content.strip()
        print(f"  → Summary: {summary[:100]}...")
        return summary

    except Exception as e:
        print(f"  → Summary failed: {e}")
        return ""


def _semantic_rerank(topics: list, anchor_text: str, min_similarity: float = 0.18) -> list:
    """
    Score each topic phrase against the debate summary using cosine similarity.
    Phrases unrelated to the actual debate content get dropped.
    
    Args:
        topics: List of (phrase, score) tuples
        anchor_text: Reference text (debate summary) to compare against
        min_similarity: Minimum semantic similarity threshold (default 0.18, lower = more permissive)
    """
    global _embed_model
    if not anchor_text or not topics:
        return topics

    try:
        if _embed_model is None:
            # Same model as KeyBERT - already cached, no extra download
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
            _embed_model.to(device)

        anchor_emb = _embed_model.encode(anchor_text, convert_to_tensor=True)

        reranked = []
        for phrase, score in topics:
            phrase_emb = _embed_model.encode(phrase, convert_to_tensor=True)
            similarity = float(util.cos_sim(anchor_emb, phrase_emb))

            # Only keep phrases semantically related to the actual debate (relaxed threshold)
            if similarity >= min_similarity:
                # Combine original KeyBERT score with semantic relevance
                combined = (score * 0.7) + (similarity * 0.3)
                reranked.append((phrase, combined))

        reranked.sort(key=lambda x: x[1], reverse=True)
        return reranked

    except Exception as e:
        print(f"  → Semantic reranking failed: {e}")
        return topics


def _fallback_topics(text: str, max_topics: int, max_keywords: int) -> dict:
    """Simple word frequency fallback if KeyBERT is unavailable."""
    tokens = [
        t for t in re.findall(r"[a-zA-Z][a-zA-Z']{1,}", text)
        if t.lower() not in _BASIC_STOPWORDS and len(t) > 2
    ]
    if not tokens:
        return {"main_topics": [], "keywords": [], "method": "fallback"}
    freq = Counter(tokens)
    keywords = [w for w, _ in freq.most_common(max_keywords)]
    return {"main_topics": keywords[:max_topics], "keywords": keywords, "method": "fallback"}


def extract_topics(
    text: str,
    segments: list = None,
    max_topics: int = 8,
    max_keywords: int = 25,
    min_score: float = 0.35,
    min_similarity: float = 0.18,
    diversity: float = 0.65
) -> dict:
    """
    Full pipeline:
      1. KeyBERT extracts candidate phrases
      2. Structural filter removes fragments/noise
      3. OpenAI summarizes the debate
      4. Semantic reranking keeps only phrases relevant to the actual debate
      5. Returns clean topics + source segments for frontend hover
    
    Parameters:
        text: Input text to extract topics from
        segments: Optional list of text segments
        max_topics: Maximum number of main topics to return (default 8)
        max_keywords: Maximum number of keywords to extract (default 25)
        min_score: Minimum KeyBERT score threshold (default 0.35, lower = more permissive)
        min_similarity: Minimum semantic similarity threshold (default 0.18, lower = more permissive)
        diversity: KeyBERT diversity parameter (default 0.65, lower = more similar topics allowed)
    """
    text = _clean_text(text)
    if not text:
        return {"main_topics": [], "keywords": [], "method": "none"}

    if not _KEYBERT_AVAILABLE:
        return _fallback_topics(text, max_topics, max_keywords)

    global _kw_model
    try:
        if _kw_model is None:
            print("  → Loading KeyBERT model...")
            import torch
            device = "cuda" if torch.cuda.is_available() else "cpu"
            _kw_model = KeyBERT(model="all-MiniLM-L6-v2", device=device)
            print(f"  ✓ KeyBERT loaded on {device.upper()}")

        # Step 1 - Extract candidates (larger pool before filtering)
        raw = _kw_model.extract_keywords(
            text,
            vectorizer=CountVectorizer(ngram_range=(1, 3), stop_words=list(_BASIC_STOPWORDS.union(_EXTRA_STOPWORDS)),min_df=1),
            use_mmr=True,
            diversity=diversity,
            top_n=max_keywords
        )
        print(f"  → {len(raw)} raw candidates extracted")

        # Step 2 - Remove structural garbage (with configurable strictness)
        filtered = _structural_filter(raw, min_score=min_score)
        print(f"  → {len(filtered)} after structural filter")

        # Step 3 - Summarize the debate (context anchor)
        summary = _generate_summary(text)

        # Step 4 - Drop topics unrelated to actual debate content (with configurable threshold)
        final = _semantic_rerank(filtered, summary, min_similarity=min_similarity) if summary else filtered
        print(f"  → {len(final)} after semantic reranking")

        keywords = [phrase for phrase, _ in final]

        # Step 5 - Find which segment each topic came from (frontend hover)
        sources = {}
        if segments:
            for phrase in keywords[:max_topics]:
                for seg in segments:
                    if phrase.lower() in seg.get("text", "").lower():
                        sources[phrase] = {
                            "text": seg.get("text", "").strip(),
                            "start": seg.get("start", 0),
                            "speaker": seg.get("speaker", "UNKNOWN")
                        }
                        break

        return {
            "main_topics": keywords[:max_topics],
            "keywords": keywords,
            "scores": {phrase: round(score, 3) for phrase, score in final},
            "summary": summary,
            "sources": sources,
            "method": "keybert+semantic"
        }

    except Exception as e:
        print(f"  KeyBERT failed: {e}, using fallback")
        return _fallback_topics(text, max_topics, max_keywords)