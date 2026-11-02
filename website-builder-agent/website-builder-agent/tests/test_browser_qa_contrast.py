"""Free browser QA tests for actual measurable contrast and scroll behavior."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.browser_qa import inspect_site


class ContrastAndScrollTests(unittest.TestCase):
    def test_browser_catches_low_contrast_without_external_resources(self):
        with TemporaryDirectory() as temp:
            file = Path(temp) / "index.html"
            file.write_text("""<!doctype html><html lang="fi"><head><title>Test</title>
              <meta name="viewport" content="width=device-width,initial-scale=1"></head>
              <body><main><h1 style="color:#bbbbbb;background-color:#ffffff">
              Tämä teksti on liian vaalea.</h1></main></body></html>""", encoding="utf-8")
            result = inspect_site(file)
            if any("Browser QA unavailable" in issue for issue in result["issues"]):
                self.skipTest("Chromium is not available in this environment.")
            self.assertTrue(any("contrast failures" in issue for issue in result["issues"]),
                            result["issues"])
            self.assertFalse(result["pass"])

    def test_browser_does_not_invent_failures_for_clear_dark_text(self):
        with TemporaryDirectory() as temp:
            file = Path(temp) / "index.html"
            file.write_text("""<!doctype html><html lang="fi"><head><title>Test</title>
              <meta name="viewport" content="width=device-width,initial-scale=1"></head>
              <body style="color:#151515;background-color:#ffffff">
              <main><h1>Readable headline.</h1><p>Readable normal text.</p></main>
              </body></html>""", encoding="utf-8")
            result = inspect_site(file)
            if any("Browser QA unavailable" in issue for issue in result["issues"]):
                self.skipTest("Chromium is not available in this environment.")
            self.assertFalse(any("contrast failures" in issue for issue in result["issues"]),
                             result["issues"])


if __name__ == "__main__":
    unittest.main()
