"""
AI-client Website Builder Agentille.

Käyttää OpenRouteria.

Tukee:
- tavallista tekstianalyysiä
- JSON-vastauksia
- kuvien lähettämistä vision-mallille
- keskitettyä resurssienhallintaa

DRY-RUN ei kutsu tätä moduulia.
"""

import base64
import json
import mimetypes
import os
import time
from datetime import datetime, timezone

import requests

import config
from utils import resource_manager


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "openrouter/free"

_client_headers = None


def _get_headers():
    global _client_headers

    if _client_headers is None:
        api_key = getattr(
            config,
            "OPENROUTER_API_KEY",
            "",
        )

        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY puuttuu. "
                "Lisää se GitHub Secretiksi."
            )

        _client_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": (
                "https://github.com/K4K33/website-builder-agent"
            ),
            "X-Title": "Website Builder Agent",
        }

    return _client_headers


def _image_to_data_url(image_path: str) -> str:
    if not image_path:
        raise ValueError("Kuvapolku puuttuu.")

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Kuvaa ei löytynyt: {image_path}"
        )

    mime_type, _ = mimetypes.guess_type(image_path)

    if not mime_type:
        mime_type = "image/png"

    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(
            image_file.read()
        ).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def _build_user_content(
    user_prompt: str,
    image_paths: list[str] | None = None,
):
    if not image_paths:
        return user_prompt

    content = [
        {
            "type": "text",
            "text": user_prompt,
        }
    ]

    for image_path in image_paths:
        data_url = _image_to_data_url(image_path)

        content.append(
            {
                "type": "image_url",
                "image_url": {
                    "url": data_url,
                },
            }
        )

    return content


def _extract_content(data: dict) -> str:
    choices = data.get("choices", [])

    if not choices:
        raise RuntimeError(
            "OpenRouter ei palauttanut choices-dataa: "
            f"{data}"
        )

    message = choices[0].get("message", {})

    content = message.get("content", "")

    if isinstance(content, list):
        text_parts = []

        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    text_parts.append(
                        part.get("text", "")
                    )

        content = "\n".join(text_parts)

    if content:
        return str(content).strip()

    return ""


def _local_free_quota_fallback(
    system: str, user_prompt: str, *, stage: str | None,
    max_tokens: int, image_paths: list[str] | None,
    json_mode: bool, capacity_code: str = "FREE_AI_CAPACITY_UNAVAILABLE",
) -> str:
    """Try explicit Workers Free once, then existing no-cloud local fallback.

    This does NOT bypass either service's quota and is never enabled without
    owner confirmation of the Workers FREE account and a server-side secret.
    """
    if config.free_only():
        from utils.cloudflare_free_ai import enabled, chat_cloudflare_free
        if enabled():
            return chat_cloudflare_free(
                system, user_prompt, stage=stage, max_tokens=max_tokens,
                image_paths=image_paths, json_mode=json_mode)
    if not config.free_only() or os.getenv("FREE_CLOUD_LOCAL_FALLBACK", "1") != "1":
        raise RuntimeError(f"{capacity_code}: free OpenRouter capacity unavailable; no paid fallback.")
    name = (os.getenv(f"OLLAMA_{stage.upper()}_MODEL", "").strip()
            if stage else "")
    name = name or os.getenv("OLLAMA_MODEL", "").strip()
    if not name or name.lower().endswith(":cloud"):
        # Distinct, non-sensitive error: the worker can defer this private job
        # without manufacturing a result or retrying a capped free API.
        raise RuntimeError(
            f"{capacity_code}: OpenRouter free capacity unavailable; "
            "no local model installed; no paid fallback."
        )
    from utils.local_ai import chat_local
    return chat_local(
        system, user_prompt, model=name,
        max_tokens=min(max_tokens, config.AI_MAX_OUTPUT_TOKENS),
        image_paths=image_paths, json_mode=json_mode,
        timeout=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "600")),
    )


def _verified_free_minute_wait_seconds(response) -> int | None:
    """Retry only a provable, near-term OpenRouter free RPM reset.

    OpenRouter's own 429 includes rate-limit headers; upstream free
    providers may instead return a short Retry-After. Only one bounded,
    explicitly timed retry is allowed. Never blindly retry a bare 429,
    a malformed header or a UTC-day reset. Both requests still reserve
    a daily free-model request; there is no paid model escalation.
    """
    headers = getattr(response, "headers", None)
    if not headers:
        return None
    retry_after = str(headers.get("Retry-After", "")).strip()
    if retry_after:
        try:
            seconds = float(retry_after)
        except (TypeError, ValueError, OverflowError):
            seconds = 0
        # Ignore long provider waits and avoid spending a second request
        # on known daily/account-wide capacity blocks.
        if 0 < seconds <= 90:
            return max(1, min(92, int(seconds) + 2))
    if str(headers.get("X-RateLimit-Remaining", "")).strip() != "0":
        return None
    try:
        reset = float(headers.get("X-RateLimit-Reset", ""))
        if reset > 1_000_000_000_000:  # Unix milliseconds
            reset /= 1000
        delta = reset - time.time()
    except (TypeError, ValueError, OverflowError):
        return None
    if not (0 < delta <= 65):
        return None
    return max(1, min(67, int(delta) + 2))


