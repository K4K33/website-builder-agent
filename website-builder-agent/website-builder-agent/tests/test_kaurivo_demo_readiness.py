"""Zero-AI source readiness gate before demo research."""
import socket
import unittest
from pathlib import Path

from utils import kaurivo_demo_readiness as r

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = lambda host, port, type=None: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))]
PRIVATE = lambda host, port, type=None: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]

WORDS = " ".join(["Teemme kattoremontit ja peltikatot omakotitaloihin Uudellamaalla."] * 40)
RICH = f"""<html><head><meta name=viewport content=width=device-width><title>Katto Oy</title></head>
<body><img src=/img/logo.png alt=logo><img src=/img/katto1.jpg><img src=/img/katto2.jpg>
<img src=/img/tyomaa.jpg width=1200 height=800><img src=/img/icon-phone.png width=24 height=24>
<a href=/palvelut>Palvelut</a><a href="tel:+358401234567">Soita</a><p>{WORDS}</p>
<footer>© 2014 Katto Oy</footer></body></html>"""
THIN = "<html><body><h1>Katto Oy</h1><p>Tervetuloa! Sivut uudistuvat.</p><img src=/a.jpg></body></html>"
SHELL = "<html><body><div id=root></div>" + "<script src=/a.js></script>" * 4 + "</body></html>"


class FakeResponse:
    def __init__(self, status, body="", location="", kind="text/html; charset=utf-8"):
        self.status_code, self._body = status, body.encode()
        self.headers = {"location": location, "content-type": kind}
        self.encoding = "utf-8"
    def iter_content(self, size=65536, chunk_size=None):
        yield self._body
    def __enter__(self): return self
    def __exit__(self, *a): return False


def fake_get(routes):
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        assert kwargs.get("allow_redirects") is False
        return routes.get(url, FakeResponse(404))
    get.calls = calls
    return get


class ReadinessTests(unittest.TestCase):
    def test_redirects_are_followed_and_rich_site_is_ready(self):
        get = fake_get({
            "https://katto.fi": FakeResponse(301, location="http://www.katto.fi/"),
            "https://www.katto.fi/": FakeResponse(200, RICH),
            "https://www.katto.fi/palvelut": FakeResponse(200, RICH),
        })
        result = r.assess_site("https://katto.fi", get=get, resolve=PUBLIC)
        self.assertEqual(result["verdict"], "ready")
        self.assertEqual(result["content_images"], 3)  # logo + icon excluded
        self.assertTrue(result["contact_phone"])
        self.assertEqual(result["copyright_year"], 2014)
        self.assertEqual(r.blocking_reason(result), "")

    def test_thin_site_blocks_with_reason(self):
        get = fake_get({"https://ohut.fi": FakeResponse(200, THIN)})
        result = r.assess_site("https://ohut.fi", get=get, resolve=PUBLIC)
        self.assertEqual(result["verdict"], "thin")
        self.assertIn("liian vähän aineistoa", r.blocking_reason(result))

    def test_script_shell_is_not_blocked(self):
        get = fake_get({"https://spa.fi": FakeResponse(200, SHELL)})
        result = r.assess_site("https://spa.fi", get=get, resolve=PUBLIC)
        self.assertEqual(result["verdict"], "needs_browser")
        self.assertEqual(r.blocking_reason(result), "")

    def test_private_address_and_redirect_to_private_are_refused(self):
        get = fake_get({})
        self.assertEqual(r.assess_site("https://intra.fi", get=get, resolve=PRIVATE)["verdict"], "unreachable")
        self.assertEqual(get.calls, [])
        resolver = lambda host, port, type=None: (PRIVATE if host == "evil.fi" else PUBLIC)(host, port, type)
        get = fake_get({"https://ok.fi": FakeResponse(302, location="https://evil.fi/")})
        result = r.assess_site("https://ok.fi", get=get, resolve=resolver)
        self.assertEqual(result["fetch_status"], "unsafe_redirect")
        self.assertNotIn("https://evil.fi/", get.calls)

    def test_unreachable_blocks(self):
        result = r.assess_site("https://down.fi", get=fake_get({}), resolve=PUBLIC)
        self.assertEqual(result["verdict"], "unreachable")
        self.assertTrue(r.blocking_reason(result))

    def test_worker_runs_gate_before_research_ai(self):
        source = (ROOT / "scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
        gate = source.index('raise HoldError("source_material_insufficient", reason)')
        research = source.index('run_cli(["research",agent_slug],stage_log,ai_deadline)')
        self.assertLess(gate, research)


if __name__ == "__main__":
    unittest.main()


class SiteAuditRedirectTests(unittest.TestCase):
    """Daily screening used to mark every www/https redirect as unchecked."""

    def test_same_site_redirect_is_followed_cross_site_is_not(self):
        from utils.kaurivo_site_audit import inspect_site
        class Resp(FakeResponse):
            def __init__(self, *a, **k):
                super().__init__(*a, **k)
                self.headers["Location"] = self.headers["location"]
                self.headers["Content-Type"] = self.headers["content-type"]
            def close(self): pass
        html = "<html><head><title>T</title></head><body><h1>Katto</h1></body></html>"
        get = fake_get({"https://katto.fi/": Resp(301, location="https://www.katto.fi/fi/"),
                        "https://www.katto.fi/fi/": Resp(200, html)})
        self.assertEqual(inspect_site("https://katto.fi", get=get, resolve=PUBLIC)["status"], "html_checked")
        self.assertEqual(len(get.calls), 2)
        get = fake_get({"https://katto.fi/": Resp(302, location="https://muu-yritys.fi/")})
        self.assertEqual(inspect_site("https://katto.fi", get=get, resolve=PUBLIC)["status"],
                         "redirect_not_followed")
        self.assertEqual(get.calls, ["https://katto.fi/"])
