# General service quality and unseen-company experiments

Owner requirement, 5 November 2026: demo feedback improves the whole service.
Every subsequent **real-company quality experiment** uses a new company.
Existing unit fixtures remain repeatable regression tests; they are not new
business trials or proof of aesthetic quality. Real customer revisions are
separate client work, not improved first-pass experimental results.

## Enforced changes

- `pipeline` now defaults to the unseen-company experiment. The explicit
  `--client-project` mode is reserved for actual client work; no customer
  project counts toward experimental first-pass success.
- The historical exclusion list includes checked-in demos and Tuuren paja.
  Identity checks compare name/slug aliases, versionless slugs, both URL fields,
  known alternative domains and a business ID when supplied. Missing identifiers
  do not magically identify an undisclosed rebrand; maintain this ledger when
  making demos outside the pipeline too.
- Reservation persists before Research. The complete build/import consumes one
  attempt before its model call or import. A failed attempt stays consumed.
  A company marked as an experiment cannot enter the revision path. Offline
  code tests may always be rerun. The registry assumes a single runner.
- First-pass evidence is immutable. Reports include sector trial/review counts
  and the unreviewed count, so one industry's success does not conceal missing
  validation elsewhere. These are counts, not a claim of cross-sector quality.
- The shared QA emits `quality_scorecard` using `kaurivo-eight-v1`: brand,
  company specificity, photography, composition, content preservation,
  commercial quality, navigation/technical quality and client handover.
  All eight have equal weight. A missing score means **unverified**, with no
  renormalized partial mean. Compare the exact mean with 9.5, then round the
  display half-up to one decimal. A displayed 9.5 from 9.45 does not pass.
- Reviewed scores require a rationale and actual evidence IDs for each area,
  matching the verified current artifact/source/design-contract bundle and a
  reviewer declared separate from the builder. This records review provenance;
  it does not authenticate a person's identity or automatically judge taste.
  Research-model-generated approvals and scorecards are discarded.
- Shared internal QA keeps missing reviews pending without blocking draft
  creation. Premium/service client acceptance recomputes the scorecard and
  refuses missing evidence, an insufficient exact mean, or open review issues.
  Existing source/task/media/CMS/rights checks remain separate prerequisites;
  numerical scores cannot override their failures.
- The shared Builder/QA prompt now explicitly requires first-viewport balance,
  actual image crop review, and route-specific composition. New photographs
  of an owner/workshop must be genuine client input, never invented.

## Next real trial

### Route experience acceptance after the Runo review

Research now returns a route_experience_plan for every planned page: visitor
task, composition, needed photo subjects, available source images, missing
assets, brand character, type hierarchy and motion/static decision. New
Research output opts into validation before Builder. Legacy projects without
this plan remain drafts requiring review; missing assets remain pending even
when a reviewer marks visual quality approved. A changed plan invalidates
previous reviews through the contract digest.

Visual and technical domain approval now requires route_results for every
rendered page, each with a concrete observation per required check and an
evidence reference. Visual checks cover media sufficiency, task composition,
brand character, readable hierarchy and motion suitability. Technical checks
cover wheel, trackpad, touch, keyboard, reduced-motion and input response,
with actual device/browser. Missing, failed or unverified observations cannot
approve delivery. Existing exact-build/source/reviewer and evidence-bundle
checks still apply. These records document observations; this offline code
cannot itself observe physical scrolling or certify visual taste.

Mailto-only icon/button actions without a visible selectable email address are
flagged. This is a text-level guard; actual visibility and native mail-app
behavior still need browser review. Existing form-receipt and CMS login/edit/
publish/mobile/rollback release requirements remain mandatory. No form is
submitted and no client contacted by these offline checks.

Changes remain in the development branch until published/merged. Synthetic
tests demonstrate gate behavior, not improved first-pass design quality or
9.5 performance on new companies. The next real trial uses a new business.

### 3D and animation scoring, 5 November 2026

Keep the eight equal-weight areas. Explicitly assess 3D/animation quality and
brand suitability within visual composition, and scroll impact within
navigation/technical quality. Effects earn no automatic bonus; a justified
static treatment may score highly. Reject scroll hijacking, observable jank,
blocked input and content delayed by effects. Observe native wheel/trackpad,
touch and keyboard scrolling, reduced-motion and usable static fallbacks.
Record device/browser and observed limits. Screenshots or code inspection
alone do not verify motion performance; missing runtime evidence is unverified.