def ask_claude(
    system: str,
    user_prompt: str,
    use_web_search: bool = False,
    max_tokens: int = 4000,
    max_retries: int = 3,
    image_paths: list[str] | None = None,
    stage: str | None = None,
    json_mode: bool = False,
) -> str:

    model = config.model_for_stage(stage)
    models = config.stage_model_candidates(stage)
    if max_retries < 1 or max_tokens < 1:
        raise ValueError("max_retries and max_tokens must be positive")

    backend = config.backend_for_stage(stage)
    if backend == "codex":
        from utils.codex_ai import chat_codex
        return chat_codex(system, user_prompt, model=model,
                          image_paths=image_paths, json_mode=json_mode)
    if backend == "ollama":
        from utils.local_ai import chat_local
        # No OpenRouter headers, credits, reservations, or cloud fallback.
        return chat_local(
            system, user_prompt, model=model, max_tokens=min(max_tokens, config.AI_MAX_OUTPUT_TOKENS),
            image_paths=image_paths, json_mode=json_mode,
            timeout=int(os.getenv("OLLAMA_TIMEOUT_SECONDS", "600")),
        )

    # When the no-inference key endpoint proves OpenRouter daily FREE quota
    # already exhausted, do not burn a known-failed OpenRouter 429 merely
    # to reach our confirmed independent Workers Free backup.
    if (config.free_only() and
            os.environ.get("KAURIVO_OPENROUTER_FREE_EXHAUSTED") == "1"):
        from utils.cloudflare_free_ai import enabled, chat_cloudflare_free
        if not enabled():
            raise RuntimeError("FREE_AI_CAPACITY_UNAVAILABLE: no verified free cloud capacity.")
        return chat_cloudflare_free(
            system, user_prompt, stage=stage, max_tokens=max_tokens,
            image_paths=image_paths, json_mode=json_mode)

    # Validate again at the final paid-provider boundary. An unrelated
    # funded API key must never make a non-free model billable in FREE_ONLY.
    if config.free_only() and not config.is_zero_cost_openrouter_model(model):
        raise RuntimeError("FREE_ONLY blocks paid model before any OpenRouter API request.")
    headers = _get_headers()
    user_content = _build_user_content(
        user_prompt,
        image_paths=image_paths,
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": user_content,
            },
        ],
        "max_tokens": max_tokens,
    }
    if len(models) > 1:
        # OpenRouter handles provider/model failover within a SINGLE counted
        # chat request. Include only exact :free IDs. No extra cloud retry.
        payload["models"] = models
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    retry_token_limits = [
        max_tokens,
        max(max_tokens * 2, 4000),
        max(max_tokens * 4, 8000),
    ]

    last_error = None
    free_provider_minute_retried = False

    for attempt in range(1, max_retries + 1):

        current_max_tokens = retry_token_limits[
            min(
                attempt - 1,
                len(retry_token_limits) - 1,
            )
        ]

        current_max_tokens = min(current_max_tokens, config.AI_MAX_OUTPUT_TOKENS)
        payload["max_tokens"] = current_max_tokens

        reserved = resource_manager.reserve("openrouter")
        if not reserved and config.free_only() and (
            resource_manager.openrouter_reservation_block_reason() == "minute"
        ):
            # A temporary, local per-minute guard must not defer the ENTIRE
            # client's build until tomorrow. Wait for at most one minute edge,
            # then make ONE bounded reserve attempt. No paid escalation.
            seconds = datetime.now(timezone.utc).second
            time.sleep(max(1, 61 - seconds))
            reserved = resource_manager.reserve("openrouter")
        if not reserved:
            if config.free_only():
                capacity_code = ("FREE_AI_CAPACITY_UNAVAILABLE"
                                 if resource_manager.openrouter_reservation_block_reason() == "daily"
                                 else "FREE_AI_RATE_LIMIT")
                return _local_free_quota_fallback(
                    system, user_prompt, stage=stage, max_tokens=max_tokens,
                    image_paths=image_paths, json_mode=json_mode,
                    capacity_code=capacity_code,
                )
            raise RuntimeError("OpenRouter request blocked by daily resource limit.")

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=180,
            )

            if response.status_code == 429:
                if config.free_only():
                    # One bounded retry ONLY if OpenRouter itself proves the
                    # minute window resets soon. Otherwise yield to the queue.
                    # A bare 429 is not proof of exhausted daily allowance.
                    wait_seconds = (_verified_free_minute_wait_seconds(response)
                                    if not free_provider_minute_retried
                                    and attempt < max_retries else None)
                    if wait_seconds is not None:
                        free_provider_minute_retried = True
                        time.sleep(wait_seconds)
                        continue
                    return _local_free_quota_fallback(
                        system, user_prompt, stage=stage, max_tokens=max_tokens,
                        image_paths=image_paths, json_mode=json_mode,
                        capacity_code="FREE_AI_RATE_LIMIT",
                    )
                last_error = response.text

                wait = (
                    getattr(
                        config,
                        "REQUEST_DELAY",
                        2,
                    )
                    * (2 ** (attempt - 1))
                )

                print(
                    f"  [OpenRouter] Rate limit, "
                    f"odotetaan {wait:.1f}s "
                    f"(yritys {attempt}/{max_retries})..."
                )

                time.sleep(wait)
                continue

            if 400 <= response.status_code < 500:
                raise RuntimeError(f"OpenRouter rejected request: HTTP {response.status_code}")

            if response.status_code >= 400:
                last_error = response.text

                print(
                    f"  [OpenRouter] API-virhe "
                    f"(yritys {attempt}/{max_retries}): "
                    f"{response.status_code} "
                    f"{response.text[:1000]}"
                )

                time.sleep(
                    getattr(
                        config,
                        "REQUEST_DELAY",
                        2,
                    )
                )

                continue

            data = response.json()
            # A successful fallback must still use a free model from the
            # explicit allowlist. Never trust a paid model ID from a provider.
            if len(models) > 1:
                returned_model = data.get("model")
                if (returned_model is not None and
                        (not isinstance(returned_model, str) or
                         returned_model not in models)):
                    raise RuntimeError("FREE_ONLY model fallback returned unapproved model.")

            content = _extract_content(data)

            choices = data.get("choices", [])

            finish_reason = ""

            if choices:
                finish_reason = choices[0].get(
                    "finish_reason",
                    "",
                )

            if finish_reason == "length":
                last_error = (
                    "OpenRouter saavutti token-rajan "
                    "ilman varsinaista content-vastausta."
                )

                next_limit = min(config.AI_MAX_OUTPUT_TOKENS,
                                 retry_token_limits[min(
                                     attempt,len(retry_token_limits)-1)])
                # Never spend another counted free request asking for exactly
                # the same already-capped output length.
                if attempt < max_retries and next_limit > current_max_tokens:
                    print(
                        f"  [OpenRouter] Vastaus katkaistiin "
                        f"token-rajaan. Yritetään "
                        f"suuremmalla budjetilla "
                        f"({current_max_tokens} -> "
                        f"{next_limit})..."
                    )

                    continue

                raise RuntimeError("OpenRouter response truncated; output rejected.")

            if finish_reason in {"content_filter", "error"}:
                raise RuntimeError(f"OpenRouter response rejected: {finish_reason}")

            if content:
                return content

            raise RuntimeError(
                "OpenRouter palautti tyhjän vastauksen: "
                f"{data}"
            )

        except requests.RequestException as e:
            last_error = e

            print(
                f"  [OpenRouter] Verkkovirhe "
                f"(yritys {attempt}/{max_retries}): {e}"
            )

            time.sleep(
                getattr(
                    config,
                    "REQUEST_DELAY",
                    2,
                )
            )

        except ValueError as e:
            last_error = e

            print(
                f"  [OpenRouter] JSON-vastausta ei voitu "
                f"lukea (yritys {attempt}/{max_retries}): {e}"
            )

            time.sleep(
                getattr(
                    config,
                    "REQUEST_DELAY",
                    2,
                )
            )

    raise RuntimeError(
        "OpenRouter-kutsu epäonnistui "
        f"{max_retries} yrityksen jälkeen: "
        f"{last_error}"
    )


def ask_claude_json(
    system: str,
    user_prompt: str,
    use_web_search: bool = False,
    max_tokens: int = 4000,
    image_paths: list[str] | None = None,
    stage: str | None = None,
) -> dict | list:

    json_system = (
        system
        + "\n\nTÄRKEÄÄ: Vastaa AINOASTAAN "
        "validilla JSON-datalla. "
        "Älä lisää selityksiä, "
        "markdown-koodilohkoja (```), "
        "tai mitään muuta tekstiä JSONin ympärille."
    )

    raw = ask_claude(
        json_system,
        user_prompt,
        use_web_search=use_web_search,
        max_tokens=max_tokens,
        image_paths=image_paths,
        stage=stage,
        json_mode=True,
    )

    cleaned = raw.strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines and lines[0].strip().lower() in (
            "```",
            "```json",
        ):
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    try:
        return json.loads(cleaned)

    except json.JSONDecodeError as e:
        raise RuntimeError(
            "OpenRouter ei palauttanut validia JSONia: "
            f"{e}\n"
            "---Raaka vastaus---\n"
            f"{raw[:3000]}"
        )
