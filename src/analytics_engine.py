"""Read-only YouTube Analytics snapshots for the channel's editorial feedback loop."""
from datetime import date, timedelta
import json
import logging
import os

from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """Collect aggregate/video-level performance without ever changing channel data."""

    METRICS = ",".join([
        "views", "estimatedMinutesWatched", "averageViewDuration",
        "averageViewPercentage", "subscribersGained",
    ])

    def __init__(self, credentials):
        if credentials is None:
            raise ValueError("OAuth credentials are required for YouTube Analytics.")
        self.service = build(
            "youtubeAnalytics", "v2", credentials=credentials,
            cache_discovery=False,
        )

    def collect_video_report(self, days=28, output_path="output/analytics_snapshot.json"):
        """Fetch the most recent complete reporting window; save locally, not to git."""
        end_date = date.today() - timedelta(days=2)
        start_date = end_date - timedelta(days=max(1, int(days)) - 1)
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
            "note": "Analytics data can be delayed or revised. Compare videos of similar age, length and format.",
        }
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=False, indent=2)
        logger.info("Saved transient read-only YouTube Analytics snapshot for this workflow run.")
        return snapshot

    @staticmethod
    def summarize(snapshot):
        rows = snapshot.get("rows", [])
        totals = {
            metric: sum(float(row.get(metric, 0) or 0) for row in rows)
            for metric in ("views", "estimatedMinutesWatched", "subscribersGained")
        }
        top_videos = sorted(
            rows,
            key=lambda row: float(row.get("estimatedMinutesWatched", 0) or 0),
            reverse=True,
        )[:10]
        return {"totals": totals, "top_videos": top_videos}
