# Source-first experience continuity: Kaurivo universal gate (2026-11-03)

## Why this exists

A real source site can already be excellent in ways a screenshot-only or text-only
redesign misses. A source page may include film, work photography, a product
gallery, real interactive 3-D, attractive paper/leather/wood textures, smooth
transitions, a recognizable wordmark and branded copy. A generic replacement
can pass link checks and still be a **visual regression**.

The Munkkiniemen Suutari review exposed this failure class. This document is
a universal cross-industry standard, NOT a request to rebuild that demo.

### Primary principle

**Do not lower the original site's successful experience level.** Identify it
before choosing a design. If authentic original motion/video/3-D is present,
retain its useful role or create a customer-approved and legally usable
alternative. If the original is restrained, do not gratuitously add 3-D,
endless animation, decorative numbers or repetitive arrows.

Preserving a brand does not require reproducing a broken layout; modernize the
structure, responsiveness, typographic quality and navigation while maintaining
the original's recognized strengths.

## Automatically collected source evidence (free)

During Research, after the bounded original-site crawl, Playwright now visits
all inventoried original URLs (up to 12, matching the source crawl limit).
The collected **original_experience_profile** includes:

- source-inventory SHA-256, actual inspected URLs and failures;
- evidence date, per-page DOM/computed-style counts, missing-coverage flag;
- observed videos/embeds, probable 3-D integrations, animation signals,
  multi-image galleries, photography and repeating background patterns.

This uses **no paid AI provider, Tavily or image-generation credits**. It
makes browser requests to source websites; timeouts/failures remain explicit.
The probes are intentionally conservative. A DOM signal does not prove a
video played, that an effect is beautiful, that a background is genuinely
textured, that an image belongs to the business, or that it may be reused.
Backgrounds implemented in complex CSS or offscreen JS may need manual review.

The profile is fed to the Research design brief and both Builder/revision
prompts. It is compared against all produced HTML routes inside
utils/universal_quality.py by utils/source_experience_gate.py.

If original pages were not captured, or the exact source hash changes, result:
**REVIEW REQUIRED**, never “nothing to preserve.”

## Stronger human/browser acceptance gate

Before telling the owner a demo is premium-ready:

1. Capture original and redesign desktop/mobile screens and one relevant
   original motion/video recording; inspect full-page galleries and backgrounds.
2. Inventory the source's **actual strong features** and whether every feature
   survives in the redesign. Source observations must cite real source URLs.
3. Inspect both versions at desktop and mobile, during interaction/scroll.
   Test reduced-motion setting, real playback, smoothness and load performance.
4. For branded photos, film or marks lacking clear reuse rights, keep the
   demo explicitly in rights-pending review. Never invent a false staff photo
   or replace a real client mark with a synthetic seal.
5. Approve changed experience only with **client** permission recorded for
   that exact original-source hash and generated-build hash. Human browser
   review is separate from legal reuse permission.
6. Block obvious visual regressions and repeated generative clichés: giant
   decorative letters, 01/02/03 blocks, arrows on every CTA, vague copy,
   enormous blank hero space, repeated monochrome service cards.
7. Verify first impression and business recognition in 5 seconds, readable
   type, company-specific copy, coherent color, quick main customer paths,
   accessible controls and responsive layout.

Any uninspected original route, missing image rights or unexplained media
loss must be reported as incomplete. Technical unit tests alone do not
establish independent 9.5/10 quality.

## Adapting the AMK website checklist to client work

The school checklist contributes useful **general quality questions**, but
requirements for a student's synopsis, target employers, academic layout plan
and final school report do **not** become visible customer-site content.

| School rubric idea | Commercial analogue |
| --- | --- |
| Synopsis / structure | Company-specific IA and route-content plan |
| Audience | Real buyer/service user, not generic “everyone” |
| Documented layout | Source-linked art direction and page-to-page structure |
| First impression and whitespace | 5-second comprehension + visual rhythm |
| Type/icons/colors | Original brand DNA, legibility and actual usefulness |
| More than standard exercises | Distinctive genuine details, not injected gimmicks |
| Usability | Contact / buy / reserve task completion, phone + desktop |
| Final report | Internal evidence packet and source-to-new QA matrix |

## Evidence-bound review example (illustrative, not a real approval)

The stored Research profile has schema:

    {
      "source_sha256": "<sha256 of current source_inventory>",
      "capture_method": "browser",
      "checked_at": "<UTC time>",
      "complete": true,
      "inspected_urls": ["https://example.org/"],
      "failed_urls": [],
      "features": {
        "video": {"present": true,
                  "source_url": "https://example.org/",
                  "observation": "Real embedded workshop video observed"},
        "three_d": {"present": false},
        "motion": {"present": false},
        "textured_background": {"present": false},
        "gallery": {"present": false},
        "photography": {"present": true,
                        "source_url": "https://example.org/",
                        "observation": "Original work photos observed"}
      }
    }

The browser probe auto-populates the basic fields. A human must verify any
weak/candidate signals. The reviewer can register exact-build observations:

    "experience_continuity_review": {
      "reviewer_kind": "human",
      "reviewer": "<actual reviewer>",
      "original_and_new_recordings_checked": true,
      "source_sha256": "<source hash>",
      "build_sha256": "<new rendered pages digest>"
    }

If the client explicitly chooses to remove one observed experience feature,
record only a **genuine** client decision:

    "experience_exceptions": [{
      "kind": "video", "reviewer_kind": "client",
      "reviewer": "<real customer>", "reason": "<specific decision>",
      "source_sha256": "<source hash>", "build_sha256": "<new pages digest>"
    }]

No placeholder example is authority to populate an actual client record.

## Tests

    python -m unittest tests.test_source_experience_gate -v
    python -m unittest discover -s tests -v

The source crawl, media probing and animation playback are not certified by
these unit tests. On an authorized real test case, verify the stored browser
evidence and compare the source's live moving content with the redesign.

**Release honesty:** A review-only demo may be shared with documented gaps
for internal critique. It must not be called completed premium delivery while
source-experience continuity or client rights remain unresolved.
