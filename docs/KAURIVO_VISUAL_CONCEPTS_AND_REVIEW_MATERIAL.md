# Visible concept comparison and actual review material

New Research records enable `visual_concepts_protocol: v1` and
`review_evidence_protocol: v1`. These apply to the builder service, not one
customer redesign. Existing records are not silently certified or migrated.

## Before the full build

1. Research records three company-specific creative directions and the source,
   brand, task, media and content plans.
2. Produce actual responsive HTML for all three directions. Each has a home
   page and the same key content route: six pages in total. A single-page
   business uses a private prototype detail route, not a claimed live page.
3. Render all six pages. Collect desktop and mobile PNGs: twelve required
   views. Missing browser captures, broken rendering, or superficial copies
   with only different text/colours block comparison.
4. A fresh comparison context receives shuffled A/B/C alternatives, all twelve
   actual views and verified business needs. It must compare each alternative
   and identify unresolved critical issues. The winning option cannot have an
   unresolved critical issue. Full Build consumes the chosen HTML design.

This is a provisional design choice. It is neither an independent premium
approval nor proof that a site deserves 9.5/10. There is no numerical visual
quality promise. The simple structural duplicate detector assists review; it
does not understand every visual similarity or prove design quality.

The default pipeline adds one bounded concept-generation call and one
comparison call through the existing provider, free-only and budget guards.
No new provider or paid fallback is provisioned. A free QA model must support
the supplied images; missing model/browser capability blocks the stage.

Private concepts disallow scripts, forms, embeds and network-loaded media.
Images must be explicitly staged intake assets. Browser file requests are
restricted to the specific variant folder. Rich video/3D experiences still
require preservation and testing in the final site; static prototypes do not
certify those behaviours.

## Review package

QA collects real bytes into `_review_material/review-*/`: new-page desktop and
mobile images, available original captures, source and copy inventories, media
decisions, browser results, journey records, prior-client comparisons and
concept captures. Each route's image is preserved before rendering another
route, including pages sharing one source folder.

Missing captures remain explicit gaps. The collector does not execute a sale,
submit a contact form, fabricate a journey recording, invent a prior-client
capture or approve its own work. Actual `journey_captures` and
`prior_client_captures` can be supplied in QA state for permitted test tasks.
Production actions still need their existing authorization.

The review manifest binds each file hash to the exact HTML/assets and current
service contract. Editing HTML, assets, source facts, selected design or review
bytes invalidates the corresponding proof. Technical, content, visual and
commercial review records must reference actual `evidence_ids` from this
manifest, alongside their existing independent-review requirements. A URL,
checkbox or numeric self-score cannot replace those files. Missing proof keeps
client readiness pending. Technical pass is not visual or commercial approval.

## Commands

Run from `website-builder-agent/website-builder-agent` inside the repository:

```bash
python main.py concept-previews COMPANY
python main.py choose-concept COMPANY
python main.py review-material COMPANY
```

To import separately authored work without a model/API call:

```bash
python main.py concept-previews COMPANY --response concepts.json --producer AUTHOR
python main.py choose-concept COMPANY --review comparison.json --reviewer REVIEWER
```

`concepts.json` contains `concepts: {direction_id: {pages: {route: HTML}}}`.
Use the three exact Research direction IDs and the two required routes. The
comparison file contains `selected_alias`, `observations` (A/B/C text),
`critical_issues` (A/B/C arrays), and all twelve `reviewed_view_ids` from the
manifest. Producer/reviewer identities must be explicit and truthful.

`review-material` gathers existing files without API calls. It does not refresh
browser captures or make the review independent. Indexes and captures are
internal working material, not public client demos.

## Validation and remaining pilot

Tests cover real HTML requirements, six-page/twelve-view coverage, superficial
duplicates, active content, file containment, changed evidence, missing task
captures, build bypass, and independent review separation. CI additionally
renders all six fixture pages in Chromium. Synthetic fixtures are explicitly
labelled; they are not real-company quality results.

The five-distinct-company pilot remains a separate validation step. At
implementation time this execution environment has free-only mode enabled but
no configured local research/builder/QA models. No paid fallback or real-company
model run was performed. After local model readiness is restored, evaluate five
new companies in distinct industries, retain source-versus-new screenshots,
record failed first attempts and judge each required domain independently.
Longer original-site observation, broader browser/state coverage and actual CMS
editing trials remain further development work, not completed capabilities of
this change.
