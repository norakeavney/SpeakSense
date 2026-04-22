"""YouTube audio downloader helper.

Note: This helper commonly works in local development but can fail in deployed
environments due to platform restrictions (missing cookies file, network egress
limits, or other hosting constraints). If it fails in production, upload audio
files instead or ensure appropriate credentials and network access are available.
"""

import yt_dlp
import uuid
import os


def download_youtube_audio(url, output_dir="uploads"):
    """Download audio from a YouTube URL and return a WAV file path."""

    os.makedirs(output_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    output_path = os.path.join(output_dir, file_id)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_path}.%(ext)s",
        # Cookie file path used in some container images; may not exist on hosts.
        "cookiefile": "/app/cookies.txt",
        "quiet": True,
        "noplaylist": True,
        "geo_bypass": True,
        "ignoreerrors": False,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "wav"},
        ],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        # Surface a generic message when platform restrictions prevent download.
        raise Exception(
            "YouTube download failed due to platform restrictions. "
            "Please upload the audio file instead."
        )

    return f"{output_path}.wav"