import json
import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from src.analytics_engine import AnalyticsEngine


class AnalyticsEngineTests(unittest.TestCase):
    @patch("src.analytics_engine.build")
    def test_collects_and_persists_video_rows(self, build):
        query = Mock()
        query.execute.return_value = {
            "columnHeaders": [{"name": "video"}, {"name": "views"}, {"name": "estimatedMinutesWatched"}],
            "rows": [["video-1", 120, 80.5]],
        }
        service = Mock()
        service.reports.return_value.query.return_value = query
        build.return_value = service

        engine = AnalyticsEngine(credentials=object())
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "analytics.json")
            snapshot = engine.collect_video_report(days=28, output_path=path)
            self.assertEqual(snapshot["row_count"], 1)
            self.assertEqual(snapshot["rows"][0]["video"], "video-1")
            with open(path, encoding="utf-8") as handle:
                persisted = json.load(handle)
            self.assertEqual(persisted["rows"][0]["views"], 120)

        summary = engine.summarize(snapshot)
        self.assertEqual(summary["totals"]["views"], 120)
        self.assertEqual(summary["top_videos"][0]["video"], "video-1")

    def test_requires_credentials(self):
        with self.assertRaisesRegex(ValueError, "credentials"):
            AnalyticsEngine(credentials=None)


if __name__ == "__main__":
    unittest.main()
