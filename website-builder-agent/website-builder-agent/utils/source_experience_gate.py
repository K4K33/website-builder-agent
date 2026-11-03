"""Evidence-bound preservation of the ORIGINAL site's visual experience.

A video, 3-D effect or textured background is part of a company's existing
creative identity when observed on its website. Static checks cannot establish
that the browser actually plays/renders it, nor confer media reuse rights.
Fail-closed for missing source evidence; never demand gratuitous motion.
"""
from __future__ import annotations

import hashlib
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256


KINDS = ("video", "three_d", "motion", "textured_background", "gallery", "photography")


def build_digest(pages: dict[str, str]) -> str:
    return hashlib.sha256("".join(
        path + "\n" + pages[path] for path in sorted(pages)
    ).encode("utf-8")).hexdigest()


def inspect_markup(pages: dict[str, str], *, stylesheets: dict[str, str] | None = None) -> dict:
    """Conservative DOM/CSS hints, not a browser motion/performance measurement."""
    html = "\n".join(pages.values())
    soup = BeautifulSoup(html, "html.parser")
    css = "\n".join((stylesheets or {}).values())
    css += "\n".join(tag.get_text(" ", strip=True) for tag in soup.find_all("style"))
    css += "\n".join(str(tag.get("style", "")) for tag in soup.find_all(style=True))
    scripts = "\n".join(tag.get_text(" ", strip=True) for tag in soup.find_all("script"))
    srcs = " ".join(str(tag.get("src") or "") for tag in soup.find_all(["iframe", "video", "script"]))
    dynamic = bool(soup.select('script[src]'))  # video/canvas may be injected at runtime
    video = bool(soup.find("video") or soup.find("source", type=re.compile(r"video/", re.I))
                 or re.search(r"(youtube\.com/embed|youtube-nocookie\.com/embed|player\.vimeo\.com/video)", srcs, re.I))
    three_d = bool(soup.find(["model-viewer", "spline-viewer"]) or
                   re.search(r"\b(three(?:\.min)?\.js|@react-three|babylon|spline-viewer|sketchfab)\b",
                             html, re.I))
    motion = bool(video or re.search(
        r"@keyframes\b|\banimation(?:-name|-duration)?\s*:|\bscroll-timeline\b|"
        r"\b(gsap|lottie|scrolltrigger|motion\.animate)\b", css + "\n" + scripts + "\n" + srcs, re.I))
    textured_background = bool(re.search(
        r"background(?:-image)?\s*:[^;}]{0,220}(?:url\(|gradient\()",
        css, re.I))
    photos = sum(1 for img in soup.find_all("img") if
                 str(img.get("src") or "").strip() and
                 not str(img.get("src") or "").strip().startswith("data:image/svg"))
    return {
        "video": video, "three_d": three_d, "motion": motion,
        "textured_background": textured_background,
        "gallery": photos >= 3, "photography": photos > 0,
        "image_elements": photos, "linked_stylesheets": bool(soup.select('link[rel="stylesheet"]')),
        "runtime_js": dynamic,
    }


def _exception_allowed(exceptions: object, kind: str, source_sha: str, build_sha: str) -> bool:
    return any(
        isinstance(e, dict) and e.get("kind") == kind
        and e.get("reviewer_kind") == "client"
        and str(e.get("reviewer") or "").strip()
        and str(e.get("reason") or "").strip()
        and e.get("source_sha256") == source_sha
        and e.get("build_sha256") == build_sha
        for e in (exceptions if isinstance(exceptions, list) else [])
    )


