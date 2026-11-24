import unittest
from types import SimpleNamespace
from unittest.mock import patch

from src.config import Config
from src.llm_wrapper import LLMWrapper


class GeminiRetryTests(unittest.TestCase):
    def make_wrapper(self, outcomes):
        wrapper = object.__new__(LLMWrapper)
        wrapper.preferred_models = ["gemini-3.8-flash"]
        wrapper.available_gen_models = ["gemini-3.8-flash"]
        wrapper.client = SimpleNamespace(
            models=SimpleNamespace(
                generate_content=unittest.mock.Mock(side_effect=outcomes)
            )
        )
        return wrapper

    def test_sdk_retries_are_disabled_and_requests_have_a_timeout(self):
        with patch.object(Config, "GEMINI_API_KEY", "test-key"), \
             patch("src.llm_wrapper.genai.Client") as client:
            LLMWrapper()

        http_options = client.call_args.kwargs["http_options"]
        self.assertEqual(http_options["timeout"], 30_000)
        self.assertEqual(http_options["retry_options"], {"attempts": 1})
        client.return_value.models.list.assert_not_called()

    def test_retries_temporary_503_on_the_same_configured_free_model(self):
        wrapper = self.make_wrapper([
            RuntimeError("503 UNAVAILABLE"),
            RuntimeError("503 Service Unavailable"),
            SimpleNamespace(text="[\"A fresh psychology topic\"]"),
        ])

        with patch.object(Config, "GEMINI_FREE_TIER_ONLY", True), \
             patch.object(Config, "GEMINI_MODEL", "gemini-3.8-flash"), \
             patch("src.llm_wrapper.time.sleep") as sleep:
            result = wrapper._call_gemini("prompt", max_retries=3)

        self.assertEqual(result, '["A fresh psychology topic"]')
        self.assertEqual(
            [call.kwargs["model"] for call in wrapper.client.models.generate_content.call_args_list],
            ["gemini-3.8-flash", "gemini-3.8-flash", "gemini-3.8-flash"],
        )
        self.assertEqual([call.args[0] for call in sleep.call_args_list], [1, 2])

    def test_free_tier_quota_failure_stops_without_retry(self):
        wrapper = self.make_wrapper([RuntimeError("429 RESOURCE_EXHAUSTED")])

        with patch.object(Config, "GEMINI_FREE_TIER_ONLY", True), \
             patch.object(Config, "GEMINI_MODEL", "gemini-3.8-flash"), \
             patch("src.llm_wrapper.time.sleep") as sleep:
            result = wrapper._call_gemini("prompt", max_retries=3)

        self.assertIsNone(result)
        wrapper.client.models.generate_content.assert_called_once()
        sleep.assert_not_called()

    def test_free_quota_routes_to_another_approved_free_gemini_model(self):
        wrapper = self.make_wrapper([
            RuntimeError("429 RESOURCE_EXHAUSTED"),
            SimpleNamespace(text="A valid script response"),
        ])
        wrapper.available_gen_models = ["gemini-3.8-flash", "gemini-3.5-flash-lite"]

        with patch.object(Config, "GEMINI_FREE_TIER_ONLY", True), \
             patch.object(Config, "GEMINI_MODEL", "gemini-3.8-flash"):
            result = wrapper._call_gemini("prompt")

        self.assertEqual(result, "A valid script response")
        self.assertEqual(
            [call.kwargs["model"] for call in wrapper.client.models.generate_content.call_args_list],
            ["gemini-3.8-flash", "gemini-3.5-flash-lite"],
        )

    def test_external_provider_requires_free_tier_confirmation(self):
        wrapper = self.make_wrapper([])
        with patch.object(Config, "GROQ_API_KEY", "test-key"), \
             patch.object(Config, "GROQ_FREE_TIER_CONFIRMED", False), \
             patch.object(LLMWrapper, "_call_groq_free") as groq:
            self.assertIsNone(wrapper._call_external_free_providers("prompt"))
        groq.assert_not_called()

    def test_confirmed_free_provider_is_used_after_gemini_exhaustion(self):
        wrapper = self.make_wrapper([RuntimeError("429 RESOURCE_EXHAUSTED")])
        with patch.object(Config, "GEMINI_FREE_TIER_ONLY", True), \
             patch.object(Config, "GEMINI_MODEL", "gemini-3.8-flash"), \
             patch.object(Config, "GROQ_API_KEY", "test-key"), \
             patch.object(Config, "GROQ_FREE_TIER_CONFIRMED", True), \
             patch.object(LLMWrapper, "_call_groq_free", return_value="fallback script") as groq:
            result = wrapper._call_gemini("prompt")
        self.assertEqual(result, "fallback script")
        groq.assert_called_once_with("prompt")

    def test_cloudflare_is_tried_after_groq_rate_limit(self):
        wrapper = self.make_wrapper([])
        with patch.object(Config, "GROQ_API_KEY", "groq-test-key"), \
             patch.object(Config, "GROQ_FREE_TIER_CONFIRMED", True), \
             patch.object(Config, "CLOUDFLARE_ACCOUNT_ID", "account-test"), \
             patch.object(Config, "CLOUDFLARE_API_TOKEN", "cloudflare-test-token"), \
             patch.object(Config, "CLOUDFLARE_WORKERS_FREE_CONFIRMED", True), \
             patch.object(LLMWrapper, "_call_groq_free", side_effect=RuntimeError("429 Too Many Requests")), \
             patch.object(LLMWrapper, "_call_cloudflare_free", return_value="cloudflare script") as cloudflare:
            result = wrapper._call_external_free_providers("prompt")

        self.assertEqual(result, "cloudflare script")
        cloudflare.assert_called_once_with("prompt")


    def test_groq_uses_current_completion_token_parameter(self):
        response = SimpleNamespace(
            raise_for_status=unittest.mock.Mock(),
            json=lambda: {"choices": [{"message": {"content": "script"}}]},
        )
        with patch.object(Config, "GROQ_API_KEY", "test-key"), \
             patch.object(Config, "GROQ_FREE_MODEL", "openai/gpt-oss-20b"), \
             patch("src.llm_wrapper.requests.post", return_value=response) as post:
            result = LLMWrapper._call_groq_free("prompt")

        self.assertEqual(result, "script")
        self.assertEqual(post.call_args.kwargs["json"]["max_completion_tokens"], 4096)
        self.assertNotIn("max_tokens", post.call_args.kwargs["json"])


if __name__ == "__main__":
    unittest.main()
