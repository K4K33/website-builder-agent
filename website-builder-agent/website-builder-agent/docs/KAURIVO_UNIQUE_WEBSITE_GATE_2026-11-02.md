# Kaurivo — every company receives a genuinely individual site

**Mandatory across all customer work — 2026-11-02.**

## Rejected experiment
TE-Service, Rosanne and RI-LI V1 were the same hero + three/four-column
card grid + feature image + CTA pattern sharing `_shared/first-pass.css`.
Changing brand colors was not a genuine redesign. They are **rejected V1
experiments** and may not be sent to prospects or counted as 9/10 results.

## Before producing each new company's design
1. Inventory all existing pages, original logos/fonts/colors, genuine
   photos, before/after pairs where real, sponsor/partner footer marks,
   services, FAQs, menus and dietary labels, contacts and actual functions.
2. Analyze at least three genuinely strong same-industry benchmark sites.
   Record useful interaction principles, not copyable branded assets.
3. Write a client-specific brief stating a different information
   hierarchy, page composition, hero approach, navigation, photography,
   signature typography, service presentation, mobile order and motion.
   The brief must explain WHY the layout fits this particular company.
4. Create a distinct page architecture, not a common commercial template
   with new colors. Common low-level accessible UI utilities are permitted.
5. Compare renders at desktop and mobile against prior Kaurivo customer
   sites. Confirm differences in DOM hierarchy, image treatment, content
   cadence and conversion paths. Remove useless numbered cards (01/02/03),
   AI phrases, fake testimonials and branding substitutions.
6. Keep the original customer-approved logo and factual details.
   For restaurants preserve actual full menu and G/L/M labels (never
   invent allergen claims). For builders present genuine portfolio photos,
   before/after only from verified matched sets, and partner logos.
7. Pass no-credit browser/accessibility/content tests, plus independent
   art-direction review BEFORE owner-facing preview. A static checker is
   not proof of actual design quality or an independent >=9/10 rating.

## Enforced gate
`utils/design_distinctness.py` checks structural similarity between
different companies before Builder saves its `index.html`. A repeated
layout + same core stylesheet blocks the site; a near-exact structure
is also rejected when stylesheet names change. Regression tests must
detect the three original V1 pages as recycled designs.

This is a necessary technical screen, not a full visual originality
classifier. A human comparison and approved real branding are also
required. The accepted Kotifixi V15 design is a quality benchmark,
not a reusable visual theme. Customer-facing release still requires
content verification, image rights, working CMS, branded HTTPS and
explicit approval.
