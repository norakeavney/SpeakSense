import subprocess
from pathlib import Path


def normalise_audio(input_path):
    """Convert audio/video to 16kHz mono WAV for ML processing."""

    input_path = Path(input_path)
    output_path = input_path.with_suffix(".wav")

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(input_path),
        "-ac",
        "1",
        "-ar",
        "16000",
        "-vn",
        str(output_path),
    ]

    subprocess.run(command, check=True)

    return output_path