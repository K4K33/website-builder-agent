# Kaurivo Premium Design Standard V4 — brand-led and genuinely bespoke

**Applies to ALL clients: new premium pitches, revisions, previews, developer handoffs and QA.**
**Mandatory per-client checklist:** `docs/KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md`.
Every real preview must receive a recorded PASS / FIX / N/A review; no score alone establishes production readiness.
Derived from the 2026-11-01 Kotifixi owner-feedback and observed iPhone screen recording.
This is a written acceptance standard, not evidence that every current auto-generated
website already meets it.

## Brand integrity ≠ conservative visuals

Verify the customer's **real** logo, brand color, imagery and locked copy before
starting. Branded material from an industry competitor cannot substitute for the
customer's identity. A major redesign must substantially improve hero,
composition, content architecture, visual storytelling, mobile usability and
conversion path **while protecting** approved names, logos, photos and phrases.
A logo made from an invented star/house/wrench glyph is not a verified original.
When true brand assets are unavailable: use typography-only name as a marked
temporary proposal and obtain approval before production.

## Never use decorative numbering everywhere

- No mechanical numbering of every hero, service card, label, section,
  image or footer (01 / 02 / 03 or similar).
- Sequence numbers are allowed only when they clarify an **actual ordered
  process**, such as the three steps of ordering a service.
- Remove repeated all-caps micro-labels and gratuitous tiny captions.
  Real service information, editorial composition and clear hierarchy win.
- Human QA must reject a page that feels assembled from repeated AI-looking
  templates, even if HTML passes validation.

## Professional information architecture and navigation

For a multi-page customer scope, use genuine independent page URLs with a
persistent, accessible navigation bar (e.g. /palvelut/, /meista/, /yhteys/).
Do not simulate separate pages by linking a menu to anchors on one
extremely long landing page. Home can still use reasonable vertical scroll;
it should not swallow the entire site's structure.

**Important current limitation:** `agents/builder.py` still only generates
one self-contained `index.html` file; its QA and saved-output format expect
one page. **It cannot be considered a production-ready multi-page builder.**
Until a separate multi-page build/QA output contract is implemented, create
multi-page demonstrations through a separate reviewed workflow and do not claim
automatic agent parity. Never alter output format by prompt-only edits that
would break QA, preview or the existing stable pipeline.

## Cross-industry, human-first visual clarity and conversion gate

- In the **first mobile viewport**, show what the business does, who it serves
  and the next useful action in plain words. Brand slogans alone cannot
  replace the offer. Reveal actual verified services early.
- Prevent *generic premium aesthetic*: symbolic fake logos, luxury lifestyle
  images unrelated to the work, repeated micro-labels and filler headings
  undermine authenticity. Customer-owned authentic visual materials take
  priority when rights and approval are verified.
- Give one coherent, clearly named primary action per context. Make contact
  and booking paths genuinely usable; test submissions if advertised.
- Review **every link destination** in context, especially external pricing
  pages, stale legacy-site URLs, contact endpoints and phone numbers.
  A legacy link is acceptable only if correctly labeled and intentional.
- Verify actual first-load/cold-start behavior on realistic hosting; a free
  preview's slow startup is a demo problem, not an acceptable production
  performance promise. Benchmarking must use real measurements and declare
  device/network.
- Independent AI review is evidence only when a distinct real reviewer/model
  has actually reviewed the supplied artifact. Do not fabricate opinions,
  prices or analysis. Human brand/customer approval remains necessary.

## Motion and visual polish

- Design a deliberate motion choreography: opening entrance, section
  disclosure, hover/focus feedback, optional image pan, responsive navigation.
- Use transforms and opacity, avoid layout shift, unnecessary continuous
  looping, janky scroll hijacking or expensive WebGL by default.
- Preserve functionality if JavaScript fails. Honour
  `prefers-reduced-motion`, show motion alternatives and keyboard focus.
- Check images load, crop and composition work for 320, 390, 768 and 1440 px.
  Unlicensed or unrelated stock photography must be marked as a proposal.
- The brand determines palette and art direction; do not force green or
  Kaurivo's own identity on client brands.

## Human visual acceptance gate

Open the **actual browser-rendered** preview (not PDF/screenshot alone) and
check menu, links, CTAs, imagery, logo fidelity, touch targets, layout overflow,
reduced-motion, form truthfulness and mobile readability. Compare with three
independent real same-industry references. Document actual site shortcomings
and what the proposal improves. No fake testimonials, awards, lead metrics or
imagined features.

An unlisted URL with `noindex` is still **public to anyone who has the URL**.
Never call it a private secure preview. Request owner authorization before
sharing unpublished branded material, use real access controls for genuinely
private client files. No production domain changes without explicit approval.
