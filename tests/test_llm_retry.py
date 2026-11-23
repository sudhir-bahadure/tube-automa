import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.config import Config
from src.llm_wrapper import LLMWrapper


class GeminiRetryTests(unittest.TestCase):
    def make_wrapper(self, outcomes):
        wrapper = object.__new__(LLMWrapper)
        wrapper.preferred_models = ["gemini-free"]
        wrapper.available_gen_models = ["gemini-free"]
        wrapper.client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=unittest.mock.Mock(side_effect=outcomes)
            )
        )
        return wrapper

    def test_sdk_retries_are_disabled_and_requests_have_a_timeout(self):
        with patch.object(Config, "GEMINI_API_KEY", "test-key"), \
             patch("src.llm_wrapper.genai.Client") as client, \
             patch.object(LLMWrapper, "_refresh_available_models"):
            LLMWrapper()

        http_options = client.call_args.kwargs["http_options"]
        self.assertEqual(http_options["timeout"], 30_000)
        self.assertEqual(http_options["retry_options"], {"attempts": 1})

    def test_retries_temporary_503_on_the_same_configured_free_model(self):
        wrapper = self.make_wrapper([
            RuntimeError("503 UNAVAILABLE"),
            RuntimeError("503 Service Unavailable"),
            SimpleNamespace(text="[\"A fresh psychology topic\"]"),
        ])

        with patch.object(Config, "GEMINI_FREE_TIER_ONLY", True), \
             patch.object(Config, "GEMINI_MODEL", "gemini-free"), \
             patch("src.llm_wrapper.time.sleep") as sleep:
            result = wrapper._call_gemini("prompt", max_retries=3)

        self.assertEqual(result, '["A fresh psychology topic"]')
        self.assertEqual(
            [call.kwargs["model"] for call in wrapper.client.models.generate_content.call_args_list],
            ["gemini-free", "gemini-free", "gemini-free"],
        )
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_free_tier_quota_failure_stops_without_retry(self):
        wrapper = self.make_wrapper([RuntimeError("429 RESOURCE_EXHAUSTED")])

        with patch.object(Config, "GEMINI_FREE_TIER_ONLY", True), \
             patch.object(Config, "GEMINI_MODEL", "gemini-free"), \
             patch("src.llm_wrapper.time.sleep") as sleep:
            result = wrapper._call_gemini("prompt", max_retries=3)

        self.assertIsNone(result)
        wrapper.client.models.generate_content.assert_called_once()
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()

