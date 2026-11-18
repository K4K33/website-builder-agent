"""World-class design execution calibration for V7 QA.

The three global craft websites are distinct from sector-specific references.
Inspect real scroll/animation behavior using a browser; never claim that a
single screenshot proves equivalent experiential design. No third-party assets
may be reused on customer sites. A motion signal is NOT a premium score.
"""
from __future__ import annotations

import json
from pathlib import Path

from utils.quality_v7 import REFERENCES_V7
from utils.reference_scroll_experience import (
    compact_scroll_observations, complete_scroll_evidence, record_scroll_experience,
)

GLOBAL_CRAFT_NAMES = ("Lando Norris", "Dropbox brand", "Igloo Inc.")


def required_global_craft_sites() -> list[dict]:
    """Exactly the three awarded craft benchmarks chosen in V7; Singer is sector only."""
    data = json.loads(REFERENCES_V7.read_text(encoding="utf-8"))
    rows = data.get("global_craft") or []
    by_name = {r.get("name"): r for r in rows if isinstance(r,dict)}
    if any(name not in by_name for name in GLOBAL_CRAFT_NAMES):
        raise RuntimeError("Global design calibration set incomplete.")
    result = [by_name[name] for name in GLOBAL_CRAFT_NAMES]
    if len({r.get("url") for r in result}) != 3 or not all(
        str(r.get("url","")).startswith("https://") for r in result
    ):
        raise RuntimeError("Global design calibration URLs not uniquely verified.")
    return result


def collect_global_craft_evidence(*, capture, cache=None, cache_root=None) -> dict:
    """Fetch real desktop AND mobile scroll, no scores/copying/assets.

    The caller owns the restricted capture/browser context and finite timeout.
    Missing competitor evidence remains PENDING, never fabricated.
    """
    output = []
    for row in required_global_craft_sites():
        try:
            shots = (cache(row["url"],capture,cache_root=cache_root,
                           require_scroll_experience=True)
                     if cache is not None else capture(row["url"],row["name"]))
            valid = complete_scroll_evidence(shots)
            out = compact_scroll_observations(shots)
            evidence = []
            if valid:
                for viewport in ("desktop","mobile"):
                    rec = shots["scroll_experience"][viewport]
                    evidence.append({"viewport":viewport,
                                     "sequence_image":rec["scroll_sequence_image"],
                                     "video":rec.get("video_path") if
                                        isinstance(rec.get("video_path"),str)
                                        and Path(rec["video_path"]).is_file() else None})
            output.append({
                "name":row["name"],"url":row["url"],"discipline":row["discipline"],
                "status":"BROWSER_SCROLLED" if valid else "EXPERIENCE_PENDING",
                "observations":out,"media_evidence":evidence,
            })
        except Exception as exc:
            output.append({"name":row["name"],"url":row["url"],
                           "discipline":row["discipline"],
                           "status":"EXPERIENCE_PENDING",
                           "error_type":type(exc).__name__,
                           "media_evidence":[]})
    complete = len(output)==3 and all(
        r.get("status")=="BROWSER_SCROLLED" for r in output)
    return {"protocol":"kaurivo-global-craft-ux-v1",
            "calibration_status":"OBSERVED_NEEDS_EXPERT_JUDGMENT" if complete else
                                  "INCOMPLETE_REFERENCE_EVIDENCE",
            "benchmarks":output,"all_three_scrolled":complete,
            "independent_9_5_score":None,
            "note":"Reference journeys are evidence for critic; visual parity cannot be inferred from screen grabs or motion counts."}


def capture_generated_home_journey(page, *, output_prefix) -> dict:
    """Use the same real scroll observer on the exact generated homepage."""
    return record_scroll_experience(page,output_prefix=output_prefix)


