"""Company-agnostic, fail-closed visual SOURCE signature continuity.

This is a preservation gate, not an aesthetic score, media licence or OCR.
It uses observed original assets, roles and browser signals; it cannot invent a
new brand. Matching an image URL alone does not demonstrate visual equivalence.
"""
from __future__ import annotations

import math
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest

GALLERY_PATH = re.compile(r"galler|gallery|portfolio|referens|kuvat|photos|work|tyonayt|työnäyt", re.I)
TEAM_PATH = re.compile(r"(?:meista|meistä|about|team|staff|henkil[oö]st|tekij[aä]|yhteystiedot)", re.I)
VIDEO_SRC = re.compile(r"(youtube(?:-nocookie)?\.com/embed|player\.vimeo\.com/video|wistia|\.mp4(?:\?|$)|\.webm(?:\?|$))", re.I)
EXCLUDED_IMAGE = re.compile(r"^(?:data:|blob:|javascript:)", re.I)


def _url(src: object, source: str = "") -> str:
    value = str(src or "").strip()
    if not value or EXCLUDED_IMAGE.match(value):
        return ""
    resolved = urljoin(source, value)
    return resolved if urlsplit(resolved).scheme in ("https", "http") and urlsplit(resolved).hostname else value


def signature_from_source(research: dict) -> dict:
    """The source inventory is the authority, NOT generated brand prose."""
    pages = [p for p in (research.get("source_inventory") or {}).get("pages") or []
             if isinstance(p, dict) and p.get("url")]
    logos, team, about, gallery, photos, videos, known = set(), set(), set(), set(), set(), set(), []
    observed_identity = 0
    for p in pages:
        url = str(p["url"])
        identity = p.get("source_identity") or {}
        if isinstance(identity, dict) and identity:
            observed_identity += 1
            for image in identity.get("original_logo_candidates") or []:
                value = _url(image, url)
                if value:
                    logos.add(value)
            for photo in identity.get("original_content_photos") or []:
                if not isinstance(photo, dict):
                    continue
                image = _url(photo.get("src"), url)
                if not image:
                    continue
                photos.add(image)
                if str(photo.get("role") or "") == "staff_portrait":
                    team.add(image)
                if TEAM_PATH.search(urlsplit(url).path) and str(photo.get("role") or "") == "staff_portrait":
                    about.add(image)
                if str(photo.get("role") or "") == "gallery_photo" or GALLERY_PATH.search(urlsplit(url).path):
                    gallery.add(image)
            source_media = identity.get("source_experience") or {}
            if isinstance(source_media, dict) and int(source_media.get("observed_videos") or 0) > 0:
                videos.add(url)
        # An unlabelled portrait from a people-focused About/Team page
        # must not be silently dropped simply because Wordpress omitted alt.
        team_copy = (str(p.get("title") or "") + " " + str(p.get("text") or ""))[:6000]
        if TEAM_PATH.search(urlsplit(url).path) and re.search(
            r"tiimi|henkil[oö]st[oö]|ty[oö]ntekij|tekij[aä]|yritt[aä]j|"
            r"our team|meet the team|our staff|employees", team_copy, re.I
        ):
            about.update(_url(item.get("src"), url)
                         for item in identity.get("original_content_photos") or []
                         if isinstance(item, dict) and _url(item.get("src"), url))
        known.append(url)
    profile = research.get("original_experience_profile") or {}
    inventory = research.get("source_inventory") or {}
    if (pages and isinstance(profile, dict)
        and profile.get("source_sha256") == source_inventory_sha256(inventory)
        and profile.get("capture_method") in ("browser", "human_browser_review")):
        media = (profile.get("features") or {}).get("video") or {}
        if media.get("present") is True and media.get("source_url") in known:
            videos.add(media["source_url"])
    return {
        "source_urls": known,
        "source_sha256": source_inventory_sha256(inventory) if pages else "",
        "identity_pages": observed_identity,
        "logos": sorted(logos),
        "staff_portraits": sorted(team),
        "about_page_people_photos": sorted(about),
        "gallery_photos": sorted(gallery),
        "all_content_photos": sorted(photos),
        "video_pages": sorted(videos),
        "no_original_site": research.get("research_mode") == "verified_no_website",
    }


