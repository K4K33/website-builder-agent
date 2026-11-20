# Award study: what winning small-business sites actually do

Measured 20.11.2026 in a real browser at 1440x900: computed fonts, sizes,
colours by page area, libraries in the page, and scroll captures. Sites were
chosen from Awwwards category listings closest to Kaurivo's clients
(construction, food producers, cafes). These are observations for learning;
never copy their text, images, colours or identity into a client site.

| Site (award) | Palette by area | Type | Motion and media | The one idea |
| --- | --- | --- | --- | --- |
| Delta Cafés, coffee (Site of the Day) | Espresso brown #2B1B14 over almost the whole page; text peach #E3C1AD, not white; brand red only in the logo | Light custom display serif (300) at 77 px, line-height 1.0, tracking -0.02em; condensed uppercase gothic for small labels | 11 videos, 5 canvases, Lenis, Rive; factory robot video hero | The product's own colour becomes the page |
| Agrumea Farm, preserves (Site of the Day) | Cream #FDF3EB, burgundy #762530 text and shape, orange #E94E1B accent, all taken from the jars | IvyMode serif display, Ivy Style sans body; burgundy body text | Cut-out jars on an arc that turns with scroll, rotating type ring; 10 canvases, Lenis | One gesture: scroll turns the product wheel |
| BCG Building Design, builder (Honorable Mention) | Warm paper #F3EFE8 and dark brown #3A3028 only | One family (Neue Haas Display) at 600, 40 px headings, 14-16 px everything else | Project photo grows from half split to full bleed on scroll while text steps aside; GSAP ScrollTrigger, SplitText, Lenis, Barba | Restraint: two colours, one font, big real photography |
| Nettie's Bees, honey (nominee) | Cream page, dark honey-brown #2B1A0E ink, honey #E4A62F action, burgundy #8E1F2F band | Boska serif 128 px / 0.9 line-height / -0.03em; General Sans body 23 px | Numbered real process steps with sticky photo carousel (genuine sequence); marquee of stockists | Process story from hive to jar with real photos |
| DC Carpentry, builder (nominee) | Sage #DCE3D8 and stone #D8CBB7 surfaces, deep green #344C3A action | Satoshi throughout, 700 headings with -0.04em | Hero video of real work, project cards with real before/after photos | Local proof: real projects, area, reviews |

## Patterns that repeat

1. Palette comes from the company's own product or place, not from a trend:
   one dominant tone covers most of the page, ink is tinted from it, and the
   accent is saved for action. `utils/award_playbook.derive_photo_palette`
   does this from the company's photos with WCAG checks.
2. Two type families at most, and the display face has character (light serif
   or tight heavy grotesque), set very large with tight leading and tracking.
3. One idea per page, executed with real media. Motion serves that idea.
4. Restraint elsewhere: small quiet navigation, few buttons, generous space,
   no rows of identical icon cards.

## Hero patterns from the "stop designing boring hero sections" reference

Product interface floating over a glowing horizon; aerial photo with a small
data card proving the claim; one product object in a cinematic scene; a
building drawn in lines that becomes real; particles forming a hand. The
common rule is one claim plus one cinematic subject plus one proof detail.
Kaurivo implements the building-from-lines idea with the company's own photo
(`data-scrub-style="blueprint"`): a free line drawing from photo and depth
edges is built up from the ground into the real photograph as the visitor
scrolls.
