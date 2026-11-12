"""Optional second FREE cloud provider for Kaurivo's strict AI pipeline.

The fallback is OFF until the owner has created a *Workers Free* account,
confirmed no paid billing, and stored a restricted token in GitHub Secrets.
Nothing is billed or called merely by importing this module.

Cloudflare official model documentation (2026-11):
  @cf/google/gemma-4-26b-a4b-it (text+vision, zero data retention)
  @cf/qwen/qwen3.8-27b (text+vision, zero data retention)

The primary Builder and separate independent QA remain subject to all the
original source fidelity, Master Prompt, screenshot and browser QA checks.
"""
from __future__ import annotations

import os
import re
from threading import Lock

import requests

FREE_MODELS = {
    "research": "@cf/google/gemma-4-26b-a4b-it",
    "builder": "@cf/google/gemma-4-26b-a4b-it",
    "qa": "@cf/qwen/qwen3.8-27b",
}
_CF_ACCOUNT = re.compile(r"^[a-f0-9]{32}$")
_CF_TOKEN = re.compile(r"^[A-Za-z0-9_-]{25,250}$")
_CF_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/v1/chat/completions"
_MAX_CALLS_PER_RUN = 6
_LOCK = Lock()
_ATTEMPTS = 0


def enabled() -> bool:
    """Only explicit no-charge opt-in may enable a second provider."""
    return (
        os.getenv("FREE_ONLY", "1").strip().lower() in ("1", "true", "yes")
        and os.getenv("KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED", "") == "1"
        and bool(_CF_ACCOUNT.fullmatch(os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()))
        and bool(_CF_TOKEN.fullmatch(os.getenv("CLOUDFLARE_API_TOKEN", "").strip()))
    )


def _reserve() -> bool:
    """Hard bounded per-run budget. Cloudflare FREE enforces actual account caps."""
    global _ATTEMPTS
    with _LOCK:
        if _ATTEMPTS >= _MAX_CALLS_PER_RUN:
            return False
        _ATTEMPTS += 1
        return True


def chat_cloudflare_free(
    system: str,
    user_prompt: str,
    *,
    stage: str | None,
    max_tokens: int,
    image_paths: list[str] | None = None,
    json_mode: bool = False,
) -> str:
    """Perform ONE allowlisted Workers Free request. Never attempt a paid model.

    Fail closed on incomplete output, exhausted free capacity, invalid model,
    unapproved accounts, or unknown responses. Never log prompts or keys.
    """
    if stage not in FREE_MODELS:
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare stage not approved.")
    if not enabled():
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare Free not confirmed.")
    if not _reserve():
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare run cap reached.")
    if not isinstance(max_tokens, int) or not 1 <= max_tokens <= 10000:
        raise ValueError("Cloudflare output token budget out of range.")
    from utils.claude_client import _build_user_content
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    model = FREE_MODELS[stage]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": _build_user_content(user_prompt, image_paths)},
        ],
        "max_tokens": max_tokens,
        "stream": False,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}
    try:
        resp = requests.post(
            _CF_URL.format(account=account),
            headers={"Authorization": "Bearer " + token,
                     "Content-Type": "application/json"},
            json=payload, timeout=170, allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare connection failure.") from exc
    if resp.status_code in (429, 503, 502, 504):
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare Free capacity exceeded.")
    if resp.status_code in (401, 403, 402):
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare Free credentials or billing not verified.")
    if resp.status_code != 200:
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare model request rejected.")
    try:
        data = resp.json()
        if not isinstance(data, dict) or (
            data.get("model") is not None and data["model"] != model
        ):
            raise ValueError("unapproved model")
        choices = data["choices"]
        first = choices[0]
        if first.get("finish_reason") not in ("stop",):
            raise ValueError("incomplete response")
        content = first["message"]["content"]
        if isinstance(content, list):
            content = "\n".join(str(part.get("text", "")) for part in content
                                if isinstance(part, dict) and part.get("type") == "text")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("empty response")
        return content.strip()
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare returned no verified full response.") from exc
