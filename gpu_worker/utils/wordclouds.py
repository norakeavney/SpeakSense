import base64
import io
import re
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from wordcloud import STOPWORDS, WordCloud
from ml.topic_extraction import ALL_STOPWORDS

CUSTOM_STOPWORDS = {
    "um", "uh", "like", "yeah", "okay", "ok",
    "just", "really", "thing", "things",
    "going", "said", "say",
    "very", "also", "even", "perhaps", "certain",
    "real", "much", "many", "lot", "something",
    "actually", "basically", "kind", "sort"
}


def clean_token(token: str) -> str:
    token = str(token or "").lower().strip()
    token = re.sub(r"[^a-z\s]", "", token)
    return token


def build_frequency_map(keywords: List[str], scores: Dict[str, float] | None = None):
    scores = scores or {}
    # Keep filtering aligned with topic extraction logic.
    stopwords = set(STOPWORDS) | CUSTOM_STOPWORDS | set(ALL_STOPWORDS)

    freq = {}

    for word in keywords or []:
        w = clean_token(word)
        if not w or w in stopwords or len(w) < 5:
            continue

        weight = float(scores.get(word, scores.get(w, 1.0)) or 1.0)
        # Accumulate frequencies instead of taking max
        freq[w] = freq.get(w, 0) + weight

    # Keep only top 40 keywords
    sorted_freq = dict(sorted(freq.items(), key=lambda x: x[1], reverse=True)[:40])
    return sorted_freq


def generate_wordcloud_base64(keywords, scores=None):
    freq = build_frequency_map(keywords, scores)

    if not freq:
        return None

    wc = WordCloud(
        width=1200,
        height=600,
        background_color="white",
        max_words=40,
        colormap="plasma",
        prefer_horizontal=0.9,
        collocations=False,
        margin=8,
        min_font_size=10,
        max_font_size=120,
    ).generate_from_frequencies(freq)

    fig = plt.figure(figsize=(12, 6))
    plt.imshow(wc, interpolation="bilinear")
    plt.axis("off")

    buffer = io.BytesIO()
    plt.savefig(buffer, format="png", bbox_inches="tight", pad_inches=0.1)
    plt.close(fig)

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{encoded}"
