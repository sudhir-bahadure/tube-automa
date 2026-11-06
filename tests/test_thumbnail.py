import os
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image
from src.asset_manager import AssetManager


class ThumbnailTests(unittest.TestCase):
    def test_thumbnail_has_exact_dimensions_and_title_overlay(self):
        manager = AssetManager()

        def fake_image(prompt, output_path, **kwargs):
            Image.new("RGB", (1280, 720), (24, 30, 42)).save(output_path, "JPEG")
            return True

        with tempfile.TemporaryDirectory() as directory:
            output = os.path.join(directory, "thumbnail.jpg")
            with patch.object(manager, "generate_image", side_effect=fake_image):
                self.assertTrue(manager.generate_thumbnail(
                    "Why Your Memory Changes Over Time", output
                ))
            with Image.open(output) as image:
                self.assertEqual(image.size, (1280, 720))
                self.assertGreater(os.path.getsize(output), 5000)


if __name__ == "__main__":
    unittest.main()
