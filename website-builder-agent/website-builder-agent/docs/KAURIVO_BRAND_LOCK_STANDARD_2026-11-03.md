# Kaurivo — Brand Lock, identity provenance and no-fabricated-marks

**Cross-company contract.** An original business redesign may change layout,
spacing, motion, accessible navigation, responsive composition and content
hierarchy. It may NOT unilaterally replace or invent a logo, emblem, letter seal,
favicon, sponsor logo, certification, customer mark, owner quote, staff image,
brand slogan, visual identity or alleged reference project.

## Source-first required sequence

1. **Inventory every original route.** Record source URL and screenshot;
   identify header logos, footer affiliations, favicon/touch icon, visual
   colors, type, photographs, confirmed slogans, brand tone and links.
   Record unread and JS-only source features instead of treating them as absent.
2. **Freeze Brand DNA before generation.** Put original asset references and
   source snapshots in structured internal records; compute a source digest.
   Explicit owner approval can designate an original mark or a permitted
   optimized replacement. A filename or verbal model claim is never proof.
3. **Asset lineage for optimized logos.** Each changed file needs the
   *original asset*, replacement path, source snapshot hash, exact current
   site digest, owner identity, approval date, lawful reuse and confirmed
   visual equivalence. Human inspection still compares the actual pixels or
   SVG geometry; a string-level URL match is NOT image authenticity.
4. **Limit generation rights.** Builder may use validated source assets,
   approved replacements and normal text using the company’s correct name.
   It must not generate letter monograms, seals, SVG brand icons, custom
   badges or matching-but-fake logos as generic styling.
5. **Validate ALL routes.** Verify header brand areas, page-specific styling,
   declared browser theme color, favicons and any approved logos on every
   subpage, not just the homepage. Verify original sponsor/partner role,
   linked logo, permission, and current relationship separately.
6. **Fail closed on invented marks.** A novel marked-up logo image or SVG in
   an explicit brand slot without evidence is a BLOCKER at demo build time.
   Missing source logos without confirmed rights may use a plain company name
   for an internal demo but stay REVIEW REQUIRED, never client-ready.
   An explicitly approved original header logo must not disappear from
   one or more pages.
7. **Release check.** Review real rendered source and redesigned screenshots,
   including full headers/footers at 320, 390, 768 and 1440. Confirm that
   any same-named image on the new site is actually the same approved asset.
   Treat uninspected CSS-generated logos, remote image bodies and dynamically
   loaded partner widgets as unresolved until a human/browser asset check.

## Implementation in Kaurivo

`utils/brand_lock.py` is the static zero-credit brand mark gate called by
`audit_universal_standards`. That same universal gate is called on all
Builder output and during QA. It identifies invented logo-like header
images and SVG marks; requires approved original logos across subpages;
checks source-verified replacements with source/build-bound client evidence;
reports favicon drift and unverified logo rights. The Research agent now
records favicon source candidates, and the brand design blueprint carries
those references to the planning stage.

**Important limitations:** Source markup does not guarantee a verified owner,
font identity, photograph rights or licence. CSS pseudo-elements, background
image URLs, SVG shapes without brand markers and spoofed source URLs can
evade a static DOM check. Dynamic browser rendering, visual logo comparison
and a real owner's signoff remain mandatory; never market passing automated
tests as a 100% authenticity guarantee.

**Hard acceptance rule:** A brand error cannot be waived because a website
received attractive visual scores. Any legitimate brand refresh is a
separate explicit owner-approved decision, not a silent redesign.
