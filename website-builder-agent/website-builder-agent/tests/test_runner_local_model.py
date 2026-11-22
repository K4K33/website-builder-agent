import os
from pathlib import Path
import unittest
from unittest.mock import patch

from utils import runner_local_model as local


class RunnerLocalModelTests(unittest.TestCase):
    def test_off_without_opt_in_or_outside_actions(self):
        with patch.dict(os.environ, {"KAURIVO_LOCAL_SALES_MODEL": "", "GITHUB_ACTIONS": "true"}):
            self.assertFalse(local.enabled())
        with patch.dict(os.environ, {"KAURIVO_LOCAL_SALES_MODEL": "gemma3:12b", "GITHUB_ACTIONS": ""}):
            self.assertFalse(local.enabled())
        with patch.dict(os.environ, {"KAURIVO_LOCAL_SALES_MODEL": "gemma3:12b-cloud:cloud",
                                     "GITHUB_ACTIONS": "true"}):
            self.assertFalse(local.enabled())
        with patch.dict(os.environ, {"KAURIVO_LOCAL_SALES_MODEL": "gemma3:12b", "GITHUB_ACTIONS": "true"}):
            self.assertTrue(local.enabled())

    def test_quota_errors_use_local_model_others_raise(self):
        def cloud(system, prompt, *, max_tokens, stage):
            raise RuntimeError("FREE_AI_RATE_LIMIT: HTTP 429")
        used = []
        with patch.object(local, "ensure", return_value="gemma3:12b"), \
                patch.object(local, "ask_json", return_value={"headline": "x"}) as ask:
            answer = local.with_local_fallback(cloud, on_local=used.append)("s", "p", max_tokens=4000,
                                                                          stage="research")
        self.assertEqual(answer, {"headline": "x"})
        self.assertEqual(used, ["gemma3:12b"])
        self.assertEqual(ask.call_args.kwargs["model"], "gemma3:12b")

        def broken(system, prompt, *, max_tokens, stage):
            raise RuntimeError("sales_plan_invalid")
        with patch.object(local, "ensure") as ensure, self.assertRaises(RuntimeError):
            local.with_local_fallback(broken)("s", "p", max_tokens=10, stage="research")
        ensure.assert_not_called()

    def test_no_local_model_keeps_original_quota_error(self):
        def cloud(system, prompt, *, max_tokens, stage):
            raise RuntimeError("quota exhausted")
        with patch.object(local, "ensure", return_value=""), self.assertRaises(RuntimeError) as err:
            local.with_local_fallback(cloud)("s", "p", max_tokens=10, stage="research")
        self.assertIn("quota", str(err.exception))

    def test_parse_json_tolerates_fences_and_prose(self):
        self.assertEqual(local.parse_json('```json\n{"a": 1}\n```'), {"a": 1})
        self.assertEqual(local.parse_json('Tässä: {"a": [1, 2]} valmis'), {"a": [1, 2]})
        with self.assertRaises(RuntimeError):
            local.parse_json("ei jsonia")

    def test_worker_wires_local_fallback_and_full_build_sales_fallback(self):
        code = (Path(__file__).resolve().parents[1] / "scripts" / "run_kaurivo_demo_queue.py").read_text()
        self.assertIn("with_local_fallback(ask_claude_json", code)
        self.assertIn('KAURIVO_SALES_FALLBACK', code)
        self.assertIn("building the sales demo instead", code)


if __name__ == "__main__":
    unittest.main()
