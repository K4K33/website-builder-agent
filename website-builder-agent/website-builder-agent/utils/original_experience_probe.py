"""Zero-paid-API browser inventory of original media and motion on ALL source pages.

Signals are browser observations, not visual excellence ratings or media rights.
A missed page or a weak animation/texture heuristic is explicitly incomplete.
"""
from __future__ import annotations

from datetime import datetime, timezone

from utils.content_parity import source_inventory_sha256
from utils.screenshot import _safe_remote_url


EXPERIENCE_SCRIPT = """() => {
  const tags = [...document.querySelectorAll('main img, article img, section img')];
  const photographs = tags.filter(el =>
    el.naturalWidth > 180 && el.naturalHeight > 100 && el.getClientRects().length).length;
  const videos = [...document.querySelectorAll('video')];
  const embeds = [...document.querySelectorAll('iframe[src]')].filter(el =>
    /youtube|vimeo|wistia/.test(el.src)).length;
  const threeD = document.querySelectorAll('model-viewer, spline-viewer').length +
    [...document.querySelectorAll('iframe[src]')].filter(el =>
      /sketchfab|spline/.test(el.src)).length;
  const srcs = [...document.querySelectorAll('script[src]')].map(el => el.src).join(' ');
  const script3d = /three(?:[.-]|js)|babylon|react-three/.test(srcs);
  const elements = [...document.querySelectorAll('body, main, header, section, article, div')]
    .slice(0, 800);
  let cssAnimated = 0, backgroundImage = 0, repeatingBackground = 0;
  for (const el of elements) {
    const s = getComputedStyle(el);
    if (s.animationName && s.animationName !== 'none') cssAnimated += 1;
    if (s.backgroundImage && s.backgroundImage !== 'none') {
      backgroundImage += 1;
      if (s.backgroundRepeat && s.backgroundRepeat !== 'no-repeat') repeatingBackground += 1;
    }
  }
  let webAnimations = 0;
  try { webAnimations = document.getAnimations().length; } catch (_) {}
  return {
    video_count: videos.length + embeds,
    three_d_candidates: threeD + (script3d ? 1 : 0),
    motion_candidates: cssAnimated + webAnimations,
    photo_count: photographs,
    textured_background_candidates: repeatingBackground,
    background_image_elements: backgroundImage,
    evidence_type: 'live_dom_computed_style',
    note: 'Candidate counts, not proof of 3D/texture artistry or smooth playback'
  };
}"""


def aggregate_source_experience(inventory: dict, observations: dict, failed: list[str]) -> dict:
    """Create a source-hash bound manifest without inventing unobserved features."""
    source_urls = [p["url"] for p in inventory.get("pages") or []
                   if isinstance(p, dict) and p.get("url")]
    features = {}
    rules = {
        "video": ("video_count", 1),
        "three_d": ("three_d_candidates", 1),
        "motion": ("motion_candidates", 1),
        "textured_background": ("textured_background_candidates", 1),
        "gallery": ("photo_count", 3),
        "photography": ("photo_count", 1),
    }
    for kind, (field, threshold) in rules.items():
        matches = [(url, details) for url, details in observations.items()
                   if int(details.get(field) or 0) >= threshold]
        if matches:
            url, details = matches[0]
            features[kind] = {
                "present": True,
                "source_url": url,
                "observation": f"Browser {field}={details[field]}; "
                               "heuristic candidates need screenshot verification.",
            }
        else:
            features[kind] = {"present": False}
    return {
        "source_sha256": source_inventory_sha256(inventory),
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "capture_method": "browser",
        "complete": len(observations) == len(source_urls) and not failed,
        "inspected_urls": list(observations),
        "failed_urls": failed,
        "features": features,
        "raw_observations": observations,
        "note": "Automated signals only. Verify original/new video, 3D, textures "
                "and image rights with actual recordings and the client.",
    }


def probe_original_site_experience(inventory: dict, *, timeout_ms: int = 12000,
                                   max_pages: int = 12) -> dict:
    """Bounded real browser crawl; no AI, search API or billable third party key."""
    source_urls = [p.get("url") for p in inventory.get("pages") or []
                   if isinstance(p, dict) and p.get("url")]
    selected = source_urls[:max_pages]
    observations, failed = {}, [u for u in source_urls[max_pages:]]
    if not selected:
        return aggregate_source_experience(inventory, observations, failed)
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    reduced_motion="no-preference", service_workers="block",
                )
                try:
                    for url in selected:
                        if not _safe_remote_url(url):
                            failed.append(url)
                            continue
                        page = context.new_page()
                        try:
                            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
                            page.wait_for_timeout(500)
                            observations[url] = page.evaluate(EXPERIENCE_SCRIPT)
                        except Exception:
                            failed.append(url)
                        finally:
                            page.close()
                finally:
                    context.close()
            finally:
                browser.close()
    except Exception:
        failed.extend(url for url in selected if url not in failed)
    return aggregate_source_experience(inventory, observations, failed)
