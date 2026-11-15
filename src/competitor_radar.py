"""Quota-bounded competitor topic research via the official YouTube Data API.

This is public-metadata sampling, not search-volume data or proof of recommendation performance.
"""
from datetime import datetime, timedelta, timezone
import json
import logging
import os
import re
import statistics

logger = logging.getLogger(__name__)

DEFAULT_QUERIES = (
    "everyday psychology human behaviour relationships",
    "why people overthink psychology social behaviour",
    "cognitive bias memory habits psychology explained",
)


def parse_iso8601_duration(value):
    """Parse a YouTube API ISO-8601 duration into seconds."""
    match = re.fullmatch(
        r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?",
        str(value or ""),
    )
    if not match:
        return 0
    hours, minutes, seconds = match.groups()
    return int(hours or 0) * 3600 + int(minutes or 0) * 60 + float(seconds or 0)


class CompetitorRadar:
    """Find recent public videos that outperform a small topic-search sample."""

    def __init__(
        self,
        youtube_service,
        queries=None,
        lookback_days=30,
        max_results_per_query=15,
        max_queries=3,
        now=None,
    ):
        if youtube_service is None:
            raise ValueError("YouTube Data API service is required.")
        self.youtube = youtube_service
        self.queries = tuple(queries or DEFAULT_QUERIES)
        self.lookback_days = max(1, int(lookback_days))
        self.max_results_per_query = min(50, max(1, int(max_results_per_query)))
        self.max_queries = min(3, max(1, int(max_queries)))
        self.now = now or datetime.now(timezone.utc)

    def collect(self, output_path="output/competitor_snapshot.json"):
        published_after = (
            self.now - timedelta(days=self.lookback_days)
        ).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

        discovered = {}
        queries_used = self.queries[: self.max_queries]
        for query in queries_used:
            response = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                order="viewCount",
                publishedAfter=published_after,
                maxResults=self.max_results_per_query,
                relevanceLanguage="en",
                safeSearch="moderate",
            ).execute()
            for item in response.get("items", []):
                video_id = item.get("id", {}).get("videoId")
                if video_id:
                    discovered.setdefault(video_id, {
                        "video_id": video_id,
                        "query": query,
                    })

        video_ids = list(discovered)
        if not video_ids:
            snapshot = {
                "generated_at": self.now.isoformat(),
                "lookback_days": self.lookback_days,
                "queries": list(queries_used),
                "result_count": 0,
                "videos": [],
                "note": "No matching public videos returned by the configured searches.",
            }
            self._persist(snapshot, output_path)
            return snapshot

        video_rows = []
        for offset in range(0, len(video_ids), 50):
            batch = video_ids[offset : offset + 50]
            response = self.youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch),
                maxResults=len(batch),
            ).execute()
            video_rows.extend(response.get("items", []))

        channel_ids = sorted({
            item.get("snippet", {}).get("channelId", "")
            for item in video_rows
            if item.get("snippet", {}).get("channelId")
        })
        channel_stats = {}
        for offset in range(0, len(channel_ids), 50):
            batch = channel_ids[offset : offset + 50]
            response = self.youtube.channels().list(
                part="statistics",
                id=",".join(batch),
                maxResults=len(batch),
            ).execute()
            for channel in response.get("items", []):
                channel_stats[channel.get("id", "")] = channel.get("statistics", {})

        rows = []
        for item in video_rows:
            video_id = item.get("id", "")
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            published = snippet.get("publishedAt")
            if not video_id or not published:
                continue
            try:
                published_at = datetime.fromisoformat(published.replace("Z", "+00:00"))
            except ValueError:
                continue

            age_days = max(1.0, (self.now - published_at).total_seconds() / 86400.0)
            views = int(stats.get("viewCount", 0) or 0)
            channel_id = snippet.get("channelId", "")
            subscriber_count = int(
                channel_stats.get(channel_id, {}).get("subscriberCount", 0) or 0
            )
            duration = parse_iso8601_duration(
                item.get("contentDetails", {}).get("duration")
            )
            rows.append({
                "video_id": video_id,
                "title": snippet.get("title", ""),
                "channel_id": channel_id,
                "channel_title": snippet.get("channelTitle", ""),
                "published_at": published_at.isoformat(),
                "age_days": round(age_days, 2),
                "views": views,
                "views_per_day": round(views / age_days, 2),
                "subscriber_count": subscriber_count or None,
                "views_per_subscriber": (
                    round(views / subscriber_count, 4) if subscriber_count else None
                ),
                "duration_seconds": duration,
                # Duration is observable; Shorts format is not reliably inferable
                # from public Data API metadata alone (orientation/eligibility matter).
                "duration_band": "under_3m" if duration < 180 else "3m_or_more",
                "search_query": discovered.get(video_id, {}).get("query", ""),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            })

        velocities = [r["views_per_day"] for r in rows if r["views_per_day"] > 0]
        median_velocity = statistics.median(velocities) if velocities else 1.0
        for row in rows:
            row["sample_velocity_ratio"] = round(
                row["views_per_day"] / max(median_velocity, 1.0), 2
            )

        rows.sort(
            key=lambda r: (r["sample_velocity_ratio"], r["views_per_day"], r["views"]),
            reverse=True,
        )
        snapshot = {
            "generated_at": self.now.isoformat(),
            "lookback_days": self.lookback_days,
            "queries": list(queries_used),
            "result_count": len(rows),
            "videos": rows[:20],
            "format_detection": "unknown_from_public_metadata",
            "note": (
                "Public YouTube search sample only. Views/day and sample velocity are "
                "directional signals, not search volume, causal evidence, or a forecast. "
                "The API sample does not reliably identify Shorts versus long-form; "
                "duration bands are provided without assigning a format."
            ),
        }
        self._persist(snapshot, output_path)
        logger.info(
            "Competitor radar collected %s recent public videos from %s bounded queries.",
            len(rows), len(queries_used),
        )
        return snapshot

    @staticmethod
    def _persist(snapshot, output_path):
        if not output_path:
            return
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=False, indent=2)
