"""V7 reference UX evidence from a REAL browser scroll, not one screenshot.

This is observational instrumentation, not a 9.5 aesthetic score or a
licence to reproduce a competitor's branding, media or interaction design.
Never click forms, bookings, purchases or external links.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from PIL import Image, ImageDraw


PROTOCOL = "real-browser-scroll-v1"
FRACTIONS = (0.0, 0.25, 0.5, 0.75, 1.0)

# Read-only DOM observation at each *actual* scroll position.
_OBSERVE = """() => {
  const visible = el => {
    const r=el.getBoundingClientRect(), s=getComputedStyle(el);
    return r.height>0 && r.width>0 && r.bottom>0 &&
      r.top<innerHeight && s.display!=='none' && s.visibility!=='hidden';
  };
  const txt = el => (el.innerText || el.textContent || '').trim().replace(/\\s+/g,' ').slice(0,100);
  const sample = (selector,limit) =>
    [...document.querySelectorAll(selector)].filter(visible).slice(0,limit).map(txt).filter(Boolean);
  return {
    y: Math.round(scrollY),
    viewport_height: innerHeight,
    page_height: Math.max(document.documentElement.scrollHeight,document.body.scrollHeight),
    headings: sample('main h1,main h2,main h3,h1,h2',7),
    ctas: sample('a[href],button',5),
    media_visible: [...document.querySelectorAll('main img,main video,picture img')]
      .filter(visible).length,
    animations_running: document.getAnimations ? document.getAnimations()
      .filter(x=>x.playState==='running').length : 0,
    sticky_visible: [...document.querySelectorAll('header,nav,[style*="sticky"],[style*="fixed"]')]
      .filter(visible).filter(x=>['fixed','sticky'].includes(getComputedStyle(x).position))
      .length
  };
}"""


def record_scroll_experience(page, *, output_prefix: str | Path) -> dict:
    """Scroll through a real loaded page in five steps with time for reveals.

    Save distinct viewport frames, DOM observations and a same-position motion
    sample. Visual differences may be video/lazy loading; they aren't graded.
    No clicks on live business actions. Browser and external URL safety belong
    to the caller's restricted Playwright context.
    """
    prefix = Path(output_prefix)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    try:
        page.evaluate("window.scrollTo(0,0)")
        page.wait_for_timeout(170)
        extent = page.evaluate("""() => Math.max(
            document.documentElement.scrollHeight,document.body.scrollHeight)-innerHeight""")
        if not isinstance(extent,(int,float)):
            return {"protocol":PROTOCOL,"status":"capture_failed",
                    "reason":"Document scroll extent could not be measured."}
        # A scene driven by canvas/transform may have no native scroll height.
        # Still issue real wheel events, but only accept it if the live scene
        # visually advances across several positions. A short static page
        # therefore remains NOT a scroll benchmark.
        # Scroll like an actual visitor instead of only moving the viewport
        # instantaneously. Wheel lets intersection/reveal handlers run.
        view = page.viewport_size or {"width":390,"height":844}
        page.mouse.move(view["width"] * .58,view["height"] * .63)
        last_goal = 0
        for index, fraction in enumerate(FRACTIONS):
            goal=round(extent*fraction) if extent>=260 else round(view["height"]*2*fraction)
            if goal>last_goal:
                chunks=max(1,min(9,round((goal-last_goal)/max(180,view["height"]*.40))))
                for step in range(chunks):
                    page.mouse.wheel(0,(goal-last_goal)/chunks)
                    page.wait_for_timeout(65)
            page.wait_for_timeout(260)
            last_goal=goal
            observation = page.evaluate(_OBSERVE)
            image = prefix.parent / (prefix.name + f"-{index}.png")
            page.screenshot(path=str(image),full_page=False,animations="allow",timeout=12000)
            frames.append({**observation,"fraction":fraction,"screenshot":str(image),
                           "sha256":sha256(image.read_bytes()).hexdigest()})
        # Five actual viewport captures become one labelled sequence: models
        # see the visual rhythm without exceeding free-vision image budgets.
        strips=[]
        for frame in frames:
            with Image.open(frame["screenshot"]) as screenshot:
                canvas_width = 300 if page.viewport_size["width"]>700 else 200
                height = max(120, round(screenshot.height * canvas_width / screenshot.width))
                strips.append(screenshot.convert("RGB").resize((canvas_width,height)))
        margin=24
        sheet=Image.new("RGB",(sum(im.width for im in strips),max(im.height for im in strips)+margin),"white")
        draw=ImageDraw.Draw(sheet)
        left=0
        for frame,im in zip(frames,strips):
            sheet.paste(im,(left,margin))
            draw.text((left+5,5),str(round(frame["fraction"]*100))+"% scroll",fill="black")
            left+=im.width
        sheet_path=prefix.parent/(prefix.name+"-scroll-sequence.jpg")
        sheet.save(sheet_path,quality=83,optimize=True)
        # Observe at one unchanged position, not merely a visual change caused
        # by scrolling to different content. This is only a motion *signal*.
        page.evaluate("(y)=>window.scrollTo(0,y)",round(extent*0.5))
        page.wait_for_timeout(110)
        a = sha256(page.screenshot(full_page=False,animations="allow")).hexdigest()
        page.wait_for_timeout(510)
        b = sha256(page.screenshot(full_page=False,animations="allow")).hexdigest()
        # No destructive navigation. Hover on actual desktop navigation only.
        hover_change = None
        if page.viewport_size and page.viewport_size["width"] > 700:
            try:
                nav = page.locator("header nav a, nav a").first
                if nav.count() and nav.is_visible(timeout=1000):
                    before = sha256(page.screenshot(full_page=False,animations="allow")).hexdigest()
                    nav.hover(timeout=1500)
                    page.wait_for_timeout(150)
                    after = sha256(page.screenshot(full_page=False,animations="allow")).hexdigest()
                    hover_change = before != after
            except Exception:
                hover_change = None
        page.evaluate("window.scrollTo(0,0)")
        steps = {row["y"] for row in frames}
        rendered_steps = {row["sha256"] for row in frames}
        # Scroll-jacked/canvas sites may animate on wheel while window.scrollY
        # remains 0. Recorded video is required by global-craft QA in this case.
        visually_advanced = len(rendered_steps) >= 3
        browser_advanced = len(steps) >= 3
        return {"protocol":PROTOCOL,
                "status":"observed" if (browser_advanced or visually_advanced) else
                         ("not_scrollable" if extent<260 else "insufficient_scroll_steps"),
                "scroll_mechanism":"native" if browser_advanced else
                                   "visual_without_native_scroll",
                "browser_scrolled":True,
                "viewport_width":page.viewport_size["width"] if page.viewport_size else 0,
                "url":page.url,
                "document_scroll_range":round(extent),
                "frames":frames,
                "scroll_sequence_image":str(sheet_path),
                "same_position_visual_change":a!=b,
                "nav_hover_visual_change":hover_change,
                "quality_review_required":True,
                "caveat":"Animation/hover signals and photos do not prove smoothness or design quality."}
    except Exception as exc:
        return {"protocol":PROTOCOL,"status":"capture_failed",
                "error_type":type(exc).__name__,"quality_review_required":True}


def complete_scroll_evidence(shots: dict, *, require_video: bool = False) -> bool:
    """Do not promote a single full-page screenshot to a UX benchmark."""
    journey = shots.get("scroll_experience") if isinstance(shots,dict) else None
    if not isinstance(journey,dict):
        return False
    for view in ("desktop","mobile"):
        record=journey.get(view)
        if not isinstance(record,dict) or record.get("protocol")!=PROTOCOL or record.get("status")!="observed":
            return False
        if require_video:
            video=record.get("video_path")
            if not isinstance(video,str):
                return False
            try:
                if not Path(video).is_file() or Path(video).stat().st_size <= 300:
                    return False
            except OSError:
                return False
        sequence=record.get("scroll_sequence_image")
        if not isinstance(sequence,str) or not Path(sequence).is_file():
            return False
        frames=record.get("frames")
        if not isinstance(frames,list) or len(frames)<5:
            return False
        moved=len({f.get("y") for f in frames if isinstance(f,dict)})>=3
        visuals=len({f.get("sha256") for f in frames if isinstance(f,dict)})>=3
        if not moved and not (require_video and visuals):
            return False
        for frame in frames:
            if not isinstance(frame,dict) or not isinstance(frame.get("screenshot"),str):
                return False
            file=Path(frame["screenshot"])
            try:
                if (not file.is_file() or file.stat().st_size<24 or
                        file.read_bytes()[:8]!=bytes.fromhex("89504e470d0a1a0a") or
                        sha256(file.read_bytes()).hexdigest()!=frame.get("sha256")):
                    return False
            except OSError:
                return False
    return True


def compact_scroll_observations(shots: dict) -> dict:
    """Facts for Builder/QA prompts; never invent a premium quality score."""
    journey=shots.get("scroll_experience") if isinstance(shots,dict) else None
    out={"protocol":PROTOCOL,"verified":complete_scroll_evidence(shots),"views":{}}
    if not isinstance(journey,dict):
        return out
    for view in ("desktop","mobile"):
        rec=journey.get(view) or {}
        if not isinstance(rec,dict):
            continue
        frames=rec.get("frames") or []
        out["views"][view]={
            "status":rec.get("status"),
            "scroll_range":rec.get("document_scroll_range"),
            "scroll_story":[{"at":f.get("fraction"),
                             "headings":(f.get("headings") or [])[:4],
                             "media_visible":f.get("media_visible"),
                             "sticky_visible":f.get("sticky_visible"),
                             "animations_running":f.get("animations_running")}
                            for f in frames[:5] if isinstance(f,dict)],
            "same_position_visual_change":rec.get("same_position_visual_change"),
            "nav_hover_visual_change":rec.get("nav_hover_visual_change"),
        }
    return out
