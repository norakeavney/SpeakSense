"""Sanity checks for optional diarization dependencies."""

import logging
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file (if present)
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

logger = logging.getLogger(__name__)

try:
    import pkg_resources
    logger.info("pkg_resources imported successfully")
except Exception:
    logger.exception("pkg_resources import failed")

try:
    from pyannote.audio import Pipeline
    logger.info("pyannote.audio imported successfully")
except Exception:
    logger.exception("pyannote.audio import failed")

try:
    hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    logger.info("HF token present: %s", bool(hf_token))
    if hf_token:
        pipeline = Pipeline.from_pretrained("pyannote/speaker-diarization-3.1", use_auth_token=hf_token)
        logger.info("Pipeline loaded successfully")
    else:
        logger.warning("No HF token found; skipping Pipeline.from_pretrained() test")
except Exception:
    logger.exception("Pipeline.from_pretrained() test failed")