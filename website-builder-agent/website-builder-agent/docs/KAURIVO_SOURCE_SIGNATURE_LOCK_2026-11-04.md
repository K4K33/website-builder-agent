# Kaurivo source-signature fail-closed v1 (2026-11-04)

## Why a green QA score was misleading

Across several source-rich real businesses, first-pass concepts passed HTML
and mobile checks while losing recognizable original logos, staff portraits,
original video, material texture and large work-photo galleries. In particular,
a responsive page with 28/28 Chromium viewports was visibly off-brand.
This is a **systemic failure in evidence and release control**, not simply
one bad hero concept. Source-HTML snapshots can miss lazy/runtime media, and
model-derived briefs can describe good intentions without actually implementing them.

## The executable change

`utils/source_signature_lock.py` now derives a source-bound inventory of:

- Original brand logo artwork URLs observed in headers, across ALL original routes
- Source-observed staff portraits with explicit contextual DOM evidence
- Original genuine work/product gallery photographs, including gallery routes
- Photographic depth on image-rich source pages, not only total generated images
- Video observed either in source HTML or an inventory-hash-bound browser probe

`audit_universal_standards` calls this on **all output routes** and maps certain
losses into the new `original_visual_assets` **BLOCKING** category. It is invoked
from `site_build_pipeline` before any HTML output file is saved, and by normal QA.
A new textual name does not count as the original graphic logo. Empty team cards
do not count as photographs, static posters do not replace video, and a link
to an old gallery does not count as migrating its photography.

There are deliberately no inferred copyright licences. If assets cannot be
lawfully reused, an internal demo remains blocked from being presented as an
approved redesign until an alternative is specifically approved. Each exception
is asset-kind + exact original + source SHA + build SHA + owner identity +
date + meaningful explanation. This stops a one-time blanket model-generated
approval being recycled across other companies.

## Capture and evidence quality

Research already crawls all bounded original pages and collects source identity;
photo extraction now labels strong visual context roles (`staff_portrait`,
`gallery_photo`) conservatively. Unclear photos remain `unclassified`,
not invented portraits. The builder's source-bound blueprint explicitly includes
the immutable visual signature and preservation instructions; it cannot silently
discard the list while choosing three competing design directions.

The original browser probe remains necessary: real-video and image-background
signals can live in JavaScript/CSS outside the fetched HTML. A partial/blocked
probe must not be interpreted as evidence that original video or personality
never existed.

## Hand-coded / Codex demo bypass closed

`scripts/audit_changed_demo_previews.py` no longer treats missing provenance
as the empty dictionary and then displays an objective PASS.

Every changed demo needs `data/demo_provenance/<slug>.json`, schema version 2.
For an original website, the manifest must carry the original full `source_inventory`
with each route's source identity (including original logo candidates, original
content photos with their roles and source-experience signals), hash-matching
`original_experience_profile` from a complete browser inspection, and paired
original/new desktop/mobile screenshot references. A URL and 11 partner logos
are **not** sufficient. A verified business without a website instead requires
an explicit independently sourced verified company profile; no fabricated brand.

The schema is a traceability contract, not an assertion that screenshot
references are truthful or permission to use a third party's content.
A human reviewer must still inspect the actual images and authorize
production rights. Legacy schema-version-1 demo evidence must be upgraded
before modifying or approving those demos.

## What remains human and release-blocking

Automated source and browser DOM checks do NOT judge pixel-level logo identity,
employee identity, complete video playback, the exact original typography
or color character, wooden material depth, editorial taste or independent
9.5/10 quality. The existing `brand_experience` source/new 320/390/1440
review requires a current-build independent human record and original media
rights before client-ready status. If the original website blocks browser
inspection or ownership is unverified, mark REVIEW REQUIRED and do not
market a score or send the demo as client-ready.

## Acceptance checklist for the next brand-rich business

1. Original source pages and browser video/media are captured with date,
   source URL, screenshot and inventory SHA. Confirm all original routes.
2. Original graphic brand mark, essential staff photography, actual work
   galleries and videos remain in the new site or have source/build-specific
   client-approved alternatives.
3. Every new page is compared against the original in real Chromium at
   320/390/768/1440, including first screen, image crops, backgrounds,
   text hierarchy, CTA affordance, true company voice and copy.
4. A reviewer unrelated to the generator compares visible snapshots across
   distinct businesses. A generic beige/black editorial surface is a regression
   if it erases the original's distinct colors/materials.
5. Every client-facing sentence is checked for research prose, invented
   testimonials, repetitive marketing contrasts and unsourced claims.
6. Demo/owner approval only after source/content/media/rights parity,
   functional journeys, editability/CMS and actual customer signoff.

**Cost:** purely local code + existing browser captures, zero additional paid
search/AI credits. Browser/GitHub CI execution still has resource usage.
