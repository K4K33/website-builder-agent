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


def audit_photo_sequences(page, *, output_dir, viewport):
    """Capture actual sequence states and verify reverse and static playback."""
    from io import BytesIO
    from PIL import Image

    selector = '[data-kaurivo-photo-sequence="ready"]'
    issues, observations = [], []
    page.emulate_media(reduced_motion="no-preference")
    page.reload(wait_until="load")
    scenes = page.locator(selector)

    def capture(scene, position):
        stage = scene.locator('[data-kaurivo-photo-stage]')
        scene.evaluate("""(scene, position) => {
            const stage = scene.firstElementChild;
            const start = scene.getBoundingClientRect().top + scrollY - parseFloat(getComputedStyle(stage).top);
            const distance = scene.offsetHeight - stage.offsetHeight * 1.25;
            scrollTo({top: start + position * distance, behavior: 'instant'});
        }""", position)
        page.evaluate("new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))")
        state = stage.evaluate("""stage => {
            const rect = stage.getBoundingClientRect();
            return {
                visible: rect.top >= -1 && rect.bottom <= innerHeight + 1 &&
                    rect.left >= -1 && rect.right <= innerWidth + 1,
                frames: [...stage.children].map(frame => +getComputedStyle(frame).opacity)
            };
        }""")
        return state, stage.screenshot(animations="disabled", timeout=4000)

    for index in range(scenes.count()):
        scene = scenes.nth(index)
        label = f"photo sequence {index + 1}"
        try:
            scene.evaluate("scene => scene.scrollIntoView({block:'start', behavior:'instant'})")
            scene.and_(page.locator("[data-photo-active]")).wait_for(timeout=4000)
            frames = scene.locator("[data-kaurivo-photo-stage] > figure").count()
            mid_step = .5 / (frames - 1)
            captures = [capture(scene, position) for position in (0, mid_step, 1, mid_step)]
            (first, first_png), (middle, middle_png), (last, last_png), (reverse, _) = captures
            if not all(state["visible"] for state, _ in captures):
                issues.append(f"{label}: stage clips or exceeds the viewport.")
            if (first["frames"][0] < .97 or first["frames"][1] > .04 or last["frames"][-1] < .97
                    or middle["frames"][0] < .97 or not .35 < middle["frames"][1] < .65
                    or len({first_png, middle_png, last_png}) != 3):
                issues.append(f"{label}: start, transition and ending are not distinctly rendered.")
            if any(abs(a - b) > .04 for a, b in zip(middle["frames"], reverse["frames"])):
                issues.append(f"{label}: reverse scrolling does not return to the same transition.")

            images = [Image.open(BytesIO(png)).convert("RGB") for png in (first_png, middle_png, last_png)]
            for image in images:
                image.thumbnail((470, 400))
            strip = Image.new("RGB", (sum(image.width for image in images), max(image.height for image in images)))
            offset = 0
            for image in images:
                strip.paste(image, (offset, 0))
                offset += image.width
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / f"{viewport}-photo-sequence-{index + 1}.jpg"
            strip.save(path, quality=88)
            observations.append({"category": "source_photo_sequence", "viewport": viewport,
                                 "sequence": index + 1, "filmstrip": str(path),
                                 "states": "Start, first transition midpoint, final frame",
                                 "note": "Headless browser evidence. Stills do not establish perceived smoothness."})
        except Exception as error:
            issues.append(f"{label}: playback inspection failed ({type(error).__name__}).")
    page.emulate_media(reduced_motion="reduce")
    page.reload(wait_until="load")
    fallback_ok = page.locator(selector).evaluate_all("""scenes => scenes.every(scene => {
        if (scene.hasAttribute('data-photo-active')) return false;
        const frames = [...scene.firstElementChild.children];
        const positions = frames.map(frame => frame.getBoundingClientRect().toJSON());
        return frames.every((frame, i) =>
            frame.firstElementChild.getBoundingClientRect().height > 0 &&
            frame.lastElementChild.getBoundingClientRect().height > 0 &&
            getComputedStyle(frame).opacity === '1' && positions[i].height > 0
        ) && positions.every((rect, i) => !i || Math.abs(rect.top - positions[i-1].top) > 1 ||
            Math.abs(rect.left - positions[i-1].left) > 1);
    })""")
    if not fallback_ok:
        issues.append("Photo sequence: reduced-motion fallback must show every frame and caption.")
    return {"issues": issues, "observations": observations}
