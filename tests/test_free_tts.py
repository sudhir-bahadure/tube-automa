import os
import unittest
from unittest.mock import AsyncMock, patch

from src.voice_engine import VoiceEngine


class FreeTtsTests(unittest.IsolatedAsyncioTestCase):
    async def test_free_tts_only_skips_paid_provider_even_if_key_exists(self):
        with patch.dict(os.environ, {"FREE_TTS_ONLY": "true"}, clear=False):
            with patch("src.voice_engine.ElevenLabsEngine") as paid_engine:
                engine = VoiceEngine()
                self.assertIsNone(engine.eleven)
                paid_engine.assert_not_called()
                with patch("src.voice_engine.edge_tts.Communicate") as communicate:
                    communicate.return_value.save = AsyncMock()
                    result = await engine.generate_audio(
                        "This is a free narration test.", "unused-output.mp3"
                    )
                self.assertTrue(result)
                self.assertIsNone(engine.eleven)
                paid_engine.assert_not_called()


if __name__ == "__main__":
    unittest.main()
