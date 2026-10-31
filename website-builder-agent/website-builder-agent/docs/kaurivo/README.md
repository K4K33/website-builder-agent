# Kaurivo — V4 premium multi-page website

Live preview after GitHub Pages deployment:
https://k4k33.github.io/website-builder-agent/kaurivo/

Pages (independent URLs, shared design system and navigation):
- Home: \`/kaurivo/\`
- Services: \`/kaurivo/services/\`
- Process: \`/kaurivo/process/\`
- FAQ: \`/kaurivo/faq/\`
- Contact: \`/kaurivo/contact/\`

## Changes based on real 30 October 2026 screen recording

The user approved the branding and navigation but found the V2 appearance
too soft, the page too flat without animations, and the one-page FAQ/sections
too long. V3 reintroduces intentional interaction rather than the V1 WebGL
background or long sticky 3D scroll animation:

- Crisp navy/black, high-contrast white type and electric-blue highlights.
- Original Kaurivo mark and familiar restrained black navigation preserved.
- Responsive HTML/CSS hero mockup with subtle GPU transform-only pointer tilt;
  short, staggered entrance and intersection-reveal animations.
- Interactive three-stage website prototype on Process. User-controlled,
  keyboard-operable and instantly switchable; not scroll-locked.
- Separate Services, Process, FAQ, Contact pages and working cross-navigation.
- FAQ uses native semantic details. No FAQuestions on the landing page.
- A clear offer for premium business websites with editable content, and
  truthful distinctions between concept examples and delivered client work.
- Contact form **only prepares a mailto email draft** (no backend, no
  automatic send or data collection). Users send manually in their mail app.
- Reduced motion, hover/coarse pointer and hidden-tab animation safeguards.
- No fake client references, testimonials, results or prices.

## Release checks

Run \`python -m unittest tests.test_kaurivo_site_v2 -v\` from the inner
project directory. Although the historical test filename ends in V2, it now
validates V3 pages. The CI suite runs Playwright Chromium at 320, 390, 768,
1440 pixel widths across all five pages, checking overflow, navigation,
FAQ, process steps, form, and JavaScript errors. Browser tests use only local
\`file://\` HTML and no external API credits.

All pages currently include \`noindex,nofollow\` because the site is still
a preview rather than a fully reviewed commercial launch. Custom domain,
integrated backend form, privacy details and client-ready copy should be
reviewed before replacing this preview with a production site.

GitHub Pages deploys from the \`docs\` subfolder on the main branch.

## V4 update — 30 October 2026

User-tested changes after V3:
- On every Services, Process, FAQ and Contact page, a conspicuous
  **← Back to Home** link appears before the main heading; Home is also a
  labeled navigation item. The brand logo is never the only return path.
- The homepage hero restores V1-inspired editorial browser depth and a
  *slow, transform-only* vertical float, without pointer-following tilt,
  WebGL or a long scroll-locked animation. Mobile and reduced-motion
  users get an effectively static hero.
- The palette is now sharp dark charcoal, off-white, and neutral
  metallic-silver details; electric blue is deliberately avoided.
- Preserve the V3 separate pages, accessible FAQ, step tabs and email
  enquiry draft (not a backend submission).
- The offline CI browser suite checks responsive layout and verifies
  the dedicated Back to Home control on each inner page.
- Keep the Kaurivo logo and overall navigation identity.

## V5 – proof before decoration, native scrolling

- Removed the artificial floating browser illustration and replaced it with Kaurivo's existing real brand mark, with a single short entrance and thin line reveal (no continuous movement).
- Removed all scroll observers and content-hiding reveal animations; every page section is immediately visible. The fixed header no longer changes padding on wheel/trackpad scrolling and anchor jumps are immediate.
- Replaced another fictional homepage browser mockup with concrete, honest handover deliverables: business-specific design, mobile experience and editable content.
- Premium benchmark for next phase: real, approved client/demo case studies with screenshots and credible process; do not invent client work, reviews, traffic gains or awards.

## V6: finished site and limits
- Home has one short Kaurivo original mark-assembly animation and strong CTA. No scroll interception or continuous hero animation.
- Two fictional but working demo websites are clearly labelled as independent concept studies. No unverified real clients or reviews.
- Native POST enquiries go through FormSubmit.co. The FIRST enquiry triggers a recipient-activation request; the owner must verify `hello.kaurivo@gmail.com` in email before deliverability can be considered confirmed.
- Dedicated Work, Privacy and Thank You pages.
- EN/FI language selector persists via localStorage; demo concepts are intentionally English.
- The performance targets are not actual measured data. Field measurements must be obtained before making result claims.
- Project remains preview-only: noindex until legal/privacy and company ownership details are completed.

## Final V6 viewport regression

Additional 960px navigation test verifies mobile menu opens as an absolute-positioned dropdown without changing layout or scroll width. Existing Playwright browser checks run at 320, 390, 768, 960 and 1440px; original interactive study pages are checked for truthfulness, back links and local-only behaviour. Full performance field metrics are not yet measured.

## iPhone-only correction (2026-10-30)

Reviewed the user's nine-second iPhone screen recording. Mobile under 600 CSS pixels now gets a compact 64px header, readable menu buttons with a full-height accessible drawer, arrow text glyphs rather than iOS emoji glyphs, a shorter hero logo module, larger body/card text, and better touch/form sizing. All changes are strictly scoped to mobile via `@media (max-width:600px)` and/or the equivalent `matchMedia` JavaScript check. Laptop/desktop appearance, behavior and layout are unchanged. The animated logo on the phone uses a short, single composited fade; the desktop's three-part animation remains untouched. Browser tests should verify iPhone, tablet and desktop layouts.

## Customer demo wishes and post-project Gmail feedback (2026-10-30)

A new `demo-review/` page receives a very short **must-haves for the final website** brief (company, reply email, mandatory features, optional wishes). FormSubmit must first be activated by confirming the Kaurivo receiving mailbox; this is **not** a verified end-to-end submission service yet. The page explicitly offers replying directly to the demo email as an alternative. Feedback is for a client proposal, not public reviews or consent for marketing.

After an actual customer handover, request **private service feedback by sending an individual email in the existing Gmail thread**, not by expecting clients to revisit the website. Never auto-send without project completion and owner approval. See `docs/CUSTOMER_FEEDBACK.md` and `utils/customer_feedback.py` for templates and offline quality triage.

## Gmail one-day-after-sale rating (2026-10-30)

A verified client sale triggers eligibility for a private Gmail feedback draft **one Finnish calendar day later**. The formatted email offers five clickable stars; each opens Kaurivo's private web form with a selected rating (requires a verified one-use invitation). A plain reply such as 4/5 and a short comment also works. This rates the purchase/onboarding experience, not a site that has not yet been delivered. The offline helper does NOT schedule, send, or verify sales. A live automation requires a private verified sale record, sender confirmation, duplicate suppression, and authorized delivery.

## Customer-review database, 31 Oct 2026

Kaurivo's real separate Supabase organization (ocglllovgdlilgcpdmon)
has its own active Free project (xhsfbcwpwbgdbatrcyuk; EU North).
Two private tables and a one-time customer invitation RPC are installed
with RLS and no anonymous table policies. The Edge Function
kaurivo-feedback-submit is deployed; the GitHub Pages
/kaurivo/feedback/ form now points to it. The form's approved star
selection, feedback, company and email fields remain the same.
A private invite token is required; no general visitor can insert a
review merely by entering an email address.

The legacy FormSubmit archive workflow remains disabled. Direct
customer email replies have a separate scheduled Gmail review watcher.
Real customer invitations still require purchase verification and
approved sending. No new OAVIR resources were touched. See
docs/CUSTOMER_FEEDBACK.md and docs/kaurivo/backend/README.md.
