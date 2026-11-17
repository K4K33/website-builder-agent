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
            self.assertTrue(any('"suggestedTextColor": "#000000"' in issue
                                for issue in result["issues"]),result["issues"])
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


    def test_private_browser_recovery_fixes_exact_ambiguous_copy_and_rerenders(self):
        from utils.concept_contrast_recovery import repair_browser_contrast
        html = ("<!doctype html><html lang='fi'><head><meta charset='utf-8'>"
                "<meta name='viewport' content='width=device-width,initial-scale=1'>"
                "<title>Test</title><style>body{font:16px Arial;color:#111;background:#fff}"
                "section{padding:60px;background-image:linear-gradient(#eee,#fff)}"
                "</style></head><body><main><h1>Verified brand</h1>"
                "<section><p style='color:#fff'>Verified source copy</p></section>"
                "</main></body></html>")
        with TemporaryDirectory() as temp:
            path = Path(temp) / "index.html"
            path.write_text(html, encoding="utf-8")
            first = inspect_site(path)
            if any("Browser QA unavailable" in x for x in first["issues"]):
                self.skipTest("Chromium unavailable")
            self.assertFalse(first["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in x for x in first["issues"]), first)
            repaired = repair_browser_contrast(html, first["issues"])
            self.assertNotEqual(repaired, html)
            self.assertIn("Verified source copy", repaired)
            self.assertIn("background-image:linear-gradient(#eee,#fff)", repaired)
            path.write_text(repaired, encoding="utf-8")
            second = inspect_site(path)
            self.assertTrue(second["pass"], second["issues"])

    def test_private_browser_recovery_fixes_solid_contrast_with_real_measurement(self):
        from utils.concept_contrast_recovery import repair_browser_contrast
        html = ("<!doctype html><html><head><meta name='viewport' "
                "content='width=device-width,initial-scale=1'><title>Test</title>"
                "</head><body><main><h1 style='background:#fff;color:#bbb'>"
                "Verified brand</h1></main></body></html>")
        with TemporaryDirectory() as temp:
            path = Path(temp) / "index.html"
            path.write_text(html, encoding="utf-8")
            first = inspect_site(path)
            if any("Browser QA unavailable" in x for x in first["issues"]):
                self.skipTest("Chromium unavailable")
            self.assertFalse(first["pass"])
            self.assertTrue(any("contrast failures" in x for x in first["issues"]), first)
            repaired = repair_browser_contrast(html, first["issues"])
            self.assertIn("color:#000000 !important", repaired)
            path.write_text(repaired, encoding="utf-8")
            second = inspect_site(path)
            self.assertTrue(second["pass"], second["issues"])

    def test_contrast_recovery_matches_inline_spacing_and_is_idempotent(self):
        import json
        from utils.concept_contrast_recovery import repair_browser_contrast

        html = "<html><body><main><a>Verified <i aria-hidden='true'></i>copy</a></main></body></html>"
        marker = "mobile: text/background contrast NOT VERIFIABLE; review the real rendered image: "
        evidence = marker + json.dumps([{
            "selector": "body > main:nth-of-type(1) > a:nth-of-type(1)",
            "tag": "A", "text": "Verified copy",
        }])
        repaired = repair_browser_contrast(html, [evidence])
        self.assertIn("opacity:1 !important", repaired)
        self.assertIn('Verified <i aria-hidden="true"></i>copy', repaired)
        self.assertEqual(repair_browser_contrast(repaired, [evidence]), repaired)

    def test_translucent_text_on_a_gradient_gets_a_readable_surface(self):
        from utils.concept_contrast_recovery import repair_browser_contrast

        html = """<!doctype html><html><head><meta name="viewport"
            content="width=device-width,initial-scale=1"><title>Test</title>
            <style>body{font:16px Arial;color:#111;background:#fff}
            main{padding:40px;background-image:linear-gradient(#888,#fff)}
            h1{color:#fff;opacity:.65}</style></head>
            <body><main><h1>Verified <i aria-hidden="true"></i>copy</h1></main></body></html>"""
        with TemporaryDirectory() as temp:
            path = Path(temp) / "index.html"
            path.write_text(html, encoding="utf-8")
            first = inspect_site(path)
            if any("Browser QA unavailable" in item for item in first["issues"]):
                self.skipTest("Chromium unavailable")
            self.assertFalse(first["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in item for item in first["issues"]), first)
            repaired = repair_browser_contrast(html, first["issues"])
            self.assertIn("background-image:linear-gradient(#888,#fff)", repaired)
            path.write_text(repaired, encoding="utf-8")
            second = inspect_site(path)
            self.assertTrue(second["pass"], second["issues"])

    def test_unverified_or_mismatched_browser_evidence_never_changes_copy(self):
        from utils.concept_contrast_recovery import repair_browser_contrast
        import json
        html = "<!doctype html><html><body><main><p>Real company copy</p></main></body></html>"
        marker = "desktop: text/background contrast NOT VERIFIABLE; review the real rendered image: "
        forged = [{"selector": "body > main:nth-of-type(1) > p:nth-of-type(1)",
                   "tag": "P", "text": "Different company's copy"}]
        self.assertEqual(repair_browser_contrast(html, [marker + json.dumps(forged)]), html)
        forged[0]["selector"] = "body > main:nth-of-type(1) > p:nth-of-type(1) > script"
        self.assertEqual(repair_browser_contrast(html, [marker + json.dumps(forged)]), html)



if __name__ == "__main__":
    unittest.main()
