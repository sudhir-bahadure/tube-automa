import unittest
from datetime import datetime, timezone
from unittest.mock import Mock

from src.competitor_radar import CompetitorRadar, parse_iso8601_duration


class CompetitorRadarTests(unittest.TestCase):
    def test_parse_iso8601_duration(self):
        self.assertEqual(parse_iso8601_duration("PT1H2M3S"), 3723)
        self.assertEqual(parse_iso8601_duration("PT42S"), 42)
        self.assertEqual(parse_iso8601_duration("P0D"), 0)

    def test_collects_public_outliers_with_bounded_searches(self):
        youtube = Mock()
        youtube.search.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": {"videoId": "v1"},
                    "snippet": {"channelId": "c1"},
                },
                {
                    "id": {"videoId": "v2"},
                    "snippet": {"channelId": "c2"},
                },
            ]
        }
        youtube.videos.return_value.list.return_value.execute.return_value = {
            "items": [
                {
                    "id": "v1",
                    "snippet": {
                        "title": "Why people overthink",
                        "channelTitle": "Channel A",
                        "channelId": "c1",
                        "publishedAt": "2026-11-10T00:00:00Z",
                    },
                    "statistics": {"viewCount": "10000"},
                    "contentDetails": {"duration": "PT45S"},
                },
                {
                    "id": "v2",
                    "snippet": {
                        "title": "How memory works",
                        "channelTitle": "Channel B",
                        "channelId": "c2",
                        "publishedAt": "2026-11-01T00:00:00Z",
                    },
                    "statistics": {"viewCount": "2000"},
                    "contentDetails": {"duration": "PT12M"},
                },
            ]
        }
        youtube.channels.return_value.list.return_value.execute.return_value = {
            "items": [
                {"id": "c1", "statistics": {"subscriberCount": "1000"}},
                {"id": "c2", "statistics": {"subscriberCount": "10000"}},
            ]
        }
        radar = CompetitorRadar(
            youtube,
            queries=("psychology one", "psychology two", "psychology three", "ignored fourth"),
            max_queries=3,
            now=datetime(2026, 11, 15, tzinfo=timezone.utc),
        )
        snapshot = radar.collect(output_path=None)
        self.assertEqual(snapshot["result_count"], 2)
        self.assertEqual(len(snapshot["queries"]), 3)
        self.assertEqual(snapshot["videos"][0]["video_id"], "v1")
        self.assertGreater(snapshot["videos"][0]["views_per_day"], 0)
        self.assertEqual(snapshot["videos"][0]["duration_seconds"], 45)
        self.assertEqual(snapshot["videos"][0]["duration_band"], "under_3m")
        self.assertNotIn("format", snapshot["videos"][0])
        self.assertEqual(snapshot["format_detection"], "unknown_from_public_metadata")
        self.assertEqual(youtube.search.return_value.list.call_count, 3)

    def test_requires_youtube_service(self):
        with self.assertRaisesRegex(ValueError, "service"):
            CompetitorRadar(None)


if __name__ == "__main__":
    unittest.main()
