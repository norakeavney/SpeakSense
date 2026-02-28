from dotenv import load_dotenv

load_dotenv()

from speech_analysis.services.political_analysis import analyse_speaker_politics


fake_speakers = {
    "SPEAKER_00": "The government should increase taxes on corporations and invest in public healthcare and climate change initiatives.",
    "SPEAKER_01": "We need lower taxes, less regulation, and stronger border control policies."
}

result = analyse_speaker_politics(fake_speakers)

print(result)