Choose a business absent from the complete history, preferably from an industry
with little reviewed coverage. Research the original's actual appearance,
content and business tasks. Compare the three real responsive concepts. Build
once, capture desktop/mobile pages and task journeys, and review all eight
dimensions with concrete evidence. Record the first result, including failures.
Apply the root-cause fix to the shared service and select another new company.

Required intake/release observations remain the existing source inventory,
task/media/voice plans, originality comparisons, browser journeys and actual
CMS edit/restore evidence. Do not replace these with a new generic checklist
or fabricated scores. No claim that the service achieves 9.5 consistently is
allowed until independent results across new companies support it.

## Verification boundary

This change uses offline adversarial fixtures: missing/forged/stale evidence,
invalid and rounded scores, high averages with blockers, renamed/versioned
companies, consumed builds, direct import bypass and sector coverage counts.
No paid calls, outreach, new company websites or customer data are used by
these tests. Real-new-company validation remains pending.

### Verification completed 5 November 2026

118 targeted tests passed, plus the three-sector orchestration test passed
with genuinely distinct synthetic company identities. The final full suite
ran 771 tests with 11 failures and zero errors. A clean detached checkout of
unchanged main (5ab0732) ran 754 tests with the **same 11 failures**: ten
existing responsive-layout cases and one Tavily fallback/cache interaction.
The added 17 tests introduced no new full-suite failures. Compile and diff
checks passed. The old demo CSS and existing quota test were not modified to
make the suite green. Real new-company quality trials remain pending.

Local browser checks used Playwright 1.56 and Chromium headless shell 1194;
the latest browser download was unavailable. The repository dependency
requirements were not changed. GitHub publication remains pending explicit
owner permission following the automatic approval review rejection.

## Premium experience corrections after Woode, 6 November 2026

New Research plans must select the editable platform, preview implementation,
delivery-parity strategy, genuine project/story/credit grouping (or justified
non-applicability), contact continuity, cold-load test, composition selection,
motion purpose and added value for every route. Validate before a new build;
legacy projects remain draft/review-pending when the plan is absent. Changes
are part of the contract hash, invalidating old reviews.

Visual review now explicitly records project presentation, new information
and actual composition comparison. Technical review adds cold-cache opening
and route transitions. Commercial review adds route-specific contact
continuity. No cache flush, screenshot, recipient submission, performance
measurement or independent review is fabricated by this code.

Client delivery now additionally requires preview_cms_parity: current approved
preview digest/version, actual CMS platform/build reference and every planned
route. Missing or duplicate route inventories cannot certify delivery. Each route
needs layout/content/task observations and capture records with roles
approved_preview, cms_after_edit, mobile_after_edit, rollback, task_completion.
Relative capture paths must remain inside evidence_root; image/video bytes
must exist, be nonempty, at most 30 MB, and match their recorded SHA-256.
Existing real editing, publication, customer acceptance and source/build
approval checks still apply. The offline check proves file integrity, not
that a screenshot depicts genuine CMS behavior; actual testing and review
are required. Synthetic fixtures are not real delivery evidence.

Runo and Woode are now excluded from future unseen-company experiments.
Implementation remains in the development branch, not the published builder.

Verification: 120 targeted offline tests passed on 6 November 2026, including
counterexamples for missing planning, skipped project/loading/contact review,
stale contracts, absent or duplicate route coverage, altered/missing capture
bytes, path escape and missing capture roles. Python compilation and diff
checks passed. No real CMS, recipient, paid API or new-company design score
was exercised. Physical performance and new-company validation remain pending.

### Published click-through regression, Vekki

The owner recording and live browser reproduced a production-only Vinext
client-router TypeError: clicking a Next Link kept the original URL/content,
while opening the exact destination URL rendered the page. The Site now uses
ordinary document anchors. After publication, all five header route links,
the quotation CTA, home return and home gallery CTA were clicked successfully
in the actual deployed Site; the original router errors did not recur. Browser
extension metadata errors were excluded from Site errors. Local preview and
direct URL checks were insufficient. Preserve the failed original trial; the
repair is not an independent visual acceptance or a new-company first pass.

## Enforced post-publication acceptance, 6 November 2026

