"""Per-demo free AI request counting works across worker subprocesses."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from utils import ai_usage

ROOT = Path(__file__).resolve().parents[1]


class AiUsageCounterTests(unittest.TestCase):
    def test_counts_from_parent_and_child_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "usage.tsv")
            with mock.patch.dict(os.environ, {"KAURIVO_AI_USAGE_FILE": path}):
                ai_usage.record("openrouter", "research")
                subprocess.run(
                    [sys.executable, "-c",
                     "from utils.ai_usage import record; record('openrouter','builder'); record('cloudflare','qa')"],
                    cwd=ROOT, check=True, env=os.environ.copy())
                data = ai_usage.summary(path)
        self.assertEqual(data["total"], 3)
        self.assertEqual(data["by_backend"], {"openrouter": 2, "cloudflare": 1})
        self.assertEqual(data["by_stage"]["openrouter:builder"], 1)

    def test_disabled_without_env_and_sanitizes_labels(self):
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop("KAURIVO_AI_USAGE_FILE", None)
            ai_usage.record("openrouter", "research")  # no file, no error
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "usage.tsv")
            with mock.patch.dict(os.environ, {"KAURIVO_AI_USAGE_FILE": path}):
                ai_usage.record("open\trouter", "re\nsearch secret@x.fi")
            text = Path(path).read_text(encoding="utf-8")
        self.assertEqual(text.count("\n"), 1)
        self.assertNotIn("@", text)

    def test_openrouter_request_is_counted(self):
        from utils import claude_client
        source = Path(claude_client.__file__).read_text(encoding="utf-8")
        record_at = source.index('_record_ai_usage("openrouter", stage)')
        post_at = source.index("requests.post(\n                OPENROUTER_URL")
        self.assertLess(record_at, post_at)


if __name__ == "__main__":
    unittest.main()
