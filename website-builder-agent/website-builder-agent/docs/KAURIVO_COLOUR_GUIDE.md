# Kaurivo colour theory and application

## Read the identity and the visual task

Start from the current approved logo, brand guide, packaging, venue and
representative photographs. Separate official identity colours, legacy UI
choices, contextual colours in photography and newly derived interface tones.
Record the source and confidence for each identity anchor. Preserve approved
marks and their clear space. An incidental colour visible in a photograph is
context for a surface or crop. It does not establish brand identity. When the
identity is poorly documented, use a defensible neutral system with restrained
accents grounded in approved material and describe the choice as a proposal.

For each concept, state the viewing conditions and visitor task. A service
comparison needs quiet readable surfaces. A project gallery may benefit from a
deep frame around bright photos. A menu may need a light, easy-to-scan surface
even if the opening uses dark photography. Design adjacent sections together so
that page rhythm supports decisions. Preserve the colour of genuine evidence
photos, including materials, skin and products.

## Understand the controls

- **Hue** distinguishes colour families and builds continuity. **Perceived
  lightness** drives tonal separation and hierarchy. **Chroma** determines how
  colourful a tone feels. Change these deliberately and diagnose them
  separately. Reducing chroma alone rarely fixes weak text contrast.
- **Area and adjacency** change perceived emphasis. The same saturated colour
  can look restrained on a button and dominate when spread across a banner.
  Adjacent strong complements can visually vibrate. Insert a neutral separator,
  change lightness or lower the chroma of one side.
- **Simultaneous contrast** means a colour is perceived in context. A neutral
  near a warm photo may read cool. Judge swatches inside the composition next
  to the actual text, photos and controls. A greyscale check helps reveal
  hierarchy hidden by hue. It does not replace a contrast measurement.
- **Temperature** is relative. Warm and cool supporting tones can frame a photo
  or separate surfaces, but universal claims about the emotions or trust a hue
  creates are unreliable. Derive suitability from the client's identity,
  industry context, content, audience and the role of the element.
- **Perceptual colour spaces**. OKLCH is useful for generating a family with
  controlled lightness, chroma and hue. Derive steps by lightness and taper
  chroma where the display gamut narrows. Same OKLCH lightness on two colours
  does not guarantee an accessible contrast ratio. Verify the resolved colours
  in the actual browser. Prefer verified sRGB tokens for critical text and
  surfaces. Test the fallback wherever modern or wide-gamut colours are used.
  Avoid naïve clipping that shifts hue or collapses adjacent steps.

## Compose and compare palette strategies

Use alternatives that fit the source. Keep the key identity anchor stable
across concepts and make the colour proposal observable in a representative
hero, the next section and a service screen.

| Strategy | Use and calibration |
| --- | --- |
| Tonal or monochromatic | Build most surfaces and ink from one hue family with significantly different lightness. Use restrained chroma on broad surfaces. Useful with a strong single-colour identity or visually busy media. Check nested surfaces and control boundaries. |
| Analogous | Use nearby hues with one dominant family and a supporting temperature shift. Distinguish their roles through value and text labels. Useful where brand colours and a coherent photographic palette already share a close range. |
| Neutral field with concentrated accent | Give media and copy a calm base. Reserve the distinctive colour for a few decisions, navigation cues or details. Derive dark/light variants for access without changing the official logo. |
| Complementary or split-complementary | Use a counter-hue as a limited counterpoint. Keep one family clearly dominant by area or chroma. Useful when a source anchor and its media support the tension. Avoid saturated equal-value text and backgrounds. |
| Multi-hue or triadic | Assign verified hues separate jobs and unequal area. Anchor the reading surface with neutrals. Suitable when the existing identity already uses several hues. Resist using all hues at full chroma in the same viewport. |
| Light and dark sections | Use a deliberate change of surface around a change of topic or media. Redesign ink, borders, buttons and focus on each surface. Avoid alternating light/dark panels by default and avoid mirroring light tokens mechanically into dark mode. |

Treat ratios such as 60/30/10 as sketches of visual weight. Actual content area,
responsive crops and element priority determine the allocation. If several
accents appear equally primary, reduce the area or chroma of secondary elements
and restore a clearly identifiable main action.

## Map selected colours to reusable roles

Assign explicit tokens for canvas, surface, elevated or inset surface, primary
ink, secondary ink, divider, links, brand display accent, action fill and ink,
focus, selected state, and required feedback states. Keep destructive actions
and error or success messages distinct from decorative brand treatments.
Specify default, hover, focus, active and disabled where applicable, including
on dark or coloured surfaces. Use the same roles across pages and language
versions, with deliberate alternate tokens when the surface changes.

For a bright logo colour with white-button contrast problems, use the original
colour in the mark, then test a dark ink on the original fill, a darker
same-family action fill, or a neutral accessible action with the brand colour
nearby. For a dark hero that competes with the photograph, shift the copy to
quiet space, change the crop, use local backing or choose a solid surface.
Retain important material and product detail in the original photo.

For gradients, decide why a transition is needed, where it starts and ends,
and what text or controls cross it. Prefer a stable backdrop for essential copy.
For transparency and glass, check the final composited state across hero
frames, scrolling positions and breakpoints. A single opaque swatch or a
gradient's endpoints cannot validate the whole text backing.

## Validate the rendered result

- Apply WCAG 2.2 AA. Normal text needs at least 4.5:1 and large text at least
  3:1 (18 pt regular or 14 pt bold, approximately 24 px or 18.67 px).
  Meaningful graphical objects and visual information needed to identify
  controls and their states need 3:1 against applicable adjacent colours
  under the non-text contrast criterion. Check actual focus visibility,
  keyboard flow and focus against each relevant surface.
- Use redundant cues for links, selected items, form errors, graphs and status.
  Prefer persistent underlines for inline links, plus labels, icons or patterns
  where information depends on distinguishing states. Inspect in greyscale and
  optionally use colour-vision simulations to find ambiguity. Neither
  simulation nor automation alone demonstrates accessibility.
- Check calculated/composited foreground and background in each relevant state,
  at desktop and mobile widths. Inspect actual photo crops, poster and video
  states. Use the existing browser findings for measurable colours. Where
  measurement is indeterminate, supply a stable backdrop or manually verify
  the actual rendered text area across states. Never infer a pass from tokens
  or a screenshot alone.
- During review identify route, viewport, component/state, competing or failing
  colour pair and a cause-specific change. Correct the role system first if
  the problem recurs. Render again and verify both the repaired element and
  the other routes, states and surfaces sharing that token.

References: [WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[non-text contrast](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast)
and [CSS Color Module Level 4](https://www.w3.org/TR/css-color-4/).
