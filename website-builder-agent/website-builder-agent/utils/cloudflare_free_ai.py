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
import time
from collections.abc import Mapping
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
_MAX_CALLS_PER_RUN = 14
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


def _short_retry_after_seconds(response) -> float | None:
    """Retry a proved short provider throttle, not a daily/account quota.

    No blind retry on HTTP 429 and no unbounded or date-form Retry-After.
    The existing per-run free-call guard still applies to the second call.
    """
    headers = getattr(response, "headers", None)
    if not isinstance(headers, Mapping):
        return None
    raw = headers.get("Retry-After", headers.get("retry-after"))
    try:
        seconds = float(str(raw).strip())
    except (TypeError, ValueError):
        return None
    if 1 <= seconds <= 30:
        return seconds
    return None


def chat_cloudflare_free(
    system: str,
    user_prompt: str,
    *,
    stage: str | None,
    max_tokens: int,
    image_paths: list[str] | None = None,
    json_mode: bool = False,
    _allow_length_retry: bool = True,
    _allow_rate_retry: bool = True,
) -> str:
    """Perform a bounded allowlisted Workers Free request. Never use a paid model.

    Fail closed on incomplete output, exhausted free capacity, invalid model,
    unapproved accounts, or unknown responses. Never log prompts or keys.
    """
    if stage not in FREE_MODELS:
        raise RuntimeError("FREE_MODEL_REQUEST_REJECTED: Cloudflare stage not approved.")
    if not enabled():
        raise RuntimeError("FREE_AI_ACCESS_REJECTED: Cloudflare Workers Free not confirmed.")
    if not _reserve():
        raise RuntimeError("FREE_AI_RATE_LIMIT: Cloudflare per-run safety cap reached.")
    if not isinstance(max_tokens, int) or not 1 <= max_tokens <= 10000:
        raise ValueError("Cloudflare output token budget out of range.")
    from utils.kaurivo_cloud_vision_packet import compact_vision_user_content
    # Screenshots are resized for inference ONLY. The unchanged original
    # files still govern browser, visual, brand and source fidelity checks.
    content = (compact_vision_user_content(user_prompt, image_paths)
               if image_paths else user_prompt)
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    model = FREE_MODELS[stage]
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": content},
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
        raise RuntimeError("NETWORK_UNAVAILABLE: Cloudflare request transport failed.") from exc
    # Distinguish a provider quota from a malformed request; previously all
    # HTTP 4xx/5xx and truncated model responses were incorrectly deferred
    # to the next day as free_ai_capacity_unavailable. Never log HTTP bodies.
    if resp.status_code == 429:
        wait = _short_retry_after_seconds(resp) if _allow_rate_retry else None
        if wait is not None:
            # Exactly one evidenced short delay; _reserve() checks the free
            # safety limit again. Never infer more capacity from a bare 429.
            time.sleep(wait)
            return chat_cloudflare_free(
                system, user_prompt, stage=stage, max_tokens=max_tokens,
                image_paths=image_paths, json_mode=json_mode,
                _allow_length_retry=_allow_length_retry,
                _allow_rate_retry=False,
            )
        raise RuntimeError("FREE_AI_RATE_LIMIT: Cloudflare Workers Free HTTP 429.")
    if resp.status_code in (502, 503, 504):
        raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: Cloudflare temporarily unavailable.")
    if resp.status_code in (401, 403):
        raise RuntimeError("FREE_AI_ACCESS_REJECTED: Cloudflare access denied.")
    if resp.status_code == 402:
        raise RuntimeError("FREE_AI_ACCOUNT_BLOCKED: Cloudflare Free billing boundary.")
    if resp.status_code == 404:
        raise RuntimeError("FREE_MODEL_UNAVAILABLE: Cloudflare exact model unavailable.")
    if resp.status_code != 200:
        # No raw provider error/body: it may echo customer HTML or instructions.
        # Keep only numeric diagnostic fields and safe request dimensions.
        code = None
        reason_class = "other"
        try:
            error_body = resp.json()
            entries = error_body.get("errors") if isinstance(error_body, dict) else None
            item = entries[0] if isinstance(entries, list) and entries else {}
            if isinstance(item, dict) and type(item.get("code")) is int:
                code = item["code"]
            detail = str(item.get("message") or "")[:300].lower()
            if any(t in detail for t in ("context length", "context window",
                                         "token limit", "too many tokens")):
                reason_class = "context"
            elif any(t in detail for t in ("image", "base64", "payload too large")):
                reason_class = "image"
            elif "max_tokens" in detail or "max_completion_tokens" in detail:
                reason_class = "output_budget"
        except (TypeError, KeyError, IndexError, ValueError, AttributeError):
            pass
        print("[Cloudflare] safe rejection:", "stage="+str(stage),
              "http="+str(resp.status_code),
              "provider_code="+str(code),
              "reason_class="+reason_class,
              "user_prompt_chars="+str(len(user_prompt)),
              "image_count="+str(len(image_paths or [])))
        raise RuntimeError("FREE_MODEL_REQUEST_REJECTED: Cloudflare HTTP "+
                           str(resp.status_code)+" ("+reason_class+").")
    try:
        data = resp.json()
        if not isinstance(data, dict) or (
            data.get("model") is not None and data["model"] != model
        ):
            raise ValueError("unapproved model")
        choices = data["choices"]
        first = choices[0]
        if first.get("finish_reason") == "length":
            # The first long, source-verified JSON response can consume its
            # initial 3,500-token output budget. Allow ONE controlled increase
            # (never an unbounded loop). _reserve() caps both requests and
            # Workers Free account enforces the no-charge daily allowance.
            if _allow_length_retry and max_tokens < 10000:
                return chat_cloudflare_free(
                    system, user_prompt, stage=stage,
                    max_tokens=min(10000, max_tokens * 2),
                    image_paths=image_paths, json_mode=json_mode,
                    _allow_length_retry=False,
                    _allow_rate_retry=_allow_rate_retry)
            raise RuntimeError("FREE_AI_RESPONSE_TRUNCATED: Cloudflare model exhausted output tokens.")
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
        raise RuntimeError("FREE_MODEL_REQUEST_REJECTED: Cloudflare response invalid or incomplete.") from exc
