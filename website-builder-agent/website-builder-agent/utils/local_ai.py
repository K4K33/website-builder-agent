"""An opt-in, loopback-only Ollama transport (NO OpenRouter/API credits).

It NEVER downloads models, installs software, calls Ollama cloud, performs
remote network fallback, or sends user content to a public AI endpoint.
The developer/operator must approve installation on the host computer.
"""
import base64
from pathlib import Path

import requests

OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
MAX_IMAGE_BYTES = 8 * 1024 * 1024


def _image_base64(path):
    file = Path(path)
    if not file.is_file():
        raise FileNotFoundError("Local model screenshot missing: " + str(path))
    size = file.stat().st_size
    if not 0 < size <= MAX_IMAGE_BYTES:
        raise ValueError("Local screenshot exceeds the 8 MB upload limit")
    return base64.b64encode(file.read_bytes()).decode("ascii")


def chat_local(system, prompt, *, model, max_tokens, image_paths=None,
               json_mode=False, timeout=600):
    if not isinstance(model, str) or not model.strip():
        raise ValueError("Explicit locally installed Ollama model is required.")
    if model.strip().lower().endswith(":cloud"):
        raise RuntimeError("Cloud Ollama models are forbidden: install a local model.")
    if not isinstance(max_tokens, int) or not 1 <= max_tokens <= 32768:
        raise ValueError("Invalid local AI token limit")
    if not isinstance(timeout, (int, float)) or not 5 <= timeout <= 1800:
        raise ValueError("Invalid local Ollama timeout")

    message = {"role": "user", "content": prompt}
    if image_paths:
        message["images"] = [_image_base64(item) for item in image_paths]
    payload = {
        "model": model.strip(),
        "messages": [{"role": "system", "content": system}, message],
        "stream": False,
        "options": {"num_predict": max_tokens},
    }
    if json_mode:
        payload["format"] = "json"
    try:
        # Hardcoded loopback destination; never follow redirects to remote hosts.
        response = requests.post(
            OLLAMA_CHAT_URL, json=payload, timeout=timeout,
            allow_redirects=False,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise RuntimeError(
            "Local Ollama is not available. No cloud fallback attempted. "
            "Check local installation, installed model and computer permissions."
        ) from exc
    except ValueError as exc:
        raise RuntimeError("Local Ollama returned invalid JSON") from exc

    if not isinstance(data, dict):
        raise RuntimeError("Invalid Ollama response")
    if data.get("done_reason") == "length":
        raise RuntimeError("Local Ollama output was truncated; manual review required")
    message = data.get("message")
    text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(text, str) or not text.strip():
        raise RuntimeError("Local Ollama returned empty output; no remote retry")
    return text.strip()
