"""Quota-proof free fallback: an open model running on the GitHub runner itself.

Every free cloud model Kaurivo uses has a daily quota (OpenRouter 50
requests, Gemini per-model limits, Cloudflare 10 000 neurons). When they are
all spent, a sales demo still needs exactly one JSON answer: the content plan
written from the company's own verified text. That fits a small open model on
the runner's CPU (4 vCPU, 16 GB): slow (10-20 min) but free and without any
quota, and verify_plan still drops every claim the source text does not back.

Only active with KAURIVO_LOCAL_SALES_MODEL on a GitHub Actions runner. Ollama
is downloaded from its pinned official GitHub release into the runner's
cache, listens on loopback only and is never used for the full builder
(too slow there). Nothing is installed on anyone's own computer.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import time

import requests

# The model registry refuses models an old Ollama cannot run, so take the
# latest official release from Ollama's own GitHub repository.
_LATEST = "https://api.github.com/repos/ollama/ollama/releases/latest"
_API = "http://127.0.0.1:11434"
_MODEL = re.compile(r"[a-z0-9][a-z0-9._-]{0,40}(?::[a-z0-9._-]{1,30})?")
LAST_ERROR = ""
QUOTA_HINTS = ("429", "rate limit", "rate_limit", "quota", "capacity", "free_ai", "free_model_unavailable",
               "resource_exhausted", "daily")


def model_name() -> str:
    name = os.getenv("KAURIVO_LOCAL_SALES_MODEL", "").strip().lower()
    if not name or name.endswith(":cloud") or not _MODEL.fullmatch(name):
        return ""
    return name


def enabled() -> bool:
    return bool(model_name()) and os.getenv("GITHUB_ACTIONS") == "true"


def is_quota_error(exc: BaseException) -> bool:
    text = str(exc).casefold()
    return any(hint in text for hint in QUOTA_HINTS)


def _up(timeout: float = 2) -> bool:
    try:
        return requests.get(_API + "/api/tags", timeout=timeout, allow_redirects=False).status_code == 200
    except requests.RequestException:
        return False


def _home() -> Path:
    return Path(os.getenv("KAURIVO_OLLAMA_HOME", str(Path.home() / ".cache" / "kaurivo-ollama")))


def _install(home: Path) -> Path:
    binary = home / "bin" / "ollama"
    if binary.is_file():
        return binary
    home.mkdir(parents=True, exist_ok=True)
    release = requests.get(_LATEST, timeout=30, headers={"Accept": "application/vnd.github+json"}).json()
    assets = {a.get("name"): a.get("browser_download_url") for a in release.get("assets") or []}
    url = next((assets[n] for n in ("ollama-linux-amd64.tar.zst", "ollama-linux-amd64.tgz") if assets.get(n)), "")
    if not url.startswith("https://github.com/ollama/ollama/releases/download/"):
        raise RuntimeError("local_model_release_not_found")
    unpack = "tar --zstd -x" if url.endswith(".zst") else "tar -xz"
    # CPU runner: skip the GPU libraries (most of the archive's size on disk).
    script = ("set -o pipefail; curl -fsSL --retry 3 '" + url + "' | " + unpack + " -C '" + str(home) +
              "' --wildcards --exclude='*cuda*' --exclude='*rocm*'")
    done = subprocess.run(["bash", "-c", script], timeout=900, stdout=subprocess.DEVNULL,
                          stderr=subprocess.PIPE, text=True)
    if done.returncode or not binary.is_file():
        found = sorted(str(x.relative_to(home)) for x in home.glob("*/*"))[:6]
        raise RuntimeError("local_model_install_failed rc=%s %s found=%s" % (
            done.returncode, done.stderr.strip()[-200:], found))
    return binary


def ensure() -> str:
    """Start Ollama on loopback and pull the model; return its name or ''."""
    name = model_name()
    if not enabled():
        return ""
    try:
        if not _up():
            home = _home()
            binary = _install(home)
            env = dict(os.environ, OLLAMA_HOST="127.0.0.1:11434", OLLAMA_MODELS=str(home / "models"),
                       OLLAMA_NUM_PARALLEL="1", OLLAMA_KEEP_ALIVE="30m")
            subprocess.Popen([str(binary), "serve"], env=env, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, start_new_session=True)
            deadline = time.monotonic() + 60
            while not _up() and time.monotonic() < deadline:
                time.sleep(1)
            if not _up():
                _note("ollama serve did not start")
                return ""
        reply = requests.post(_API + "/api/pull", json={"model": name, "stream": False},
                              timeout=1200, allow_redirects=False)
        if reply.status_code != 200 or (reply.json() or {}).get("status") != "success":
            _note("pull HTTP %s %s" % (reply.status_code, reply.text[:160]))
            return ""
        return name
    except (OSError, subprocess.SubprocessError, requests.RequestException, ValueError, RuntimeError) as exc:
        _note(type(exc).__name__ + " " + str(exc)[:300])
        return ""


def _note(text: str) -> None:
    global LAST_ERROR
    LAST_ERROR = text


def parse_json(text: str):
    text = str(text or "").strip()
    text = re.sub(r"\A```(?:json)?\s*|\s*```\Z", "", text)
    try:
        return json.loads(text)
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise RuntimeError("local_model_invalid_json") from None
        return json.loads(text[start:end + 1])


def ask_json(system: str, prompt: str, *, max_tokens: int, model: str) -> dict | list:
    from utils.local_ai import chat_local
    os.environ.setdefault("OLLAMA_NUM_CTX", "12288")
    answer = chat_local(system + "\n\nAnswer with valid JSON only.", prompt, model=model,
                        max_tokens=max_tokens, json_mode=True,
                        timeout=int(os.getenv("KAURIVO_LOCAL_SALES_TIMEOUT", "1700")))
    return parse_json(answer)


def with_local_fallback(ask, *, on_local=None):
    """Wrap a cloud JSON ask: on a free-quota error use the runner's model."""
    def wrapped(system, prompt, *, max_tokens=4000, stage=None, **kwargs):
        try:
            return ask(system, prompt, max_tokens=max_tokens, stage=stage, **kwargs)
        except RuntimeError as exc:
            if not is_quota_error(exc):
                raise
            model = ensure()
            if not model:
                raise
            if on_local:
                on_local(model)
            return ask_json(system, prompt, max_tokens=max_tokens, model=model)
    return wrapped
