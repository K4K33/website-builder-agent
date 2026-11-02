# Kaurivo: sustained 9.5 / 10 independent-quality gate

**Scope:** Every customer demo, redesign, public preview, client pitch and
production delivery. This is not a one-time Kotifixi-only milestone.

## Release rule

A demo may be built, revised and privately previewed before the gate passes,
but it must be labelled a **candidate / NOT APPROVED FOR CUSTOMER OUTREACH**.
The first outbound demo pitch must not be marked approved until:

1. The current exact source build has passed offline static checks, real
   browser interaction across 320, 390, 768 and 1440 px, working destinations,
   mobile navigation, loading/error states and tested forms (mock for demo).
2. A genuinely **independent AI reviewer** has inspected the *actual current*
   build, at minimum the home page and two separate inner pages, on **mobile
   and desktop**, with video/screenshots or browser evidence. Document the
   exact reviewer model, date, evidence reference, tested commit, explicit
   0–10 overall score and unresolved critical issues. The reviewer must be
   independent of the model/agent authoring the site; verify provenance.
3. The external review is **at least 9.5/10**, and **no critical issue** is
   unresolved. A qualitative review on an iPhone video alone can suggest
   fixes but cannot satisfy this full-site gate.
4. For proof of *repeatable agency quality*, retain the most recent
   independent reviews of **at least three distinct real client-demo
   projects**. Each must independently meet the same ≥9.5 threshold.
   One exceptional project does not establish a reliable generator.
   Recheck after template, model, design standard or QA changes.
5. Human owner approval of the final website and source/rights evidence
   remains separate. Neither an AI score nor passing this code gate
   establishes client permission, an implemented CMS or production readiness.

The offline `utils/kaurivo_site_quality_gate.py` gives a deterministic
**HOLD** or **PASS** decision on provided evidence. It NEVER calls AI,
never manufactures a score and cannot independently prove source authenticity.
Do not set human-verified flags without actual independent evidence.

## Text style: human and specific

- A "contrast slogan" (e.g. "Vähemmän X. Enemmän Y.", "Ei vain X vaan Y")
  is **limited to ONE per entire website across all pages**, not one per
  section or page. Zero is preferred if it is not genuinely memorable.
- Avoid repeated invented taglines, rhythmic 2-clause slogans,
  three-parallel phrases in every section, arrow-studded cards, numbered
  decorations, repetitive empty sales claims and all-caps label clutter.
- Write like the actual owner explaining their real service. Use
  concrete verified nouns, correct local Finnish and natural sentences.
  Preserve client-locked slogans exactly, without repeating them throughout.
- Remove repeated paragraphs and repeated identical CTA narratives
  across distinct pages; use one main action where it actually helps.
- The offline linter counts high-confidence contrast slogans sitewide
  and repeated long paragraphs, but DOES NOT judge whether prose
  is elegant; an independent editorial pass must still check readability.

## Photos, identity and conversion

- Original company photos FIRST **if actually approved for this usage**.
  If absent, relevant coherent licensed sample photos with an honest
  clearly visible but unobtrusive disclosure. Avoid dark photo badges
  looking like interface controls. A small caption or an adjacent
  plain-language note works better. Never invent a logo or misidentify
  stock subjects as company staff.
- Keep contact/quote path visible in the mobile hero; do not replace
  the real action solely with "Palvelut" and "Hinnasto".
- Client photos are optional; the first demo can be made without requesting
  any. Under the demo link/card in the offer email say that sample photos
  are examples and the company may optionally send their preferred images.
- Preserve brand and actual protected slogans; never invent staff,
  geographic coverage, tax deduction rates, testimonials or outcomes.
- Keep motion purposeful and tested for reduced motion, avoid stock galleries
  with inconsistent color/subject/crop/season.
- For prices: cite approved client source and check for changes; don't
  invent eligibility for local tax benefits.

## Repeatable workflow without exhausting credits

1. **Free local preflight** for ALL demos in a sample batch, not only the
   prettiest case: HTML and factual source review, image-source mapping,
   sitewide contrast-copy lint, missing links, local browser screenshots
   and mocked forms. Keep a deterministic snapshot of blockers.
2. Perform human visual QA against the current real industry leaders.
   Correct all obvious defects BEFORE invoking an external AI.
3. Use **one controlled independent evaluation per meaningful revision**
   with the same written rubric and real screenshot/video scope.
   Do not run an unbounded paid model loop or claim to work in background.
4. Fix supported issues, rerun all free checks, present again and log the
   external score and provenance. Iterate in actual working sessions
   until the threshold is evidenced.
5. Sample at least 3 separate client projects. The latest one cannot
   "pass by itself" while others still fail. Record and correct quality
   regressions shared by all demo builders and templates.

## Latest baseline: Kotifixi V7, 2026-11-02

An external Claude Sonnet 5.5 Medium **iPhone-video-only** review rated
the pre-revision Kotifixi V7 around **8.5 / 10**. It liked the much less
AI-looking service-led approach, mobile hero and current contact path,
while noting an artificial "Vähemmän... Enemmän..." slogan, repetitive
copy, visually uneven service photos and dark photo overlay badges.
This is NOT ≥9.5 and does not cover desktop or all functions.
The revised copy/photo styling is a **new candidate awaiting re-review**.
Never carry the old score over to the new commit or invent new ratings.

The `9.5` gate applies to this demo AND the repeatability sample;
a single independent AI score is a subjective indicator, not
proof of conversion performance or professional market valuation.
