import os
import unittest
from unittest.mock import Mock, patch

from src.youtube_uploader import YouTubeUploader


class YouTubeDestinationTests(unittest.TestCase):
    def setUp(self):
        self.uploader = YouTubeUploader.__new__(YouTubeUploader)
        self.uploader.youtube = Mock()
        self.uploader.youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [{
                "id": "UC_expected_channel",
                "snippet": {"title": "MARROW PSYCHOLOGY"},
            }]
        }

    @patch.dict(os.environ, {
        "YOUTUBE_EXPECTED_CHANNEL_TITLE": "MARROW PSYCHOLOGY",
        "YOUTUBE_EXPECTED_CHANNEL_ID": "UC_expected_channel",
    }, clear=False)
    def test_accepts_exact_channel_id_and_title(self):
        self.uploader._verify_expected_channel()
        self.assertEqual(self.uploader.channel_id, "UC_expected_channel")

    @patch.dict(os.environ, {
        "YOUTUBE_EXPECTED_CHANNEL_TITLE": "MARROW PSYCHOLOGY",
        "YOUTUBE_EXPECTED_CHANNEL_ID": "UC_wrong_channel",
    }, clear=False)
    def test_rejects_wrong_channel_id_even_when_title_matches(self):
        with self.assertRaisesRegex(RuntimeError, "destination mismatch"):
            self.uploader._verify_expected_channel()

    @patch.dict(os.environ, {
        "YOUTUBE_EXPECTED_CHANNEL_TITLE": "MARROW PSYCHOLOGY",
    }, clear=False)
    def test_requires_expected_channel_id(self):
        os.environ.pop("YOUTUBE_EXPECTED_CHANNEL_ID", None)
        with self.assertRaisesRegex(RuntimeError, "YOUTUBE_EXPECTED_CHANNEL_ID"):
            self.uploader._verify_expected_channel()


if __name__ == "__main__":
    unittest.main()
