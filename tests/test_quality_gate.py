import json
import os
import tempfile
import unittest
from unittest.mock import patch, Mock

from src.quality_gate import validate_video


class QualityGateTests(unittest.TestCase):
    def _valid_probe(self, duration="35.0", width=1080, height=1920):
        return {
            "format": {"duration": duration},
            "streams": [
                {"codec_type": "video", "width": width, "height": height},
                {"codec_type": "audio"},
            ],
        }

    def _file(self):
        handle = tempfile.NamedTemporaryFile(delete=False)
        handle.write(b"x" * 12000)
        handle.close()
        self.addCleanup(lambda: os.path.exists(handle.name) and os.unlink(handle.name))
        return handle.name

    @patch("src.quality_gate.subprocess.run")
    def test_accepts_valid_portrait_short(self, run):
        run.return_value = Mock(stdout=json.dumps(self._valid_probe()), returncode=0)
        result = validate_video(self._file(), is_short=True)
        self.assertEqual(result["width"], 1080)
        self.assertEqual(result["height"], 1920)

    @patch("src.quality_gate.subprocess.run")
    def test_rejects_landscape_short(self, run):
        run.return_value = Mock(
            stdout=json.dumps(self._valid_probe(width=1920, height=1080)),
            returncode=0,
        )
        with self.assertRaisesRegex(ValueError, "portrait"):
            validate_video(self._file(), is_short=True)

    @patch("src.quality_gate.subprocess.run")
    def test_rejects_missing_audio(self, run):
        data = self._valid_probe()
        data["streams"] = [data["streams"][0]]
        run.return_value = Mock(stdout=json.dumps(data), returncode=0)
        with self.assertRaisesRegex(ValueError, "no audio"):
            validate_video(self._file(), is_short=True)

    @patch("src.quality_gate.subprocess.run")
    def test_rejects_portrait_long_form(self, run):
        run.return_value = Mock(stdout=json.dumps(self._valid_probe(duration="480", width=1080, height=1920)), returncode=0)
        with self.assertRaisesRegex(ValueError, "landscape"):
            validate_video(self._file(), is_short=False)

    @patch("src.quality_gate.subprocess.run")
    def test_rejects_too_short_long_form(self, run):
        run.return_value = Mock(stdout=json.dumps(self._valid_probe(duration="240", width=1920, height=1080)), returncode=0)
        with self.assertRaisesRegex(ValueError, "minimum quality threshold"):
            validate_video(self._file(), is_short=False)

    @patch("src.quality_gate.subprocess.run")
    def test_accepts_valid_long_form(self, run):
        run.return_value = Mock(stdout=json.dumps(self._valid_probe(duration="480", width=1920, height=1080)), returncode=0)
        result = validate_video(self._file(), is_short=False)
        self.assertEqual(result["duration_seconds"], 480.0)

    def test_rejects_missing_file(self):
        with self.assertRaisesRegex(ValueError, "does not exist"):
            validate_video("not-a-real-video.mp4", is_short=True)


if __name__ == "__main__":
    unittest.main()
