"""Bounded Workers Free retry and truthful production workflow regression.

Only synthetic HTTP replies and temporary files; never call an AI provider,
modify an actual customer job, or bypass research/source/visual QA gates.
"""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from utils import cloudflare_free_ai as cf
from scripts import run_kaurivo_demo_queue as worker

CONFIRMED = {
    "FREE_ONLY": "1",
    "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED": "1",
    "CLOUDFLARE_ACCOUNT_ID": "a" * 32,
    "CLOUDFLARE_API_TOKEN": "K" * 40,
}
ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = (
    ROOT.parents[1] / ".github/workflows/kaurivo-demo-worker.yml"
).read_text(encoding="utf-8")
RUNNER = (ROOT / "scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")


def success():
    response = Mock(status_code=200)
    response.json.return_value = {
        "model": cf.FREE_MODELS["research"],
        "choices": [{"finish_reason": "stop", "message": {"content": "verified"}}],
    }
    return response


class BoundedFreeRetry(unittest.TestCase):
    def test_cloudflare_honors_only_one_short_proven_429(self):
        rate = Mock(status_code=429, headers={"Retry-After": "2"})
        with patch.dict(os.environ, CONFIRMED, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch.object(cf.requests, "post", side_effect=[rate, success()]) as post, \
             patch.object(cf.time, "sleep") as sleep:
            self.assertEqual(
                cf.chat_cloudflare_free("rules", "source", stage="research", max_tokens=400),
                "verified",
            )
            self.assertEqual(post.call_count, 2)
            sleep.assert_called_once_with(2.0)

    def test_no_blind_or_unbounded_429_retries(self):
        for header in ({}, {"Retry-After": "180"}, {"Retry-After": "nonsense"}):
            with self.subTest(header=header), \
                 patch.dict(os.environ, CONFIRMED, clear=True), \
                 patch.object(cf, "_ATTEMPTS", 0), \
                 patch.object(cf.requests, "post",
                              return_value=Mock(status_code=429, headers=header)) as post, \
                 patch.object(cf.time, "sleep") as sleep:
                with self.assertRaisesRegex(RuntimeError, "FREE_AI_RATE_LIMIT"):
                    cf.chat_cloudflare_free(
                        "rules", "source", stage="research", max_tokens=400
                    )
                post.assert_called_once()
                sleep.assert_not_called()

    def test_two_evidenced_429s_still_stop_after_second(self):
        response = Mock(status_code=429, headers={"Retry-After": "1"})
        with patch.dict(os.environ, CONFIRMED, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch.object(cf.requests, "post", return_value=response) as post, \
             patch.object(cf.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "FREE_AI_RATE_LIMIT"):
                cf.chat_cloudflare_free(
                    "rules", "source", stage="research", max_tokens=400
                )
            self.assertEqual(post.call_count, 2)
            sleep.assert_called_once_with(1.0)


class HonestGithubStatus(unittest.TestCase):
    def test_only_confirmed_terminal_update_writes_marker(self):
        with TemporaryDirectory() as temp, \
             patch.dict(os.environ, {"RUNNER_TEMP": temp}), \
             patch.object(worker, "LOCAL_WORKER", False), \
             patch.object(worker, "working_job", {"id": "synthetic-job"}), \
             patch.object(worker, "call_worker", return_value={"ok": True}) as call:
            marker = Path(temp, "kaurivo-worker-state-persisted")
            worker.update("researching", "synthetic")
            self.assertFalse(marker.exists())
            worker.update("queued", "deferred", error_code="free_ai_rate_limit")
            self.assertTrue(marker.exists())
            call.assert_called_with(
                "update", job_id="synthetic-job", status="queued",
                progress="deferred", error_code="free_ai_rate_limit",
            )

    def test_rejected_update_never_writes_terminal_marker(self):
        with TemporaryDirectory() as temp, \
             patch.dict(os.environ, {"RUNNER_TEMP": temp}), \
             patch.object(worker, "LOCAL_WORKER", False), \
             patch.object(worker, "working_job", {"id": "synthetic-job"}), \
             patch.object(worker, "call_worker", side_effect=RuntimeError("state rejected")):
            with self.assertRaisesRegex(RuntimeError, "state rejected"):
                worker.update("hold", "not ready")
            self.assertFalse(Path(temp, "kaurivo-worker-state-persisted").exists())

    def test_workflow_preserves_existing_private_failure_and_is_not_green(self):
        self.assertIn("return 0 if LOCAL_WORKER else 2", RUNNER)
        self.assertIn("kaurivo-worker-state-persisted", WORKFLOW)
        self.assertIn("if: failure() && steps.claim.outputs.has_job == 'true'", WORKFLOW)
        self.assertIn("run: python -m scripts.run_kaurivo_demo_queue", WORKFLOW)
        self.assertIn("verify_public(url,marker,routes)", RUNNER)
        self.assertIn("qa.get(\"overall_pass\") is True", RUNNER)


if __name__ == "__main__":
    unittest.main()
