import os
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from src.asset_manager import AssetManager


class AssetFallbackTests(unittest.TestCase):
    def test_local_fallback_creates_valid_portrait_jpeg(self):
        manager = AssetManager()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "fallback.jpg")
            self.assertTrue(
                manager.generate_fallback_visual(
                    "a stickman thinking beside a clock", path, "portrait"
                )
            )
            self.assertGreater(os.path.getsize(path), 1000)
            with Image.open(path) as image:
                self.assertEqual(image.size, (1080, 1920))
                self.assertEqual(image.format, "JPEG")

    def test_distinct_scene_prompts_create_distinct_artwork(self):
        manager = AssetManager()
        with tempfile.TemporaryDirectory() as directory:
            spotlight = os.path.join(directory, "spotlight.jpg")
            conference = os.path.join(directory, "conference.jpg")
            self.assertTrue(
                manager.generate_fallback_visual(
                    "A stickman under a sharp yellow spotlight", spotlight, "portrait"
                )
            )
            self.assertTrue(
                manager.generate_fallback_visual(
                    "A stickman at a conference table with two people", conference, "portrait"
                )
            )
            with Image.open(spotlight) as first, Image.open(conference) as second:
                self.assertEqual(first.size, (1080, 1920))
                self.assertEqual(second.size, (1080, 1920))
                self.assertNotEqual(first.tobytes(), second.tobytes())

    def test_psych_stickman_visuals_do_not_call_external_image_service(self):
        manager = AssetManager()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "scene.jpg")
            with patch.object(manager, "download_file") as download:
                self.assertTrue(
                    manager.generate_image(
                        "A stickman illuminated by a yellow spotlight",
                        path,
                        orientation="portrait",
                        style="psych_stickman",
                        video_type="short",
                        allow_fallback=False,
                    )
                )
                download.assert_not_called()
            with Image.open(path) as image:
                self.assertEqual(image.size, (1080, 1920))

    def test_local_thumbnail_has_expected_dimensions(self):
        manager = AssetManager()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "thumbnail.jpg")
            self.assertTrue(
                manager.generate_thumbnail("The Spotlight Effect: Why Nobody Notices", path)
            )
            with Image.open(path) as image:
                self.assertEqual(image.size, (1280, 720))
                self.assertEqual(image.format, "JPEG")
            self.assertGreater(os.path.getsize(path), 5000)

    def test_other_styles_remain_fail_closed_without_fallback_opt_in(self):
        manager = AssetManager()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "scene.jpg")
            with patch.object(manager, "download_file", return_value=False):
                self.assertFalse(
                    manager.generate_image(
                        "A surrealist noir image of a mirror",
                        path,
                        orientation="landscape",
                        style="noir",
                        video_type="long",
                        allow_fallback=False,
                    )
                )
            self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
