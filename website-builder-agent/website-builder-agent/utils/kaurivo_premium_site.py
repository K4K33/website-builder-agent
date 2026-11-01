"""Free, offline Kaurivo website preflight. No external requests or fake scores.

Structural checks do NOT replace Lighthouse, browser/device testing, WCAG
audits, consent tests, real submissions, CMS tests or customer acceptance.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import unquote, urlsplit
from bs4 import BeautifulSoup


def inspect_site_file(html_path, *, site_root=None, production=False):
    """Inspect a candidate page and its local references; never publish it.

    production=True blocks a noindex preview. Everything else is the same.
    Only already-existing local assets may be inspected. No network access.
    """
    path = Path(html_path).resolve()
    root = Path(site_root).resolve() if site_root else path.parent
    errors, warnings = [], []
    if not path.is_file() or not path.is_relative_to(root):
        return {"pass": False, "errors": ["HTML file missing or outside site root."],
                "warnings": [], "measured": {}, "limitations": ["No browser tests were run."]}
    if path.stat().st_size > 2_000_000:
        errors.append("HTML exceeds 2 MB; review payload.")
    html = path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")
    if not html.lstrip().lower().startswith("<!doctype html>"):
        errors.append("Missing HTML5 doctype.")
    if not soup.html or not str(soup.html.get("lang", "")).strip():
        errors.append("Missing document language.")
    if not soup.title or len(soup.title.get_text(" ", strip=True)) < 6:
        errors.append("Missing meaningful page title.")
    description = soup.find("meta", attrs={"name": lambda s: isinstance(s, str) and s.lower() == "description"})
    if not description or len(str(description.get("content", "")).strip()) < 30:
        errors.append("Missing meaningful meta description.")
    if not soup.find("meta", attrs={"name": "viewport"}):
        errors.append("Missing mobile viewport.")
    if len(soup.find_all("main")) != 1:
        errors.append("Exactly one main landmark required.")
    if len(soup.find_all("h1")) != 1:
        errors.append("Exactly one H1 required.")
    if not soup.find("nav"):
        warnings.append("Navigation landmark missing; confirm this is intentional.")
    ids = [str(item.get("id")) for item in soup.find_all(id=True)]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate HTML id values.")
    id_set = set(ids)
    robots = soup.find("meta", attrs={"name": "robots"})
    if production and robots and "noindex" in str(robots.get("content", "")).lower():
        errors.append("Production page is noindex.")
    forms = soup.find_all("form")
    for form in forms:
        if not form.get("action") and not form.get("id"):
            warnings.append("Form has neither action nor id; verify submission handling.")
        for field in form.find_all(["input", "select", "textarea"]):
            if field.name == "input" and field.get("type", "").lower() in {"hidden", "submit", "button", "checkbox"}:
                continue
            fid = field.get("id")
            wrapped = field.find_parent("label")
            if not wrapped and not (fid and soup.find("label", attrs={"for": fid})) and not field.get("aria-label"):
                errors.append("Unlabelled form field.")
    for img in soup.find_all("img"):
        if not img.has_attr("alt"):
            errors.append("Image without alt attribute.")
        if not img.get("width") or not img.get("height"):
            warnings.append("Image dimensions not declared; check for layout shift.")
    local_css = []
    checked = set()
    for element, attr in [(a, "href") for a in soup.find_all("a", href=True)] + [
        (a, "src") for a in soup.find_all(["img", "script", "source"], src=True)
    ] + [(a, "href") for a in soup.find_all("link", href=True)]:
        raw = str(element.get(attr, "")).strip()
        if not raw or raw.startswith(("data:", "mailto:", "tel:", "sms:")):
            continue
        if raw.lower().startswith(("javascript:", "vbscript:")):
            errors.append("Unsafe script URL.")
            continue
        parsed = urlsplit(raw)
        if parsed.scheme or parsed.netloc:
            if parsed.scheme == "http":
                warnings.append("Insecure HTTP external asset/link: " + parsed.netloc[:80])
            continue
        if parsed.path.startswith("/"):
            # File-style root-relative URLs depend on deployment base; test in browser.
            warnings.append("Root-relative URL needs deployment-base validation.")
            continue
        decoded = unquote(parsed.path)
        if not decoded:
            if parsed.fragment and parsed.fragment not in id_set:
                errors.append("Broken same-page anchor: #" + parsed.fragment[:60])
            continue
        target = (path.parent / decoded).resolve()
        if not target.is_relative_to(root):
            errors.append("Local reference escapes site root.")
            continue
        if (str(target), attr) not in checked:
            checked.add((str(target), attr))
            if not target.exists():
                errors.append("Missing local reference: " + decoded[:120])
        if element.name == "link" and "stylesheet" in element.get("rel", []) and target.is_file():
            local_css.append(target)
    css = "\n".join([tag.get_text() for tag in soup.find_all("style")])
    for file in set(local_css):
        if file.stat().st_size < 1_000_000:
            css += "\n" + file.read_text(encoding="utf-8", errors="replace")
    if "prefers-reduced-motion" not in css:
        warnings.append("Reduced-motion CSS fallback not detected; manually verify interactions.")
    if "@media" not in css and "clamp(" not in css:
        warnings.append("No obvious responsive CSS rules found; browser testing required.")
    if not forms:
        # Contact via verified mailto/tel or links can also be a legitimate conversion.
        contact_links = [a.get("href", "") for a in soup.find_all("a", href=True)]
        if not any(s.startswith(("mailto:", "tel:")) or "contact" in s or "yhteys" in s
                   for s in contact_links):
            warnings.append("No visible contact/conversion link detected.")
    return {
        "pass": not errors,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "measured": {"html_bytes": path.stat().st_size, "images": len(soup.find_all("img")),
                     "forms": len(forms), "local_references_checked": len(checked)},
        "limitations": [
            "No Lighthouse/Core Web Vitals or real-user performance measured.",
            "No actual browser, keyboard, screen-reader or responsive screenshot test.",
            "No live form delivery, consent, legal, security, CMS login or backup tested.",
            "A passing static audit cannot approve publication or customer handover.",
        ],
    }
