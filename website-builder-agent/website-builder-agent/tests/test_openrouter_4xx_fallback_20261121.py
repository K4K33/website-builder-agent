import os
import unittest
from unittest.mock import MagicMock, patch

import utils.claude_client as cc


class OpenRouter4xxFallbackTests(unittest.TestCase):
    def _reply(self, status):
        response = MagicMock(status_code=status, text="{}", headers={})
        response.json.return_value = {}
        return response

    def test_withdrawn_free_model_falls_back_to_other_free_provider(self):
        with patch.dict(os.environ, {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
                                     "OPENROUTER_API_KEY": "k" * 40, "QA_MODEL": "qwen/qwen3.8-27b:free", "QA_FALLBACK_MODELS": ""}), \
                patch.object(cc.config, "free_only", return_value=True), \
                patch.object(cc, "_get_headers", return_value={}), \
                patch.object(cc, "requests") as req, \
                patch.object(cc, "_other_free_cloud", return_value="ok from workers") as other:
            req.post.return_value = self._reply(404)
            req.RequestException = __import__("requests").RequestException
            result = cc.ask_claude("s", "u", stage="qa")
            self.assertEqual(result, "ok from workers")
            other.assert_called_once()

    def test_without_alternative_the_rejection_is_reported(self):
        with patch.dict(os.environ, {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
                                     "OPENROUTER_API_KEY": "k" * 40, "QA_MODEL": "qwen/qwen3.8-27b:free", "QA_FALLBACK_MODELS": ""}), \
                patch.object(cc.config, "free_only", return_value=True), \
                patch.object(cc, "_get_headers", return_value={}), \
                patch.object(cc, "requests") as req, \
                patch.object(cc, "_other_free_cloud", return_value=None):
            req.post.return_value = self._reply(404)
            req.RequestException = __import__("requests").RequestException
            with self.assertRaisesRegex(RuntimeError, "HTTP 404"):
                cc.ask_claude("s", "u", stage="qa")


if __name__ == "__main__":
    unittest.main()
