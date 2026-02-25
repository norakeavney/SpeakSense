import os
import time
import json
from typing import Dict, Any, List, Optional, Tuple

import requests


HF_INFERENCE_URL = "https://router.huggingface.co/hf-inference/models"


class PoliticalAnalysisError(Exception):
    pass


def _hf_headers() -> Dict[str, str]:
    token = os.getenv("HF_INFERENCE_TOKEN")
    if not token:
        raise PoliticalAnalysisError("HF_INFERENCE_TOKEN is missing. Set it in your backend .env")
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }


def _post_with_retries(
    url: str,
    payload: Dict[str, Any],
    timeout_seconds: int = 60,
    max_retries: int = 3,
    backoff_seconds: float = 1.5,
) -> Dict[str, Any]:
    """
    Calls HF Inference API with retries.
    Handles common HF states: loading (503) and throttling.
    """
    headers = _hf_headers()
    last_err: Optional[str] = None

    for attempt in range(1, max_retries + 1):
        try:
            resp = requests.post(
                url,
                headers=headers,
                data=json.dumps(payload),
                timeout=timeout_seconds,
            )

            # HF sometimes returns 503 when model is loading
            if resp.status_code == 503:
                # Try to parse estimated_time if present
                try:
                    body = resp.json()
                    wait = float(body.get("estimated_time", 3))
                except Exception:
                    wait = 3.0
                time.sleep(min(wait, 8))
                continue

            # Rate limits / temporary issues
            if resp.status_code in (429, 500, 502, 504):
                last_err = f"HF temporary error {resp.status_code}: {resp.text[:200]}"
                time.sleep(backoff_seconds * attempt)
                continue

            if not resp.ok:
                raise PoliticalAnalysisError(
                    f"HF request failed ({resp.status_code}): {resp.text[:400]}"
                )

            return resp.json()

        except requests.RequestException as e:
            last_err = str(e)
            time.sleep(backoff_seconds * attempt)

    raise PoliticalAnalysisError(f"HF request failed after retries. Last error: {last_err}")


def _zero_shot(
    text: str,
    candidate_labels: List[str],
    model_id: str = "facebook/bart-large-mnli",
    hypothesis_template: str = "This text is about {}.",
) -> Dict[str, Any]:
    """
    Calls HF zero-shot classification model.
    Always returns dict: {labels: [...], scores: [...]}
    Handles both dict and list responses from HF router.
    """
    url = f"{HF_INFERENCE_URL}/{model_id}"

    payload = {
        "inputs": text,
        "parameters": {
            "candidate_labels": candidate_labels,
            "hypothesis_template": hypothesis_template,
            "multi_label": False,
        },
        "options": {
            "wait_for_model": True
        },
    }

    response = _post_with_retries(url, payload)

    # Normalize router response shape
    if isinstance(response, list):
        if len(response) > 0 and isinstance(response[0], dict):
            response = response[0]
        else:
            raise PoliticalAnalysisError("Unexpected HF response format (list).")

    if not isinstance(response, dict):
        raise PoliticalAnalysisError("Unexpected HF response format (not dict).")

    return response
def _normalize_scores(labels: List[str], scores: List[float]) -> Dict[str, float]:
    """
    Converts HF output into label->score mapping.
    Scores from zero-shot should already sum ~1, but we normalize defensively.
    """
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
    """
    Returns axis in [-1, +1]
      negative = closer to neg_label (e.g., economically progressive)
      positive = closer to pos_label (e.g., economically conservative)
    """
    pos = float(mapping.get(pos_label, 0.0))
    neg = float(mapping.get(neg_label, 0.0))
    denom = max(pos + neg, 1e-9)
    # convert to signed preference: (pos - neg)/(pos + neg)
    return (pos - neg) / denom


