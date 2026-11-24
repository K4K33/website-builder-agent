"""Craft floor for every built page, distilled from two open-source skill sets.

Sources (installed in full under the repository's .claude/skills/ for Claude's own work):
- Impeccable by Paul Bakaus (Apache 2.0): modes, craft floor, refuse-list.
- Emil Kowalski's design-engineering skills (MIT): animation decision framework,
  easing, durations, press feedback, performance and accessibility rules.
The builder cannot load skills, so the rules it needs are restated here in our
own words and added to every build prompt.
"""

CRAFT_BRIEF = """CRAFT FLOOR (Impeccable + Emil Kowalski, applied to every page):
Mode first: a business site is PERSUADE (the visitor decides and acts: bold, committed, real imagery); a booking
or customer area is OPERATE (scanability and known patterns beat expression); a long guide is READ.
Motion decisions, in order:
- Should it animate? Things seen many times a minute (menus, hovers, keyboard actions) barely move; a scroll story,
  a first visit or a confirmation may.
- Purpose: show how the work happens, keep spatial sense, confirm an action, or soften an otherwise jarring
  change. "Looks cool" alone is not a purpose.
- Easing: entering/exiting = strong ease-out cubic-bezier(.23,1,.32,1); moving on screen = ease-in-out
  cubic-bezier(.77,0,.175,1); never ease-in for interface motion; constant motion = linear.
- Duration: press 100-160ms, small popovers 125-200ms, menus 150-250ms, drawers/modals 200-500ms; exits faster
  than entrances; storytelling scroll motion may be longer.
- Nothing appears from nothing: start at scale(.95)+opacity 0, never scale(0); popovers grow from their trigger.
- Every pressable element answers the press: transform: scale(.97) on :active.
- Hover effects only under @media (hover:hover) and (pointer:fine).
- Use transitions (interruptible) for interface state, keyframes only for fixed sequences; one authored moment
  per page, not the same entrance on every section; stagger groups 30-80ms, uneven, never blocking input.
- Animate transform, opacity, clip-path, filter (blur under 20px) only; never width/height/margins. A light
  blur hides an imperfect crossfade. clip-path inset() is the tool for reveals, wipes and before/after sliders.
- Reduced motion means gentler, not none: keep opacity/colour changes, drop movement.
Craft floor checks on the rendered page:
- Contrast: body text 4.5:1, large text 3:1; secondary text on a colour field is tinted from that hue, never grey.
- Brand: keep the client's existing logo, colours and typeface on every page and strengthen them; never swap the
  brand for a new look. One type system for the site's own text (one family ideal, two at most); showcased example/client work keeps its
  own identity inside a framed [data-showcase]. Never ship wireframe guides or annotation labels; text never overlaps text.
- Type: body 65-75 characters per line; display tracking no tighter than -0.04em; balanced headings; clear size
  and weight steps; a real display face chosen for the brand, never the platform sans as the display voice.
- Spacing: tight inside groups, generous between them, more space above a heading than below it.
- Browser surfaces carry the design too: text selection colour, focus rings, caret, underline offset, numerals.
- States: hover, focus, disabled, loading, error and empty all designed.
Refuse unless the brief explicitly asks: same-size icon+heading+text cards as page structure; the big-number hero
template; an eyebrow/kicker label above headings (always refuse); 01/02/03 numbering (even for a real sequence, prefer words; a plain numbered how-to list is the only exception);
gradient text; decorative glassmorphism; a coloured bar down one side of a box; hard zero-blur offset shadows;
emoji or unicode as icons; a circle or polygon mask faking a photo cut-out; light or dark chosen by category
instead of by where and how the site is used."""
