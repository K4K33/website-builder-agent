"""Business-first presentation QA: research facts are never customer copy.

No LLM, browsing, paid credits, invented ratings or inferred brand permissions.
Definitive violations fail the static build. Subjective editorial/layout choices
are openly marked pending independent screenshot + source comparison.
"""
from __future__ import annotations

import re
import unicodedata
import hashlib
import json

from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest


# Unlike explanatory copy on an agency portfolio case study, these phrases
# are in a CUSTOMER'S own main content: they narrate evidence collection.
RESEARCH_NARRATION = (
    re.compile(
        r"\balkuperäis(?:en|ellä|eltä|elle|et|iä)\s+"
        r"(?:verkkosivuston|verkkosivun|sivuston|sivun|sivuilta|hinnaston|hinnastosivun)"
        r"\b", re.I
    ),
    re.compile(
        r"\b(?:yrityksen|asiakkaan)\s+(?:omalla|omilla|omilta|alkuperäisellä|alkuperäisiltä)"
        r"\s+(?:verkkosivustolla|verkkosivuilta|verkkosivuilla|sivulla|sivuilta|yhteystietosivuilta)\b",
        re.I
    ),
    re.compile(
        r"\b(?:tiedot|hinnat|kuvat|lainaukset|palvelut)\s+"
        r"(?:on|ovat)\s+(?:siirretty|poimittu|kerätty|kopioitu|otettu)\s+"
        r"(?:alkuperäis(?:eltä|estä)|yrityksen)\b", re.I
    ),
    re.compile(
        r"\b(?:\d+|yksi|kaksi|kolme|neljä|viisi|kuusi|seitsemän|kahdeksan|yhdeksän|kymmenen)\s+"
        r"(?:työtä|hintariviä|palvelua|arvostelua|kuvaa)\s+"
        r"(?:alkuperäis(?:eltä|estä)|lähdesivulta|lähdesivustolta)\b", re.I
    ),
    re.compile(r"\b(?:päiväämätön|vanhentunut)\s+.{0,65}"
               r"(?:ilmoitus|tiedote|lähdetieto)\b", re.I),
    re.compile(
        r"\b(?:source[- ](?:inventory|snapshot|page|evidence)|"
        r"content parity|research notes?|source[- ]to[- ]destination)\b", re.I
    ),
    re.compile(
        r"\b(?:according to (?:the|their|our) (?:old|original|source) website|"
        r"(?:taken|copied|transferred) from (?:the|their) original website|"
        r"\d+ (?:services|price rows) from (?:the|their) original website)\b", re.I
    ),
)

INTERNAL_ROLE = re.compile(
    r"(?:^|[-_ ])(?:research[-_ ]?(?:note|evidence)|qa[-_ ]?(?:note|result)|"
    r"source[-_ ]?(?:note|provenance|evidence)|internal[-_ ]?(?:note|report))"
    r"(?:$|[-_ ])", re.I
)
GENERIC_HEADINGS = {
    "laadukasta palvelua", "luotettavaa palvelua", "ammattitaitoista palvelua",
    "tule käymään", "tutustu palveluihimme", "takaisin arkeen",
    "käsityötä läheltä", "korjauta tuttu tavara", "palvelumme",
    "welcome", "our services", "quality you can trust", "get in touch",
}
BRAND_MARK_CLASS = re.compile(
    r"(?:monogram|wordmark-seal|logo-initial|brand-initial|initial-logo|"
    r"brand-letter|lettermark|emblem-letter|fake-logo)", re.I
)
MAP_DECORATION_CLASS = re.compile(
    r"(?:map-drawing|fake-map|pseudo-map|illustrative-map|map-sketch|map-illustration)",
    re.I
)


