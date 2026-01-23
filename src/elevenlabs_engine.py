import requests
import os
from .config import Config

class ElevenLabsEngine:
    def __init__(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID") # Cloned voice ID
        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

    def generate_audio(self, text, output_path):
        """
        Generates high-quality cloned audio using ElevenLabs API.
        """
        if not self.api_key or not self.voice_id:
            print("ElevenLabs credentials missing. Falling back to default voice.")
            return False

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "style": 0.0,
                "use_speaker_boost": True
            }
        }

        try:
            response = requests.post(self.url, json=data, headers=headers)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                return True
            else:
                print(f"ElevenLabs Error {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"ElevenLabs Connection Error: {e}")
            return False