def capture_generated_site_journey(homepage: str | Path, *, output_root: str | Path) -> dict:
    """Private actual wheel-scroll/video evidence of exact generated homepage.

    Browses LOCAL prepared assets only: customer JS cannot open network origins.
    Video files and screenshots stay out of public-site deliverable.
    """
    from urllib.parse import unquote, urlsplit
    from playwright.sync_api import sync_playwright

    source=Path(homepage).resolve()
    if not source.is_file():
        raise RuntimeError("Exact homepage missing for global craft comparison.")
    directory=Path(output_root).resolve()
    directory.mkdir(parents=True,exist_ok=True)
    results={}
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        try:
            for name,width,height in (("desktop",1440,900),("mobile",390,844)):
                video_dir=directory/name
                video_dir.mkdir(parents=True,exist_ok=True)
                context=browser.new_context(
                    viewport={"width":width,"height":height},
                    device_scale_factor=1,is_mobile=width<=390,has_touch=width<=390,
                    reduced_motion="no-preference",service_workers="block",
                    record_video_dir=str(video_dir))
                def local_only(route):
                    url=route.request.url
                    safe=url.startswith("data:")
                    if url.startswith("file:"):
                        parsed=urlsplit(url)
                        file=Path(unquote(parsed.path)).resolve()
                        safe=(parsed.netloc in ("","localhost")
                              and file.is_relative_to(source.parent) and file.is_file())
                    return route.continue_() if safe else route.abort()
                context.route("**/*",local_only)
                page=context.new_page()
                try:
                    page.goto(source.as_uri(),wait_until="load",timeout=15000)
                    page.wait_for_timeout(350)
                    results[name]=record_scroll_experience(
                        page,output_prefix=directory/(name+"-build"))
                except Exception as exc:
                    results[name]={"status":"capture_failed","error_type":type(exc).__name__}
                finally:
                    video=page.video
                    context.close()
                    try:
                        movie=Path(video.path()) if video else None
                        if movie and movie.is_file() and movie.stat().st_size>300:
                            results[name]["video_path"]=str(movie)
                    except Exception:
                        pass
        finally:
            browser.close()
    return results


def compare_experiences(reference_report: dict, generated_journeys: dict) -> dict:
    """Prepare inspectable, honest QA contract. No automatic taste scores."""
    ref = reference_report if isinstance(reference_report,dict) else {}
    gen = generated_journeys if isinstance(generated_journeys,dict) else {}
    valid_generated = all(
        isinstance(gen.get(v),dict) and gen[v].get("status")=="observed"
        for v in ("desktop","mobile")
    )
    return {
        "protocol":"kaurivo-global-vs-company-experience-v1",
        "references":ref.get("benchmarks") or [],
        "reference_all_three_scrolled":ref.get("all_three_scrolled") is True,
        "generated_home_scrolled":valid_generated,
        "generated_journey":{
            v: {"status":(gen.get(v) or {}).get("status"),
                "frames":[{"at":f.get("fraction"),"headings":(f.get("headings") or [])[:4],
                           "media_visible":f.get("media_visible"),
                           "sticky_visible":f.get("sticky_visible"),
                           "animations_running":f.get("animations_running")}
                          for f in ((gen.get(v) or {}).get("frames") or [])[:5]],
                "same_position_visual_change":(gen.get(v) or {}).get("same_position_visual_change"),
                "nav_hover_visual_change":(gen.get(v) or {}).get("nav_hover_visual_change"),
                "video":(gen.get(v) or {}).get("video_path")}
            for v in ("desktop","mobile")},
        "comparison_assessed_by_expert":False,
        "quality_score":None,
        "review_instructions":(
            "Compare the actual scrolling experience: purpose and pacing of each section; "
            "semantic storytelling and real customer task; photographic composition; "
            "typographic rhythm and spacing; timing of reveals and transitions; "
            "hover/touch/navigation feedback; motion smoothness, mobile and reduced-motion. "
            "Assess execution CARE relative to the real client's sector, not stylistic "
            "similarity or number of animations. Record observed weaknesses and repair "
            "actions. Do not claim independent 9.5 without actual third-party judgment."
        ),
    }
