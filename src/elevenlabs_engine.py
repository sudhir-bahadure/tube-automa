import requests
import os
from .config import Config

class ElevenLabsEngine:
    def __init__(self):
        self.api_key = os.environ.get("ELEVENLABS_API_KEY")
        self.voice_id = os.environ.get("ELEVENLABS_VOICE_ID") # Cloned voice ID
        self.url = f"https://api.elevenlabs.io/v1/text-to-speech/{self.voice_id}"

    def generate_audio(self, text, output_path, voice_settings=None, remove_silence=False):
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

        # Default settings or user override
        settings = {
            "stability": 0.5,
            "similarity_boost": 0.75,
            "style": 0.0,
            "use_speaker_boost": True
        }
        if voice_settings:
            settings.update(voice_settings)

        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": settings
        }

        try:
            response = requests.post(self.url, json=data, headers=headers)
            if response.status_code == 200:
                with open(output_path, "wb") as f:
                    f.write(response.content)
                
                # Post-Processing: Remove Silence and Speed Adjustment
                if remove_silence:
                   try:
                       import subprocess
                       # ffmpeg filter: silence remove (start & end, and middle gaps > 0.3s)
                       # atempo=1.0 is default, user asked for speed 1.
                       temp_path = output_path + ".tmp.mp3"
                       cmd = [
                           "ffmpeg", "-y", "-i", output_path,
                           "-af", "silenceremove=stop_periods=-1:stop_duration=0.2:stop_threshold=-30dB",
                           temp_path
                       ]
                       subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                       
                       if os.path.exists(temp_path):
                           os.replace(temp_path, output_path)
                           print(f"  [AUDIO] Silence removed from {output_path}")
                   except Exception as e:
                       print(f"  [WARN] Failed to remove silence: {e}")

                return True
            else:
                print(f"ElevenLabs Error {response.status_code}: {response.text}")
                return False
        except Exception as e:
            print(f"ElevenLabs Connection Error: {e}")
            return False
