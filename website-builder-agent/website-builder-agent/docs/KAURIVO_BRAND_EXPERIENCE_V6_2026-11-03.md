# Kaurivo V6 — source-bound brand character, real mobile first-fold evidence

**3 November 2026. Universal system improvement, not a per-client redesign.**

## Known failure

The Karjalanneito demo included the original florist logo image and the
entire 45-photo source gallery. Its code tests and public responsive browser
checks passed. Yet side-by-side mobile review showed that the original
delicate script-like brand experience and pale palette had become a dark,
bold, all-caps agency identity. Authentic bouquet photography began later
than an image-led flower-shop's most useful first-screen introduction.

The underlying bug was a **false equivalence**: original logo URL in HTML
and consistent site tokens did not imply original brand personality.

## Implemented gates

1. **Source evidence first** — `extract_source_identity` now records
   observed text-bearing original header wordmarks where the source DOM
   provides them. It never invents the font family from a string and
   cannot extract font artwork embedded inside an image. The source-bound
   blueprint exposes actual wordmark text, original logo candidate URLs,
   palette theme metadata and source photographic references.
2. **Independent brand-experience audit** —
   `audit_brand_experience(rendered_pages,research)` distinguishes
   deterministic errors from unverified visual comparisons.
   Explicit `brand_character_plan.replace_wordmark`,
   `replace_brand_character` or `replace_source_photography` triggers
   a **blocking** unapproved rebrand unless a current source/build-bound
   client approval exists. All other apparent visual preservation stays
   **review required** until source/new paired screenshot evidence has
   been reviewed across the exact site routes and at 320, 390, 1440 px.
   A matching source logo alone cannot satisfy this criterion.
3. **Browser first fold** — real Chromium inspect_site outputs an
   evidence-only `first_fold_observations` record at 320 / 390 / 768 /
   1440 and a human review flag when a page contains authentic-looking
   image elements but they begin below the entire phone viewport.
   It is NOT a universal image-first rule: service, legal, booking,
   informational and accessibility contexts may be text-first. A CSS
   background may require screenshot review and cannot be classified by
   the image-element metric.
4. **No fake 9.5/10** — a human screenshot evidence record must cite
   the exact source snapshot and rendered build, route set, three paired
   before/after viewport references, and six observations (full original
   wordmark, character of original color palette, mobile fold, company
   voice, photo priority and other-client template similarity).
   Metadata validation is NOT verification that screenshot files are
   genuine, the reviewer is independent, the rights are cleared, or
   the design deserves a score. Those remain real human/client checks.
5. **Regressions** — tests with fictional company facts demonstrate that
   an unchanged logo does not silently approve a new identity, stale
   builds/source invalidate comparisons, unauthorised declared rebrands
   block, an image-less first phone fold is flagged without penalizing
   legitimate text-first businesses, and real images above the fold are
   measured.

## Required acceptance workflow for any future client

- Compare ORIGINAL and NEW site side by side at 320 / 390 / 1440.
- Check real company full logo/wordmark, not only asset path.
- Determine true sector, company identity, original color character,
  approved work photos, customer voice and special sensitive service paths.
- Identify original company first-fold objective and whether actual
  work / product should be seen immediately.
- Record exact-build, source-bound human reviewer observations for every
  route, including why each major design choice preserves or intentionally
  changes original identity.
- If source screenshots or image rights cannot be verified, mark
  REVIEW REQUIRED. Do not call an internal demo client-ready.
- The customer may explicitly approve a major brand refresh. That
  is a separate documented choice, not an accidental redesign.
- Test external image permission/reachability and customer-editable CMS
  before final commercial launch.

## What this does not yet do

This change does **not** visually rebuild Karjalanneito V1, independently
score it or claim it reaches 9.5/10. It closes an important quality-system
blind spot and makes the next client design less likely to silently repeat
the same mistake. It does not assert that a URL alone grants media rights.
