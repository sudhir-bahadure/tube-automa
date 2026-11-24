import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.topic_bank import TOPIC_BANK
from src.trends import TrendEngine


class TopicQueueTests(unittest.TestCase):
    def test_topic_selection_uses_local_queue_without_llm_request(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TrendEngine(str(Path(temp_dir) / "used.json"))
            llm = Mock()

            topic = engine.get_viral_topic(llm)

        self.assertEqual(topic, TOPIC_BANK[0][0])
        llm._call_gemini.assert_not_called()

    def test_topic_selection_never_repeats_case_insensitively(self):
        first_topic = TOPIC_BANK[0][0]
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TrendEngine(str(Path(temp_dir) / "used.json"))
            engine.used_topics = [first_topic.upper()]

            topic = engine.get_viral_topic()

        self.assertNotEqual(topic.casefold(), first_topic.casefold())
        self.assertIn(topic, [candidate for candidate, _ in TOPIC_BANK[1:]])

    def test_recent_performance_can_prioritize_a_topic_category(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TrendEngine(str(Path(temp_dir) / "used.json"))

            topic = engine.get_viral_topic(
                performance_context=[{"title": "Memory recall strategies", "views": 1000}]
            )

        self.assertEqual(topic, "Why familiar places can make it easier to remember")

    def test_exhausted_queue_uses_free_provider_for_one_new_topic(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            engine = TrendEngine(str(Path(temp_dir) / "used.json"))
            engine.used_topics = [topic for topic, _ in TOPIC_BANK]
            llm = Mock()
            llm._call_gemini.return_value = '"Why context changes a memory"'

            topic = engine.get_viral_topic(llm)

        self.assertEqual(topic, "Why context changes a memory")
        llm._call_gemini.assert_called_once()


if __name__ == "__main__":
    unittest.main()
