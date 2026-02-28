import time
from typing import Dict, Any, List, Optional, Tuple

from transformers import pipeline


class PoliticalAnalysisError(Exception):
    pass


# ---------------------------------------------------
# GLOBAL CLASSIFIER (loads once, reused forever)
# ---------------------------------------------------
_classifier = None


def _get_classifier():
    global _classifier
    if _classifier is None:
        print("Loading BART MNLI model locally...")
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )
        print("Model loaded.")
    return _classifier


# ---------------------------------------------------
# CORE ZERO SHOT FUNCTION (LOCAL)
# ---------------------------------------------------
def _zero_shot(
    text: str,
    candidate_labels: List[str],
) -> Dict[str, Any]:

    classifier = _get_classifier()

    result = classifier(
        text,
        candidate_labels,
        multi_label=False
    )

    return {
        "labels": result["labels"],
        "scores": result["scores"]
    }


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------
def _normalize_scores(labels: List[str], scores: List[float]) -> Dict[str, float]:
    if not labels or not scores or len(labels) != len(scores):
        return {}

    total = sum(scores) if sum(scores) > 0 else 1.0
    return {lab: float(sc) / total for lab, sc in zip(labels, scores)}


def _pick_top(mapping: Dict[str, float]) -> Tuple[Optional[str], float]:
    if not mapping:
        return None, 0.0
    top_label = max(mapping, key=mapping.get)
    return top_label, float(mapping[top_label])


def _axis_score(pos_label: str, neg_label: str, mapping: Dict[str, float]) -> float:
    pos = float(mapping.get(pos_label, 0.0))
    neg = float(mapping.get(neg_label, 0.0))
    denom = max(pos + neg, 1e-9)
    return (pos - neg) / denom


# ---------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------
def analyse_speaker_politics(
    speaker_texts: Dict[str, str],
    max_chars: int = 2000,   # trimmed for speed
) -> Dict[str, Any]:

    results: Dict[str, Any] = {
        "model": "facebook/bart-large-mnli (local)",
        "speakers": {},
        "notes": [
            "Political alignment is an estimate based on language patterns.",
            "Use these scores as probabilistic indicators, not ground truth.",
        ],
    }

    all_labels = [
        "left-wing politics",
        "centrist politics",
        "right-wing politics",
        "economically conservative",
        "economically progressive",
        "socially conservative",
        "socially liberal",
    ]

    for speaker_id, raw_text in speaker_texts.items():
        text = (raw_text or "").strip()
        if not text:
            results["speakers"][speaker_id] = {"error": "No text provided."}
            continue

        if len(text) > max_chars:
            text = text[:max_chars]

        classifier = _get_classifier()

        start = time.time()
        result = classifier(text, all_labels, multi_label=False)
        duration = round(time.time() - start, 2)

        resp = {
            "labels": result["labels"],
            "scores": result["scores"]
        }

        mapping = _normalize_scores(
            resp.get("labels", []),
            resp.get("scores", [])
        )

        # 1D
        one_d_map = {
            k: v for k, v in mapping.items()
            if k in ["left-wing politics", "centrist politics", "right-wing politics"]
        }
        one_d_top, one_d_conf = _pick_top(one_d_map)

        # Economic
        econ_map = {
            k: v for k, v in mapping.items()
            if k in ["economically conservative", "economically progressive"]
        }
        econ_axis = _axis_score(
            "economically conservative",
            "economically progressive",
            econ_map
        )
        econ_top, econ_conf = _pick_top(econ_map)

        # Social
        soc_map = {
            k: v for k, v in mapping.items()
            if k in ["socially conservative", "socially liberal"]
        }
        soc_axis = _axis_score(
            "socially conservative",
            "socially liberal",
            soc_map
        )
        soc_top, soc_conf = _pick_top(soc_map)

        results["speakers"][speaker_id] = {
            "processing_time_seconds": duration,
            "one_dimensional": {
                "scores": one_d_map,
                "top_label": one_d_top,
                "confidence": round(one_d_conf, 4),
            },
            "two_dimensional": {
                "economic": {
                    "scores": econ_map,
                    "axis": round(float(econ_axis), 4),
                    "top_label": econ_top,
                    "confidence": round(econ_conf, 4),
                    "interpretation": "negative=progressive, positive=conservative",
                },
                "social": {
                    "scores": soc_map,
                    "axis": round(float(soc_axis), 4),
                    "top_label": soc_top,
                    "confidence": round(soc_conf, 4),
                    "interpretation": "negative=liberal, positive=conservative",
                },
            },
        }

    return results