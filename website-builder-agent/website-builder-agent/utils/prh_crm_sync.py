"""PRH nightly shortlist → Kaurivo-only Supabase lead inbox using GitHub OIDC.

Zero static API secrets. Authentication is by GitHub-signed short-lived JWT,
verified server-side for the exact repo, workflow, branch and audience.
This script never submits customer contacts or sends sales messages.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from urllib.parse import urlencode

import requests

AUDIENCE = "kaurivo-prh-ingest-xhsfbcwpwbgdbatrcyuk"
FUNCTION_URL = "https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-prh-ingest"
MAX_BYTES = 200_000


def push_packet(packet_path, *, env=None, get=requests.get, post=requests.post):
    """Single OIDC request and one idempotent Kaurivo Edge Function request."""
    env = os.environ if env is None else env
    packet = Path(packet_path)
    if not packet.is_file() or packet.stat().st_size > MAX_BYTES:
        raise RuntimeError("Shortlist packet missing or exceeds limit")
    content = packet.read_bytes()
    data = json.loads(content)
    if (not isinstance(data, dict) or data.get("schema") != "kaurivo_prh_shortlist_v1"
            or data.get("mode") != "pilot-live"
            or data.get("not_verified_for_outreach") is not True
            or not isinstance(data.get("candidates"), list)
            or not 1 <= len(data["candidates"]) <= 50):
        raise RuntimeError("Only an official real PRH pilot-live shortlist can be synced")

    request_url = env.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    request_token = env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not request_url.startswith("https://") or not request_token:
        raise RuntimeError("GitHub OIDC token request is not available")
    query = urlencode({"audience": AUDIENCE})
    request_url += ("&" if "?" in request_url else "?") + query
    response = get(request_url, headers={
        "Authorization": "bearer " + request_token,
        "Accept": "application/json",
    }, timeout=(6, 20))
    response.raise_for_status()
    id_token = response.json().get("value")
    if not isinstance(id_token, str) or len(id_token) > 7000 or len(id_token) < 100:
        raise RuntimeError("GitHub OIDC did not return a valid token")

    result = post(FUNCTION_URL, headers={
        "Authorization": "Bearer " + id_token,
        "Content-Type": "application/json",
    }, data=content, timeout=(6, 30))
    if not result.ok:
        # Do not print tokens, raw response content, business records or
        # unexpected provider errors into a public Actions log.
        raise RuntimeError("Kaurivo ingest rejected request (HTTP "
                           + str(result.status_code) + ")")
    payload = result.json()
    if payload.get("ok") is not True or payload.get("emails_sent") != 0:
        raise RuntimeError("Unexpected ingest result")
    return {
        "processed": int(payload.get("processed", 0)),
        "ai_credits_used": 0,
        "emails_sent": 0,
        "target": "Kaurivo-only private lead review queue",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", default="output/nightly-prh/crm-shortlist.json")
    args = parser.parse_args(argv)
    print(json.dumps(push_packet(args.packet), ensure_ascii=False))


if __name__ == "__main__":
    main()
