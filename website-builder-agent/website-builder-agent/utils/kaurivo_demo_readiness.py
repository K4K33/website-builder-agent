"""Zero-AI check: does the original site hold enough material for a demo?

Run BEFORE any model call. A job whose source is unreachable, private or thin
used to spend free AI requests on research and then stop at
"source_research_incomplete" / "primary offering unverified" (12 of 33 jobs
on 20.11.2026). This module only fetches public HTML pages (no assets, forms,
logins or contacts stored) and counts what a truthful redesign needs:

* reachable public HTML, following at most 4 redirects on validated hosts
* distinct content photos (logos, icons, SVGs and tracking pixels excluded)
* visible words describing the business
* a contact route (tel:/mailto:/phone or e-mail pattern) - reported, not required

Verdicts: ``ready``, ``thin``, ``unreachable``, ``restricted`` and
``needs_browser`` (a script-rendered shell whose HTML says little; never
blocked here, the browser-based research decides). Only ``thin``,
``unreachable`` and ``restricted`` stop a build. Thresholds are deliberately
low: the gate removes hopeless sources, it never judges design quality.
"""
from __future__ import annotations

import ipaddress
import re
import socket
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup

USER_AGENT = "KaurivoDemoReadiness/1.0 (public page check before demo research)"
MAX_REDIRECTS = 4
MAX_PAGES = 6
MAX_HTML_BYTES = 1_500_000
MIN_CONTENT_IMAGES = 3
MIN_WORDS = 200
# Photo-rich, text-light sites are typical Kaurivo prospects (Maalaus Valo
# 20.11.2026: 10 own photos, 192 words). Plenty of own photos compensates
# for sparse copy; a truly empty page still stops.
PHOTO_RICH_IMAGES = 6
PHOTO_RICH_MIN_WORDS = 120
SHELL_MAX_WORDS = 60

_PRIORITY_LINK = re.compile(
    r"palvel|tuott|tuote|meist|yritys|yhtey|referen|galleri|kohtee|projekt|"
    r"hinnast|menu|ruokalist|tjänst|produkt|om-oss|kontakt|services?|about|"
    r"contact|gallery|portfolio|work|projects?|pricing", re.I)
_NOT_PHOTO = re.compile(
    r"logo|icon|favicon|sprite|flag|badge|avatar|pixel|spacer|blank|"
    r"placeholder|loader|arrow|social|facebook|instagram|linkedin|twitter|"
    r"whatsapp|youtube|tiktok|payment|visa|mastercard|klarna|cookie", re.I)
_PHONE = re.compile(r"(?:\+358|\b0)\s?\d{1,3}[\s-]?\d{2,4}[\s-]?\d{2,4}(?:[\s-]?\d{1,4})?\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]{2,}\b")
_YEAR = re.compile(r"(?:©|&copy;|copyright)\s*(?:\d{4}\s*[-–]\s*)?((?:19|20)\d{2})", re.I)
_SKIP_EXT = re.compile(r"\.(?:pdf|jpe?g|png|gif|webp|svg|zip|docx?|xlsx?|mp4|mp3)$", re.I)


def safe_url(url: str, resolve=socket.getaddrinfo) -> str:
    """Return the URL if it is public HTTPS on a globally routable host."""
    if not isinstance(url, str) or len(url) > 1500:
        return ""
    try:
        parsed = urlsplit(url.strip())
        if parsed.scheme != "https" or not parsed.hostname:
            return ""
        if parsed.username or parsed.password or parsed.port not in (None, 443):
            return ""
        host = parsed.hostname.lower().rstrip(".")
        if ("." not in host or len(host) > 200 or
                host.endswith((".local", ".internal", ".localhost", ".test")) or
                any(ch in host for ch in "\\%@")):
            return ""
        addresses = resolve(host, 443, type=socket.SOCK_STREAM)
        if not addresses:
            return ""
        for address in addresses:
            if not ipaddress.ip_address(address[4][0]).is_global:
                return ""
        return parsed._replace(fragment="").geturl()
    except (ValueError, IndexError, OSError, TypeError):
        return ""


