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
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,

        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36'
        },

        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },

        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return f"{output_path}.wav"