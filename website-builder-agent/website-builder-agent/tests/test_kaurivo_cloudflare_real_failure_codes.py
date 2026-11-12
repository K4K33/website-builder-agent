"""Goodcaf regression: never conflate real Workers Free HTTP 400 with quota 429.

No customer source, credentials, model or network access is used by these tests.
"""
from __future__ import annotations

import io
import os
import unittest
from unittest.mock import Mock, patch

from utils import cloudflare_free_ai as cf
from utils.claude_client import ask_claude
from scripts.run_kaurivo_demo_queue import classify_stage_failure

VALID={
    "FREE_ONLY":"1",
    "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED":"1",
    "CLOUDFLARE_ACCOUNT_ID":"a"*32,
    "CLOUDFLARE_API_TOKEN":"T"*40,
}
FREE_MODEL={"AI_BACKEND":"openrouter",
            "RESEARCH_MODEL":"google/gemma-4-26b-a4b-it:free",
            "RESEARCH_FALLBACK_MODELS":"",
            "KAURIVO_OPENROUTER_FREE_EXHAUSTED":""}


class CloudflareFailureCodes(unittest.TestCase):
    def test_different_rejections_do_not_become_overnight_quota(self):
        cases={
            400:"FREE_MODEL_REQUEST_REJECTED",
            413:"FREE_MODEL_REQUEST_REJECTED",
            401:"FREE_AI_ACCESS_REJECTED",
            403:"FREE_AI_ACCESS_REJECTED",
            402:"FREE_AI_ACCOUNT_BLOCKED",
            404:"FREE_MODEL_UNAVAILABLE",
            429:"FREE_AI_RATE_LIMIT",
            503:"FREE_AI_CAPACITY_UNAVAILABLE",
            500:"FREE_MODEL_REQUEST_REJECTED",
        }
        for status,expected in cases.items():
            with self.subTest(status=status):
                response=Mock(status_code=status)
                with patch.dict(os.environ,VALID,clear=True), \
                     patch.object(cf,"_ATTEMPTS",0), \
                     patch.object(cf.requests,"post",return_value=response) as post:
                    with self.assertRaisesRegex(RuntimeError,expected):
                        cf.chat_cloudflare_free("source rule","synthetic research",
                            stage="research",max_tokens=3500,json_mode=True)
                    post.assert_called_once()
                    self.assertFalse(post.call_args.kwargs["allow_redirects"])
                    self.assertEqual(post.call_args.kwargs["json"]["model"],
                                     cf.FREE_MODELS["research"])

    def test_one_bounded_retry_on_only_truncated_responses(self):
        truncated=Mock(status_code=200)
        truncated.json.return_value={
            "model":cf.FREE_MODELS["research"],
            "choices":[{"finish_reason":"length","message":{"content":"unfinished"}}],
        }
        success=Mock(status_code=200)
        success.json.return_value={
            "model":cf.FREE_MODELS["research"],
            "choices":[{"finish_reason":"stop","message":{"content":'{"facts":[]}'}}],
        }
        with patch.dict(os.environ,VALID,clear=True), \
             patch.object(cf,"_ATTEMPTS",0), \
             patch.object(cf.requests,"post",side_effect=[truncated,success]) as post:
            result=cf.chat_cloudflare_free("rules","synthetic",stage="research",
                                             max_tokens=3500,json_mode=True)
            self.assertEqual(result,'{"facts":[]}')
            self.assertEqual(post.call_count,2)
            self.assertEqual(post.call_args_list[0].kwargs["json"]["max_tokens"],3500)
            self.assertEqual(post.call_args_list[1].kwargs["json"]["max_tokens"],7000)

    def test_two_truncations_fail_closed_without_third_request(self):
        truncated=Mock(status_code=200)
        truncated.json.return_value={
            "model":cf.FREE_MODELS["research"],
            "choices":[{"finish_reason":"length","message":{"content":"partial"}}],
        }
        with patch.dict(os.environ,VALID,clear=True), \
             patch.object(cf,"_ATTEMPTS",0), \
             patch.object(cf.requests,"post",return_value=truncated) as post:
            with self.assertRaisesRegex(RuntimeError,"FREE_AI_RESPONSE_TRUNCATED"):
                cf.chat_cloudflare_free("rules","synthetic",stage="research",
                                         max_tokens=3500,json_mode=True)
            self.assertEqual(post.call_count,2)

    def test_safe_job_error_codes_are_classified_correctly(self):
        cases={
            "FREE_AI_RATE_LIMIT":"free_ai_rate_limit",
            "FREE_AI_CAPACITY_UNAVAILABLE":"free_ai_capacity_unavailable",
            "FREE_MODEL_REQUEST_REJECTED":"free_model_request_rejected",
            "FREE_AI_ACCESS_REJECTED":"free_ai_access_rejected",
            "FREE_AI_ACCOUNT_BLOCKED":"free_ai_account_blocked",
            "FREE_MODEL_UNAVAILABLE":"free_model_unavailable",
            "FREE_AI_RESPONSE_TRUNCATED":"free_ai_response_truncated",
            "NETWORK_UNAVAILABLE":"research_network_unavailable",
        }
        for code,expected in cases.items():
            with self.subTest(code=code):
                handle=io.StringIO("RuntimeError: "+code+": safe generic reason.\n")
                self.assertEqual(classify_stage_failure(handle,"researching"),expected)

    def test_real_openrouter_429_switches_remaining_stages_to_free_cloud(self):
        openrouter_429=Mock(status_code=429,headers={})
        with patch.dict(os.environ,{**VALID,**FREE_MODEL},clear=True), \
             patch("utils.claude_client.resource_manager.reserve",return_value=True), \
             patch("utils.claude_client._get_headers",return_value={"Authorization":"redacted"}), \
             patch("utils.claude_client._verified_free_minute_wait_seconds",return_value=None), \
             patch("utils.claude_client.requests.post",return_value=openrouter_429) as or_request, \
             patch("utils.cloudflare_free_ai.chat_cloudflare_free",
                   return_value="verified cloud answer") as backup:
            first=ask_claude("sys","source",stage="research",max_tokens=3500,
                              max_retries=1,json_mode=True)
            second=ask_claude("sys","different source",stage="research",
                               max_tokens=3500,max_retries=1,json_mode=True)
            self.assertEqual(first,"verified cloud answer")
            self.assertEqual(second,"verified cloud answer")
            self.assertEqual(os.environ.get("KAURIVO_PREFER_CLOUDFLARE"),"1")
            or_request.assert_called_once()
            self.assertEqual(backup.call_count,2)

if __name__=="__main__":
    unittest.main()
