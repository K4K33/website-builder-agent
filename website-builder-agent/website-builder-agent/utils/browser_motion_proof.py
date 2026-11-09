"""Real-browser evidence for explicitly claimed visual interactions.

The test checks rendered changes, not merely CSS/JS tokens. A pixel difference
is NOT an aesthetic score, smoothness benchmark or proof of commercial quality.
Source and target stay inside the caller's sandboxed Playwright context.
"""
from __future__ import annotations
from hashlib import sha256


def audit_declared_interactions(page, *, max_elements=6) -> dict:
    controls = page.locator("[data-premium-interaction]")
    count = min(controls.count(), max_elements)
    if not count:
        return {"blocking": [], "pending": [
            "No declared premium interaction in this page; do not infer visual quality "
            "from source code. Independent screenshot and interaction review required."
        ], "observations": []}
    blocking, pending, observations = [], [], []
    # The ordinary QA view uses reduced motion. Reload under no-preference
    # BEFORE exercising any JS handlers that were registered at DOMContentLoaded.
    page.emulate_media(reduced_motion="no-preference")
    page.reload(wait_until="load")
    page.wait_for_timeout(180)
    count = min(page.locator("[data-premium-interaction]").count(), max_elements)
    for index in range(count):
        item = page.locator("[data-premium-interaction]").nth(index)
        kind = (item.get_attribute("data-premium-interaction") or "").strip()
        label = f"interaction #{index+1} ({kind})"
        if kind not in ("pointer-depth", "hover", "focus"):
            blocking.append(label + ": unknown interaction type; cannot verify actual effect.")
            continue
        try:
            item.scroll_into_view_if_needed(timeout=3000)
            rect = item.bounding_box()
            if not rect or rect["width"] < 24 or rect["height"] < 24:
                blocking.append(label + ": effect target is missing or too small.")
                continue

            def picture():
                return sha256(item.screenshot(animations="disabled", timeout=9000)).hexdigest()

            if kind == "focus":
                page.mouse.move(0, 0)
                before = picture()
                item.focus()
                page.wait_for_timeout(180)
                after = picture()
            else:
                page.mouse.move(0, 0)
                page.wait_for_timeout(120)
                before = picture()
                if kind == "pointer-depth":
                    page.mouse.move(rect["x"] + rect["width"] * .24,
                                    rect["y"] + rect["height"] * .27)
                    page.wait_for_timeout(160)
                    middle = picture()
                    page.mouse.move(rect["x"] + rect["width"] * .76,
                                    rect["y"] + rect["height"] * .70)
                    page.wait_for_timeout(160)
                    after = picture()
                else:
                    page.mouse.move(rect["x"] + rect["width"] / 2,
                                    rect["y"] + rect["height"] / 2)
                    page.wait_for_timeout(160)
                    after = picture()
            changed = (before != after or
                       (kind == "pointer-depth" and middle != after))
            observations.append({"kind": kind, "label": label,
                                 "screenshot_changed": changed,
                                 "rendered_in_browser": True})
            if not changed:
                blocking.append(label +
                                ": claimed effect produced no detectable rendered difference.")
            else:
                pending.append(
                    label + ": visible change observed but its magnitude, premium "
                    "aesthetics, motion smoothness and brand fit require human review."
                )
        except Exception as error:
            blocking.append(label + ": browser inspection failed: " + type(error).__name__)

    # Same page with user's reduced-motion preference must remain readable
    # and visually stable. Pointer interactions may still provide a keyboard
    # equivalent, but animated effects must not be mandatory for content.
    page.emulate_media(reduced_motion="reduce")
    page.reload(wait_until="load")
    page.wait_for_timeout(120)
    for index in range(min(count, page.locator("[data-premium-interaction]").count())):
        item = page.locator("[data-premium-interaction]").nth(index)
        kind = (item.get_attribute("data-premium-interaction") or "").strip()
        if kind != "pointer-depth":
            continue
        try:
            item.scroll_into_view_if_needed(timeout=3000)
            rect = item.bounding_box()
            if not rect:
                continue
            page.mouse.move(0, 0)
            baseline = sha256(item.screenshot(animations="disabled")).hexdigest()
            page.mouse.move(rect["x"] + rect["width"] * .7,
                            rect["y"] + rect["height"] * .45)
            page.wait_for_timeout(140)
            reduced = sha256(item.screenshot(animations="disabled")).hexdigest()
            if baseline != reduced:
                blocking.append(f"interaction #{index+1}: effect still animates under reduced-motion preference.")
        except Exception as error:
            blocking.append(f"interaction #{index+1}: reduced-motion check failed: " + type(error).__name__)
    return {"blocking": blocking, "pending": pending, "observations": observations}
