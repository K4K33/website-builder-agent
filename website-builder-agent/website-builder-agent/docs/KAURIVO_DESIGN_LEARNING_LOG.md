# Kaurivo — continuous customer and independent review learning log

## 2026-11-02 — V11: more dimensional design without hijacking scroll

Two owner-uploaded videos evaluated V10 (desktop 41.9 seconds) and Claude Sonnet 5.5 Medium qualitative desktop review (17.1 seconds). Owner observed still-small nav and insufficient depth and animation, and rejected overly generic "Kotifixiltä apua arjen töihin." Claude likewise noted a weaker headline, "Meistä" page not really about the team, overly neutral visual style and browser-managed Chrome translate popup. Follow-up: target explicit question "Tarvitsetko apua kotitöissä tai pihatöissä?", 17–18px nav when space allows, consistent labeled "Näin toimimme" page, layered cobalt/white perspective hero, hover 3D on service cards and small one-shot reveals. No window scroll handler, no WebGL; preserve no-JS and reduced-motion paths. Do not add unsupported social proof. Independent latest-build and mobile reviews are pending.

## 2026-11-02 — V10: human first impression, legibility and Finnish copy

External owner video of V9, owner's friend's independent feedback, and Claude Sonnet 5.5 Medium critique: 12–13px header links are too small, detached plain phone number breaks hierarchy, repetitive "kotona tai pihalla" feels unnatural. About source-report phrasing lacks confident visitor-oriented voice. Some stock imagery visibly contains third-party brands. Scroll interaction was intentionally light but could gain subtle, low-cost entrances.

Next candidate: 15px desktop nav, integrated bordered "Soita + number" action, readable button/focus states, concise Finnish hero and About text, neutral furniture-assembly photo, one-shot below-fold IntersectionObserver reveals honoring reduced motion. Preserve proper demo disclosure, no fabricated business proof, exact contact/price facts. Add multi-width browser tests and programmatic permanent QA rules. No independent exact V10 >=9.5 review yet.

## 2026-11-02 — Kotifixi desktop V8 review → V9 refinement

User review: "ihan ok" visually, scrolling felt somewhat slow on trackpad, some pale text bars looked below premium, and raw.githack's warning page must never be presented to prospects. External Claude Sonnet 5.5 desktop video assessed approximately 8.5/10. Verified video contains the "One more step" raw.githack interstitial, real content, and overly crowded pricing sidebar. Sitewide changes: reduced paint-heavy filters/backdrop and scroll-listener overhead; removed offset hero decoration; separated source-link and tax info to distinct sections; clearer editorial hierarchy and readable copy. Add regression tests and sales-ready branded-domain gate. Maintain owner's preference of zero generic antithesis formulas and client-authentic content. Do not invent owner biography, ratings, photos or tax benefits.

**Status:** candidate only. GitHub integration confirms files, not a real perceptual performance measurement. Reviewer saw prior version; actual latest-commit mobile+desktop independent rating ≥9.5 and three-project consistency are not proven. No client production launch or outreach. For full review, profile with real physical trackpad and complete first-load without interstitial.



## 2026-11-02 — Kotifixi V8: concrete copy, mobile disclosure, feedback as global QA rule

**User instruction:** continue iterative development until quality is good and convert every piece of feedback into cross-project standards, without copying client-specific brands to other customers.

**Findings on merged V7:** slogan repetition was reduced but home section headings still repeated the same "apua" message; the pricing section added little new information; the main demo warning was intentionally hidden on <=700 px mobile layouts. Visual premium and cross-browser evidence remained incomplete.

**Changes in next candidate:** customer-question hero, factual service examples, service-specific descriptions, pricing discovery in a purposeful home section, less duplicated About narrative; preserve verified contact, price source, official brand phrase and explicit test-only form. Keep the demo notice fully visible on narrow phones, fix narrow header spacing. Implement no-credit regression covering rhythmic one–many and contrast formulas with default ZERO tolerated, plus explicit single-exception API. Link a mandatory feedback-to-standard workflow to the cross-client design checklist and builder prompt.

**Evidence limitations:** Checked repo source and real business's public informational page, and noted the earlier iPhone-review feedback; no actual independent reviewer has scored this V8 build, no real browser/screenshots have been executed for the new branch yet. No client production site, sales outreach or customer CMS was changed. Status: **HOLD** pending actual browser QA + independent review of new commit and three-project consistency sample.


Every future customer concept and redesign should append:
date, build/commit, real customer feedback, independent review
scope/model, verified issues, chosen change, measured/visual retest,
and whether the change introduced a regression. Do not overwrite
previous findings when one version scores differently.

## 2026-11-02 — Kotifixi V7 review: anti-formula copy and consistent quality

The user rejected recurring AI-sounding antonym/contrast formulas:
"Vähemmän tekemättömiä töitä. Enemmän omaa aikaa." They prefer
ordinary human-written business language, fewer repeated headings
and slogans, and **max 1** useful contrast pair per ENTIRE site,
or zero by default. This rule applies to ALL customers, not Kotifixi only.

Independent Claude Sonnet 5.5 Medium review of the earlier V7
via an iPhone recording: about 8.5/10. Positives: genuine service-led
structure and much less AI-generated feel, clear quote CTA, better
pricing presentation and transparent demo. Unresolved:
inconsistent service photography, oversized dark stock-photo
labels, repeated idiomatic slogan fragments and need for optional
additional verified content. Claude did not independently test desktop,
media ownership or customer permissions. No fabricated 9.5 score.

**Global decision:** don't claim Kaurivo has achieved a repeatable
premium standard until an independently validated ≥9.5/10 score
is achieved on the actual current build and the same threshold is
proven across at least THREE distinct recent customer demos.
The offline gate records HOLD until evidence exists. User-approved
image/brand rights, real forms, source checks, CMS and sales law
remain separate. Iteration consumes free local resources first;
external reviews are only requested after meaningful revisions.

## 2026-11-02 — clarification: company photos first, examples second

The user explicitly clarified the precedence:
1) Use actual company photos wherever properly available and permitted.
2) Otherwise use curated, licensed, stylistically coherent example photos.
3) Under the demo visual/link in the personalized outreach, disclose
   example images and give a short **optional** invitation to send
   desired company photos for the final site. Don't demand pictures
   or launch an unsolicited image collection.
4) The statement must match the verified *actual demo*, not merely
   the presence of source photos somewhere on the company's website.

General implementation: `demo_photo_source_policy`,
`demo_image_caption`, `place_demo_caption`, `demo_card_caption`
and the global outreach & design QA standards. No automatic sending.

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
