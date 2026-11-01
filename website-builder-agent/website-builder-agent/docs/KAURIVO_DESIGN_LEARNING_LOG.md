# Kaurivo — continuous customer and independent review learning log

Every future customer concept and redesign should append:
date, build/commit, real customer feedback, independent review
scope/model, verified issues, chosen change, measured/visual retest,
and whether the change introduced a regression. Do not overwrite
previous findings when one version scores differently.

## 2026-11-01 / 2026-11-02 — Kotifixi pilot

**Customer-owner feedback context**
- A redesign should be a **substantial upgrade**, not a recoloring;
  don't overwrite a recognizable existing brand, images, messages
  or slogans without permission.
- The owner wants to be able to edit their website later; a single
  HTML file and a demo form don't prove a working CMS.
- The owner doesn't want Kotifixi's production site changed as part of
  an exploratory pilot.

**Kaurivo creative-quality feedback**
- The early synthetic logo and green generic styling were poor. Keep
  the real customer identity; no imaginary star/house/work icons.
- A long scroll-only site, repeated numbered section labels, excessive
  arrows, circular 'Tutustu' links and repeated images feel templated.
- Sector-specific, matching imagery beats random unrelated stock.
  A smaller curated image set is acceptable, but sparse imagery alone
  isn't a reason to leave the site visually underdesigned.
- A reliable tested form and honest demo status are necessary; a
  mailto composer masquerading as a sending form is unacceptable.
- Removing overdone motion, decorative arrows and stock filler
  meaningfully reduced the AI-generated look.

**External review scope**
Claude Sonnet 5.5 Medium assessed an **iPhone screen recording only**
around 2026-11-02 and estimated roughly **8/10** for the version it saw:
cleaner and more honest functionally, less AI-looking, but not as
visually expressive. This is a reviewer opinion, not a benchmark,
customer acceptance, tested desktop layout or a legal/rights audit.
The reviewer did not have all client photo agreements and constraints.

**Regression to avoid while making it less AI-looking**
- The primary 'Kysy arviota' / 'Soita' action was lost as buttons
  became only 'Palvelut' and 'Hinnasto'. A plain text link without
  visual affordance was insufficient. Restore clear conversion tasks
  and clickable styling, not decorative arrows.
- Copy repetition, tiny grey text and missing supported trust/area
  details are still relevant UX checks. Only add real verified
  evidence, never invented reviews/tax entitlements.

**Generalized decision for ALL future projects**
- Make a cohesive, ambitious visual concept with restrained,
  purpose-driven interactions and a clear first-screen business action.
- A prospect does not owe us photos: only after explicit interest and
  a documented need should a human-approved optional photo request
  be drafted. Verify rights, people permissions, client selection and
  separate public demo/portfolio use. Offer no-photo art direction.
- Test real browser interaction on multiple devices. Record what
  improved, what regressed and what remains unverified. Incorporate
  actual customer feedback even when an external AI opinion differs.

Implementation is documented in
`docs/KAURIVO_CLIENT_PHOTOGRAPHY_INTAKE.md`,
`docs/KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md`,
`docs/KAURIVO_DESIGN_STANDARD_V4.md` and the V7 builder/QA prompts.
This file logs lessons; it is not evidence that old demos are now fixed.