def normalized(text: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", text).casefold().split())


def _record_valid(record: object, pages: dict[str, str], research: dict) -> bool:
    if not isinstance(record, dict):
        return False
    if not (
        record.get("approved") is True
        and record.get("reviewer_kind") == "client"
        and str(record.get("reviewer") or "").strip()
        and str(record.get("checked_at") or "").strip()
        and record.get("build_sha256") == site_digest(pages)
    ):
        return False
    inventory = research.get("source_inventory") or {}
    if inventory.get("pages"):
        return record.get("source_sha256") == source_inventory_sha256(inventory)
    return bool(record.get("source_evidence"))


def audit_client_facing_integrity(
    rendered_pages: dict[str, str], research: dict | None = None,
    *, stage: str = "internal_demo",
) -> dict:
    """Return robust blockers and honest editorial reviews for all pages.

    A thin, clearly labelled *demo-only* banner OUTSIDE <main> is allowed for
    internal concept links; never treat it as a substitute for customer copy.
    In a production release even that banner must be removed.
    """
    if stage not in ("internal_demo", "client_release"):
        raise ValueError("Unknown review stage")
    research = research or {}
    blocked: list[dict] = []
    pending: list[dict] = []
    inspected = []
    generic: list[dict] = []
    for route, html in rendered_pages.items():
        soup = BeautifulSoup(html, "html.parser")
        main = soup.find("main")
        if main is None:
            # Existing structural validator diagnoses missing <main>.
            continue
        main_copy = BeautifulSoup(str(main), "html.parser")
        for tag in main_copy.select("script,style,noscript,template"):
            tag.decompose()
        text = " ".join(main_copy.get_text(" ", strip=True).split())
        for pattern in RESEARCH_NARRATION:
            match = pattern.search(text)
            if match:
                blocked.append({
                    "category": "research_leak",
                    "route": route,
                    "excerpt": text[max(0, match.start()-45):match.end()+80],
                })
        for node in main.select("*"):
            classes = " ".join(node.get("class") or [])
            marker = " ".join((classes, str(node.get("data-role") or "")))
            if INTERNAL_ROLE.search(marker):
                blocked.append({
                    "category": "visible_internal_note",
                    "route": route,
                    "element": node.name,
                    "marker": marker[:120],
                })
                break
        for heading in main.select("h1,h2,h3"):
            label = normalized(heading.get_text(" ", strip=True))
            if label in GENERIC_HEADINGS:
                generic.append({"route": route, "heading": label})

        # Don't allow a generated icon of a single initial to masquerade as
        # the company's approved logo. Client-signed source/build evidence is
        # required; a research model's design plan is not approval.
        header = soup.find("header")
        if header:
            for el in header.find_all(["span", "div", "b", "strong", "svg"], recursive=True):
                cls = " ".join(el.get("class") or [])
                if not BRAND_MARK_CLASS.search(cls):
                    continue
                label = el.get_text(" ", strip=True)
                if el.name == "svg" or re.fullmatch(r"[\wÅÄÖåäö]{1,3}\.?|[A-Z]{1,3}\.", label):
                    if not _record_valid(
                        research.get("approved_new_brand_mark"), rendered_pages, research
                    ):
                        blocked.append({
                            "category": "unsourced_brand_mark", "route": route,
                            "marker": cls[:150], "text": label[:30],
                        })
                    break

        # A pseudo-street-map is not geospatial information even if a nearby
        # button links to Google Maps. Require a real georeferenced map, an
        # authentic place photo or a simple address instead.
        map_art = [
            node for node in main.select("svg,canvas")
            if MAP_DECORATION_CLASS.search(" ".join(node.get("class") or []))
            or (
                node.find_parent(class_=re.compile(
                    r"(?:^|[-_ ])(?:map-panel|map-illustration|map-placeholder)"
                    r"(?:$|[-_ ])", re.I
                )) is not None
                and node.name == "svg"
            )
        ]
        # CSS-only faux location panels need the same review as drawn SVGs.
        for panel in main.find_all(class_=re.compile(
            r"(?:^|[-_ ])(?:map-panel|map-illustration|map-placeholder)"
            r"(?:$|[-_ ])", re.I
        )):
            has_pin = bool(panel.select(".map-pin,.map-drawing,.location-label"))
            real_embed = bool(panel.select('iframe[src*="google.com/maps/"],'
                                          'iframe[src*="openstreetmap.org/"]'))
            actual_image = bool(panel.select("img[src]"))
            if has_pin and not real_embed and not actual_image and panel not in map_art:
                map_art.append(panel)
        if map_art and not _record_valid(
            research.get("verified_geospatial_illustration"),
            rendered_pages, research
        ):
            blocked.append({
                "category": "misleading_map", "route": route,
                "issue": "Decorative street-map presented as location aid without geospatial verification.",
            })
        # Tool-generated disclaimers and system notes are not production
        # website sections, even when outside main.
        if stage == "client_release":
            for node in soup.select("[data-demo-disclosure],.source-note,.demo-note"):
                blocked.append({"category": "demo_note_in_release", "route": route,
                                "element": node.name})
        inspected.append(route)

    if len(generic) >= 2:
        pending.append({
            "category": "template_headlines",
            "issue": "Several generic headings require editorial comparison with company voice.",
            "examples": generic[:8],
        })
    pending.append({
        "category": "visual_editorial_proof",
        "issue": "A human independent reviewer must inspect actual screenshots, source brand continuity, authentic maps and compositional balance.",
    })
    return {
        "pass": not blocked, "blocking": blocked, "pending": pending,
        "pages_checked": inspected, "generic_headings": generic,
        "note": "Static precision checks plus explicit human review; no invented visual score.",
    }


def audit_layout_review_flags(
    flags: list[dict], rendered_pages: dict[str, str], research: dict
) -> dict:
    """A layout warning is provisional until another person reviews the screenshot.

    A partial signoff, absent image, stale build or AI self-approval fails.
    The review does NOT pretend the pixel imbalance is automatically ugly.
    """
    flags = [dict(flag) for flag in (flags or []) if isinstance(flag, dict)]
    if not flags:
        return {"pass": True, "issues": [], "flags": []}
    review = research.get("layout_composition_review") or {}
    normalized_flags = json.dumps(flags, ensure_ascii=False, sort_keys=True)
    flags_hash = hashlib.sha256(normalized_flags.encode("utf-8")).hexdigest()
    issues = []
    if review.get("reviewer_kind") not in ("human", "independent_human"):
        issues.append("A real independent visual reviewer must inspect large asymmetric columns.")
    if review.get("reviewer_id") in ("builder", "generator", None, ""):
        issues.append("Missing distinct visual reviewer identity.")
    if review.get("approved") is not True or not review.get("checked_at"):
        issues.append("Whitespace/composition findings have not been approved.")
    if review.get("build_sha256") != site_digest(rendered_pages):
        issues.append("Composition review applies to a different build.")
    if review.get("flags_sha256") != flags_hash:
        issues.append("Composition review does not cover all measured gaps.")
    if not review.get("screenshot_evidence"):
        issues.append("Full-page screenshot evidence missing.")
    return {"pass": not issues, "issues": issues,
            "flags": flags, "flags_sha256": flags_hash}
