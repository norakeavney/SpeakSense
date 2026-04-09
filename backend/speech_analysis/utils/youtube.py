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
        'outtmpl': f"{output_path}.%(ext)s",
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'quiet': False,  # TURN THIS OFF FOR DEBUG
        'noplaylist': True,

        'extractor_args': {
            'youtube': {
                'player_client': ['android']
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