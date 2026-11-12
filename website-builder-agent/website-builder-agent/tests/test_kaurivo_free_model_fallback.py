"""Kaurivo no-cost model fallback tests: never bill, never reuse QA builder pool.

Pure mocks: no provider, customer or network request is performed.
"""
import os
import unittest
from unittest.mock import Mock, patch

import config
from utils import claude_client, resource_manager


class KaurivoFreeModelFallbackTests(unittest.TestCase):
    def test_single_request_falls_back_between_exact_free_models(self):
        reply=Mock(status_code=200)
        reply.json.return_value={"model":"google/backup:free","choices":[{
            "message":{"content":"Verified text"},"finish_reason":"stop"}]}
        env={"FREE_ONLY":"1","AI_BACKEND":"openrouter",
             "RESEARCH_MODEL":"google/primary:free",
             "RESEARCH_FALLBACK_MODELS":"google/backup:free",
             "BUILDER_MODEL":"google/code:free","QA_MODEL":"qwen/review:free"}
        with patch.dict(os.environ,env,clear=True), \
             patch.object(claude_client,"_get_headers",return_value={"Authorization":"mock"}), \
             patch.object(resource_manager,"reserve",return_value=True) as ledger, \
             patch.object(claude_client.requests,"post",return_value=reply) as request:
            text=claude_client.ask_claude("system","text",stage="research")
        self.assertEqual(text,"Verified text")
        self.assertEqual(request.call_count,1)
        ledger.assert_called_once_with("openrouter")
        sent=request.call_args.kwargs["json"]
        self.assertEqual(sent["models"],["google/primary:free","google/backup:free"])
        self.assertNotIn("paid",str(sent))

    def test_free_only_rejects_paid_or_untrusted_backup_before_request(self):
        for candidate in ("openai/paid","openrouter/free",
                          "google/gemma-4-31b-it:free,openai/paid",
                          "https://provider.invalid:free","provider/fake:free;evil"):
            with self.subTest(candidate=candidate),patch.dict(os.environ,{
                    "FREE_ONLY":"1","AI_BACKEND":"openrouter",
                    "RESEARCH_MODEL":"google/primary:free",
                    "RESEARCH_FALLBACK_MODELS":candidate},clear=True), \
                 patch.object(claude_client.requests,"post") as request:
                with self.assertRaises(RuntimeError):
                    claude_client.ask_claude("system","text",stage="research")
                request.assert_not_called()

    def test_qa_and_builder_pools_never_overlap(self):
        env={"FREE_ONLY":"1","AI_BACKEND":"openrouter",
             "BUILDER_MODEL":"google/builder:free",
             "BUILDER_FALLBACK_MODELS":"google/backup:free",
             "QA_MODEL":"qwen/reviewer:free",
             "QA_FALLBACK_MODELS":"google/backup:free"}
        with patch.dict(os.environ,env,clear=True):
            with self.assertRaisesRegex(RuntimeError,"Independent QA"):
                config.stage_model_candidates("builder")
            with self.assertRaisesRegex(RuntimeError,"Independent QA"):
                config.stage_model_candidates("qa")

    def test_unknown_or_paid_provider_response_is_never_accepted(self):
        reply=Mock(status_code=200)
        reply.json.return_value={"model":"company/paid","choices":[{
            "message":{"content":"Claim to pass"},"finish_reason":"stop"}]}
        env={"FREE_ONLY":"1","AI_BACKEND":"openrouter",
             "RESEARCH_MODEL":"google/primary:free",
             "RESEARCH_FALLBACK_MODELS":"google/backup:free"}
        with patch.dict(os.environ,env,clear=True), \
             patch.object(claude_client,"_get_headers",return_value={"Authorization":"mock"}), \
             patch.object(resource_manager,"reserve",return_value=True), \
             patch.object(claude_client.requests,"post",return_value=reply):
            with self.assertRaisesRegex(RuntimeError,"unapproved model"):
                claude_client.ask_claude("sys","text",stage="research")

    def test_already_capped_truncated_output_does_not_burn_identical_request(self):
        reply=Mock(status_code=200)
        reply.json.return_value={"choices":[{
            "message":{"content":"unfinished"},"finish_reason":"length"}]}
        env={"FREE_ONLY":"1","AI_BACKEND":"openrouter",
             "BUILDER_MODEL":"google/primary:free","QA_MODEL":"qwen/qa:free"}
        with patch.dict(os.environ,env,clear=True), \
             patch.object(claude_client,"_get_headers",return_value={"Authorization":"mock"}), \
             patch.object(resource_manager,"reserve",return_value=True), \
             patch.object(claude_client.requests,"post",return_value=reply) as call, \
             patch.object(config,"AI_MAX_OUTPUT_TOKENS",8000):
            with self.assertRaisesRegex(RuntimeError,"truncated"):
                claude_client.ask_claude("system","text",stage="builder",max_tokens=8000)
            call.assert_called_once()

    def test_unverified_429_does_not_fan_out_more_cloud_requests(self):
        reply=Mock(status_code=429,headers={},text="provider limit")
        env={"FREE_ONLY":"1","AI_BACKEND":"openrouter",
             "RESEARCH_MODEL":"google/primary:free",
             "RESEARCH_FALLBACK_MODELS":"google/backup:free",
             "OLLAMA_MODEL":"","OLLAMA_RESEARCH_MODEL":""}
        with patch.dict(os.environ,env,clear=True), \
             patch.object(claude_client,"_get_headers",return_value={"Authorization":"mock"}), \
             patch.object(resource_manager,"reserve",return_value=True), \
             patch.object(claude_client.requests,"post",return_value=reply) as request:
            with self.assertRaisesRegex(RuntimeError,"FREE_AI_RATE_LIMIT"):
                claude_client.ask_claude("system","text",stage="research")
            request.assert_called_once()


if __name__=="__main__":
    unittest.main()
