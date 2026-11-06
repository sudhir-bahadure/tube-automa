import os
import tempfile
import unittest

import numpy as np
from moviepy.audio.AudioClip import AudioArrayClip

from src.video_editor import VideoEditor


class VideoEditorFailClosedTests(unittest.TestCase):
    def test_missing_narration_stops_render(self):
        with tempfile.TemporaryDirectory() as directory:
            editor = VideoEditor()
            with self.assertRaisesRegex(RuntimeError, "narration file is missing"):
                editor.create_video(
                    [{
                        "audio_path": os.path.join(directory, "missing.mp3"),
                        "video_path": os.path.join(directory, "missing.jpg"),
                        "text": "This scene must not be rendered silently.",
                    }],
                    os.path.join(directory, "out.mp4"),
                    is_short=True,
                    style="psych_stickman",
                )

    def test_missing_visual_stops_render_instead_of_using_placeholder(self):
        with tempfile.TemporaryDirectory() as directory:
            audio_path = os.path.join(directory, "voice.mp3")
            samples = np.zeros((44100, 2), dtype=np.float32)
            AudioArrayClip(samples, fps=44100).write_audiofile(
                audio_path, fps=44100, nbytes=2, codec="libmp3lame", logger=None
            )
            with self.assertRaisesRegex(RuntimeError, "refusing to render a placeholder"):
                VideoEditor().create_video(
                    [{
                        "audio_path": audio_path,
                        "video_path": os.path.join(directory, "missing.jpg"),
                        "text": "A scene without a real visual must not pass.",
                    }],
                    os.path.join(directory, "out.mp4"),
                    is_short=True,
                    style="psych_stickman",
                )


if __name__ == "__main__":
    unittest.main()
