import edge_tts
import asyncio
from .config import Config
from .elevenlabs_engine import ElevenLabsEngine

class VoiceEngine:
    def __init__(self):
        self.voice = Config.VOICE_NAME
        self.eleven = ElevenLabsEngine()

    async def generate_audio(self, text, output_file, mood="neutral", **kwargs):
        """
        Generates speech using ElevenLabs (Primary) or Edge TTS (Fallback).
        """
        try:
            # Clean text
            import re
            clean_text = re.sub(r'[*_#~>]', '', text)
            
            # 1. Try ElevenLabs first (High Quality / Cloned Voice)
            logger_print = f"--- Using ElevenLabs for: '{clean_text[:30]}...' ---"
            if self.eleven.api_key and self.eleven.voice_id:
                print(logger_print)
                success = self.eleven.generate_audio(clean_text, output_file, **kwargs)
                if success:
                    return True
                print("ElevenLabs failed or out of credits. Falling back to Edge TTS.")

            # 2. Fallback to Edge TTS (Free Forever)
            mood_params = {
                "excited": {"rate": "+15%", "pitch": "+4Hz"},
                "serious": {"rate": "-8%", "pitch": "-4Hz"},
                "whispering": {"rate": "-18%", "pitch": "-8Hz"},
                "curious": {"rate": "+5%", "pitch": "+10Hz"},
                "neutral": {"rate": "+0%", "pitch": "+0Hz"}
            }
            
            params = mood_params.get(mood.lower(), mood_params["neutral"])
            
            communicate = edge_tts.Communicate(
                clean_text, 
                self.voice, 
                rate=params["rate"], 
                pitch=params["pitch"]
            )
            await communicate.save(output_file)
            
            # Post-Process Edge TTS if requested
            if kwargs.get("remove_silence", False):
                try:
                   import subprocess
                   temp_path = output_file + ".tmp.mp3"
                   # Same ffmpeg filter: silence remove
                   cmd = [
                       "ffmpeg", "-y", "-i", output_file,
                       "-af", "silenceremove=stop_periods=-1:stop_duration=0.2:stop_threshold=-30dB",
                       temp_path
                   ]
                   subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                   
                   if os.path.exists(temp_path):
                       os.replace(temp_path, output_file)
                       print(f"  [AUDIO] Silence removed from {output_file} (EdgeTTS)")
                except Exception as e:
                   print(f"  [WARN] Failed to remove silence: {e}")

            return True
        except Exception as e:
            print(f"Error generating audio: {e}")
            return False
