"""Offline checks: Kaurivo 08:00 lead notifications, PWA and GitHub OIDC.

No external HTTP calls, paid credits, synthetic production leads or email sends.
"""
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from utils.kaurivo_morning_push import send_daily_push, AUDIENCE


class FakeHttpResponse:
    def __init__(self, data):
        self.data = data

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def read(self):
        return json.dumps(self.data).encode("utf-8")


class KaurivoMorningPushTests(unittest.TestCase):
    def test_oidc_auth_and_no_static_secrets(self):
        requests = []

        def fake_urlopen(request, timeout):
            requests.append(request)
            if len(requests) == 1:
                return FakeHttpResponse({"value": "x" * 101})
            return FakeHttpResponse({"ok": True, "day": "2026-11-01",
                                     "companies": 36, "notifications": 1})

        result = send_daily_push(
            env={"ACTIONS_ID_TOKEN_REQUEST_URL": "https://token.actions.githubusercontent.com/a?foo=1",
                 "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "short-lived-internal"},
            open_url=fake_urlopen,
        )
        self.assertEqual(result["companies"], 36)
        self.assertEqual(result["notifications"], 1)
        self.assertEqual(result["marketing_emails_sent"], 0)
        self.assertEqual(result["ai_credits_used"], 0)
        self.assertEqual(parse_qs(urlparse(requests[0].full_url).query)["audience"], [AUDIENCE])
        self.assertEqual(requests[1].get_method(), "POST")
        self.assertEqual(json.loads(requests[1].data), {"action": "notify"})
        self.assertEqual(requests[1].get_header("Authorization"), "Bearer " + "x" * 101)

    def test_refuse_without_gitHub_oidc(self):
        with self.assertRaises(RuntimeError):
            send_daily_push(env={})

    def test_admin_is_installed_pwa_and_push_requires_opt_in(self):
        ui = ROOT / "docs/kaurivo/admin"
        manifest = json.loads((ui / "manifest.webmanifest").read_text(encoding="utf-8"))
        self.assertEqual(manifest["display"], "standalone")
        self.assertEqual(manifest["scope"], "./")
        self.assertIn("prospects", manifest["start_url"])
        html = (ui / "index.html").read_text(encoding="utf-8")
        script = (ROOT / "docs/kaurivo/assets/crm.js").read_text(encoding="utf-8")
        worker = (ui / "sw.js").read_text(encoding="utf-8")
        self.assertIn('id="enable-push"', html)
        self.assertIn('id="prospect-day"', html)
        self.assertIn("Notification.requestPermission()", script)
        self.assertIn('action:"subscribe"', script)
        self.assertIn("website_listed_url", script)
        self.assertIn("showNotification", worker)
        self.assertNotIn("addEventListener(\"fetch\"", worker)

    def test_schedule_is_helsinki_dst_aware_with_backup(self):
        yaml = (ROOT.parents[1] / ".github/workflows/kaurivo-morning-push.yml").read_text(encoding="utf-8")
        self.assertIn('cron: "0 8 * * *"', yaml)
        self.assertIn('cron: "27 8 * * *"', yaml)
        self.assertEqual(yaml.count('timezone: "Europe/Helsinki"'), 2)


if __name__ == "__main__":
    unittest.main()