def _site_key(host: str) -> str:
    host = (host or "").lower().rstrip(".")
    return host[4:] if host.startswith("www.") else host


def fetch_html(url: str, *, get=requests.get, resolve=socket.getaddrinfo):
    """GET one public HTML page, following validated redirects only.

    Returns (final_url, html) or (status_code_string, "") on failure.
    """
    current = safe_url(url, resolve)
    if not current:
        return "unsafe_url", ""
    for _ in range(MAX_REDIRECTS + 1):
        try:
            with get(current, headers={"User-Agent": USER_AGENT, "Accept": "text/html"},
                     timeout=(5, 12), stream=True, allow_redirects=False) as response:
                if response.status_code in (301, 302, 303, 307, 308):
                    location = response.headers.get("location", "")
                    nxt = urljoin(current, location)
                    if nxt.startswith("http://"):
                        nxt = "https://" + nxt[len("http://"):]
                    current = safe_url(nxt, resolve)
                    if not current:
                        return "unsafe_redirect", ""
                    continue
                if response.status_code != 200:
                    return "http_" + str(response.status_code), ""
                kind = response.headers.get("content-type", "").lower()
                if "html" not in kind:
                    return "non_html", ""
                body = b""
                for chunk in response.iter_content(65536):
                    body += chunk
                    if len(body) > MAX_HTML_BYTES:
                        break
                encoding = response.encoding or "utf-8"
                return current, body.decode(encoding, errors="replace")
        except requests.RequestException:
            return "unavailable", ""
    return "too_many_redirects", ""


def _photo_urls(soup: BeautifulSoup, base: str) -> set[str]:
    found = set()
    for img in soup.find_all("img"):
        candidates = [img.get("src"), img.get("data-src"), img.get("data-lazy-src")]
        srcset = img.get("srcset") or img.get("data-srcset") or ""
        if srcset:
            candidates.append(srcset.split(",")[-1].strip().split(" ")[0])
        width, height = img.get("width"), img.get("height")
        try:
            if width and height and int(width) < 80 and int(height) < 80:
                continue
        except (TypeError, ValueError):
            pass
        alt_and_class = " ".join([str(img.get("alt") or ""), " ".join(img.get("class") or [])])
        for value in candidates:
            if not value or value.startswith("data:"):
                continue
            full = urljoin(base, value.strip())
            path = urlsplit(full).path.lower()
            if path.endswith(".svg") or _NOT_PHOTO.search(path) or _NOT_PHOTO.search(alt_and_class):
                continue
            found.add(full.split("?")[0])
            break
    for tag in soup.select("[style*='background']"):
        for match in re.findall(r"url\(['\"]?([^'\")]+)", tag.get("style", "")):
            full = urljoin(base, match)
            path = urlsplit(full).path.lower()
            if not path.endswith(".svg") and not _NOT_PHOTO.search(path):
                found.add(full.split("?")[0])
    og = soup.find("meta", attrs={"property": "og:image"})
    if og and og.get("content") and not _NOT_PHOTO.search(og["content"]):
        found.add(urljoin(base, og["content"]).split("?")[0])
    return found


def _visible_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "noscript", "template", "svg"]):
        tag.decompose()
    return " ".join(soup.get_text(" ", strip=True).split())


def _internal_links(soup: BeautifulSoup, base: str) -> list[str]:
    key = _site_key(urlsplit(base).hostname or "")
    preferred, other = [], []
    for anchor in soup.find_all("a", href=True):
        href = urljoin(base, anchor["href"]).split("#")[0]
        parts = urlsplit(href)
        if parts.scheme not in ("https", "http") or _site_key(parts.hostname or "") != key:
            continue
        if _SKIP_EXT.search(parts.path) or parts.path in ("", "/"):
            continue
        href = "https://" + href.split("://", 1)[1]
        label = anchor.get_text(" ", strip=True) + " " + parts.path
        (preferred if _PRIORITY_LINK.search(label) else other).append(href)
    seen, ordered = set(), []
    for href in preferred + other:
        if href not in seen:
            seen.add(href)
            ordered.append(href)
    return ordered


