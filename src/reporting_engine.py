"""Optional daily thumbnail-reach reports through the YouTube Reporting API.

Daily reports can take up to 24 hours to appear. API enablement failures or pending reports
are optional diagnostics and must never block video production.
"""
import csv
import gzip
import io
import json
import logging
import os

import requests
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class ReportingEngine:
    REPORT_TYPE_ID = "channel_reach_basic_a1"
    REPORT_NAME = "TubeAutoma Channel Reach Basic"

    def __init__(self, credentials):
        if credentials is None:
            raise ValueError("OAuth credentials are required for YouTube Reporting.")
        self.credentials = credentials
        self.service = build(
            "youtubereporting", "v1", credentials=credentials,
            cache_discovery=False,
        )

    def _get_or_create_job(self):
        response = self.service.jobs().list().execute()
        for job in response.get("jobs", []):
            if job.get("reportTypeId") == self.REPORT_TYPE_ID:
                return job
        job = self.service.jobs().create(
            body={
                "name": self.REPORT_NAME,
                "reportTypeId": self.REPORT_TYPE_ID,
            }
        ).execute()
        logger.info("Created daily YouTube Reporting job %s.", job.get("id", ""))
        return job

    def collect_latest_reach_report(self, output_path="output/thumbnail_reach_snapshot.json"):
        """Create the daily job once, then download the newest available report."""
        job = self._get_or_create_job()
        job_id = job.get("id")
        if not job_id:
            raise RuntimeError("YouTube Reporting API returned a job without an ID.")

        response = self.service.jobs().reports().list(
            jobId=job_id,
            pageSize=10,
        ).execute()
        reports = response.get("reports", [])
        if not reports:
            snapshot = {
                "available": False,
                "job_id": job_id,
                "report_type": self.REPORT_TYPE_ID,
                "rows": [],
                "note": "The daily report has not arrived yet; YouTube says reports can take up to 24 hours.",
            }
            self._persist(snapshot, output_path)
            logger.info("Thumbnail reach report is pending; continuing without it.")
            return snapshot

        report = max(reports, key=lambda item: item.get("createTime", ""))
        download_url = report.get("downloadUrl")
        if not download_url:
            raise RuntimeError("Latest YouTube Reporting report has no download URL.")

        if self.credentials.expired:
            from google.auth.transport.requests import Request
            self.credentials.refresh(Request())
        response = requests.get(
            download_url,
            headers={"Authorization": f"Bearer {self.credentials.token}"},
            timeout=60,
        )
        response.raise_for_status()
        payload = response.content
        if payload.startswith(b"\x1f\x8b"):
            payload = gzip.decompress(payload)
        text_data = payload.decode("utf-8-sig")
        rows = list(csv.DictReader(io.StringIO(text_data)))
        snapshot = {
            "available": True,
            "job_id": job_id,
            "report_id": report.get("id"),
            "report_type": self.REPORT_TYPE_ID,
            "create_time": report.get("createTime"),
            "start_time": report.get("startTime"),
            "end_time": report.get("endTime"),
            "row_count": len(rows),
            "rows": rows,
        }
        self._persist(snapshot, output_path)
        logger.info("Downloaded YouTube thumbnail reach report (%s rows).", len(rows))
        return snapshot

    @staticmethod
    def _persist(snapshot, output_path):
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as handle:
            json.dump(snapshot, handle, ensure_ascii=False, indent=2)
