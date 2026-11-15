"""Read-only YouTube Analytics snapshots for the channel's editorial feedback loop."""
from datetime import date, timedelta
import json
import logging
import os

from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Collect aggregate/video-level performance without changing channel data."""

    METRICS = ",".join([
        "views", "estimatedMinutesWatched", "averageViewDuration",
        "averageViewPercentage", "subscribersGained", "likes", "comments", "shares",
    ])
    RETENTION_METRICS = ",".join([
        "audienceWatchRatio", "relativeRetentionPerformance",
        "startedWatching", "stoppedWatching", "totalSegmentImpressions",
    ])

    def __init__(self, credentials):
        if credentials is None:
            raise ValueError("OAuth credentials are required for YouTube Analytics.")
        self.service = build(
            "youtubeAnalytics", "v2", credentials=credentials,
            cache_discovery=False,
        )

    @staticmethod
    def _date_window(days):
        end_date = date.today() - timedelta(days=2)
        start_date = end_date - timedelta(days=max(1, int(days)) - 1)
        return start_date, end_date

    def collect_video_report(self, days=28, output_path="output/analytics_snapshot.json"):
        """Fetch a recent complete reporting window; save privately on the runner."""
        start_date, end_date = self._date_window(days)
        response = self.service.reports().query(
            ids="channel==MINE",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            metrics=self.METRICS,
            dimensions="video",
            sort="-estimatedMinutesWatched",
            maxResults=200,
        ).execute()

        headers = [item.get("name", "") for item in response.get("columnHeaders", [])]
        rows = [dict(zip(headers, raw)) for raw in response.get("rows", [])]
        snapshot = {
            "generated_on": date.today().isoformat(),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "dimensions": "video",
            "metrics": self.METRICS.split(","),
            "row_count": len(rows),
            "rows": rows,
            "note": "Private channel analytics. Reporting data can be delayed or revised; compare similar formats and video ages.",
        }
        self._persist(snapshot, output_path)
        logger.info("Saved transient read-only YouTube Analytics video snapshot.")
        return snapshot

    def collect_retention_report(self, video_id, days=28, output_path=None):
        """Fetch the audience-retention curve for one video (the API requires one ID)."""
        if not video_id:
            raise ValueError("A single video ID is required for audience-retention reporting.")
        start_date, end_date = self._date_window(days)
        response = self.service.reports().query(
            ids="channel==MINE",
            startDate=start_date.isoformat(),
            endDate=end_date.isoformat(),
            metrics=self.RETENTION_METRICS,
            dimensions="elapsedVideoTimeRatio",
            filters=f"video=={video_id}",
        ).execute()
        headers = [item.get("name", "") for item in response.get("columnHeaders", [])]
        rows = [dict(zip(headers, raw)) for raw in response.get("rows", [])]
        snapshot = {
            "generated_on": date.today().isoformat(),
            "video_id": video_id,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "dimensions": "elapsedVideoTimeRatio",
            "metrics": self.RETENTION_METRICS.split(","),
            "row_count": len(rows),
            "rows": rows,
        }
        if output_path is None:
            output_path = f"output/retention_{video_id}.json"
        self._persist(snapshot, output_path)
        logger.info("Saved transient retention curve for %s (%s points).", video_id, len(rows))
        return snapshot

    @staticmethod
    def summarize(snapshot):
        rows = snapshot.get("rows", [])
        top_videos = sorted(
            rows,
            key=lambda row: float(row.get("estimatedMinutesWatched", 0) or 0),
            reverse=True,
        )[:10]
        return {"top_videos": top_videos}

    @staticmethod
    def summarize_retention(snapshot):
        """Return compact diagnostics from the private retention curve."""
        rows = snapshot.get("rows", [])
        if not rows:
            return {"video_id": snapshot.get("video_id"), "points": 0}
        ordered = sorted(
            rows,
            key=lambda row: float(row.get("elapsedVideoTimeRatio", 0) or 0),
        )
        first, last = ordered[0], ordered[-1]
        midpoint = min(
            ordered,
            key=lambda row: abs(float(row.get("elapsedVideoTimeRatio", 0) or 0) - 0.5),
        )
        return {
            "video_id": snapshot.get("video_id"),
            "points": len(ordered),
            "opening_watch_ratio": float(first.get("audienceWatchRatio", 0) or 0),
            "midpoint_watch_ratio": float(midpoint.get("audienceWatchRatio", 0) or 0),
            "ending_watch_ratio": float(last.get("audienceWatchRatio", 0) or 0),
            "opening_relative_retention": float(
                first.get("relativeRetentionPerformance", 0) or 0
            ),
            "ending_relative_retention": float(
                last.get("relativeRetentionPerformance", 0) or 0
            ),
        }

    @staticmethod
    def _persist(snapshot, output_path):
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=False, indent=2)