def _signed_exception(research: dict, kind: str, original: str,
                      source_hash: str, build_hash: str) -> bool:
    """Only a specific CLIENT decision for exact original and exact build counts."""
    for record in research.get("source_signature_exceptions") or []:
        if not isinstance(record, dict):
            continue
        if (record.get("kind") == kind and record.get("original") == original
            and record.get("source_sha256") == source_hash
            and record.get("build_sha256") == build_hash
            and record.get("approved") is True
            and record.get("reviewer_kind") == "client"
            and str(record.get("reviewer") or "").strip()
            and str(record.get("checked_at") or "").strip()
            and len(str(record.get("reason") or "").strip()) >= 20):
            return True
    return False


def _signed_replacements(research: dict, source_hash: str,
                         build_hash: str) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for item in research.get("approved_asset_replacements") or []:
        if not isinstance(item, dict):
            continue
        original = _url(item.get("original_src"), item.get("source_url") or "")
        replacement = str(item.get("replacement_src") or "").strip()
        if (original and replacement
            and item.get("source_sha256") == source_hash
            and item.get("build_sha256") == build_hash
            and item.get("reviewer_kind") == "client"
            and str(item.get("reviewer") or "").strip()
            and item.get("rights_verified") is True
            and item.get("visual_match_verified") is True):
            mapping[original] = replacement
    return mapping


def _rendered(pages: dict[str, str]) -> dict:
    images, header_images, images_by_route = set(), {}, {}
    videos = 0
    for route, html in pages.items():
        soup = BeautifulSoup(html, "html.parser")
        header = soup.find("header")
        header_images[route] = set()
        images_by_route[route] = set()
        for img in soup.find_all("img"):
            for value in [img.get("src"), img.get("data-src")]:
                if value:
                    images.add(str(value).strip())
                    images_by_route[route].add(str(value).strip())
                    if header is not None and img in header.descendants:
                        header_images[route].add(str(value).strip())
            # srcset is responsive source evidence, not a substitute for
            # visual pixel comparison / rights clearance.
            for key in ("srcset", "data-srcset"):
                for part in str(img.get(key) or "").split(","):
                    candidate = part.strip().split(" ", 1)[0]
                    if candidate:
                        images.add(candidate)
                        images_by_route[route].add(candidate)
                        if header is not None and img in header.descendants:
                            header_images[route].add(candidate)
        videos += len(soup.select("video,source[type^='video/']"))
        videos += sum(bool(VIDEO_SRC.search(str(i.get("src") or "")))
                      for i in soup.select("iframe[src]"))
    return {"images": images, "header_images": header_images,
            "images_by_route": images_by_route, "video": videos}


