"""Password-protected review-only Kotifixi website.

No CMS, e-mail delivery, DNS updates, tracking, cookies or outgoing API calls.
The Render free instance receives only staging HTML from this branch.
"""
from __future__ import annotations

import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
HTML = ROOT / "index.html"
USERNAME = os.environ.get("PREVIEW_USERNAME", "")
PASSWORD = os.environ.get("PREVIEW_PASSWORD", "")
PORT = int(os.environ.get("PORT", "10000"))
if not USERNAME or len(PASSWORD) < 16:
    raise SystemExit("Set PREVIEW_USERNAME and long PREVIEW_PASSWORD env vars before starting.")
if not HTML.is_file():
    raise SystemExit("Private preview index.html is missing.")

class Handler(BaseHTTPRequestHandler):
    def _headers(self, code, content_type, length=0, extra=()):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(length))
        self.send_header("Cache-Control", "private, no-store, max-age=0")
        self.send_header("X-Robots-Tag", "noindex, nofollow, noarchive")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; style-src 'unsafe-inline'; "
                         "img-src 'self' data:; font-src 'self'; "
                         "base-uri 'none'; object-src 'none'; "
                         "form-action 'none'; frame-ancestors 'none'")
        for key, value in extra:
            self.send_header(key, value)
        self.end_headers()

    def _authorized(self):
        auth = self.headers.get("Authorization", "")
        if not auth.startswith("Basic "):
            return False
        try:
            raw = base64.b64decode(auth[6:].encode("ascii"), validate=True)
            supplied = raw.decode("utf-8")
        except (UnicodeError, ValueError, TypeError):
            return False
        expected = f"{USERNAME}:{PASSWORD}"
        return secrets.compare_digest(supplied, expected)

    def _reply(self, head=False):
        path = urlsplit(self.path).path
        if path == "/_health":
            body = b"ok"
            self._headers(200, "text/plain; charset=utf-8", len(body))
        elif path == "/robots.txt":
            body = b"User-agent: *\nDisallow: /\n"
            self._headers(200, "text/plain; charset=utf-8", len(body))
        elif not self._authorized():
            body = b"Authentication required"
            self._headers(401, "text/plain; charset=utf-8", len(body),
                          (("WWW-Authenticate", 'Basic realm="Kotifixi private preview", charset="UTF-8"'),))
        elif path in ("/", "/index.html"):
            body = HTML.read_bytes()
            self._headers(200, "text/html; charset=utf-8", len(body))
        elif path in ("/palvelut", "/palvelut/", "/yhteys", "/yhteys/"):
            target = "/#palvelut-sivu" if path.startswith("/palvelut") else "/#yhteystiedot-sivu"
            body = b""
            self._headers(302, "text/plain; charset=utf-8", 0, (("Location", target),))
        else:
            body = b"Not found"
            self._headers(404, "text/plain; charset=utf-8", len(body))
        if not head:
            self.wfile.write(body)

    def do_GET(self):
        self._reply()

    def do_HEAD(self):
        self._reply(head=True)

if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Kotifixi private preview: running with authentication required.", flush=True)
    server.serve_forever()