def analyze_speaker_politics(
    speaker_texts: Dict[str, str],
    model_id: str = "facebook/bart-large-mnli",
    max_chars: int = 6000,
) -> Dict[str, Any]:
    """
    Input:
      speaker_texts = {"SPEAKER_00": "combined text...", "SPEAKER_01": "..."}
    Output:
      {
        "model": "...",
        "speakers": {
          "SPEAKER_00": {
            "one_dimensional": {...},
            "two_dimensional": {...}
          },
          ...
        },
        "notes": [...]
      }

    max_chars trims long transcripts so inference calls stay reasonable.
    """
    results: Dict[str, Any] = {
        "model": model_id,
        "speakers": {},
        "notes": [
            "Political alignment is an estimate based on language patterns and semantic similarity; treat as probabilistic.",
            "Use these scores as indicators, not ground truth.",
        ],
    }

    # --- Labels ---
    one_d_labels = [
        "left-wing politics",
        "centrist politics",
        "right-wing politics",
    ]

    # For axes, we do two separate 2-label runs to keep interpretation clean
    econ_labels = [
        "economically conservative",
        "economically progressive",
    ]
    social_labels = [
        "socially conservative",
        "socially liberal",
    ]

    for speaker_id, raw_text in speaker_texts.items():
        text = (raw_text or "").strip()
        if not text:
            results["speakers"][speaker_id] = {"error": "No text provided for speaker."}
            continue

        # Trim to prevent huge payloads / costs / latency
        if len(text) > max_chars:
            text = text[:max_chars]

        speaker_out: Dict[str, Any] = {}

        # --- 1D ideology ---
        one_d_resp = _zero_shot(text, one_d_labels, model_id=model_id)
        one_d_map = _normalize_scores(one_d_resp.get("labels", []), one_d_resp.get("scores", []))
        one_d_top, one_d_conf = _pick_top(one_d_map)

        speaker_out["one_dimensional"] = {
            "scores": one_d_map,                 # probabilities per label
            "top_label": one_d_top,              # label name
            "confidence": round(one_d_conf, 4),  # probability of top label
        }

        # --- Economic axis ---
        econ_resp = _zero_shot(text, econ_labels, model_id=model_id)
        econ_map = _normalize_scores(econ_resp.get("labels", []), econ_resp.get("scores", []))
        # axis negative = progressive, positive = conservative
        econ_axis = _axis_score("economically conservative", "economically progressive", econ_map)
        econ_top, econ_conf = _pick_top(econ_map)

        # --- Social axis ---
        soc_resp = _zero_shot(text, social_labels, model_id=model_id)
        soc_map = _normalize_scores(soc_resp.get("labels", []), soc_resp.get("scores", []))
        # axis negative = liberal, positive = conservative
        soc_axis = _axis_score("socially conservative", "socially liberal", soc_map)
        soc_top, soc_conf = _pick_top(soc_map)

        speaker_out["two_dimensional"] = {
            "economic": {
                "scores": econ_map,
                "axis": round(float(econ_axis), 4),   # [-1, +1]
                "top_label": econ_top,
                "confidence": round(econ_conf, 4),
                "interpretation": "negative=progressive, positive=conservative",
            },
            "social": {
                "scores": soc_map,
                "axis": round(float(soc_axis), 4),    # [-1, +1]
                "top_label": soc_top,
                "confidence": round(soc_conf, 4),
                "interpretation": "negative=liberal, positive=conservative",
            },
        }

        results["speakers"][speaker_id] = speaker_out

    return results


def build_speaker_texts_from_diarized_transcript(
    diarized_transcript: List[Dict[str, Any]],
    speaker_field: str = "speaker",
    text_field: str = "text",
) -> Dict[str, str]:
    """
    Helper to combine all transcript turns per speaker from your diarization output.
    diarized_transcript example items:
      {"speaker": "SPEAKER_00", "start": 0.0, "end": 1.2, "text": "Hello ..."}
    Returns:
      {"SPEAKER_00": "Hello ... (all combined)", "SPEAKER_01": "..."}
    """
    out: Dict[str, List[str]] = {}
    for turn in diarized_transcript or []:
        sid = str(turn.get(speaker_field, "")).strip()
        t = str(turn.get(text_field, "")).strip()
        if not sid or not t:
            continue
        out.setdefault(sid, []).append(t)

    return {sid: " ".join(chunks) for sid, chunks in out.items()}