def audit_experience_continuity(
    pages: dict[str, str], research: dict, *,
    stylesheets: dict[str, str] | None = None,
) -> dict:
    """Verify experience *continuity*, without copying client assets or effects.

    The source profile is an evidence record, NEVER a model-invented checklist.
    Real video/3D/background and smoothness still need original/new browser
    recordings, rights review, device testing and owner sign-off.
    """
    original = (research.get("source_inventory") or {}).get("pages") or []
    original = [p for p in original if isinstance(p, dict) and p.get("url")]
    rendered = inspect_markup(pages, stylesheets=stylesheets)
    result = {"blocking": [], "pending": [], "rendered_signals": rendered,
              "original_profile_status": "not_applicable" if not original else "missing"}
    if not original:
        return result

    source_sha = source_inventory_sha256(research["source_inventory"])
    build_sha = build_digest(pages)
    profile = research.get("original_experience_profile")
    if not isinstance(profile, dict):
        result["pending"].append(
            "Original site's motion, video, 3-D, galleries and background textures were "
            "not inventoried at all. Capture actual original desktop/mobile browser evidence "
            "before calling this redesign premium-ready.")
        return result
    if profile.get("source_sha256") != source_sha:
        result["pending"].append("Original visual-experience profile is missing or stale "
                                 "against the latest source inventory hash.")
        return result
    if profile.get("capture_method") not in ("browser", "human_browser_review") or not str(
            profile.get("checked_at") or "").strip():
        result["pending"].append("Visual-experience profile lacks dated actual browser evidence.")
        return result

    if profile.get("complete") is not True:
        result["pending"].append(
            "Original browser probe did not cover every source page; omitted "
            "pages may contain video, 3-D or animations. Finish source inspection.")
    features = profile.get("features") or {}
    if not isinstance(features, dict):
        result["pending"].append("Original experience features must be an evidence map.")
        return result
    observed_urls = {p["url"] for p in original}
    for kind in KINDS:
        item = features.get(kind)
        if not isinstance(item, dict) or not isinstance(item.get("present"), bool):
            result["pending"].append(f"Source feature '{kind}' not assessed; do not assume absent.")
            continue
        if item["present"]:
            url = str(item.get("source_url") or "")
            if url not in observed_urls or not str(item.get("observation") or "").strip():
                result["pending"].append(f"Source feature '{kind}' has no source-page-linked observation.")
                continue
    result["original_profile_status"] = "recorded"

    approval = research.get("experience_continuity_review") or {}
    review_valid = (
        isinstance(approval, dict)
        and approval.get("reviewer_kind") == "human"
        and str(approval.get("reviewer") or "").strip()
        and approval.get("original_and_new_recordings_checked") is True
        and approval.get("source_sha256") == source_sha
        and approval.get("build_sha256") == build_sha
    )

    for kind in KINDS:
        source = features.get(kind)
        if not isinstance(source, dict) or source.get("present") is not True:
            continue
        if source.get("source_url") not in observed_urls or not str(source.get("observation") or "").strip():
            continue
        if _exception_allowed(research.get("experience_exceptions"), kind, source_sha, build_sha):
            continue
        if kind in ("video", "three_d") and not rendered[kind]:
            # An external script can inject media; static silence is not
            # conclusive, so require recorded browser inspection.
            if rendered["runtime_js"]:
                result["pending"].append(
                    f"Original {kind} observed, absent in static redesign DOM; "
                    "check runtime browser recording and preserve or get a client-authorized alternative.")
            else:
                result["blocking"].append(
                    f"Original {kind} observed but not represented in redesign; "
                    "preserve its role or record exact-build client-approved exception.")
        elif kind == "gallery" and not rendered["gallery"]:
            result["blocking"].append(
                "Original product/work photo gallery disappeared from redesign; "
                "restore with licensed media or get a client-approved alternative.")
        elif kind == "photography" and not rendered["photography"]:
            result["pending"].append(
                "Original site had real photography but redesigned HTML has no photo elements. "
                "Rights-safe replacement is unresolved; do not call it final.")
        elif kind in ("motion", "textured_background") and not rendered[kind]:
            result["pending"].append(
                f"Original {kind} is not evidenced by inline markup/styles. "
                "Check linked CSS, JS and paired real browser recordings.")
        if not review_valid:
            result["pending"].append(
                f"Original {kind} requires human source/new browser continuity review "
                "bound to the current build and source.")

    # A source with no 3-D never implies every redesign needs 3-D.
    # Extra effects can be justified, but must not become agency boilerplate.
    source_3d = features.get("three_d") or {}
    source_motion = features.get("motion") or {}
    if source_motion.get("present") is False and rendered["motion"]:
        result["pending"].append(
            "Added animation on a previously still site: confirm purposeful "
            "interaction, accessible reduced-motion fallback and mobile performance.")
    if source_3d.get("present") is False and rendered["three_d"]:
        result["pending"].append(
            "New 3-D effect on a previously non-3-D site: require an explicit "
            "business-specific purpose, performance and reduced-motion review.")
    return result