`utils/published_experience.py` is now called by universal QA and client
handover. A final publication needs a `delivery.published_experience` record
bound to the exact site SHA-256, build version, published URL and hosting
publication reference. Test timestamps must be after that publication and no
older than 14 days. The declared HTTPS route URL map must cover every planned
page uniquely on that origin.

Each route requires desktop and mobile CLICK observations: source URL, clicked
href, observed URL, expected and observed heading, no Site errors, and an
unchanged captured image/video file. Direct URL/goto checks, wrong headings,
old deploys and local previews cannot pass. Extra failed clicks cannot be
hidden by adding a successful duplicate. Captures must remain within the
record's evidence_root and match their SHA-256. The record needs an actual
reviewer; Research-generated approval is not authority.

A source contact form requires an authorized test recipient, actual receipt
reference, input-validation, success and error feedback, and a capture. Draft
creation cannot replace receipt. Genuine source email/phone contacts or an
observed existing booking platform have source-appropriate separate tests.
The gate NEVER performs calls, submissions or messages itself.

Public-demo readiness and client-delivery readiness are separate. A clearly
disclosed draft contact may be shown for review ONLY after published navigation
passes. It never becomes a working lead-delivery approval. Unverified published
navigation prevents public-demo readiness even when static checks pass. CMS
parity/edit/publish/restore evidence remains a separate handover prerequisite.

Offline gate checks verify record integrity and consistency, not the truth of
what a capture depicts. Real published-browser and CMS execution is still
required. These code changes do not assert 9.5 design quality or update the
failed first-pass demo score.

Verification: 136 targeted offline tests passed, including reproduction-shaped
counterexamples for goto-only checks, unchanged route content, missing mobile
coverage, production router errors, stale deployments, altered evidence,
unreceived forms, and draft-vs-client-release separation. No real recipients,
paid APIs or CMS platforms were contacted by these tests. Changes remain in
the development branch until approved publication to the public source repo.

## 7 November: complete visual information and placement evidence

Suutariesteri's first self-review was 6.375/10, not an independent acceptance.
The original had six footwear logos. Four manufacturer names survived as text,
while two makers disappeared because their only evidence was unlabelled art.
A genuine repair photo was also presented as a retail assortment. These are
regression cases, not a reason to silently polish the same first-pass result.
The business is now in the historical exclusion ledger.

The implemented source extractor enumerates **all** HTML images (including
blank-alt and lazy images), inline SVGs and inline image backgrounds, without
the old 70-photo cap. Identical source artwork shared across pages is classified
once while every source URL remains recorded. Wix resize variants are matched
only for the identical CDN media ID. Filenames and alt text are hints, never
semantic observations or proof that a blank image is decorative. External CSS,
JS-loaded material, galleries and information within pixels still require
actual source inspection; the static extractor is not OCR or complete browsing.

`visual_asset_plan` must classify every deterministic candidate id before a
Builder request. Each record contains role, observed_subject, visible_information,
supported_uses, not_depicted and explicit destinations. Brand marks require name
and uncropped image artwork; body text cannot replace them. An information
graphic may instead map **all** observed facts to exact visible text destinations.
Each image destination records route, unique selector, actual src, purpose,
expected_alt and crop_mode. A placement purpose must be among observed supported
uses and outside not_depicted. All output images, inline SVGs and inline image
backgrounds are checked, including header/footer/partner marks and images after
the first hero. Existing media integrity/licensing gates remain in force.

Known missing placements, hidden artwork, wrong alternative text, unplanned
images and inline cropped logos block preflight even with a high numerical score.
Presence alone does not approve pixels, crops, identity or rights. Both original
classification and **each output placement at desktop and mobile** require a
separate reviewer, exact source/plan/contract/artifact hashes and actual verified
review-bundle files. Every source capture names the asset ids it shows, not just
an unrelated homepage URL. Per-placement observations cover subject_match,
alt_accuracy, crop_integrity and visual_information_preserved. Changed source,
plan, build, route or viewport invalidates old evidence. Generated Research
approvals are discarded. Observations and file integrity do not authenticate a
reviewer's identity or replace their actual inspection.

The route visual review additionally requires whitespace_rhythm, cta_repetition,
image_subject_match, crop_integrity, visual_information_preserved and
sector_specificity. Existing technical wheel/trackpad/touch/keyboard,
reduced-motion and motion-input observations remain mandatory. Static CSS is
not proof of smooth scrolling. Numerical means still cannot override any
blocking or pending acceptance condition.

