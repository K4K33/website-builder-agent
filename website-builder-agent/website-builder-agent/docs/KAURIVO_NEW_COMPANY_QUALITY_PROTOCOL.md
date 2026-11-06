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
