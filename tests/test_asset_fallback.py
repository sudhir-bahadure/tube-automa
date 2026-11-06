import os
import tempfile
import unittest
from PIL import Image
from src.asset_manager import AssetManager

class AssetFallbackTests(unittest.TestCase):
    def test_local_fallback_creates_valid_portrait_jpeg(self):
        manager = AssetManager()
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, 'fallback.jpg')
            self.assertTrue(manager.generate_fallback_visual('a stickman thinking beside a clock', path, 'portrait'))
            self.assertTrue(os.path.getsize(path) > 1000)
            with Image.open(path) as image:
                self.assertEqual(image.size, (1080, 1920))

if __name__ == '__main__':
    unittest.main()
