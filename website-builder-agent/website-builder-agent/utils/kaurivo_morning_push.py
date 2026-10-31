"""Daily Kaurivo-only mobile PWA notification via short-lived GitHub OIDC.

No database secret, AI API request, customer contact, or marketing send.
The Edge Function validates signed GitHub claims and deduplicates by day/device.
"""
from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen

AUDIENCE = "kaurivo-morning-push-xhsfbcwpwbgdbatrcyuk"
FUNCTION_URL = "https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-daily-push"


def send_daily_push(*, env=None, open_url=urlopen):
    env = os.environ if env is None else env
    url = env.get("ACTIONS_ID_TOKEN_REQUEST_URL", "")
    credentials = env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN", "")
    if not url.startswith("https://") or not credentials:
        raise RuntimeError("The short-lived GitHub Actions OIDC token is unavailable")
    req = Request(
        url + ("&" if "?" in url else "?") + urlencode({"audience": AUDIENCE}),
        headers={"Authorization": "bearer " + credentials, "Accept": "application/json"},
    )
    with open_url(req, timeout=20) as response:
        token = json.load(response).get("value", "")
    if not isinstance(token, str) or not 100 <= len(token) <= 7000:
        raise RuntimeError("Invalid GitHub identity token")
    payload = json.dumps({"action": "notify"}).encode("utf-8")
    req = Request(
        FUNCTION_URL,
        method="POST",
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"},
        data=payload,
    )
    with open_url(req, timeout=45) as response:
        data = json.load(response)
    if data.get("ok") is not True:
        raise RuntimeError("Notification request failed")
    return {"day": data.get("day"), "companies": data.get("companies"),
            "notifications": data.get("notifications"), "reason": data.get("reason"),
            "ai_credits_used": 0, "marketing_emails_sent": 0}


if __name__ == "__main__":
    print(json.dumps(send_daily_push(), ensure_ascii=False))
