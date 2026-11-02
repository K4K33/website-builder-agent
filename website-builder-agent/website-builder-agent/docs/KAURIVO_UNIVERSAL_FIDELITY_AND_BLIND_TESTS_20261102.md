# Kaurivo: source fidelity + truly unseen-business QA

Effective: 2026-11-02. This is a **global Builder requirement**, not a
fix tailored to the last six website demos.

## Why the prior tests were insufficient

A page could pass a technical 27/27 browser smoke test while:
- dropping existing sponsor/partner marks, chain badges or linked logos;
- replacing rich original pages with a 3-section brochure;
- dropping pricing, sales/product sections, languages or project work;
- replacing the real brand palette/personality with a generic fashion palette;
- linking a supposedly redesigned product/shop/service section back to
  the hard-to-read **old** original page;
- displaying text over an image/gradient/translucent layer that static
  CSS contrast checking skipped.

No amount of polished gradients, motion, or 3D can compensate for those.

## Universal hard gates

**Research/plan:** Capture the original website's bounded multi-page inventory
and source-specific text, headings, images, header/footer marks and links.
Original-site desktop/mobile screenshots must be captured when possible.
Every observed source URL and H2/H3 topic requires an explicit local target
in `research.source_content_map`. The Research stage fails if a whole source
page/topic has no plan; the Builder checks again before paid generation.
Missing or failed crawl URLs must not be silently treated as a complete scan.

**Preservation:** The actual generated HTML must contain every mapped target
and section. Large original-to-new text shrinkage (conservatively >=650 original
words, new below 38%) is a **blocking anomaly**, not a claim that all shorter
copy is wrong. A documented, exact-snapshot **client** approval can authorize
intentional condensation. Exact content meaning still requires independent
human comparison; no keyword/word-count heuristic proves parity.

**Affiliations and sponsors:** Capture semantically marked footers AND common
div-based/ARIA footer regions. List original logos **and** linked text-only
partner/social destinations; preserve the visual mark and its correct URL
together. The old page footer image is an UNVERIFIED AFFILIATION, not proof
of an active sponsor. Require a correct relationship label and reuse rights
before public delivery. A removed original mark/link requires a
source-snapshot-bound, individual client approval, reason and reviewer.
A generic 'approved' flag cannot waive an entire old footer.

**Brand:** Preserve owner-approved old logo, original company media, relevant
colors, typography personality and voice by default. Old-site desktop/mobile
screenshots are shown alongside the rendered new site at independent QA.
A fresh fake letter logo or random fashionable palette is not approved
rebranding. If the source was never visually reviewed, mark brand fidelity
UNVERIFIED. A brand update requires explicit owner approval.

**Task continuity:** Products, offers, gallery, reference cases, sales and
price information must work in the new site when they are core customer tasks.
An old-site product/service/listing link is a FAIL unless a documented
source-specific, human-reviewed live integration is justified (e.g. actual
checkout, booking backend). Linking back to the broken old site is not a redesign.

**Readability:** WCAG 2.2 Level AA contrast minimum: 4.5:1 ordinary text,
3:1 large text. A live browser test checks solid background contrast,
flags essential content under 12px, and explicitly HOLDS text on images,
gradients or translucent panels when the ratio cannot be established.
Fix by using a genuinely legible opaque text panel or obtain verified
exact-build visual evidence. Do not convert 'cannot measure' into PASS.
Test 320/390/768/1440px, original fonts and original photo crops.

**Editorial and creative quality:** Do not copy the same hero-left/photo-right
+ three-card CTA pattern across companies. Avoid generic AI copy, repeated
antithesis formulas, decorative numbering, fabricated products/reviews and
forced 3D. Layout may be completely redesigned while logo/brand/content
stay recognizable. If a source site has multiple languages, preserve those
unless the client explicitly approves the change.

**Customer delivery** additionally requires licensed media, real contact
handling, approved HTTPS domain, a genuinely editable CMS, human approval
and independent visual >=9.5/10 on the exact build. Static automated
checks cannot claim 10/10 quality or a legal reuse right.

## One NEW company per blind quality experiment

Never use the same business repeatedly to inflate the 'first pass' score.
Previously examined companies are held in
`docs/KAURIVO_HISTORICAL_DEMO_TRIALS.json`. New blind trials are
reserved once through `utils/blind_trials.py` when
`pipeline --benchmark-mode` runs. Repeated slugs or domains are rejected;
already-tested candidates in a larger scout list are skipped; repeated
same-company visual revisions in benchmark mode are forbidden.

For each unseen company record:
1. Source URL and industry, date, original-site inventory size.
2. Initial generated build, browser/mobile results, original-brand fidelity
   misses, partner and product task misses, text legibility issues.
3. Genuine first-pass independent quality score, or **NOT VERIFIED**.
4. Root cause and a generalized rule/regression test rather than a
   company-specific layout patch.

Then choose a different company for the next experiment. Prefer rotating
industries, size, content density and visual identities. A true customer
project, unlike a benchmark, may of course be revised when the owner asks.
No company outreach or paid services are authorized by a quality trial.

### Known remaining limitations

- The original fetcher is bounded and can miss JavaScript-rendered
  or very large multi-language product inventories. Incomplete evidence
  stays pending instead of being called complete.
- Semantic preservation is not fully automatable from page headings;
  exact source/build human review is still required.
- Static source HTML and Playwright snippets do not directly prove all
  content is visible over CSS images or that a logo may be legally reused.
- GitHub Actions ephemeral runners do not provide a persistent shared
  database. The registry under ignored `output/` works on a persistent
  host, but unattended cloud deployment needs the connected app's
  durable DB/storage before claiming cross-run uniqueness. Historical
  seeded demos are always excluded locally.
- A one-file HTML Builder cannot truthfully claim to have delivered
  a multi-page CMS. When original site breadth requires more,
  the release gate stays blocked until a multi-page implementation
  preserves the content; do not silently compress it.

## Free offline tests

```bash
python -m unittest tests.test_source_fidelity tests.test_blind_trials -v
python -m unittest tests.test_browser_legibility -v
```

A separate GitHub Actions workflow runs these new general gates
without Tavily, OpenRouter, or credit-limited paid APIs.
