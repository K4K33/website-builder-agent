"""Preflight for Kaurivo's zero-API-credit, local-only Windows builder.

Only queries Ollama on loopback. It never starts a job, downloads a model,
reads credentials, checks Codex, or calls an external AI service.
"""
from __future__ import annotations

import sys
import requests

from scripts.kaurivo_local_worker import LocalWorkerError, OLLAMA, models


def check_models() -> tuple[bool, str]:
    try:
        selected = models()
    except LocalWorkerError as exc:
        return False, str(exc)

    try:
        with requests.Session() as session:
            response = session.get(OLLAMA + "/api/tags", timeout=5, allow_redirects=False)
            response.raise_for_status()
            payload = response.json()
            available = {
                str(model.get("name") or "")
                for model in payload.get("models", [])
                if isinstance(model, dict)
            }
            required = set(selected.values())
            missing = sorted(
                name for name in required
                if name not in available and name + ":latest" not in available
            )
            if missing:
                return False, "Paikalliset mallit puuttuvat: " + ", ".join(missing)
            result = session.post(
                OLLAMA + "/api/show", json={"model": selected["qa"]},
                timeout=8, allow_redirects=False,
            )
            result.raise_for_status()
            abilities = result.json().get("capabilities", [])
            if not isinstance(abilities, list) or "vision" not in abilities:
                return False, "QA-malli ei tue kuvia; laaduntarkistusta ei saa ohittaa."
    except (requests.RequestException, ValueError, TypeError, KeyError) as exc:
        return False, ("Paikallinen Ollama ei vastaa. Avaa Ollama-sovellus ja "
                       "tarkista palvelu osoitteessa 127.0.0.1:11434 "
                       "(" + type(exc).__name__ + ").")
    return True, ("Maksuton paikallinen AI valmis: rakentaja "
                  + selected["builder"] + ", riippumaton kuvallinen QA "
                  + selected["qa"] + ". Codexia ei käytetä.")


def main() -> int:
    ready, message = check_models()
    print(message, flush=True)
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main())