def assess_pages(pages: list[tuple[str, str]]) -> dict:
    """Pure scoring of already-fetched (url, html) pages. No network."""
    from utils.kaurivo_site_audit import is_restricted_homepage
    if not pages:
        return {"verdict": "unreachable", "pages": 0}
    home_url, home_html = pages[0]
    if is_restricted_homepage(home_html):
        return {"verdict": "restricted", "pages": 1}
    photos: set[str] = set()
    words = 0
    phone = email = False
    years: list[int] = []
    viewport = False
    script_count = 0
    for index, (url, html) in enumerate(pages):
        soup = BeautifulSoup(html, "html.parser")
        if index == 0:
            viewport = bool(soup.find("meta", attrs={"name": "viewport"}))
            script_count = len(soup.find_all("script"))
        phone = phone or bool(soup.select("a[href^='tel:']"))
        email = email or bool(soup.select("a[href^='mailto:']"))
        photos |= _photo_urls(soup, url)
        text = _visible_text(soup)
        words += len(text.split())
        phone = phone or bool(_PHONE.search(text))
        email = email or bool(_EMAIL.search(text))
        years += [int(y) for y in _YEAR.findall(html)]
    result = {
        "pages": len(pages),
        "content_images": len(photos),
        "words": words,
        "contact_phone": phone,
        "contact_email": email,
        "viewport": viewport,
        "copyright_year": max(years) if years else None,
    }
    home_words = len(_visible_text(BeautifulSoup(home_html, "html.parser")).split())
    if home_words <= SHELL_MAX_WORDS and len(pages) == 1 and script_count >= 3:
        result["verdict"] = "needs_browser"
    elif len(photos) < MIN_CONTENT_IMAGES or words < PHOTO_RICH_MIN_WORDS:
        result["verdict"] = "thin"
    elif words < MIN_WORDS and len(photos) < PHOTO_RICH_IMAGES:
        result["verdict"] = "thin"
    else:
        result["verdict"] = "ready"
    return result


def assess_site(url: str, *, get=requests.get, resolve=socket.getaddrinfo) -> dict:
    final, html = fetch_html(url, get=get, resolve=resolve)
    if not html:
        return {"verdict": "unreachable", "pages": 0, "fetch_status": final}
    pages = [(final, html)]
    links = _internal_links(BeautifulSoup(html, "html.parser"), final)
    for link in links[: MAX_PAGES * 2]:
        if len(pages) >= MAX_PAGES:
            break
        page_url, page_html = fetch_html(link, get=get, resolve=resolve)
        if page_html and _site_key(urlsplit(page_url).hostname or "") == _site_key(urlsplit(final).hostname or ""):
            pages.append((page_url, page_html))
    result = assess_pages(pages)
    result["fetch_status"] = "ok"
    return result


BLOCKING = {"thin", "unreachable", "restricted"}


def blocking_reason(result: dict) -> str:
    """Short Finnish admin message for a blocking verdict ('' when allowed)."""
    verdict = result.get("verdict")
    if verdict not in BLOCKING:
        return ""
    if verdict == "unreachable":
        return "Alkuperäinen sivu ei vastannut julkisena HTML-sivuna (" + str(result.get("fetch_status", "")) + ")"
    if verdict == "restricted":
        return "Alkuperäinen sivu on yksityinen tai kirjautumisen takana"
    return ("Lähdesivulla liian vähän aineistoa demolle: "
            f"{result.get('content_images', 0)} omaa kuvaa ja {result.get('words', 0)} sanaa "
            f"{result.get('pages', 0)} sivulla (vaaditaan väh. {MIN_CONTENT_IMAGES} kuvaa ja "
            f"{MIN_WORDS} sanaa, tai {PHOTO_RICH_IMAGES} kuvaa ja {PHOTO_RICH_MIN_WORDS} sanaa)")


def main(argv=None) -> int:
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url")
    args = parser.parse_args(argv)
    print(json.dumps(assess_site(args.url), ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
