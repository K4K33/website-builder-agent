"""Kaurivo Motion Kit: deterministic, premium section renderer.

A free model is good at choosing and filling content but poor at authoring
high-end CSS/JS from scratch (20.11.2026 audit). Here the hand-built kit owns
layout, motion, accessibility and responsiveness; a model only returns a
JSON section plan (archetype + slots) built from VERIFIED source content and
the company's own images. All text is HTML-escaped. Brand colours and fonts
arrive as tokens; the kit never supplies a brand, stock image or claim.

Archetypes map to docs/KAURIVO_VISUAL_PLAYBOOK.md compositions:
    process_reveal   - "Product or process reveal" + "Transition as scroll"
    cinematic        - "Wide cinematic scene"
    masthead         - "Masthead with inset project"
    editorial_split  - "Paired stage and copy" / "Asymmetric editorial grid"
    project_explorer - "Project explorer" / "Spatial browsing"
    before_after     - "Sequence or before/after"
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

ASSET_DIR = Path(__file__).resolve().parents[1] / "assets" / "motion_kit"
KIT_VERSION = "kaurivo-motion-kit-v1"

ARCHETYPES = ("process_reveal", "cinematic", "masthead", "editorial_split",
              "project_explorer", "before_after")
HERO_ARCHETYPES = ("process_reveal", "cinematic", "masthead")

_HEX = re.compile(r"#[0-9a-fA-F]{6}")
_FONT = re.compile(r"[A-Za-z0-9 \-]{2,40}")
TOKEN_KEYS = ("canvas", "surface", "ink", "ink_2", "line", "accent", "accent_ink",
              "dark", "dark_ink")


def kit_css() -> str:
    return (ASSET_DIR / "kit.css").read_text(encoding="utf-8")


def kit_js() -> str:
    return (ASSET_DIR / "kit.js").read_text(encoding="utf-8")


def _t(value, limit=600) -> str:
    text = " ".join(str(value or "").split())
    if not text:
        raise ValueError("empty text slot")
    return escape(text[:limit], quote=True)


def _opt(value, limit=600) -> str:
    text = " ".join(str(value or "").split())
    return escape(text[:limit], quote=True) if text else ""


def _href(value) -> str:
    url = str(value or "").strip()
    if not re.fullmatch(r"(https://|mailto:|tel:\+?[0-9 ]{5,20}$|/|\./|#)[^\s\"'<>]*", url):
        raise ValueError("unsafe or missing link")
    return escape(url, quote=True)


def _img(image: dict, *, eager=False, sizes="100vw") -> str:
    if not isinstance(image, dict):
        raise ValueError("image slot must be an object")
    src = str(image.get("src") or "")
    if not re.fullmatch(r"(https://|\./|assets/|media/|data:image/(webp|jpeg|png|svg\+xml);base64,)[^\s\"'<>]+", src):
        raise ValueError("image src must be a local asset or https URL")
    alt = _t(image.get("alt"), 180)
    width, height = int(image.get("width") or 0), int(image.get("height") or 0)
    dims = f' width="{width}" height="{height}"' if width > 0 and height > 0 else ""
    position = str(image.get("position") or "50% 50%")
    if not re.fullmatch(r"\d{1,3}% \d{1,3}%", position):
        position = "50% 50%"
    loading = 'loading="eager"' if eager else 'loading="lazy" decoding="async"'
    return (f'<img src="{escape(src, quote=True)}" alt="{alt}"{dims} {loading} '
            f'sizes="{sizes}" style="object-position:{position}">')


def _actions(slots: dict, *, dark=False) -> str:
    parts = []
    primary = slots.get("primary_action")
    if isinstance(primary, dict):
        parts.append(f'<a class="k-button" href="{_href(primary.get("href"))}">{_t(primary.get("label"), 60)}</a>')
    secondary = slots.get("secondary_action")
    if isinstance(secondary, dict):
        parts.append(f'<a class="k-textlink" href="{_href(secondary.get("href"))}">{_t(secondary.get("label"), 60)}</a>')
    return f'<div class="k-actions">{"".join(parts)}</div>' if parts else ""


def render_tokens(tokens: dict) -> str:
    """CSS custom properties from verified brand tokens (hex + font names)."""
    tokens = tokens if isinstance(tokens, dict) else {}
    lines = []
    for key in TOKEN_KEYS:
        value = str(tokens.get(key) or "")
        if _HEX.fullmatch(value):
            lines.append(f"--k-{key.replace('_', '-')}: {value};")
    for key, var in (("font_display", "--k-font-display"), ("font_body", "--k-font-body")):
        value = str(tokens.get(key) or "")
        if _FONT.fullmatch(value):
            lines.append(f"{var}: '{value}', system-ui, sans-serif;")
    weight = tokens.get("display_weight")
    if isinstance(weight, int) and 100 <= weight <= 900:
        lines.append(f"--k-display-weight: {weight};")
    leading = tokens.get("display_leading")
    if isinstance(leading, (int, float)) and 0.85 <= leading <= 1.3:
        lines.append(f"--k-display-leading: {leading};")
    radius = tokens.get("radius_px")
    if isinstance(radius, int) and 0 <= radius <= 24:
        lines.append(f"--k-radius: {radius}px;")
    return ":root{" + "".join(lines) + "}"


def render_process_reveal(s: dict) -> str:
    stages = s.get("stages")
    if not isinstance(stages, list) or not 2 <= len(stages) <= 6:
        raise ValueError("process_reveal needs 2-6 real stages")
    frames = "".join(
        f'<figure class="k-process__frame{" is-active" if i == 0 else ""}" style="margin:0">'
        f'{_img(st.get("image"), eager=(i == 0))}</figure>' for i, st in enumerate(stages))
    steps = "".join(
        f'<li class="k-process__step{" is-active" if i == 0 else ""}"><div><strong>{_t(st.get("title"), 80)}</strong>'
        f'<span>{_t(st.get("text"), 220)}</span></div></li>' for i, st in enumerate(stages))
    hint = _opt(s.get("scroll_hint"), 80)
    return (f'<section class="k-process" data-k-process aria-label="{_t(s.get("aria_label") or s.get("heading"), 120)}">'
            f'<div class="k-process__track" style="--k-steps:{len(stages)}"><div class="k-process__stage">'
            f'<div class="k-process__frames">{frames}</div>'
            f'<div class="k-process__panel"><h1 class="k-display">{_t(s.get("heading"), 120)}</h1>'
            f'<ol class="k-process__steps">{steps}</ol>'
            f'{f"<p class=k-process__hint>{hint}</p>" if hint else ""}'
            f'{_actions(s, dark=True)}</div></div></div></section>')


def render_cinematic(s: dict) -> str:
    side = " k-cine--right" if s.get("copy_side") == "right" else ""
    return (f'<section class="k-cine{side}" data-k-cine><div class="k-cine__media">{_img(s.get("image"), eager=True)}</div>'
            f'<div class="k-cine__copy"><h1 class="k-display">{_t(s.get("heading"), 120)}</h1>'
            f'<p class="k-lead">{_t(s.get("lead"), 260)}</p>{_actions(s)}</div></section>')


def render_masthead(s: dict) -> str:
    caption = _opt(s.get("caption"), 160)
    return (f'<section class="k-mast"><div class="k-wrap"><h1 class="k-display">{_t(s.get("heading"), 90)}</h1>'
            f'<div class="k-mast__grid"><div><p class="k-lead">{_t(s.get("lead"), 260)}</p>{_actions(s)}</div>'
            f'<figure class="k-mast__figure">{_img(s.get("image"), eager=True, sizes="(min-width: 820px) 55vw, 100vw")}'
            f'{f"<figcaption>{caption}</figcaption>" if caption else ""}</figure></div></div></section>')


def render_editorial_split(s: dict) -> str:
    facts = s.get("facts") or []
    if not isinstance(facts, list) or len(facts) > 6:
        raise ValueError("editorial_split facts must be a list of at most 6")
    rows = "".join(f'<div><dt>{_t(f.get("term"), 60)}</dt><dd>{_t(f.get("detail"), 200)}</dd></div>' for f in facts)
    flip = " k-split--flip" if s.get("image_side") == "right" else ""
    sid = re.sub(r"[^a-z0-9-]", "", str(s.get("id") or "")) or "palvelut"
    return (f'<section class="k-split{flip}" id="{sid}"><div class="k-wrap k-split__grid">'
            f'<div class="k-split__media">{_img(s.get("image"), sizes="(min-width: 820px) 58vw, 100vw")}</div>'
            f'<div class="k-split__copy"><h2 class="k-h2">{_t(s.get("heading"), 100)}</h2>'
            f'<p class="k-body">{_t(s.get("text"), 700)}</p>'
            f'{f"<dl class=k-facts>{rows}</dl>" if rows else ""}{_actions(s)}</div></div></section>')


def render_project_explorer(s: dict) -> str:
    items = s.get("items")
    if not isinstance(items, list) or not 2 <= len(items) <= 12:
        raise ValueError("project_explorer needs 2-12 real projects")
    cards = "".join(
        f'<li><figure class="k-explore__item">{_img(it.get("image"), eager=(i < 2), sizes="(min-width: 720px) 620px, 86vw")}'
        f'<figcaption><strong>{_t(it.get("title"), 80)}</strong>'
        f'{"<span>" + _opt(it.get("detail"), 140) + "</span>" if it.get("detail") else ""}'
        f'</figcaption></figure></li>' for i, it in enumerate(items))
    labels = s.get("control_labels") or {}
    prev_label = _t(labels.get("previous") or "Edellinen", 30)
    next_label = _t(labels.get("next") or "Seuraava", 30)
    sid = re.sub(r"[^a-z0-9-]", "", str(s.get("id") or "")) or "kohteet"
    return (f'<section class="k-explore" id="{sid}" data-k-explore><div class="k-wrap k-explore__head">'
            f'<h2 class="k-h2" style="margin:0">{_t(s.get("heading"), 100)}</h2>'
            f'<div class="k-explore__controls"><button type="button" data-k-prev aria-label="{prev_label}">&#8592;</button>'
            f'<button type="button" data-k-next aria-label="{next_label}">&#8594;</button></div></div>'
            f'<ul class="k-explore__track" role="list">{cards}</ul></section>')


def render_before_after(s: dict) -> str:
    labels = s.get("labels") or {}
    return (f'<section class="k-compare"><div class="k-wrap"><h2 class="k-h2">{_t(s.get("heading"), 100)}</h2>'
            f'<p class="k-body">{_t(s.get("text"), 400)}</p>'
            f'<div class="k-compare__frame" data-k-compare>{_img(s.get("before"))}'
            f'<div class="k-compare__after">{_img(s.get("after"))}</div>'
            f'<span class="k-compare__label k-compare__label--before">{_t(labels.get("before") or "Ennen", 30)}</span>'
            f'<span class="k-compare__label k-compare__label--after">{_t(labels.get("after") or "Jälkeen", 30)}</span>'
            f'<input type="range" min="0" max="100" value="50" aria-label="{_t(labels.get("slider") or "Vertaa ennen ja jälkeen", 60)}">'
            f'<span class="k-compare__divider"></span></div></div></section>')


RENDERERS = {
    "process_reveal": render_process_reveal,
    "cinematic": render_cinematic,
    "masthead": render_masthead,
    "editorial_split": render_editorial_split,
    "project_explorer": render_project_explorer,
    "before_after": render_before_after,
}


def render_section(section: dict) -> str:
    if not isinstance(section, dict) or section.get("archetype") not in RENDERERS:
        raise ValueError("unknown archetype; allowed: " + ", ".join(ARCHETYPES))
    return RENDERERS[section["archetype"]](section.get("slots") or {})


def render_page(plan: dict) -> str:
    """Complete one-file page from a validated plan (header, sections, contact)."""
    company = plan.get("company") or {}
    sections = plan.get("sections") or []
    if not sections or sections[0].get("archetype") not in HERO_ARCHETYPES:
        raise ValueError("the first section must be a hero archetype: " + ", ".join(HERO_ARCHETYPES))
    nav = "".join(f'<a href="{_href(n.get("href"))}">{_t(n.get("label"), 30)}</a>' for n in plan.get("nav") or [])
    tel = company.get("phone")
    tel_link = (f'<a class="k-tel" href="tel:{escape(re.sub(r"[^0-9+]", "", str(tel)), quote=True)}">{_t(tel, 30)}</a>'
                if tel else "")
    logo = company.get("logo")
    brand = (_img(logo, eager=True, sizes="200px") if isinstance(logo, dict) else _t(company.get("name"), 80))
    contact = plan.get("contact") or {}
    contact_html = ""
    if contact:
        lines = "<br>".join(_t(x, 120) for x in contact.get("address_lines") or [])
        email = contact.get("email")
        contact_html = (f'<section class="k-contact" id="yhteys"><div class="k-wrap k-contact__grid"><div>'
                        f'<h2 class="k-h2">{_t(contact.get("heading"), 100)}</h2><p class="k-lead">{_t(contact.get("lead"), 260)}</p></div>'
                        f'<address>{lines}<br>{tel_link}'
                        f'{f"<br><a href=mailto:{escape(email, quote=True)}>{_t(email, 80)}</a>" if email else ""}'
                        f'</address></div></section>')
    footer = _opt(plan.get("footer"), 200)
    fonts = plan.get("font_stylesheet")
    font_link = (f'<link rel="stylesheet" href="{escape(fonts, quote=True)}">'
                 if isinstance(fonts, str) and fonts.startswith("https://fonts.googleapis.com/") else "")
    lang = "sv" if plan.get("lang") == "sv" else "fi"
    return ("<!doctype html>"
            f'<html lang="{lang}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<meta name="robots" content="noindex,nofollow"><meta name="generator" content="{KIT_VERSION}">'
            f'<title>{_t(plan.get("title"), 90)}</title><meta name="description" content="{_t(plan.get("description"), 160)}">'
            f'{font_link}<style>{kit_css()}{render_tokens(plan.get("tokens") or {})}</style></head><body>'
            f'<a class="k-skip" href="#sisalto">Siirry sisältöön</a>'
            f'<header class="k-header"><div class="k-wrap k-header__row"><a class="k-header__logo" href="./" aria-label="{_t(company.get("name"), 80)}, etusivu">{brand}</a>'
            f'<nav class="k-nav" aria-label="Päävalikko">{nav}{tel_link}</nav></div></header>'
            f'<main id="sisalto">{"".join(render_section(s) for s in sections)}{contact_html}</main>'
            f'<footer class="k-footer"><div class="k-wrap"><span>{footer}</span></div></footer>'
            f"<script>{kit_js()}</script></body></html>")
