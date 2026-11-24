"""Hero library and page-flow rules, collected from award-winning first folds.

Observed 24.11.2026 in a real browser (Awwwards Sites of the Month: THE LINE,
Dropbox Brand, Siena Film, Watson, Akaru, Son Daven, Terminal Industries,
Floema, Inkfish, Lama Lama, Era Residence; Squarespace home; a "steal these
interactions" reel: transition as scroll, live 3D room, spatial browsing,
touchable surface) and prototyped for Kaurivo (steel K, wordmark, blade wipe,
spatial gallery). None of them is built from boxes: the first fold is one
full-bleed subject with large, quiet type, and sections flow into each other.

The builder picks ONE hero pattern per site from what the business really
has (its photos, logo, process, products), writes why in its design notes and
builds it with the [data-story] runtime (utils.scroll_story).
"""

HERO_LIBRARY = """HERO LIBRARY (choose ONE per site from the material the business really has; name it in design notes):
1. CINEMATIC PHOTO - one full-bleed real photo or video, lots of quiet space, the name or one line in large thin
   type; scroll slowly pushes in or reveals the next scene (Son Daven, Terminal). Needs one strong own image.
2. GIANT WORDMARK - the company name across the whole width, cropped by the viewport edge; on scroll the letters
   part (alternate up/down) to reveal the work behind (THE LINE, Watson, Akaru, Kaurivo option B).
3. BRAND MARK ASSEMBLY - the logo in pieces close to the camera assembles in 3D (Kaurivo steel K; automatic via
   utils.logo_story when no own photos exist).
4. BEFORE / AFTER WIPE - the old state fills the screen; a shape from the brand (a blade, a brush stroke, a beam)
   sweeps across and leaves the finished result behind (renovation, painting, cleaning, web redesign).
5. TRANSITION AS SCROLL - full-bleed scenes that flow into each other as you scroll (through clouds, from room to
   room, from bare plot to finished house); text sits large and thin on the image.
6. SPATIAL GALLERY - the company's real work images float at different depths; the camera flies through them and
   lands on one (Floema, Squarespace wall, spatial browsing). Needs 6+ own or approved images.
7. SLATTED REVEAL - the name or photo seen through moving vertical slats that open (Siena).
8. VIDEO + INDEX - full-bleed video of the work with a quiet list of projects/services over it; hovering a row
   changes the footage (Inkfish). Needs real footage.
9. TOUCHABLE SURFACE - the hero image answers the cursor (a light that follows, a gentle ripple); always paired
   with one of the above, never alone.
Rules: the subject fills the viewport at frame 0; type is large, few words, never inside a card; the headline
and call to action are visible on load and move away as scrolling starts the story; mobile gets its own crop (phone screenshots, tall images)."""

FLOW_RULES = """PAGE FLOW, NOT BOXES (owner: "en pidä siitä, että kaikki on palikoissa"):
- Do not stack sections as rectangles with a heading left and text right, and do not put content in rows of
  bordered cards. Max one card grid per page, and only for genuinely parallel items with images.
- Alternate scale instead: a full-bleed image or scene, then a quiet text moment with lots of space, then a
  typographic list (services/prices as large type lines, not cards), then the next full-bleed moment.
- Sections may overlap and flow into each other (an image that continues under the next heading, background
  tone that blends, a sticky image while text scrolls past). No visible borders around content blocks.
- Numbers (01/02) only for a real sequence; no eyebrow label above every heading."""
