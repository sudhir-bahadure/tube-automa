import os
import tempfile
import unittest

import numpy as np
from PIL import Image
from moviepy.audio.AudioClip import AudioArrayClip

from src.video_editor import VideoEditor


class VideoRenderSmokeTests(unittest.TestCase):
    def test_renders_one_scene_with_audio_and_visual(self):
        with tempfile.TemporaryDirectory() as directory:
            audio_path = os.path.join(directory, "voice.mp3")
            image_path = os.path.join(directory, "scene.jpg")
            output_path = os.path.join(directory, "smoke.mp4")

            Image.new("RGB", (720, 1280), (35, 45, 60)).save(image_path, "JPEG")
            samples = np.zeros((44100, 2), dtype=np.float32)
            samples[:, 0] = 0.02 * np.sin(2 * np.pi * 440 * np.arange(44100) / 44100)
            samples[:, 1] = samples[:, 0]
            AudioArrayClip(samples, fps=44100).write_audiofile(
                audio_path, fps=44100, nbytes=2, codec="libmp3lame", logger=None
            )

            result = VideoEditor().create_video(
                [{
                    "audio_path": audio_path,
                    "video_path": image_path,
                    "text": "A small test scene confirms that the renderer combines narration, visuals and captions.",
                }],
                output_path,
                is_short=True,
                style="psych_stickman",
            )
            self.assertTrue(result)
            self.assertTrue(os.path.isfile(output_path))
            self.assertGreater(os.path.getsize(output_path), 10000)


if __name__ == "__main__":
    unittest.main()
