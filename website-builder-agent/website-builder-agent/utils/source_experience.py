"""Free, source-bound inventory of motion and visual richness.

DOM observations are not screenshots: externally loaded CSS, JavaScript, video
posters and runtime 3D must also be inspected in a real browser. The original
site determines a baseline, not a requirement to copy copyrighted assets.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_CAROUSEL = re.compile(r"(?:swiper|slick|owl-carousel|splide|flickity|glide|carousel|slider|slideshow)", re.I)
_MOTION_LIB = re.compile(r"(?:gsap|scrolltrigger|lottie|anime\.js|framer-motion|motion\.one)", re.I)
_3D = re.compile(r"(?:preserve-3d|perspective\s*:|rotate(?:X|Y|3d)\s*\(|translate3d\s*\(|matrix3d\s*\()", re.I)
_CSS_BG = re.compile(r"background(?:-image)?\s*:[^;{}]*url\(\s*['\"]?([^)'\" ]+)", re.I)
_VIDEO_IFRAME = re.compile(r"(?:youtube\.com/embed|youtube-nocookie\.com/embed|player\.vimeo\.com/video|wistia|video\.)", re.I)


def extract_source_experience(html: str, source_url: str = "") -> dict:
    """Inventory observable source media, meaningful interactions and motion.

    No request is made and no effect is inferred from a brand name, industry or
    external script filename alone. Missing evidence means browser review,
    never a fabricated claim that an animation exists or does not exist.
    """
    soup = BeautifulSoup(html or "", "html.parser")
    main = soup.find("main") or soup.body or soup
    photo_srcs = []
    for img in main.find_all("img"):
        if img.find_parent(("header", "footer", "nav")):
            continue
        # Lazy-loaded source sites may put a data-URI placeholder in src;
        # the photographed work is held in data-src or data-srcset.
        src = ""
        for key in ("data-src", "data-lazy-src", "data-original",
                    "src", "data-srcset", "srcset"):
            candidate = str(img.get(key) or "").strip()
            if key.endswith("srcset") and candidate:
                candidate = candidate.split(",", 1)[0].strip().split(" ", 1)[0]
            if candidate and not candidate.lower().startswith(
                    ("data:", "blob:", "javascript:", "#")):
                src = candidate
                break
        if src and not src.startswith("data:image/svg"):
            url = urljoin(source_url, src) if source_url else src
            if url not in photo_srcs:
                photo_srcs.append(url)
    videos = list(main.select("video,iframe[src]"))
    video_nodes = [
        node for node in videos
        if node.name == "video"
        or (node.name == "iframe" and _VIDEO_IFRAME.search(str(node.get("src") or "")))
    ]
    carousel_nodes = [
        node for node in main.find_all(True)
        if _CAROUSEL.search(" ".join(node.get("class") or [])
                            + " " + str(node.get("id") or "")
                            + " " + str(node.get("data-carousel") or "")
                            + " " + str(node.get("aria-roledescription") or ""))
    ]
    styles = "\n".join(
        [style.get_text(" ", strip=True) for style in soup.find_all("style")]
        + [str(node.get("style")) for node in soup.find_all(style=True)]
    )
    scripts = "\n".join(script.get_text(" ", strip=True)
                        for script in soup.find_all("script"))
    backgrounds = list(dict.fromkeys(
        urljoin(source_url, match) if source_url else match
        for match in _CSS_BG.findall(styles)
        if not match.startswith(("data:", "#"))
    ))
    three_d = bool(
        main.select("canvas,model-viewer,spline-viewer")
        or _3D.search(styles)
        or re.search(r"(?:three(?:\.min)?\.js|@splinetool|babylon|webgl)", scripts, re.I)
    )
    animated = bool(
        re.search(r"@keyframes|animation(?:-name)?\s*:|scroll-timeline\s*:", styles, re.I)
        or _MOTION_LIB.search(scripts)
    )
    explicit_motion = bool(video_nodes or three_d or animated or carousel_nodes)
    if video_nodes or three_d:
        level = "rich"
    elif carousel_nodes or animated:
        level = "moderate"
    else:
        level = "restrained"
    external_css = [str(node.get("href")) for node in soup.select('link[rel~="stylesheet"][href]')]
    external_js = [str(node.get("src")) for node in soup.select("script[src]")]
    return {
        "profile": level,
        "observed_videos": len(video_nodes),
        "observed_photo_assets": len(photo_srcs),
        "observed_carousel_nodes": len(carousel_nodes),
        "observed_textured_backgrounds": backgrounds[:24],
        "observed_3d": three_d,
        "observed_css_or_js_animation": animated,
        "has_meaningful_observed_motion": explicit_motion,
        "observed_photo_urls": photo_srcs[:40],
        "external_stylesheets": external_css[:20],
        "external_scripts": external_js[:20],
        "browser_inspection_required": bool(external_css or external_js),
        "evidence_scope": "source_HTML_only",
    }


def source_experience_brief(research: dict) -> dict:
    """Choose a conservative effect budget from source evidence, not templates."""
    profiles = [
        (page.get("source_identity") or {}).get("source_experience")
        for page in (research.get("source_inventory") or {}).get("pages") or []
        if isinstance(page, dict)
    ]
    observed = [p for p in profiles if isinstance(p, dict)]
    rank = {"restrained": 0, "moderate": 1, "rich": 2}
    if not observed:
        return {
            "status": "unverified",
            "motion_budget": "undetermined",
            "required_next_step": "Inspect source video, galleries, textured backgrounds, CSS, scripts and runtime before creative direction.",
            "do_not_assume_original_site_is_static": True,
        }
    budget = max((p.get("profile", "restrained") for p in observed),
                 key=lambda value: rank.get(value, 0))
    return {
        "status": "HTML_observed_browser_review_still_required",
        "motion_budget": budget,
        "video_present": any(p.get("observed_videos", 0) for p in observed),
        "gallery_present": any(p.get("observed_carousel_nodes", 0) for p in observed),
        "3d_present": any(p.get("observed_3d") for p in observed),
        "animation_present": any(p.get("observed_css_or_js_animation") for p in observed),
        "texture_background_present": any(p.get("observed_textured_backgrounds") for p in observed),
        "photo_rich": len({url for p in observed for url in
                           (p.get("observed_photo_urls") or [])}) >= 3,
        "external_assets_need_browser_review": any(p.get("browser_inspection_required") for p in observed),
        "creative_policy": (
            "Preserve or improve meaningful original interactions, movement, "
            "photography and material depth if observed. Never reduce video "
            "or galleries to generic cards or invented illustrations; obtain "
            "rights-cleared equivalents or block preview quality approval. "
            "For restrained original sites, do not auto-add decorative 3D "
            "or heavy animation. Motion must serve the business. Respect "
            "reduced-motion, performance and accessibility."
        ),
    }


def audit_source_experience_parity(rendered_pages: dict[str, str], research: dict) -> dict:
    """Detect obvious source-to-demo experiential downgrades without AI credits."""
    if research.get("research_mode") == "verified_no_website":
        return {"blocking": [], "pending": [], "brief": {"status": "no_original_site"}}
    brief = source_experience_brief(research)
    if brief["status"] == "unverified":
        return {"blocking": [], "pending": [
            "Original motion/media baseline is unverified; inspect live source before declaring preview quality."
        ], "brief": brief}
    generated = [extract_source_experience(html) for html in rendered_pages.values()]
    videos = sum(item["observed_videos"] for item in generated)
    photos = sum(item["observed_photo_assets"] for item in generated)
    carousels = sum(item["observed_carousel_nodes"] for item in generated)
    three_d = any(item["observed_3d"] for item in generated)
    animated = any(item["observed_css_or_js_animation"] for item in generated)
    texture = any(item["observed_textured_backgrounds"] for item in generated)
    blocked, pending = [], []
    if brief["video_present"] and not videos:
        blocked.append(
            "Original site contains an observable video, but redesign has no video. "
            "Obtain permitted source/replacement media or independently approve "
            "an explicit video-free content-equivalent approach."
        )
    if brief["photo_rich"] and photos == 0 and not videos:
        blocked.append(
            "Photo-rich original replaced by a site without actual work/product images "
            "or videos. Do not fill the gap with initials, decorative numbers or generic SVGs."
        )
    if brief["gallery_present"] and not carousels and photos < 2:
        pending.append(
            "Original gallery/carousel has no verified equivalent work/product browsing experience."
        )
    if brief["texture_background_present"] and not texture:
        pending.append(
            "Original has source-observed material/image backgrounds; browser-compare "
            "their depth with the new CSS/background treatment."
        )
    if brief["motion_budget"] == "rich" and not (videos or three_d or carousels or animated):
        pending.append(
            "Original rich motion level appears lost; browser-compare creative richness and relevance."
        )
    if brief["motion_budget"] == "restrained" and (three_d or animated):
        pending.append(
            "New effects added to a restrained original; verify business relevance, fast loading "
            "and reduced-motion behavior rather than introducing automatic 3D."
        )
    if brief["external_assets_need_browser_review"]:
        pending.append(
            "Source has external CSS/JS; HTML-only observation cannot establish its full effects. "
            "Record original-vs-redesign runtime and screenshots before approval."
        )
    return {"blocking": blocked, "pending": pending, "brief": brief}
