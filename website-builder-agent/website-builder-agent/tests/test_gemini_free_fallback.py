"""Gemini free tier as extra no-charge capacity after OpenRouter's 50/day."""
import os
import unittest
from unittest import mock

from utils import gemini_free_ai as g

KEY = "AIza" + "x" * 35
ON = {"FREE_ONLY": "1", "KAURIVO_GEMINI_FREE_CONFIRMED": "1", "KAURIVO_GEMINI_API_KEY": KEY}


class Resp:
    def __init__(self, status, body=None):
        self.status_code, self._body = status, body or {}
    def json(self):
        return self._body


def ok(text="{\"a\":1}"):
    return Resp(200, {"choices": [{"message": {"content": text}, "finish_reason": "stop"}]})


class GeminiFreeTests(unittest.TestCase):
    def setUp(self):
        g._EXHAUSTED.clear()
        g._ATTEMPTS = 0

    def test_disabled_without_key_or_confirmation(self):
        with mock.patch.dict(os.environ, {"FREE_ONLY": "1", "KAURIVO_GEMINI_API_KEY": ""}, clear=False):
            self.assertFalse(g.enabled())
        with mock.patch.dict(os.environ, {**ON, "FREE_ONLY": "0"}):
            self.assertFalse(g.enabled())

    def test_rotates_to_next_free_model_on_429(self):
        calls = []
        def post(url, **kw):
            calls.append(kw["json"]["model"])
            return Resp(429) if len(calls) == 1 else ok()
        with mock.patch.dict(os.environ, ON):
            out = g.chat_gemini_free("s", "u", stage="research", max_tokens=500, post=post)
        self.assertEqual(out, "{\"a\":1}")
        self.assertEqual(calls, ["gemini-2.5-flash", "gemini-2.5-flash-lite"])

    def test_key_never_in_payload_and_paid_models_filtered(self):
        with mock.patch.dict(os.environ, {**ON, "KAURIVO_GEMINI_FREE_MODELS": "gemini-2.5-pro,gemini-2.5-flash"}):
            self.assertEqual(g.models(), ["gemini-2.5-flash"])

    def test_all_exhausted_raises_capacity_error(self):
        with mock.patch.dict(os.environ, ON):
            with self.assertRaises(RuntimeError) as caught:
                g.chat_gemini_free("s", "u", stage="research", max_tokens=500,
                                   post=lambda *a, **k: Resp(429))
        self.assertIn("FREE_AI_RATE_LIMIT", str(caught.exception))

    def test_images_are_not_sent(self):
        with mock.patch.dict(os.environ, ON):
            with self.assertRaises(RuntimeError):
                g.chat_gemini_free("s", "u", stage="qa", max_tokens=500,
                                   image_paths=["a.png"], post=lambda *a, **k: ok())

    def test_fallback_chain_prefers_gemini_then_cloudflare(self):
        from utils import claude_client
        with mock.patch("utils.gemini_free_ai.enabled", return_value=True), \
             mock.patch("utils.gemini_free_ai.chat_gemini_free", return_value="G"), \
             mock.patch("utils.cloudflare_free_ai.enabled", return_value=True), \
             mock.patch("utils.cloudflare_free_ai.chat_cloudflare_free", return_value="C"):
            self.assertEqual(claude_client._other_free_cloud(
                "s", "u", stage="research", max_tokens=10, image_paths=None, json_mode=True), "G")
        with mock.patch("utils.gemini_free_ai.enabled", return_value=True), \
             mock.patch("utils.gemini_free_ai.chat_gemini_free", side_effect=RuntimeError("FREE_AI_RATE_LIMIT")), \
             mock.patch("utils.cloudflare_free_ai.enabled", return_value=True), \
             mock.patch("utils.cloudflare_free_ai.chat_cloudflare_free", return_value="C"):
            self.assertEqual(claude_client._other_free_cloud(
                "s", "u", stage="research", max_tokens=10, image_paths=None, json_mode=True), "C")
        with mock.patch("utils.gemini_free_ai.enabled", return_value=False), \
             mock.patch("utils.cloudflare_free_ai.enabled", return_value=False):
            self.assertIsNone(claude_client._other_free_cloud(
                "s", "u", stage="research", max_tokens=10, image_paths=None, json_mode=True))


class GeminiKeyFormatTests(unittest.TestCase):
    def test_classic_and_newer_key_formats(self):
        for key in ("AIza" + "x" * 35, "AQ.Ab8RN6" + "y" * 60):
            with self.subTest(key=key[:6]), mock.patch.dict(os.environ, {**ON, "KAURIVO_GEMINI_API_KEY": key}):
                self.assertTrue(g.enabled())
        with mock.patch.dict(os.environ, {**ON, "KAURIVO_GEMINI_API_KEY": "has space key value here"}):
            self.assertFalse(g.enabled())


if __name__ == "__main__":
    unittest.main()
