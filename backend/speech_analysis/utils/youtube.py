import yt_dlp
import uuid
import os

def download_youtube_audio(url, output_dir="uploads"):
    """
    Downloads audio from a YouTube video and converts it to WAV.
    Returns the path to the WAV file.
    """

    os.makedirs(output_dir, exist_ok=True)

    file_id = str(uuid.uuid4())
    output_path = os.path.join(output_dir, file_id)

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': f'{output_path}.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return f"{output_path}.wav"