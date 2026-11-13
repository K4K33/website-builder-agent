"""A fresh owner-selected demo can use all approved free pipeline stages.

Offline synthetic tests: do not spend any AI or provider credits.
"""
from __future__ import annotations

import os
from unittest import TestCase
from unittest.mock import Mock, patch

from scripts import run_kaurivo_demo_queue as worker
from utils import cloudflare_free_ai as cf

FREE_ENV = {
    "FREE_ONLY": "1",
    "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED": "1",
    "CLOUDFLARE_ACCOUNT_ID": "a" * 32,
    "CLOUDFLARE_API_TOKEN": "T" * 40,
}


class FreshDemoBudgetTests(TestCase):
    def test_cloud_runner_reserves_time_for_release(self):
        self.assertEqual(worker.TIMEOUT_PER_STAGE, 480)
        self.assertEqual(worker.RESEARCH_TIMEOUT, 720)
        self.assertEqual(worker.AI_STAGE_BUDGET_SECONDS, 2400)
        self.assertLess(worker.AI_STAGE_BUDGET_SECONDS, 55 * 60 - 300)

    def test_twenty_free_calls_then_fail_closed(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "model": cf.FREE_MODELS["research"],
            "choices": [
                {"finish_reason": "stop", "message": {"content": "validated synthetic result"}}
            ],
        }
        with patch.dict(os.environ, FREE_ENV, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch.object(cf.requests, "post", return_value=response) as request:
            self.assertTrue(cf.enabled())
            for _ in range(20):
                self.assertEqual(
                    cf.chat_cloudflare_free("rules", "example", stage="research", max_tokens=200),
                    "validated synthetic result",
                )
            with self.assertRaisesRegex(RuntimeError, "FREE_AI_RATE_LIMIT"):
                cf.chat_cloudflare_free("rules", "example", stage="research", max_tokens=200)
            self.assertEqual(request.call_count, 20)

    def test_never_call_cloud_without_free_confirmation(self):
        with patch.dict(os.environ, {**FREE_ENV,
                                     "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED": "0"},
                        clear=True), \
             patch.object(cf.requests, "post") as request:
            with self.assertRaisesRegex(RuntimeError, "FREE_AI_ACCESS_REJECTED"):
                cf.chat_cloudflare_free("rules", "example", stage="research", max_tokens=200)
            request.assert_not_called()

    def test_real_qa_is_still_required_before_release(self):
        from pathlib import Path
        source = (Path(__file__).resolve().parents[1] /
                  "scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
        self.assertIn('qa.get("overall_pass") is True', source)
        self.assertIn('get("build_version")', source)
        self.assertIn('verify_public(url,marker,routes)', source)
        self.assertIn('save_private_checkpoint("researched",agent_slug)', source)
        self.assertIn('save_private_checkpoint("built",agent_slug)', source)


if __name__ == "__main__":
    import unittest
    unittest.main()
