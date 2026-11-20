# Kaurivo Motion Kit v1

Hand-built, company-agnostic sections (`assets/motion_kit/kit.css`, `kit.js`)
rendered by `utils/motion_kit.py`. The kit owns layout, motion, responsiveness
and accessibility. A free model only chooses an archetype and fills its slots
with verified source content and the company's own images, as JSON.

Why: free 26-31B models write generic CSS when asked to author a premium page
from scratch. A fixed, reviewed kit keeps the visual floor high on every build
and uses far fewer output tokens.

## Archetypes

| id | Playbook composition | Use when the source has |
| --- | --- | --- |
| `process_reveal` | Product or process reveal, transition as scroll | 2-6 real photos of consecutive work stages |
| `cinematic` | Wide cinematic scene | one strong wide photo with quiet space for copy |
| `masthead` | Masthead with inset project | a clear offer and one good project photo |
| `editorial_split` | Paired stage and copy | a service with a portrait or detail photo and verified facts |
| `project_explorer` | Project explorer | 2-12 real projects or work photos |
| `before_after` | Sequence or before/after | a genuine before and after pair of the same subject |

The first section must be a hero (`process_reveal`, `cinematic`, `masthead`).
Never fabricate a stage, project or before/after pair to fit an archetype.

## Plan format

```json
{
  "title": "...", "description": "...", "lang": "fi",
  "font_stylesheet": "https://fonts.googleapis.com/css2?family=...",
  "tokens": {"canvas": "#f6f6f3", "ink": "#1e2124", "accent": "#d2ae79",
             "accent_ink": "#1e2124", "dark": "#1e2124", "dark_ink": "#f6f6f3",
             "font_display": "Anton", "font_body": "Fira Sans",
             "display_weight": 400, "display_leading": 1.02, "radius_px": 2},
  "company": {"name": "...", "phone": "...", "logo": {"src": "...", "alt": "..."}},
  "nav": [{"label": "Palvelut", "href": "#palvelut"}],
  "sections": [{"archetype": "process_reveal", "slots": {"heading": "...",
                "stages": [{"image": {...}, "title": "...", "text": "..."}],
                "primary_action": {"label": "...", "href": "#yhteys"}}}],
  "contact": {"heading": "...", "lead": "...", "address_lines": ["..."], "email": "..."}
}
```

Images: `{"src", "alt", "width", "height", "position": "50% 40%"}`; `src` is a
local asset, an https URL or an image data URI. Tokens accept only `#rrggbb`
colours and plain font names; colours must come from the observed brand.

## Guarantees

- All text escaped; links limited to https, mailto, tel and in-page anchors.
- No external scripts or libraries; works without JavaScript.
- `prefers-reduced-motion` and no-JS show every process stage as stills.
- One `h1`, skip link, visible focus, keyboard-operable explorer and comparison.
- No stock media, brand colours or claims ship inside the kit.

## Verified on 20.11.2026

Three private concepts for the package's test company (process reveal,
cinematic, masthead) rendered at 1440x900 and 390x844 in Chromium: no console
errors, no horizontal overflow. Builder integration (model returns a plan,
renderer produces the concept) is the next step.