def audit_source_signature_lock(pages: dict[str, str], research: dict) -> dict:
    """Block known identity/media losses BEFORE saving a redesigned site.

    Missing source inspection stays PENDING, not an assertion of no logo.
    Customer-rights and human original/new screenshot review remain mandatory.
    """
    source = signature_from_source(research)
    blocking, pending = [], []
    if source["no_original_site"]:
        return {"blocking": blocking, "pending": pending, "source": source}
    if not source["source_urls"]:
        pending.append("Original source inventory unavailable: no brand fidelity can be certified.")
        return {"blocking": blocking, "pending": pending, "source": source}
    if source["identity_pages"] < len(source["source_urls"]):
        pending.append("Some original routes lack identity/media extraction; complete research first.")

    rendered = _rendered(pages)
    build_hash = site_digest(pages)
    replacement = _signed_replacements(research, source["source_sha256"], build_hash)

    def present(asset: str) -> bool:
        return asset in rendered["images"] or replacement.get(asset, "") in rendered["images"]

    def excepted(kind: str, asset: str) -> bool:
        return _signed_exception(research, kind, asset,
                                 source["source_sha256"], build_hash)

    # A readable new company name is NOT the same artwork as its original logo.
    # Of several originals we require at least ONE source-bound real mark across
    # every page, unless an exact-build customer approves that route's change.
    if source["logos"]:
        for route, header_assets in rendered["header_images"].items():
            if not any(asset in header_assets or replacement.get(asset, "") in header_assets
                       for asset in source["logos"]):
                if not excepted("logo", route):
                    blocking.append({
                        "kind": "source_logo_lost", "route": route,
                        "originals": source["logos"][:6],
                        "reason": "Original company logo is replaced/missing in this header. "
                                  "A text wordmark is not proof of the same brand.",
                    })
        pending.append("Original logo reuse rights and visual artwork match require owner verification.")

    # Staff portraits provide local-service trust. Four white text cards are
    # not an acceptable substitute for four sourced photographs.
    for asset in source["staff_portraits"]:
        if not present(asset) and not excepted("staff_portrait", asset):
            blocking.append({
                "kind": "staff_portrait_lost", "original": asset,
                "reason": "A source-observed team portrait was removed; preserve or obtain a specific customer decision.",
            })

    team_routes = [route for route in pages if TEAM_PATH.search(route)]
    # The portraits should appear in the company/team area, not merely be
    # hidden inside a product gallery on an unrelated subpage.
    if team_routes:
        for asset in source["staff_portraits"]:
            if (present(asset)
                and not any(asset in rendered["images_by_route"][route]
                            or replacement.get(asset, "") in rendered["images_by_route"][route]
                            for route in team_routes)
                and not excepted("staff_portrait_placement", asset)):
                blocking.append({
                    "kind": "staff_portrait_disconnected_from_team",
                    "original": asset,
                    "reason": "Staff photo exists only outside the company's team/about pages.",
                })
        if source["about_page_people_photos"]:
            preserved = [
                asset for asset in source["about_page_people_photos"]
                if any(asset in rendered["images_by_route"][route]
                       or replacement.get(asset, "") in rendered["images_by_route"][route]
                       for route in team_routes)
                or excepted("about_page_photo", asset)
            ]
            if not preserved:
                blocking.append({
                    "kind": "team_page_all_real_photos_lost",
                    "originals": source["about_page_people_photos"][:8],
                    "reason": "Original team/about page included people-related photographs "
                              "but the redesigned team area has none of the originals.",
                })

    # Preserve each photo in a true gallery instead of pointing customers
    # back to the old site. Reorganization between routes is allowed.
    for asset in source["gallery_photos"]:
        if not present(asset) and not excepted("gallery_photo", asset):
            blocking.append({
                "kind": "original_gallery_photo_lost", "original": asset,
                "reason": "Original gallery media disappeared or is only reachable on the old site.",
            })

    # For source-rich sites not already covered by specific gallery/staff
    # categories, a handful of decorative images must not pass as parity.
    other = set(source["all_content_photos"]) - set(source["gallery_photos"]) - set(source["staff_portraits"])
    if len(other) >= 6:
        preserved = sum(1 for item in other if present(item) or excepted("content_photo", item))
        required = min(len(other), max(3, math.ceil(len(other)*0.55)))
        if preserved < required:
            blocking.append({
                "kind": "original_photographic_depth_lost",
                "preserved": preserved, "required": required,
                "source_total": len(other),
                "reason": "Large original photography set compressed to generic or sparse visuals.",
            })

    for url in source["video_pages"]:
        if rendered["video"] == 0 and not excepted("video", url):
            blocking.append({
                "kind": "source_video_lost", "source_page": url,
                "reason": "Original source had video; the redesigned pages contain no playable video embed.",
            })

    # Static checks cannot assess CSS wood grain, brand typography, the true
    # original first fold, player playback or the quality of photo crops.
    pending.append("Compare original/new 320, 390, 768 and 1440px screenshots, "
                   "logo artwork, staff faces, video playback, material textures "
                   "and brand mood; external media rights are NOT established.")
    return {"blocking": blocking, "pending": pending,
            "source": source, "rendered": {"video": rendered["video"],
            "image_assets": len(rendered["images"])}}
