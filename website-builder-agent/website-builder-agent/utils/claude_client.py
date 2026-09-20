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


def ask_claude(
    system: str,
    user_prompt: str,
    use_web_search: bool = False,
    max_tokens: int = 4000,
    max_retries: int = 3,
    image_paths: list[str] | None = None,
) -> str:

    headers = _get_headers()

    model = getattr(
        config,
        "OPENROUTER_MODEL",
        DEFAULT_MODEL,
    )

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

    retry_token_limits = [
        max_tokens,
        max(max_tokens * 2, 4000),
        max(max_tokens * 4, 8000),
    ]

    last_error = None

    for attempt in range(1, max_retries + 1):

        current_max_tokens = retry_token_limits[
            min(
                attempt - 1,
                len(retry_token_limits) - 1,
            )
        ]

        payload["max_tokens"] = current_max_tokens

        if not resource_manager.reserve("openrouter"):
            raise RuntimeError(
                "OpenRouter-kutsu estettiin Resource "
                "Managerin toimesta. Kuukausiresurssia "
                "ei ole turvallisesti käytettävissä."
            )

        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=180,
            )

            if response.status_code == 429:
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

            content = _extract_content(data)

            if content:
                return content

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

                if attempt < max_retries:
                    next_limit = retry_token_limits[
                        min(
                            attempt,
                            len(retry_token_limits) - 1,
                        )
                    ]

                    print(
                        f"  [OpenRouter] Vastaus katkaistiin "
                        f"token-rajaan. Yritetään "
                        f"suuremmalla budjetilla "
                        f"({current_max_tokens} -> "
                        f"{next_limit})..."
                    )

                    continue

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
