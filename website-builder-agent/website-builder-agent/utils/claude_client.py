"""
AI-client Website Builder Agentille.

Käyttää OpenRouteria Anthropic API:n sijaan.
Muut agentit voivat edelleen käyttää samoja ask_claude()
ja ask_claude_json() -funktioita, joten muu projektirakenne
pysyy mahdollisimman muuttumattomana.
"""

import json
import time

import requests

import config


OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Ilmainen OpenRouter-malli.
# Tämä voidaan vaihtaa myöhemmin ilman muiden agenttien muuttamista.
DEFAULT_MODEL = "openrouter/free"

_client_headers = None


def _get_headers():
    global _client_headers

    if _client_headers is None:
        api_key = getattr(config, "OPENROUTER_API_KEY", "")

        if not api_key:
            raise RuntimeError(
                "OPENROUTER_API_KEY puuttuu. "
                "Lisää se GitHub Secretiksi ja varmista, että config.py lukee sen."
            )

        _client_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/K4K33/website-builder-agent",
            "X-Title": "Website Builder Agent",
        }

    return _client_headers


def ask_claude(
    system: str,
    user_prompt: str,
    use_web_search: bool = False,
    max_tokens: int = 4000,
    max_retries: int = 3,
) -> str:
    """
    Lähettää pyynnön OpenRouterille.

    Funktion nimi ask_claude säilytetään tarkoituksella, jotta muiden
    agenttien koodia ei tarvitse tässä vaiheessa muuttaa.

    Huom:
    OpenRouterin kautta käytettävä malli ei automaattisesti saa
    Anthropicin web_search-työkalua. Web-haku käsitellään erikseen
    projektin myöhemmässä vaiheessa.
    """

    headers = _get_headers()

    model = getattr(config, "OPENROUTER_MODEL", DEFAULT_MODEL)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": system,
            },
            {
                "role": "user",
                "content": user_prompt,
            },
        ],
        "max_tokens": max_tokens,
    }

    last_error = None

    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                OPENROUTER_URL,
                headers=headers,
                json=payload,
                timeout=120,
            )

            if response.status_code == 429:
                last_error = response.text

                wait = getattr(config, "REQUEST_DELAY", 2) * (2 ** (attempt - 1))

                print(
                    f"  [OpenRouter] Rate limit, odotetaan "
                    f"{wait:.1f}s (yritys {attempt}/{max_retries})..."
                )

                time.sleep(wait)
                continue

            if response.status_code >= 400:
                last_error = response.text

                print(
                    f"  [OpenRouter] API-virhe "
                    f"(yritys {attempt}/{max_retries}): "
                    f"{response.status_code} {response.text[:500]}"
                )

                time.sleep(getattr(config, "REQUEST_DELAY", 2))
                continue

            data = response.json()

            choices = data.get("choices", [])

            if not choices:
                raise RuntimeError(
                    f"OpenRouter ei palauttanut choices-dataa: {data}"
                )

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                raise RuntimeError(
                    f"OpenRouter palautti tyhjän vastauksen: {data}"
                )

            return content.strip()

        except requests.RequestException as e:
            last_error = e

            print(
                f"  [OpenRouter] Verkkovirhe "
                f"(yritys {attempt}/{max_retries}): {e}"
            )

            time.sleep(getattr(config, "REQUEST_DELAY", 2))

        except ValueError as e:
            last_error = e

            print(
                f"  [OpenRouter] JSON-vastausta ei voitu lukea "
                f"(yritys {attempt}/{max_retries}): {e}"
            )

            time.sleep(getattr(config, "REQUEST_DELAY", 2))

    raise RuntimeError(
        f"OpenRouter-kutsu epäonnistui {max_retries} yrityksen jälkeen: "
        f"{last_error}"
    )


def ask_claude_json(
    system: str,
    user_prompt: str,
    use_web_search: bool = False,
    max_tokens: int = 4000,
) -> dict | list:
    """
    Sama kuin ask_claude(), mutta parsii vastauksen JSONiksi.
    """

    json_system = (
        system
        + "\n\nTÄRKEÄÄ: Vastaa AINOASTAAN validilla JSON-datalla. "
        "Älä lisää selityksiä, markdown-koodilohkoja (```), "
        "tai mitään muuta tekstiä JSONin ympärille."
    )

    raw = ask_claude(
        json_system,
        user_prompt,
        use_web_search=use_web_search,
        max_tokens=max_tokens,
    )

    cleaned = raw.strip()

    # Poistetaan mahdollinen markdown-koodilohko.
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
            f"{e}\n---Raaka vastaus---\n{raw[:2000]}"
        )