CMS delivery also requires current-build `shared_cms_edit_evidence` for header,
footer and observed phone/email/opening-hours fields. It must describe customer
editor actions without code editing, every affected route, before/after values,
and hash-bound before/after/mobile/rollback captures. A developer editing theme
HTML and a separate downloadable ZIP do not qualify as self-service editing.
The actual CMS tasks must be performed before recording a passing observation.

### External builders and Sites

The same static gate is available without a model call through:

```
python scripts/audit_visual_continuity.py --research research.json --pages rendered-pages.json --stage preflight
python scripts/audit_visual_continuity.py --research research.json --pages rendered-pages.json --stage acceptance --company company.json --artifact exact-deployment.tar.gz
```

`rendered-pages.json` maps real customer routes to their rendered HTML, **not**
React source or a list of URLs. Preflight can exit successfully with pending
visual inspection; its report explicitly keeps `ready: false`. Acceptance exits
nonzero without independent verified evidence, and never grants whole-site
release approval. It uses the normal review-bundle verifier for actual capture
bytes. Apply this adapter to externally built/manual Sites demos before calling
them complete. Sites hosting itself is not instrumented by this repository;
there is no claim that an unrelated native deployment automatically runs this
CLI. Main Builder, external-response import and QA use the integrated gate.

Validation: counterexample tests exercise blank-alt logos, six-maker-style
artwork losses, hidden/text-only substitutes, subject errors after the lead,
alt mismatch, mobile crop failures, stale evidence, source-page/asset/viewport
capture mismatch and shared editor tasks. Synthetic fixtures verify integrity
rules only. A new unseen real-company field trial and real CMS/device validation
are still pending; implementation alone is not a proven 9.5/10 service.

Original page pixels now accompany Research's existing design-brief request:
the existing source browser visit saves a full-page capture for each source
route, hashes it and labels target-company images separately from competitor
references. Before model/search credits, source image inputs must exist inside
the permitted output directory, have image signatures and matching hashes, and
cover all source routes. Missing captures stop the source-rich flow instead of
inviting an alt-text-only classification. Captures start with empty `asset_ids`;
a reviewer must identify which artworks are actually visible. Full-page capture
does not establish that hidden gallery frames or JS backgrounds were observed.
No additional model/search request was introduced. Source-pixel tests use a
mocked browser and synthetic bytes; actual browser capture remains unverified
in this environment.

Final local validation (7 November): 204 targeted tests ran, 199 passed and 5
were skipped. The 34 new visual/source-pixel/shared-CMS counterexamples passed.
Compilation and whitespace checks passed. The full suite ran 834 tests with
4 failures, 19 errors and 15 skips. An isolated unchanged correction-branch
checkout ran 800 tests with the exact same 23 failing/error test names. Those
cases depend on a Chromium executable unavailable in this environment. They
are not counted as verified passes. A pre-existing Tavily fallback test was
isolated from persistent cache contents so reruns do not consume or bypass its
mocked request accidentally; no provider/cache behavior was changed.

An offline check against the actual saved Suutariesteri source included all
six known footwear logo assets in the new candidate inventory, including those
with blank alt text. This proves discovery of this regression's files, not
correct logo classification, licences, a new-company result or 9.5 quality.

## 8 November: canonical master prompt and whole-site adapter

Current instructions are in `docs/KAURIVO_MESTARI_PROMPT.md`, loaded by
`utils/master_prompt.py` into the shared service policy. Research, Builder,
revision and QA receive that same text. Its SHA-256 is part of the service
contract; changing it invalidates previous exact-contract review evidence.
The root AGENTS.md directs manual implementations to the same contract.

Design Kehys remains a historical failed first pass (self-review 60/9, no
independent acceptance) and is excluded from new-company trials. The review
exposed a procedural bypass: the standalone visual preflight was used instead
of the whole-site gates. Genuine framing photos were assigned to an unrelated
service, FAQ depth was lost, source narration leaked into visitor text, 3D
labels overlapped, and CMS operation remained untested. A static placement
match cannot decide if the subject actually supports a service claim.

Use the new offline whole-site adapter for manual/Sites output:

