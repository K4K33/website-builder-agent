# Kaurivo V3 — multi-page motion and visual direction

The site is now a five-page static experience: Home, Services, Process, FAQ and Contact.

Changes:
- Sharper black, white and vivid electric-blue contrast. Avoid generic grey-on-grey sections.
- Retain the original user-approved Kaurivo mark and familiar navigation proportions.
- Restore **purposeful** motion: compositor-friendly reveal, marquee, animated accent, 3D pointer tilt (on fine-pointer devices only) and a progressive process showcase.
- Do not run WebGL or continuous full-screen shader loops; no 420vh pinned scrolling.
- Suspend interaction updates when there is no pointer movement. Respect reduced-motion.
- FAQ is a separate routed page, never buried in homepage scroll.
- Contact remains an honest mailto draft; no server collection or false claims about submissions.
- No fabricated testimonials, client case studies, revenue numbers, or prices.
- The static site has 0 paid API dependencies.

QA: tests/test_kaurivo_v3.py tests all routes, assets, links, mobile no-overflow, FAQ, navigation, and reduced-motion behavior using local Playwright. No network credentials or external AI calls.
