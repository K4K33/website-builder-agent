# Kaurivo — V3 multi-page premium website

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