```
python scripts/audit_site_contract.py --research research.json --pages rendered-pages.json --stage preflight
python scripts/audit_site_contract.py --research research.json --pages rendered-pages.json --company company.json --artifact deployment.tar.gz --stage public_demo
python scripts/audit_site_contract.py --research research.json --pages rendered-pages.json --company company.json --artifact deployment.tar.gz --stage client_release
```

It combines the existing universal, visual, source-fidelity, price/FAQ and
content checks. Source narration and missing observed questions block even
when the visual-only preflight passes. Unverified runtime, semantic, visual,
publication and CMS evidence stays pending; no passing preflight becomes
client-release acceptance. Actual hosting is not instrumented by this adapter:
an operator must run it. Files and attestations do not prove reviewer identity
or the truth of an observation. No absolute “impossible to repeat” claim is made.

FAQ extraction now includes question-shaped headings and accordion buttons,
not only native details. Inventory truncation caps for headings, table prices
and FAQ questions were removed. Script-only and HTML-hidden output questions
cannot satisfy preservation. These checks establish explicit topic presence,
not semantic answer equivalence, CSS visibility or nuanced factual completeness;
source/new review is still required.

The current rubric is `kaurivo-nine-v2`: the original eight dimensions plus a
separate `motion_scroll` dimension. All nine are equally weighted. Historical
eight-dimension reviews are retained as history, not silently converted.
Missing dimensions produce no accepted mean. Purposeful static treatment can
be justified; merely adding effects does not earn points. Device, reduced-motion
and native scrolling evidence remain necessary.

The new contract preserves company-specific layout decisions; it does not
mandate one visual template, image aspect ratio, effect or card structure.
No additional paid API/model request is introduced. This update does not rewrite
the Design Kehys demo, run a real CMS, authorize messages or certify 9.5 quality.

Validation on 8 November: 155 targeted offline tests passed, including all 10
new master-contract counterexamples. One targeted browser-runtime test was
excluded explicitly, not counted as passed. Compilation and diff checks passed.
The full suite ran 844 tests with 4 failures, 19 errors and 15 skips. A fresh
unchanged HEAD worktree ran 834 tests with exactly the same 23 failure/error
names; the browser executable is unavailable and subsequent browser cases also
report the inherited Playwright sync/async-loop issue. No new failure/error
case was introduced. These are not successful browser or CMS tests.

The existing customer-copy checker was also run on the 17 saved rendered
Design Kehys routes. It found source narration on the article listing,
contact page and portrait article. This confirms that the narrower visual
preflight had missed known whole-contract blockers; it does not rescore or
repair that published demo or prove semantic/visual acceptance.

## 8 November: premium execution after Marttila

Master Prompt v3 preserves brand fidelity as a baseline and adds explicit
prebuild decisions for image scale, service-specific compositions, authentic
work/context, motion material quality and enquiry preparation. The shared
Research schema, service-plan validator and route review requirements use the
same rules; manual/Sites operators remain responsible for running the adapter.
New visual observations require actual display-scale image quality, image
hierarchy, service composition rationale, responsive type detail, authentic
company work and motion material quality. Commercial review additionally
requires enquiry preparation. Static choices remain valid when justified.
These records require observed evidence; strings/checklists cannot establish
sharpness, taste, smoothness or independent reviewer identity automatically.

Rubric kaurivo-nine-v3 keeps nine equal weights and the exact >=9.5 mean,
adding a minimum of 9 for every dimension. Historical v2 reviews remain
history and cannot approve a v3 build. Stricter existing consensus conditions
are preserved. The first Marttila self-review (65/9, no independent acceptance)
is recorded unchanged and the company excluded from future unseen trials.
CMS runtime and native device proof remain pending, not synthetic successes.

Validation: 165 selected offline tests passed (77 shared-contract/service/
scorecard/route/premium tests plus 88 universal/source/media/CMS contract
checks). Five new test methods cover all five missing plan fields, all seven
missing/failed/pending review observations, stale image-scale plans, a >9.5
mean with a dimension below 9, the exact floor boundary, and stale v2 reviews.
Diff whitespace checks passed. No browser/CMS session, paid API request,
customer message or new-company visual acceptance was run by this update.

The adapter's internal-demo/client-release mapping and price-table extraction
fixes from the Marttila build are included: honest draft disclosure is allowed
in preflight, while client release still blocks it; nested legacy layout tables
must not create false price rows. Their two regression tests are included above.
