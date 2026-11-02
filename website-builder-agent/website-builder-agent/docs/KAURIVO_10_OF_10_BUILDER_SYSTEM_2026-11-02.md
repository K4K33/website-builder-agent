# Kaurivo — one premium Builder for all clients (2026-11-02)

## Goal and truthfulness
The aspirational design target is **10/10** for every new client website.
Design quality is partly subjective: no internal regex, self-rated AI score or
one-off screenshot is proof of 10/10. Internal first-approval threshold remains
**independent >=9.5/10**, exact build, both desktop and mobile, no critical
issues, source fidelity and ownership approval. A high score does not excuse
missing legal/permission/CMS/functional requirements. Keep all these gates separate.

The product to improve is the **system that designs sites**, not three specific
HTML snapshots. Client examples are *regression cases*, never reusable templates.
Any new failure creates a rule, test, documented fix and repeatable QA check;
ensure the new rule applies to previously unseen companies.

## Stage A — first-party research and creative DNA (no website template)
1. Inventory every important original page: accurate products/services, customer
   questions, all pricing and hours, menu/dietary labels, photo galleries,
   verified logo, approved colors, partners in the footer, link destinations.
2. Mark assets as client-owned/permission-confirmed, source-only internal demo,
   third-party licensed or missing. Never confuse source display with permission.
3. Collect at least three specific same-industry design benchmarks with desktop
   and mobile captures. Use patterns/lessons, not competitor designs or company facts.
4. Create a distinct company-specific 'visual DNA' decision sheet: first-view
   thesis, dominant credible media/typography choice, grid/spacing rhythms,
   text personality, brand cues, photo treatment, contact journey, functional
   interaction and measurable acceptance criteria. Reject shared agency grids
   when visually indistinguishable.
5. Record a concrete media plan: source URL or local file, right/license status,
   required display resolution, crop/focal point, stable delivery and fallback.
   If a photo is unavailable, choose a deliberate text-led art direction, never
   an empty hero placeholder. A restaurant and a construction company can both
   use high-end design but should not share the same hero/card layout.

## Stage B — production-quality build (mixed content and page architecture)
- Use real company-specific assets; source logo must be original and sharp.
  SVG/vector preferred where available, raster logo minimum 1.5x rendered
  size and ideally 2x. Do not invent replacement branding.
- Build independent page compositions, not just different palettes on a
  common skeleton. Preserve essential original information and footer logos.
- Implement native navigation, genuine CTA and full mobile hierarchy.
- Visual depth is **optional**: purposeful layering, restrained shadows,
  CSS transform/opacity, only on fine-pointer devices when meaningful.
  Full functionality without motion, hover or JS; reduced-motion respected.
- Prefer accessible, fast native scrolling and responsive, optimized pictures.
  No hardcoded client images or CSS themes in the universal Builder module.

## Stage C — machine-checkable visual media integrity
The free `utils/visual_media_gate.py` runs on **every** generated HTML page
before an expensive review. It blocks absent local assets and undersized
header raster logos. It marks unverified remote images as **not ready** for
first owner preview until public HTTP/image checks are tied to the exact
HTML build. It never claims rights or aesthetics from an HTTP 200.
The local Playwright browser QA force-loads lazy images, detects broken
images and measures real displayed vs natural pixels for header logos.
Screenshots must be inspected even if these deterministic checks pass.
No external API credits are required for this preflight.

For remotely hosted images, one of two paths is required:
- The owner/licensor supplies a permitted local optimized copy, checked
  offline in the built site; or
- Exact public image URLs are independently checked on the published
  preview and the evidence stores the corresponding HTML SHA-256; only then
  can external images be marked verified (permissions remain separate).
  The offline browser still blocks remote network resources, so local media
  remains preferred for reliable visual screenshot QA.

## Stage D — functional, content, and real multi-device QA
- Check copy quality, exact links, authentic logo, full source content parity,
  no invented prices/reviews/food allergens and no formulaic AI slogans.
- Capture 320, 390, 768, 1440px at minimum (1920 recommended) with real
  assets and intended fonts. Verify first viewport, page rhythm, photo crop,
  depth, contrast, keyboard/touch, native scrolling, layout stability, image
  loading, reduced motion and no script/console issues.
- Missing visual proof is a HOLD, not an auto-generated 10/10.
- If any objective check fails, repair the **shared cause in the pipeline**,
  add a free regression test and rerun. Site-specific creative refinements
  remain site-specific rather than contaminating the global design system.

## Stage E — independent and sample-based acceptance
- External reviewer receives exact published build, screenshots for desktop
  and mobile, brand source, goals and industry references. Review at least
  three routes if multi-page, plus real CTA and navigation tests.
- Target: 10/10 experience; accept only independently supported >=9.5/10
  and zero critical issues. Audit originality, imagery, typography, conversion,
  accessibility, trust, copy and motion individually. Do NOT fabricate scores.
- Test a blind holdout of multiple **unseen industries/companies** before
  claiming the Builder generalizes. A revised set of three known demos is
  not proof of first-pass quality.
- Customer release remains separate: rights, branded HTTPS, verified
  contact-form delivery, actual customer-editable CMS and client permission.

## Examples are evidence, never special cases
- Automotive garage: missing workshop photo or blank colored hero is a
  generalized 'critical first-view asset' failure; use proper reliable media
  and purposeful contact hierarchy.
- Restaurant: undersized cropped script logo is a generalized 'primary brand
  raster sharpness' failure; request full-resolution original. All food and
  allergen claims must have sourced dates and exact labels.
- Construction: successful dark portfolio hierarchy can be a positive design
  reference, but it must NOT become the next default theme. Repeat images
  and unverified partner marks still get checked.

## Regression budget
Offline fixture tests run on every PR, before any real network access.
Use free browser/fixture tests for the first QA pass, and avoid Tavily/LLM
or limited API credits on deterministic failures. External public HTTP
verification can be run after a successful Pages deploy. No new domains,
paid media, customer outreach or purchases without explicit consent.
