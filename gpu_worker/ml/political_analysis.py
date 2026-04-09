import time
import logging
from typing import Dict, Any, List, Optional, Tuple
from unittest import result

from transformers import pipeline

logger = logging.getLogger(__name__)


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
        import torch
        device = 0 if torch.cuda.is_available() else -1  # Use GPU if available, else CPU
        _classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=device
        )
        device_msg = f"GPU" if device == 0 else "CPU"
        print(f"Model loaded on {device_msg}.")
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

    logger.info(f"Political analysis input speakers: {list(speaker_texts.keys())}")

    for sid, txt in speaker_texts.items():
        logger.info(f"{sid} text length: {len(txt)}")
        logger.info(f"{sid} sample: {txt[:100]}")

    results: Dict[str, Any] = {
        "model": "facebook/bart-large-mnli (local)",
        "speakers": {},
        "notes": [
            "Political alignment is an estimate based on language patterns.",
            "Use these scores as probabilistic indicators, not ground truth.",
        ],
    }

    # Validate input
    if not speaker_texts:
        logger.warning("Political analysis: No speaker texts provided")
        results["error"] = "No speaker texts provided"
        results["speakers"] = {}
        return results

    logger.info(f"Political analysis: Starting analysis for {len(speaker_texts)} speakers")

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
            results["speakers"][speaker_id] = {"warning": "Empty text - skipped", "error": "No text provided."}
            continue

        if len(text) > max_chars:
            text = text[:max_chars]

        classifier = _get_classifier()

        start = time.time()
        result = classifier(text, all_labels, multi_label=False)
        duration = round(time.time() - start, 2)

        logger.info(f"{speaker_id} raw labels: {result['labels']}")
        logger.info(f"{speaker_id} raw scores: {result['scores']}")

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
                "top_label": one_d_top or "neutral",
                "confidence": round(one_d_conf, 4),
            },
            "two_dimensional": {
                "economic": {
                    "scores": econ_map,
                    "axis": round(float(econ_axis), 4),
                    "top_label": econ_top or "neutral",
                    "confidence": round(econ_conf, 4),
                    "interpretation": "negative=progressive, positive=conservative",
                },
                "social": {
                    "scores": soc_map,
                    "axis": round(float(soc_axis), 4),
                    "top_label": soc_top or "neutral",
                    "confidence": round(soc_conf, 4),
                    "interpretation": "negative=liberal, positive=conservative",
                },
            },
        }

    logger.info(f"Political analysis: Completed for {len(results['speakers'])} speakers")
    logger.info(f"{speaker_id} final result: {results['speakers'][speaker_id]}")
    
    # Final safety check: ensure we always return valid structure
    if results is None:
        logger.error("CRITICAL: Political analysis results are None!")
        return {
            "model": "facebook/bart-large-mnli (local)",
            "speakers": {},
            "error": "Political analysis failed - internal error",
            "notes": ["Political analysis internal error"]
        }
    
    if not isinstance(results, dict):
        logger.error(f"CRITICAL: Political analysis results are not dict: {type(results)}")
        return {
            "model": "facebook/bart-large-mnli (local)",
            "speakers": {},
            "error": "Political analysis failed - invalid result type",
            "notes": ["Political analysis returned invalid type"]
        }
    
    return results

def build_speaker_texts_from_diarized_transcript(
    diarized_transcript: List[Dict[str, Any]],
    speaker_field: str = "speaker",
    text_field: str = "text",
) -> Dict[str, str]:
    """
    Combines transcript turns per speaker.
    Input example:
      {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.2, "text": "Hello"}
    Output:
      {"SPEAKER_00": "Hello ... combined"}
    """

    out: Dict[str, List[str]] = {}
    empty_text_count = 0
    missing_speaker_count = 0

    for turn in diarized_transcript or []:
        sid = str(turn.get(speaker_field, "")).strip()
        t = str(turn.get(text_field, "")).strip()

        if not sid:
            missing_speaker_count += 1
            continue
        
        if not t:
            empty_text_count += 1
            continue

        out.setdefault(sid, []).append(t)
    
    if empty_text_count > 0 or missing_speaker_count > 0:
        logger.warning(
            f"build_speaker_texts: Skipped {empty_text_count} empty texts, "
            f"{missing_speaker_count} missing speakers"
        )

    return {sid: " ".join(chunks) for sid, chunks in out.items()}