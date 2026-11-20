"""Google Gemini API free tier as an extra no-charge model provider.

Why: OpenRouter's free tier allows 50 requests/day, and one Kaurivo demo
needs roughly 20-40, so active development stalled after one or two runs
(20.11.2026). The Gemini API free tier has a separate daily quota per model.

Safety rules (FREE_ONLY):
* enabled only with KAURIVO_GEMINI_API_KEY and KAURIVO_GEMINI_FREE_CONFIRMED=1;
  the key must belong to a Google AI Studio project WITHOUT billing, so the
  provider itself cannot charge (Google requires billing setup to leave the
  free tier);
* a fixed allowlist of free models, rotated on a per-model daily 429;
* bounded per-run calls; no prompt, answer or key is ever logged.

Free-tier prompts may be used by Google to improve its products, so callers
send only public website content and public company facts, which is what
the demo pipeline already sends to the other free providers.
"""
from __future__ import annotations

import os
import re
from threading import Lock

import requests

_URL = "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
# Classic AI Studio keys are "AIza" + 35 chars; newer Google keys can be
# longer and contain dots. Accept any printable token without whitespace.
_KEY = re.compile(r"[A-Za-z0-9_.\-]{20,300}")
DEFAULT_MODELS = ("gemini-2.5-flash", "gemini-2.5-flash-lite")
_MAX_CALLS_PER_RUN = 60
_LOCK = Lock()
_ATTEMPTS = 0
_EXHAUSTED: set[str] = set()


def enabled() -> bool:
    return (
        os.getenv("FREE_ONLY", "1").strip().lower() in ("1", "true", "yes")
        and os.getenv("KAURIVO_GEMINI_FREE_CONFIRMED", "") == "1"
        and bool(_KEY.fullmatch(os.getenv("KAURIVO_GEMINI_API_KEY", "").strip()))
    )


def models() -> list[str]:
    raw = os.getenv("KAURIVO_GEMINI_FREE_MODELS", "")
    picked = [m.strip() for m in raw.split(",") if m.strip()] if raw else list(DEFAULT_MODELS)
    allowed = re.compile(r"(gemini-[0-9.]+-flash(?:-lite)?|gemma-[0-9a-z.\-]+)")
    return [m for m in picked if allowed.fullmatch(m)][:4]


def _reserve() -> bool:
    global _ATTEMPTS
    with _LOCK:
        if _ATTEMPTS >= _MAX_CALLS_PER_RUN:
            return False
        _ATTEMPTS += 1
        return True


def chat_gemini_free(system: str, user_prompt: str, *, stage: str | None,
                     max_tokens: int, image_paths: list[str] | None = None,
                     json_mode: bool = False, post=requests.post) -> str:
    """One complete answer from the first free Gemini model with quota left."""
    if not enabled():
        raise RuntimeError("FREE_AI_ACCESS_REJECTED: Gemini free tier not confirmed.")
    if image_paths:
        # Vision packets stay on the already verified providers.
        raise RuntimeError("FREE_MODEL_UNAVAILABLE: Gemini fallback is text-only.")
    if not isinstance(max_tokens, int) or not 1 <= max_tokens <= 16000:
        raise ValueError("Gemini output token budget out of range.")
    key = os.getenv("KAURIVO_GEMINI_API_KEY", "").strip()
    last = "FREE_AI_CAPACITY_UNAVAILABLE: Gemini free models exhausted."
    for model in models():
        if model in _EXHAUSTED:
            continue
        if not _reserve():
            raise RuntimeError("FREE_AI_RATE_LIMIT: Gemini per-run safety cap reached.")
        payload = {"model": model, "max_tokens": max_tokens,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user_prompt}]}
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        from utils.ai_usage import record
        record("gemini", stage)
        try:
            resp = post(_URL, headers={"Authorization": "Bearer " + key,
                                       "Content-Type": "application/json"},
                        json=payload, timeout=300, allow_redirects=False)
        except requests.RequestException:
            last = "FREE_AI_CAPACITY_UNAVAILABLE: Gemini transport failed."
            continue
        if resp.status_code == 429:
            _EXHAUSTED.add(model)  # per-model daily or minute quota; try the next one
            last = "FREE_AI_RATE_LIMIT: Gemini free quota reached."
            continue
        if resp.status_code in (401, 403):
            raise RuntimeError("FREE_AI_ACCESS_REJECTED: Gemini key rejected.")
        if resp.status_code in (404, 400):
            _EXHAUSTED.add(model)
            last = "FREE_MODEL_UNAVAILABLE: Gemini model rejected the request."
            continue
        if resp.status_code != 200:
            last = "FREE_AI_CAPACITY_UNAVAILABLE: Gemini HTTP " + str(resp.status_code) + "."
            continue
        try:
            first = resp.json()["choices"][0]
            text = first["message"]["content"]
        except (ValueError, KeyError, IndexError, TypeError):
            last = "FREE_MODEL_REQUEST_REJECTED: Gemini response invalid."
            continue
        if first.get("finish_reason") not in (None, "stop") or not isinstance(text, str) or not text.strip():
            last = "FREE_MODEL_REQUEST_REJECTED: Gemini response incomplete."
            continue
        return text
    raise RuntimeError(last)
