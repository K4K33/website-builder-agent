# Kaurivo — purpose-first hard acceptance for every company (2026-11-04)

## What failed

A previous real Finnish vintage-company demo passed **20/20 responsive browser checks**,
full unit QA and source-logo/photo presence checks, yet its product/rental/contact
pages opened with the same giant text-only hero. One original satin photo
was recycled across four unrelated pages. Three product thumbnails were
enlarged substantially, and the customer task was delayed below the fold.
These defects were flagged as PENDING and therefore did not block publication.
Adding more prose about quality to agent prompts did not fix the causal bug.

## Changes that modify outcomes rather than recommendations

### 1. Before any paid Builder generation

The original source inventory plus verified sitemap and page user tasks produce
a deterministic, company-specific ROUTE PURPOSE CONTRACT. It assigns
visitor jobs (collection, rental, contact, people, booking, service, general)
using actual researched routes and purposes. The chosen brand system must
remain original to the company. It never generates fake photos or invented
business facts. Repeated identical visitor tasks now fail source-plan validation.

The Builder and Reviser's prompts contain route-by-route first-section
requirements. Product and rental pages with actual original photography
lead with genuine products, location pages with verified contact details
show those details promptly, and each route must have its own narrative
and visual sequence.

### 2. BEFORE the first HTML file is saved

The site build pipeline and universal QA enforce the route contract.
On source-rich multi-page sites, the following defects cause a **blocking
error**, not a warning:

- a product/gallery or rental page whose first substantive HTML section
  contains no image/video of the original company's work or products;
- a contact page which hides genuinely researched address/phone/email
  beyond the first substantive section;
- the same original work/product photograph recycled across 3+ routes;
- 3+ text-only headline intros on a source-photo-rich site;
- an identical long substantive CTA heading repeated across 3+ routes.

This is source-conditional: an evidence-poor business is not required to
produce unlicensed photography. Legitimate exceptional visual arrangements
need **independent human approval bound to the exact original snapshot and
exact resulting HTML**, with screenshot evidence and a meaningful explanation.
The builder cannot self-approve with a generic exception string.

If the gate fails, the generated site is not saved or marked successfully built.
Fix the problematic page composition or choose a different opportunity that
has enough approved source assets. Do not auto-loop paid model calls.

### 3. In actual Chromium at four widths

Images inside a source file can still sit 1000px below a large heading.
Page-specific QA now uses 320, 390, 768 and 1440px viewports to test
**first-fold rendered picture area** for source-rich product and rental
routes. A trivial image sliver does not count as useful first-screen
merchandise. Absent real first-screen evidence fails browser QA; image
quality and independent design judgment remain manual review tasks.

### 4. In manually coded and Codex-supplied demos

A hand-authored static preview no longer bypasses this rule: the changed-demo
pre-publish audit reads the source manifest, derives route roles from the
actual HTML paths, runs the same hard composition audit and fails the
GitHub Pages deployment if a changed demo breaks policy.

Existing historic demos remain available as labelled internal previews,
but they do NOT retroactively become premium-approved. Their content must
pass the new gate if a new version is submitted.

## Verification

The permanent regression suite includes a fixture using the **actual
previously published Penny Lane V1 HTML and source inventory**. It MUST fail
the new gate for missing product-first images, repeated same source photo
and repeated text-only intros. A separate purpose-specific five-page example
MUST pass. Other cases verify legitimate image-poor sites, real source and
build-specific human exceptions, distinct visitor tasks and rejection
**before** any files are written.

A separate real-Chromium test proves that placing <img> inside the HTML
hero is NOT enough when the photo is still below the first viewport.

The mechanisms are deterministic and free of external paid AI credits;
browser/GitHub CI runs still consume runtime. Passing these tests is a
minimum objective floor, NOT a 9.5/10 aesthetic score.

## Remaining honest limitations

- A real designer/independent reviewer must compare the original and
  redesign at the same widths and inspect business voice, palette,
  image crops, depth, logo treatment, and usability.
- Exact first-fold pixel area does not tell whether a photographed product
  is commercially attractive or even the correct product; authenticity,
  ownership rights and page suitability must be grounded by source records.
- A client-ready handover still requires licensed owner-controlled media,
  an editable CMS, hosting/domain access and actual client approval.
- No static QA can guarantee every future company is subjectively 9.5/10.
  The new rule **stops known generic-pattern failures** instead of
  pretending to have solved aesthetic judgment.

## Commercial policy

Do not send a failed or unreviewed preview as a customer-ready offer, and
do not spend additional paid research/build credits looping on the same
known structural failure without a corrected route plan. Continue prospect
discovery and prioritize companies where authentic evidence permits a
strong demo with truthful content.
