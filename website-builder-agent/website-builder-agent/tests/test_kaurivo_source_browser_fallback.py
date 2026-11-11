"""No-network regression tests for resilient public business-site fetching.

A real Chrome/24-page GitHub-runner probe is separately verified on the
public Kurki-Suonio site. No authenticated content or external APIs here.
"""
from __future__ import annotations
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock,patch

import requests
from utils.fetch import fetch_html,_PLAIN_HEADERS_HOSTS,_fetch_html_from_browser

PAGE="https://fixture.example.org/ihmiset"


def response(status=200,text="<html><body>Verified public business information and details</body></html>"):
    return SimpleNamespace(status_code=status,url=PAGE,
        headers={"Content-Type":"text/html;charset=utf-8"},text=text,
        content=text.encode("utf-8"))


def fake_session(result=None,exception=None):
    session=MagicMock()
    session.headers={}
    if exception:
        session.get.side_effect=exception
    else:
        session.get.return_value=result or response()
    return session


class PublicSiteFetchResilienceTests(unittest.TestCase):
    def setUp(self):
        _PLAIN_HEADERS_HOSTS.clear()

    def tearDown(self):
        _PLAIN_HEADERS_HOSTS.clear()

    def test_remote_disconnect_falls_back_to_plain_http_once_same_url(self):
        original=fake_session(exception=requests.exceptions.ConnectionError(
            "('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))"))
        plain=fake_session(result=response())
        with patch("utils.fetch.requests.Session",side_effect=[original,plain]) as sessions:
            result=fetch_html(PAGE)
        self.assertTrue(result["success"])
        self.assertEqual(result["status_code"],200)
        self.assertEqual(sessions.call_count,2)
        original.get.assert_called_once_with(PAGE,timeout=20,allow_redirects=True)
        plain.get.assert_called_once_with(PAGE,timeout=20,allow_redirects=True)
        self.assertIn("fixture.example.org",_PLAIN_HEADERS_HOSTS)

    def test_subsequent_page_uses_plain_headers_without_double_fetch(self):
        _PLAIN_HEADERS_HOSTS.add("fixture.example.org")
        plain=fake_session(result=response())
        with patch("utils.fetch.requests.Session",return_value=plain) as sessions:
            result=fetch_html(PAGE)
        self.assertTrue(result["success"])
        sessions.assert_called_once()
        self.assertNotIn("User-Agent",plain.headers)
        plain.get.assert_called_once()

    def test_403_can_use_only_real_browser_result_not_fabricated_content(self):
        blocked=fake_session(result=response(status=403,text="Forbidden"))
        verified={"success":True,"html":"<html><body>Real public law office</body></html>",
                  "status_code":200,"final_url":PAGE,"error":""}
        with patch("utils.fetch.requests.Session",return_value=blocked),patch(
             "utils.fetch._fetch_html_from_browser",return_value=verified) as browser:
            result=fetch_html(PAGE)
        self.assertTrue(result["success"])
        self.assertEqual(result["html"],verified["html"])
        browser.assert_called_once_with(PAGE,20)

    def test_403_remains_failure_when_browser_cannot_read_public_content(self):
        blocked=fake_session(result=response(status=403,text="Forbidden"))
        with patch("utils.fetch.requests.Session",return_value=blocked),patch(
             "utils.fetch._fetch_html_from_browser",return_value=None):
            result=fetch_html(PAGE)
        self.assertFalse(result["success"])
        self.assertEqual(result["status_code"],403)

    def test_empty_202_is_not_accepted_as_real_source(self):
        pending=fake_session(result=response(status=202,text="<html>wait</html>"))
        with patch("utils.fetch.requests.Session",return_value=pending),patch(
             "utils.fetch._fetch_html_from_browser",return_value=None):
            result=fetch_html(PAGE)
        self.assertFalse(result["success"])
        self.assertIn("HTML",result["error"])

    def test_dns_error_does_not_trigger_unrelated_browser_or_repeat_requests(self):
        bad=fake_session(exception=requests.exceptions.ConnectionError(
            "NameResolutionError"))
        with patch("utils.fetch.requests.Session",return_value=bad) as sessions,patch(
             "utils.fetch._fetch_html_from_browser") as browser:
            result=fetch_html(PAGE)
        self.assertFalse(result["success"])
        sessions.assert_called_once()
        browser.assert_not_called()

    def test_browser_fallback_is_disabled_outside_explicit_private_worker(self):
        with patch.dict(os.environ,{"KAURIVO_BROWSER_SOURCE_FALLBACK":"0"}):
            self.assertIsNone(_fetch_html_from_browser(PAGE))

    def test_worker_enables_bounded_browser_fallback_after_chromium_setup(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[3]
        workflow=(root/".github/workflows/kaurivo-demo-worker.yml").read_text()
        self.assertIn('KAURIVO_BROWSER_SOURCE_FALLBACK: "1"',workflow)
        self.assertIn("python -m playwright install --with-deps chromium",workflow)
        fetch=(root/"website-builder-agent/website-builder-agent/utils/fetch.py").read_text()
        self.assertIn("status_code == 403",fetch)
        self.assertIn("status_code == 202",fetch)
        self.assertIn("wait_until=\"domcontentloaded\"",fetch)


if __name__=="__main__":
    unittest.main()
