"""Browser tab and small-detail contract for every new Kaurivo client demo.

A good hero screenshot does not make a finished business website. Title, icon,
real page language and description, correct customer identity, and genuine
navigation are required on every route. A branded favicon is NEVER invented
to make a fake identity look professional. An explicitly neutral design-
preview icon is allowed only with a visible "not official site" disclaimer,
and cannot be mistaken for an approved customer logo.
"""
from __future__ import annotations

from bs4 import BeautifulSoup

BAD_TITLES = ("etusivu", "index", "home", "untitled", "kaurivo demo",
              "demo", "website", "test", "preview")


def audit_browser_identity(pages: dict[str, str], business_name: str = "") -> dict:
    issues = []
    valid_icons: set[str] = set()
    if not pages:
        return {"pass": False, "issues": ["No rendered website pages exist."]}
    if not isinstance(business_name, str):
        business_name = ""
    for route, html in sorted(pages.items()):
        soup = BeautifulSoup(html, "html.parser")
        head = soup.head
        title = " ".join(soup.title.get_text(" ", strip=True).split()) if soup.title else ""
        if not title or title.casefold() in BAD_TITLES or len(title) < 20 or len(title) > 100:
            issues.append(f"{route}: Browser tab title missing, generic, or poorly sized.")
        if any(x in title.casefold() for x in ("kaurivon suunnitteludemo",
                                              "kaurivo demo", "laatutarkistus",
                                              "technical preview")):
            issues.append(f"{route}: Browser tab title displays internal agency/debug terms.")
        if business_name and business_name.casefold() not in title.casefold():
            issues.append(f"{route}: Browser tab title does not show the verified company name.")
        lang = (soup.html.get("lang") or "").strip() if soup.html else ""
        if lang not in ("fi", "sv", "en"):
            issues.append(f"{route}: Real page language is missing or unverified.")
        meta = head.select_one('meta[name="description"]') if head else None
        description = str(meta.get("content") or "").strip() if meta else ""
        if not 35 <= len(description) <= 200:
            issues.append(f"{route}: Missing useful unique browser/search description.")
        icons = head.select('link[rel~="icon"][href]') if head else []
        if not icons:
            issues.append(f"{route}: Browser favicon is missing.")
        else:
            for icon in icons:
                href = str(icon.get("href") or "").strip()
                if not href or href.startswith(("javascript:", "http://", "//")):
                    issues.append(f"{route}: Browser favicon URL is empty or unsafe.")
                if icon.has_attr("data-demo-neutral-icon") and not soup.select_one(".demo-band"):
                    issues.append(f"{route}: Neutral temporary favicon lacks visible independent-demo notice.")
                if href:
                    valid_icons.add(href)
        if not soup.select_one("header") or not soup.select_one("nav"):
            issues.append(f"{route}: The browser view lacks the essential site header/navigation.")
    # On a multi-page site, all routes should use the SAME brand icon/path,
    # except for normal "../" prefixes; avoid accidental tab-icon drift.
    canonical_icons = {v.lstrip("../") for v in valid_icons}
    if len(canonical_icons) > 1:
        issues.append("Different pages have inconsistent tab/favicon identity.")
    return {"pass": not issues, "issues": issues,
            "pages_checked": len(pages),
            "notes": "Static checks only: favicon rendering and title clipping must also be checked in a real browser on phone and desktop."}
