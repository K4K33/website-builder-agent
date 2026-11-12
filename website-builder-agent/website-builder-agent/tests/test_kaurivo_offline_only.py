"""Offline-only Kaurivo Windows regression tests (no model calls or network)."""
import os
from pathlib import Path
import unittest
from unittest.mock import MagicMock, patch

from scripts.kaurivo_local_worker import LocalWorkerError, models
from scripts.check_local_models import check_models

ROOT = Path(__file__).resolve().parents[1]
START = (ROOT / "scripts/start_kaurivo_worker.ps1").read_text(encoding="utf-8")
SWITCH = (ROOT / "scripts/switch_kaurivo_to_offline.ps1").read_text(encoding="utf-8")
SETUP = (ROOT / "scripts/setup_kaurivo_windows.ps1").read_text(encoding="utf-8")
DAEMON = (ROOT / "scripts/kaurivo_local_worker.py").read_text(encoding="utf-8")
RUNNER = (ROOT / "scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")


class OfflineOnlyWorkerTests(unittest.TestCase):
    def test_codex_mode_cannot_infer_even_when_legacy_config_remains(self):
        with patch.dict(os.environ, {"KAURIVO_WINDOWS_BACKEND": "codex"}), \
             patch("utils.codex_ai.discover_models") as codex:
            with self.assertRaisesRegex(LocalWorkerError, "Codex is not allowed"):
                models()
            codex.assert_not_called()

    def test_valid_offline_configuration_has_independent_visual_qa(self):
        env = {"KAURIVO_WINDOWS_BACKEND": "ollama",
               "OLLAMA_RESEARCH_MODEL": "qwen2.5-coder:7b",
               "OLLAMA_BUILDER_MODEL": "qwen2.5-coder:7b",
               "OLLAMA_QA_MODEL": "llava:7b"}
        with patch.dict(os.environ, env):
            selected = models()
        self.assertEqual(selected["builder"], "qwen2.5-coder:7b")
        self.assertNotEqual(selected["builder"], selected["qa"])
        with patch.dict(os.environ, {**env, "OLLAMA_QA_MODEL": "llava:7b:cloud"}):
            with self.assertRaises(LocalWorkerError):
                models()

    def test_switch_does_not_replace_key_or_download_without_consent(self):
        self.assertIn('Read-Host "Ladataanko ilmaiset', SWITCH)
        self.assertIn('if ($allow -notin', SWITCH)
        self.assertIn('Set-Content -Encoding ascii -Path $backend -Value "ollama"', SWITCH)
        self.assertIn('if ($LASTEXITCODE -ne 0)', SWITCH)
        self.assertNotIn("codex login", SWITCH)
        self.assertNotIn("worker.token.dpapi\" -Value", SWITCH)
        self.assertIn('ConvertTo-SecureString', START)
        self.assertIn('KAURIVO_WINDOWS_BACKEND = "ollama"', START)
        self.assertIn('throw "Codex on poistettu', START)
        self.assertIn('throw "Codex ei ole enää tuettu', SETUP)
        self.assertIn('$backend = "ollama"', SETUP)
        self.assertIn('backend="ollama"', DAEMON)

    @staticmethod
    def session(tags, vision=True):
        fake = MagicMock()
        fake.__enter__.return_value = fake
        fake.get.return_value.json.return_value = {
            "models": [{"name": model} for model in tags]
        }
        fake.post.return_value.json.return_value = {
            "capabilities": ["completion", "vision"] if vision else ["completion"]
        }
        return fake

    def test_preflight_checks_both_models_without_external_requests(self):
        available = self.session(["qwen2.5-coder:7b", "llava:7b"])
        names = {"research": "qwen2.5-coder:7b",
                 "builder": "qwen2.5-coder:7b", "qa": "llava:7b"}
        with patch("scripts.check_local_models.models", return_value=names), \
             patch("scripts.check_local_models.requests.Session", return_value=available):
            ok, status = check_models()
        self.assertTrue(ok, status)
        self.assertIn("Codexia ei käytetä", status)
        self.assertEqual(available.get.call_args.args[0],
                         "http://127.0.0.1:11434/api/tags")
        self.assertEqual(available.post.call_args.args[0],
                         "http://127.0.0.1:11434/api/show")

    def test_preflight_refuses_missing_model_and_nonvisual_qa(self):
        names = {"research": "qwen2.5-coder:7b",
                 "builder": "qwen2.5-coder:7b", "qa": "llava:7b"}
        for tags, vision, expected in (
            (["qwen2.5-coder:7b"], True, "puuttuvat"),
            (["qwen2.5-coder:7b", "llava:7b"], False, "ei tue kuvia"),
        ):
            with self.subTest(tags=tags, vision=vision), \
                 patch("scripts.check_local_models.models", return_value=names), \
                 patch("scripts.check_local_models.requests.Session",
                       return_value=self.session(tags, vision)):
                ok, reason = check_models()
            self.assertFalse(ok)
            self.assertIn(expected, reason)

    def test_original_quality_and_publication_gates_remain(self):
        for guard in ("restore_private_checkpoint(", "save_private_checkpoint(",
                      "quality_gate_not_approved", "verify_public(url,marker,routes)",
                      "quality_gate_build_version_mismatch",
                      'update("internal_preview"'):
            self.assertIn(guard, RUNNER)


    def test_local_inference_keeps_source_context_and_loopback_only(self):
        from utils.local_ai import chat_local
        response = MagicMock()
        response.json.return_value = {
            "done_reason": "stop",
            "message": {"content": "validoitu vastaus"}
        }
        with patch.dict(os.environ, {"OLLAMA_NUM_CTX": "8192"}), \
             patch("utils.local_ai.requests.post", return_value=response) as post:
            self.assertEqual(chat_local("system", "prompt",
                model="qwen2.5-coder:7b", max_tokens=1024),
                "validoitu vastaus")
        self.assertEqual(post.call_args.args[0], "http://127.0.0.1:11434/api/chat")
        self.assertFalse(post.call_args.kwargs["allow_redirects"])
        self.assertEqual(post.call_args.kwargs["json"]["options"]["num_ctx"], 8192)


if __name__ == "__main__":
    unittest.main()
