"""
Ohut kääre Anthropic API:n ympärille.
Kaikki agentit kutsuvat Claudea tämän moduulin kautta, jotta
uudelleenyritykset, viiveet ja web-haku on toteutettu vain yhdessä paikassa.
"""
import time
import anthropic

import config

_client = None


def _get_client():
    global _client
    if _client is None:
        if not config.ANTHROPIC_API_KEY:
            raise RuntimeError(
                "ANTHROPIC_API_KEY puuttuu. Täytä .env-tiedosto (katso .env.example)."
            )
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def ask_claude(system: str, user_prompt: str, use_web_search: bool = False,
                max_tokens: int = 4000, max_retries: int = 3) -> str:
    """
    Lähettää yhden viestin Claudelle ja palauttaa vastauksen tekstinä.

    use_web_search=True antaa Claudelle mahdollisuuden hakea tietoa netistä
    (esim. kilpailijoiden sivustoja, toimialatietoa). Tämä käyttää
    Anthropicin server-puolen web_search-työkalua, joten se vaatii
    voimassa olevan API-avaimen jolla on web-haku käytössä.
    """
    client = _get_client()

    tools = []
    if use_web_search:
        tools.append({"type": "web_search_20250305", "name": "web_search"})

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            kwargs = dict(
                model=config.CLAUDE_MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user_prompt}],
            )
            if tools:
                kwargs["tools"] = tools

            response = client.messages.create(**kwargs)

            # Vastaus voi sisältää useita content-blockeja (teksti + web-haun
            # tulokset). Poimitaan kaikki tekstiosat ja yhdistetään.
            text_parts = []
            for block in response.content:
                if getattr(block, "type", None) == "text":
                    text_parts.append(block.text)
            return "\n".join(text_parts).strip()

        except anthropic.RateLimitError as e:
            last_error = e
            wait = config.REQUEST_DELAY * (2 ** attempt)
            print(f"  [Claude] Rate limit, odotetaan {wait:.1f}s (yritys {attempt}/{max_retries})...")
            time.sleep(wait)
        except anthropic.APIError as e:
            last_error = e
            print(f"  [Claude] API-virhe (yritys {attempt}/{max_retries}): {e}")
            time.sleep(config.REQUEST_DELAY)

    raise RuntimeError(f"Claude-kutsu epäonnistui {max_retries} yrityksen jälkeen: {last_error}")


def ask_claude_json(system: str, user_prompt: str, use_web_search: bool = False,
                     max_tokens: int = 4000) -> dict | list:
    """
    Sama kuin ask_claude, mutta olettaa vastauksen olevan JSON ja parsii sen.
    Lisää systeemipromptiin ohjeen vastata VAIN JSON-muodossa.
    """
    import json

    json_system = (
        system
        + "\n\nTÄRKEÄÄ: Vastaa AINOASTAAN validilla JSON-datalla. "
        "Älä lisää selityksiä, markdown-koodilohkomerkintöjä (```), "
        "tai mitään muuta tekstiä JSONin ympärille."
    )
    raw = ask_claude(json_system, user_prompt, use_web_search=use_web_search, max_tokens=max_tokens)

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:]
    cleaned = cleaned.strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"Claude ei palauttanut validia JSONia: {e}\n---Raaka vastaus---\n{raw[:1000]}"
        )
