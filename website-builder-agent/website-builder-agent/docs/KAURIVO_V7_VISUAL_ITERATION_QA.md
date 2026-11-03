# Kaurivo V7 — evidence-first visual comparison and bounded repair

## Production default

Research captures the **actual original company website**, with explicit source
URL and timestamp, at 320×740, 390×844, 768×1024 and 1440×900. Builder
does **not** get to replace that evidence with competitor images.

After deterministic static QA passes, browser QA renders the rebuilt pages at
matching viewport sizes, including mobile emulation. The V7 visual comparison:

- Finds existing, locally captured original and redesigned images.
- Creates a side-by-side **first-fold PNG** per viewport, plus a simple local
  HTML contact sheet and machine-readable source/build/screenshot SHA-256 manifest.
- Keeps those reports under `output/_visual_reports/<company>/`, **outside the
  deliverable website**, to avoid publishing original website screenshots.
- Checks the original source homepage against the redesigned homepage. Other
  redesigned routes retain their own browser screenshot QA; source subpage
  coverage and identity still require an independent per-route review.
- Produces an actionable **review-and-repair** hint only if an image-led
  business had a clearly prominent real main image on the original small
  phone first view and virtually no visible main photo/video in the redesign.
  CSS hero backgrounds are excluded from this deterministic heuristic.
- Does NOT infer artistic quality from pixel difference. New sites should be
  better designed and need not copy pixels or the exact old layout.
- Marks missing source image, invalid local capture, failed paired image
  rendering or incomplete viewport evidence **review required**, rather than
  scoring an unseen company brand as verified.
- Supplies three of the paired screenshots (320, 390, 1440) to the QA model
  before generated-site screenshots, if and only if paid QA is explicitly
  authorized and benchmark validation succeeds. A model's own score is NOT an
  independent third-party 9.5/10 assessment.
- Never treats site screenshots/source photos as a licence to republish.

## Run without paid AI/search tokens

Within `website-builder-agent/website-builder-agent`:

```bash
python main.py visual-evidence <existing-company-slug>
# For old research records with only 390/1440 or stale/missing screenshots:
python main.py visual-evidence <existing-company-slug> --refresh-original
```

This uses Chromium and, with `--refresh-original`, reads the actual original
public website. It does not call any paid AI or send outreach. Review the
printed `comparison_html` file and `visual-comparison.json` manifest.

Source pages can refuse automated capture or change since the research crawl.
Missing evidence remains pending; a real client/source comparison is needed.

## Opt-in capped automatic fixes

The pipeline retains **default zero paid repair attempts**. For a production
run where the operator explicitly permits paid external APIs, use:

```bash
python main.py pipeline --company <slug> --confirm-live-run --max-revisions 2
```

(Up to three repairs are accepted by the existing CLI.)

The retry decision operates on a **specific actionable QA failure**:
first-fold photo regression, browser overflow, content omission or a concrete
model-review defect. It passes the actual repair hint and report path to Builder,
then rechecks. Repeating exactly the same defect signature stops further
retries, even if the numeric allowance is not exhausted. If evidence is
missing, a browser cannot run, only human/rights signoff remains, or a new
global rule lacks a tested checker, the loop **stops rather than burning
additional credits**.

`QA PASS` does not mean client approval or permission to send emails. Exact
build/source-bound independent assessment, original wordmark/palette/photos
fidelity, comprehensive content parity, accessibility, photo rights and owner
signoff remain in the existing release gate.

## Non-negotiable creative standards

At least the 320px and 390px matched first screens must be visibly reviewed
for (1) complete wordmark treatment and original palette character;
(2) business-specific visual identity and appropriate photo priority;
(3) natural and grounded local copy; (4) no misleading prices, logo marks or
ratings; (5) genuine company-specific user tasks. The remaining pages, 768px
and 1440px views are also evaluated. Original company language and legitimate
photography have priority over a generic agency dark-hero template.

**This implementation is a repeatable QA system, not a claim that every new
site already has a human-certified 9.5/10 result.**
