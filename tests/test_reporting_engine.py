import unittest
from unittest.mock import Mock, patch

from src.reporting_engine import ReportingEngine


class ReportingEngineTests(unittest.TestCase):
    @patch("src.reporting_engine.build")
    def test_creates_daily_reach_job_when_missing(self, build):
        service = Mock()
        service.jobs.return_value.list.return_value.execute.return_value = {"jobs": []}
        service.jobs.return_value.create.return_value.execute.return_value = {
            "id": "job-1",
            "reportTypeId": "channel_reach_basic_a1",
        }
        build.return_value = service
        engine = ReportingEngine(credentials=Mock())
        job = engine._get_or_create_job()
        self.assertEqual(job["id"], "job-1")
        service.jobs.return_value.create.assert_called_once()
        self.assertEqual(
            service.jobs.return_value.create.call_args.kwargs["body"]["reportTypeId"],
            "channel_reach_basic_a1",
        )

    @patch("src.reporting_engine.build")
    def test_reuses_existing_reach_job(self, build):
        service = Mock()
        existing = {"id": "existing", "reportTypeId": "channel_reach_basic_a1"}
        service.jobs.return_value.list.return_value.execute.return_value = {"jobs": [existing]}
        build.return_value = service
        engine = ReportingEngine(credentials=Mock())
        self.assertEqual(engine._get_or_create_job(), existing)
        service.jobs.return_value.create.assert_not_called()


if __name__ == "__main__":
    unittest.main()
