"""Entirely offline tests for Kaurivo's opt-in local Ollama backend.

No Ollama installation, actual model run, external API call or paid credit.
"""
import base64
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import config
import main
from utils import claude_client, local_ai, resource_manager


class OllamaBackendTests(unittest.TestCase):
    def env(self, **updates):
        values = {
            "AI_BACKEND": "ollama", "FREE_ONLY": "1",
            "OLLAMA_MODEL": "locally-installed-text-model",
            "OLLAMA_BUILDER_MODEL": "local-coder",
            "OLLAMA_QA_MODEL": "local-vision",
            "OLLAMA_TIMEOUT_SECONDS": "60",
        }
        values.update(updates)
        return patch.dict(os.environ, values)

    def test_free_only_blocks_openrouter_even_if_key_exists(self):
        with self.env(AI_BACKEND="openrouter"):
            with self.assertRaisesRegex(RuntimeError, "FREE_ONLY"):
                config.ai_backend()
            with patch.object(claude_client, "_get_headers") as credentials:
                with self.assertRaisesRegex(RuntimeError, "FREE_ONLY"):
                    claude_client.ask_claude("system", "prompt")
                credentials.assert_not_called()

    def test_unknown_backend_rejected_and_cloud_model_disabled(self):
        with self.env(AI_BACKEND="remote"):
            with self.assertRaisesRegex(RuntimeError, "AI_BACKEND"):
                config.ai_backend()
        with self.env(OLLAMA_BUILDER_MODEL="remote-model:cloud"):
            with self.assertRaisesRegex(RuntimeError, "cloud"):
                config.model_for_stage("builder")
        with self.assertRaisesRegex(RuntimeError, "Cloud"):
            local_ai.chat_local("sys", "question", model="model:cloud", max_tokens=5)

    def test_explicit_local_builder_and_vision_models_required(self):
        with self.env(OLLAMA_BUILDER_MODEL=""):
            with self.assertRaisesRegex(RuntimeError, "OLLAMA_BUILDER_MODEL"):
                config.model_for_stage("builder")
        with self.env(OLLAMA_QA_MODEL=""):
            with self.assertRaisesRegex(RuntimeError, "OLLAMA_QA_MODEL"):
                config.model_for_stage("qa")
        with self.env():
            self.assertEqual(config.model_for_stage("builder"), "local-coder")
            self.assertEqual(config.model_for_stage("qa"), "local-vision")

    def test_local_chat_never_uses_openrouter_and_supports_json(self):
        reply = Mock(status_code=200)
        reply.raise_for_status.return_value = None
        reply.json.return_value = {"message": {"role": "assistant", "content": '{"ok":true}'},
                                   "done": True, "done_reason": "stop"}
        with self.env(), \
             patch.object(claude_client, "_get_headers") as headers, \
             patch.object(resource_manager, "reserve") as reserve, \
             patch("utils.local_ai.requests.post", return_value=reply) as local:
            result = claude_client.ask_claude_json("system", "prompt", stage="builder")
            self.assertEqual(result, {"ok": True})
            headers.assert_not_called()
            reserve.assert_not_called()
            local.assert_called_once()
            call = local.call_args
            self.assertEqual(call.args[0], local_ai.OLLAMA_CHAT_URL)
            self.assertFalse(call.kwargs["allow_redirects"])
            self.assertEqual(call.kwargs["json"]["model"], "local-coder")
            self.assertTrue(call.kwargs["json"]["format"] == "json")
            self.assertFalse(call.kwargs["json"]["stream"])

    def test_vision_image_encoded_as_base64_not_openrouter_data_url(self):
        with tempfile.TemporaryDirectory() as root:
            file = Path(root) / "shot.png"
            file.write_bytes(b"fake-png-fixture")
            reply = Mock()
            reply.raise_for_status.return_value = None
            reply.json.return_value = {"message": {"content": "Looks good"}, "done_reason": "stop"}
            with patch("utils.local_ai.requests.post", return_value=reply) as local:
                answer = local_ai.chat_local(
                    "vision", "check image", model="local-vision",
                    image_paths=[str(file)], max_tokens=100
                )
            self.assertEqual(answer, "Looks good")
            upload = local.call_args.kwargs["json"]["messages"][1]["images"][0]
            self.assertEqual(base64.b64decode(upload), b"fake-png-fixture")
            self.assertNotIn("data:", upload)
            file.write_bytes(b"")
            with self.assertRaisesRegex(ValueError, "8 MB"):
                local_ai.chat_local("vision", "check", model="local-vision",
                                    image_paths=[str(file)], max_tokens=100)

    def test_ollama_down_is_never_cloud_fallback(self):
        with self.env(), \
             patch.object(claude_client, "_get_headers") as cloud, \
             patch("utils.local_ai.requests.post", side_effect=local_ai.requests.ConnectionError):
            with self.assertRaisesRegex(RuntimeError, "No cloud fallback"):
                claude_client.ask_claude("system", "prompt", stage="builder")
            cloud.assert_not_called()

    def test_invalid_or_truncated_local_output_rejected(self):
        reply = Mock()
        reply.raise_for_status.return_value = None
        reply.json.return_value = {"message": {"content": "partial"}, "done_reason": "length"}
        with patch("utils.local_ai.requests.post", return_value=reply):
            with self.assertRaisesRegex(RuntimeError, "truncated"):
                local_ai.chat_local("sys", "prompt", model="local-coder", max_tokens=10)
        reply.json.return_value = {"message": {"content": ""}, "done_reason": "stop"}
        with patch("utils.local_ai.requests.post", return_value=reply):
            with self.assertRaisesRegex(RuntimeError, "empty"):
                local_ai.chat_local("sys", "prompt", model="local-coder", max_tokens=10)

    def test_local_mode_does_not_require_openrouter_api_key_for_preflight(self):
        with self.env(TAVILY_API_KEY="offline-fixture", OPENROUTER_API_KEY=""), \
             patch.object(config, "OPENROUTER_API_KEY", ""), \
             patch.object(config, "model_for_stage", wraps=config.model_for_stage), \
             patch.object(main.scout, "run_scout", return_value=[]) as scout:
            args = SimpleNamespace(confirm_live_run=True, count=1,
                                   industry="kampaamo", location="Tampere",
                                   benchmark_mode=True)
            with self.assertRaisesRegex(RuntimeError, "No prequalified lead"):
                main.cmd_pipeline(args)
            scout.assert_called_once()

    def test_direct_local_AI_commands_do_not_require_paid_provider_consent(self):
        with self.env():
            main._require_paid_consent(SimpleNamespace(confirm_paid_apis=False))
        with patch.dict(os.environ, {"AI_BACKEND": "openrouter", "FREE_ONLY": "0"}):
            with self.assertRaisesRegex(RuntimeError, "confirm-paid-apis"):
                main._require_paid_consent(SimpleNamespace(confirm_paid_apis=False))


if __name__ == "__main__":
    unittest.main()
