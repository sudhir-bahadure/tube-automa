import os
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
