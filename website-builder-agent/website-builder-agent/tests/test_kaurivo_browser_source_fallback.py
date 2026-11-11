"""Free, offline regression: never invent source when HTTP fails."""
from unittest import TestCase
from unittest.mock import Mock, patch
import requests
from utils.fetch import fetch_html

class SourceFallbackTest(TestCase):
    def test_http_403_uses_real_browser_only_when_browser_verified(self):
        response=Mock(status_code=403,url="https://example.org/",content=b"forbidden")
        response.headers={"Content-Type":"text/html"}
        with patch("utils.fetch.requests.Session") as session, \
             patch("utils.fetch._fetch_html_from_browser") as browser:
            session.return_value.get.return_value=response
            browser.return_value={
              "success":True, "html":"<h1>real page</h1>",
              "final_url":"https://example.org/", "status_code":200,"error":""}
            result=fetch_html("https://example.org/")
            self.assertTrue(result["success"])
            browser.assert_called_once()
            browser.return_value=None
            failed=fetch_html("https://example.org/")
            self.assertFalse(failed["success"])
            self.assertEqual(failed["status_code"],403)

    def test_connection_failure_can_fall_back_to_verified_browser(self):
        with patch("utils.fetch.requests.Session") as session, \
             patch("utils.fetch._fetch_html_from_browser") as browser:
            session.return_value.get.side_effect=requests.exceptions.ConnectionError("blocked")
            browser.return_value={"success":True,"html":"real page",
              "final_url":"https://example.org/","status_code":200,"error":""}
            got=fetch_html("https://example.org/")
            self.assertTrue(got["success"])
            browser.return_value=None
            failed=fetch_html("https://example.org/")
            self.assertFalse(failed["success"])
            self.assertIn("Yhteysvirhe",failed["error"])

    def test_timeout_browser_fallback_does_not_fake_success(self):
        with patch("utils.fetch.requests.Session") as session, \
             patch("utils.fetch._fetch_html_from_browser",return_value=None):
            session.return_value.get.side_effect=requests.exceptions.Timeout("timed out")
            result=fetch_html("https://example.org/")
            self.assertFalse(result["success"])
            self.assertIn("Timeout",result["error"])
