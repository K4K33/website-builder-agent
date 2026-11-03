# Kaurivo — agency-wide, authentic 9.5–10/10 website method

**Status:** Permanent standard for *all future businesses and industries*, including
small companies with no original website. Not a client template, not an
instruction to rebuild a previously reviewed demo.

## The evidence-based lesson

A green unit suite is not evidence of premium design. Previous first-pass
comparisons repeatedly exposed the same *systemic* classes of defects:
original identity lost under fashionable agency typography; internal source
and QA notes shown to customers; plausible but invented brand marks and map
drawings; repetitive headings and decorative gimmicks; accidental content
compression; dead-end CTAs; unbalanced columns on subpages. These defects can
coexist with correct URLs and 100 accurately reproduced pricing rows.

A quality system must **prevent the class of error** rather than hard-code
special cases for the last client. Each customer gets a new independently
researched design, while the same adversarial QA applies across sectors.

## Documented industry methods worth adapting (not copying)

Reviewed official product documentation on 2026-11-03. These companies
demonstrate structured AI website generation, but **their marketing claims do
not prove every customer site is 10/10**. Their templates, source code,
protected content and imagery must never be imported without permission.

| Company / primary documentation | Verified public workflow | Kaurivo adaptation | Important difference |
|---|---|---|---|
| [Relume Site Builder](https://www.relume.ai/resources/faqs/how-does-relume-s-ai-website-builder-work) and [sitemap docs](https://resources-relume-io.relume.work/resources/docs/building-a-sitemap-with-ai) | Brief → sitemap → per-section wireframes → style guide; designers may compare alternate sitemaps and edit | Derive a source-bound **sitemap + section plan + selected direction** BEFORE generation | Kaurivo must retain actual original business facts and source-to-new content trace, not assume generated wireframe text is factual |
| [Webflow AI builder](https://help.webflow.com/hc/en-us/articles/38840145286035-Build-a-site-with-Webflow-s-AI-site-builder) | Review/reorder per-page section plan and generate common global style guide; typography, spacing, color, effects and buttons can be edited across routes | Derive a common **original brand kit** for all planned pages, audit contradictory browser theme metadata, keep final customer editing accessible | Webflow itself warns that editing the original AI structure via regeneration overwrites previous edits; Kaurivo must preserve locked client details |
| [Wix Harmony Brand](https://support.wix.com/en/article/wix-harmony-editor-setting-up-your-brand) | Site-wide brand colors, text styles and controls defined once and propagated across pages | Use source-linked original identity as the authority rather than randomly selected theme colors; constrain site-wide consistency | Sourced brand colors and client permission beat generated aesthetic guesses |
| [10Web Redesign Agent](https://10web.io/product-release/redesign-agent/) | Existing website URL → redesign attempt that retains the page's content/structure and changes the visual language | Prioritize provenance-rich page/content parity while redesigning independently | 10Web documentation explicitly describes its current workflow as **page-level**, not a verified complete multi-page content audit |
| [10Web terms](https://10web.io/legal/terms-of-service/) | Recreating third-party websites has important ownership and permission requirements | Block publication of unlicensed client photos/logos/copy and require rights review | A public URL is NOT a licence to clone an owner's materials |
| [Squarespace Blueprint AI](https://www.squarespace.com/websites/ai-website-builder) | Company description informs a cohesive personalized design direction | Use company-specific business details to choose the art direction; assess subpage cohesion | Treat all claims of high quality as promotional, not independent proof |

**Implementation:** `utils/brand_design_blueprint.py` now derives a deterministic
company-specific plan from the existing verified Research fields. No paid API
credits, no templates from competitors, no fabricated original brand colors.
`agents/builder.py` injects this plan for fresh generation and revisions,
and applies the same preflight to external-agent imports. A cross-route
theme-color consistency check supplements human screenshot review. Current
scope is a *structured planning contract*, not a real drag-and-drop
wireframe UI, CMS licence, or automated visual art director.

**Evidence hierarchy:** real original assets → actual source fact inventory →
source-bound style guide and page outline → chosen creative concept →
generated pages → static/dynamic QA → independently reviewed screenshots →
customer-approved production delivery. Each stage is distinguishable.

## 1. Separate four data layers *before any copy is rendered*

| Layer | Examples | May be shown on client website? |
|---|---|---|
| Verified original business facts | Services, addresses, actual quotes, sourced prices, employee names, original brand | Yes, in customer-first language |
| Original source references | Source URL, date fetched, image origin, unsure price/date, OCR/JS gaps | No; internal evidence report |
| QA / builder notes | "six rows from the original prices", "phone copied from source", "missing approval", "unverified holiday notice" | No; internal issue tracker only |
| Preview disclosure / approvals | Demo status, missing licence, user/customer consent, prototype disclaimer | A minimal clearly separated DEMO label outside main; never production copy |

**Hard rule:** Explanations of how the agent found information must not
appear in the client's headings, sections, pricing row captions, footers or
service descriptions. A publicly shown concept is a preview, not a production
site; its small, clearly separate demo notice is not a sales heading.

When an old site publishes a possibly expired opening time or price: investigate
actual validity; until verified, mark unresolved internally. Never insert a
detailed "the original website said…" meta-paragraph into the client's site.
A discreet generic customer-facing "Varmista ajantasaiset hinnat liikkeeltä"
may be appropriate if it reflects genuine uncertainty and adds utility; do
not claim a precise new price or opening time without evidence.

**Automated check:** multi-page visible main content is scanned for source
narration in Finnish/English, and internal-note components in main are blocked.
Client release also rejects preview-only disclosure. Detection is necessarily
partial; editorial review is still required for semantically similar wording.

## 2. Build an immutable Original Brand DNA dossier

Collect from every important old page:
- Original wordmark, actual logo artwork, colors, type character, tone of voice,
  product/staff/place imagery, favicons, client-approved slogans, recurring
  identity and source-linked permissions.
- Positive identity: what people recognize about this particular business.
- Non-negotiables: licensed mark; owner-selected phrasing and photos; real
  geographic place; genuine project and review evidence.
- Flexible elements: layout, responsive architecture, rhythm, animation,
  accessibility and content hierarchy. Modernization may radically improve these.
- Explicit uncertainties: no usable source logo, no confirmed photo rights,
  potentially outdated trademark/brand assets.

**Hard rule:** Never automatically synthesize a new initial logo, J.-style
round seal, ornamental SVG emblem, fake team portrait, or unsourced identity
and present it as the client's official brand. If an original logo cannot be
legally used in the preview, use the exact company name in clean typography.
A new brand mark requires customer permission with source/build-specific
proof; a model's preference is not approval. The actual customer could choose
rebranding later, but that is a separate, explicit project.

The brand preservation plan must cite actual source pages. Record approvals
and digest the final entire build so outdated approvals cannot be reused.

## 3. Every useful fact has an old → new destination

Create an inventory by page and content item, not only a page summary.
Sections, FAQ, policy text, products, complete price rows, exceptions,
sponsors/partners with exact active roles, menus, accessibility info,
contact methods, booking destinations, review quote and verified stars, staff,
gallery, awards, business history and substantive paragraphs must be traced.

Every record needs: source URL; content excerpt; change type
retain / reorganize / rewrite / exclude with *client-approved reason*;
destination page and element; reviewer; current verified timestamp.
Strong evidence rules for high-risk claims:
- Pricing: exact denomination, size band, variants, mandatory surcharges.
- Products/services: exactly the correct category/brand/breed/material.
- Reviews: actual quote, author if sourced, original *associated* star count;
  never add 5 stars to unrated reviews and never invent testimonials.
- Rights: logos, source images, affiliations and customer quotes require approval.
- Dynamic widgets: inspect rendered output in a real browser or mark incomplete.
- New businesses without a site: facts need independently verifiable external
  evidence; do not fabricate source pages.

Textual similarity is not semantic proof. Rewritten important descriptions
remain *pending* until independently reviewed against the original source.
Pass/fail gate: no unreviewed materially missing fact, no fake fact.

## 4. Explore genuinely different directions before writing markup

Review the company's visual DNA and three relevant real industry benchmarks.
Produce 3 concept directions differing in information architecture, opening
composition, type system, photographic treatment and the task journey—not
merely CSS palette or card corners. Choose one via explicit rationale that
connects its aesthetic to this company's own facts and visitors.

**Anti-template rule:** do not append an arrow to every CTA, number every
card 01/02/03, reuse an exaggerated serif hero across unrelated industries,
or repeat several broad slogans that could fit any other company. Use the
brand's original voice and concrete material, and introduce movement only when
it improves orientation/interaction. More animations do not imply more quality.

Make all subpages visually intentional; a premium homepage cannot hide a
generic contact page and a badly aligned long pricing table.

## 5. Copy must sound like the real business

Before publication perform a dedicated *customer-perspective editorial pass*:
- Is the text saying something useful about an actual service/choice?
- Is it written directly for the visitor rather than describing research?
- Does each important headline communicate a concrete relevant value?
- Does an existing genuine client phrase deserve preservation?
- Are there "vähemmän X, enemmän Y", automatic contrast pairs, repeated arrows,
  meaningless counters, vague "quality/trust/service" clichés, or identical
  section captions on all sites?
- Are all factual claims sourced and the call to action genuinely achievable?
- Does the text avoid implying a new brand, experience, guarantee or rating?

Prefer natural Finnish appropriate to the business. Sentence-level polish is
valuable, but do not rewrite original regulated/service facts into new claims.
A single editorial test catches recurring patterns; independent human tone
review must catch subtle artificiality beyond regexes.

## 6. Every location visual must be geographically meaningful

A CSS street drawing with a round pin can suggest a genuine map but give zero
usable navigation. A "view in Google Maps" link beside it does not turn the
drawing into geographic evidence.

Use either:
1. A real, verified map embed or static map with true coordinates/provider
   and correct licensed attribution, with a real directions link; or
2. A clean address card with explicit street, city, accessibility guidance,
   directions link and optionally an approved authentic storefront photo.

Never create an unverified decorative street map to occupy empty space.
For directions, preserve the true place and ensure opening the link leads to
the right location. Static analysis catches obvious fake SVG/CSS map panels;
live provider accuracy needs human or real browser validation.

## 7. Build the actual visitor task journeys

Define the primary task for each real customer type: service booking,
calling, emailing, finding the shop, comparing a service, purchasing, or
obtaining a quote. Use the exact known booking deep link, not merely the booking
vendor homepage. Each page should have a clear, limited CTA hierarchy.

Test keyboard and touch interactions; check real forms deliver the right message
with usable success/failure states. Keep page count and navigation matched to
the amount of original content. Check 320px, 390px, tablet and wide desktop.
Mobile should have appropriate spacing, touch targets and readable copy
without horizontal overflow.

## 8. Screenshot-based visual composition review

Inspect *every page* at desktop/tablet/normal-small mobile, including bottom
sections, scroll transitions and expanded menus. Check:
- Do hero image and title represent this exact company?
- Are photos genuinely theirs, correctly cropped and rights-approved?
- Are long tables readable and source-accurate?
- Are there large accidental blank columns, stranded sections, clipping,
  optical imbalance, strange oversized empty blocks, unwanted loops,
  abrupt rhythm changes or uncomfortably huge headings?
- Does anything look like the same AI-prompt theme applied to 10 clients?
- Does the final layout have a credible business voice and proper hierarchy?

A local browser can detect overflow, tiny controls, inaccessible contrast and
*potential* severe column imbalance. It cannot decide whether deliberate
whitespace is attractive. Large asymmetry is a **flag for visual judgment**,
not a claim of failure. Acceptance requires a separate identified reviewer,
exact-build image proof and a resolved decision.

## 9. Quantifiable engineering is not a subjective design score

Mandatory verified technical gates: no broken route, no console errors,
WCAG 2.2 AA checks + human keyboard/contrast review, legible headings and
responsive typography, meaningful alt texts, reduced motion, fast pages,
no unlicensed resources, safe HTML/data handling, real CTA paths,
structured page metadata and tested content-editable CMS handover.
Use genuine field p75 metrics where available:
LCP <=2.5s, INP <=200ms, CLS <=0.1. For a new low-traffic demo,
report lab data separately and DO NOT claim field performance.

100% passing tests is the **minimum**, never proof of aesthetics. New
counterexamples become generalized regression tests.

## 10. Independent two-reviewer threshold, exact build

For all new customer-ready projects:
- Two separate reviewers independent of the builder inspect original site
  AND each redesigned route in actual screenshots at 1440, 768, 390 and 320.
- Each of ten dimensions independently scores >=9.5/10: visual design,
  originality, brand, content, real imagery, natural language, usability,
  mobile, accessibility, interaction quality.
- All critical issues must be resolved; do not average away a 5/10 brand.
- Identify reviewer, evidence references, reviewed source digest, reviewed
  build digest, and signed material/rights uncertainty.
- Don't call a site verified 9.5/10 without the independent results.
- Repeat on at least three unrelated sectors before claiming **agency-wide**
  consistency rather than one cherry-picked success.

An aesthetically promising internal demo may be shared for critique as
**unapproved prototype** with pending evidence clearly called out, never as
verified client release.

## 11. Continuous learning loop without refitting the last company

For each critique: (a) identify customer-visible symptom; (b) reproduce
with an invented but realistic unrelated company; (c) find where source,
model instruction, CMS, browser or gate allowed it; (d) introduce *one
cross-sector constraint with an appropriate false-positive control*;
(e) add a positive and negative test; (f) run every mandatory test again
on the exact final commit; (g) publish what was verified and what remains
unknown; (h) evaluate the NEXT DIFFERENT industry.

Do not revise the same example repeatedly merely to show inflated scores.
Do not remove tests or loosen thresholds just to get a green dashboard.
The highest leverage is **prevention at source + independent adversarial
review**, not visual polishing of a poor first concept.

## 12. Evidence and consent boundaries

Source research may inspect public pages; copying photographs, logos,
proprietary copy or third-party reviews into a public demo is not
automatically licensed. Collect permissions and respect privacy,
copyright, trademark, consumer marketing, commercial outreach and
client approval requirements. Do not claim owner endorsement.
Client should independently be able to edit, publish, undo and back up
text, images, prices, reviews and contacts via a tested CMS workflow.

## Operational acceptance card

| Dimension | Evidence | Minimum |
|---|---|---|
| Content parity | Full source/build inventory, exact price + FAQ check, semantic signoff | No material omission |
| Brand continuity | Evidence-linked logo/colors/staff/media rights | No fabricated identity |
| Authentic reviews | Original quotes and true associated stars | No invention |
| Customer-facing language | Multi-page copy lint + editorial comparison | No research notes / empty slogans |
| Geographic UX | Real georeferenced map or usable address/directions | No pseudo-map |
| Layout | Full-page screenshots, independent whitespace review | No unresolved critical issue |
| Function | Real journeys, browser + keyboard/touch | Correct direct task destinations |
| Technical/accessibility | Full suite, WCAG evidence, responsive + safe media | 0 failures, 0 errors, 0 skipped |
| Performance | Honest lab / field provenance | Good thresholds where measurable |
| Experience/design | Two real independent exact-build reviewers | >=9.5 each dimension, each reviewer |
| Customer delivery | Rights, domain, CMS editing, backup, client acceptance | Explicit signoff |

**The goal is approaching 10/10 on real diverse client work—not manufacturing
a 10/10 claim from code, green tests, or an unverified AI rating.**


## 2026-11-03 continuation: brand token and approval-staleness regression

**Cross-page identity check:** A copied stylesheet or generated subpage can
accidentally introduce another client's brand color and typography. The
shared static QA now compares explicitly declared global `:root` tokens
(`--brand-*`, `--identity-*`, heading/body font and brand color tokens)
across routes and blocks contradictory values. It deliberately does not
force every section to have the same palette, does not parse external CSS,
and never claims to judge design taste. Full-page rendered comparison
remains mandatory.

**Customer signoff must apply to the current deliverable:** Flags such as
`client_approved: true` are insufficient. The final release manifest must
have a real client reviewer, a traceable approval reference, date,
`build_sha256` matching the complete current HTML route set and
`source_sha256` matching the current crawled inventory (when available).
Any subsequent build change or refreshed source research voids that
approval evidence until a new signoff. This supplements, rather than
replaces, proof of permitted media, verified contacts, CMS handover,
accessibility, performance and independent review.

**Prevent recurrence in CI:** The creative multi-page GitHub Actions suite
must trigger on brand blueprint, client-facing integrity, premium quality
and their regression tests, in addition to general build changes.
It runs targeted static tests on each affected PR; the separate complete
quality workflow remains the source of truth for the full browser suite.
A green static build is still not evidence of an independently proven 9.5/10.
