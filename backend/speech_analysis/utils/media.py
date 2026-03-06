import subprocess
import os
from pathlib import Path

def normalize_audio(input_path):
    """
    Convert any audio/video input into
    16kHz mono WAV format for ML processing
    """

    input_path = Path(input_path)

    output_path = input_path.with_suffix(".wav")

    command = [
        "ffmpeg",
        "-y",              # overwrite if exists
        "-i", str(input_path),
        "-ac", "1",        # mono
        "-ar", "16000",    # 16kHz
        "-vn",             # drop video
        str(output_path)
    ]

    subprocess.run(command, check=True)

    return output_path