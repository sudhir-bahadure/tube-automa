import edge_tts
import asyncio
from .config import Config

class VoiceEngine:
    def __init__(self):
        self.voice = Config.VOICE_NAME

    async def generate_audio(self, text, output_file, mood="neutral"):
        """
        Generates speech from text using MS Edge TTS with emotional parameters.
        Moods: neutral, excited, serious, whispering, curious
        """
        try:
            # Clean text: Remove markdown emphasis and asterisks
            import re
            clean_text = re.sub(r'[*_#~>]', '', text)
            
            # Map moods to edge-tts parameters
            # Rate: +X% (faster), -X% (slower)
            # Pitch: +XHz (higher), -XHz (lower)
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
            return True
        except Exception as e:
            print(f"Error generating audio with mood {mood}: {e}")
            return False
