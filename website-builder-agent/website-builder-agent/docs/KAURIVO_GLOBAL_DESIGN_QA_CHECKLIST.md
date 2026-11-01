# KAURIVO — EVERY CLIENT PROJECT: UNIVERSAL PREMIUM DESIGN & DELIVERY CHECKLIST

**Learning history:** `docs/KAURIVO_DESIGN_LEARNING_LOG.md`. New owner/external feedback must be recorded there with review scope and regression checks before altering the universal rules.

**Scope:** ALL clients, new builds, redesigns, demo revisions, private previews,
full site deliveries. Not a special rule set for any single company.
**Use:** Designer + agent + independent QA + human reviewer. Record each as
PASS / FIX / N/A (with reason and evidence). Any **BLOCKER** means **do not**
approve for customer-facing presentation or production. A static/AI score,
mocked test, screenshot or design prompt never substitutes for browser evidence.

## Universal V7 learning: interest-triggered asset intake and visual premium gate

**Always use** `docs/KAURIVO_CLIENT_PHOTOGRAPHY_INTAKE.md` for every
prospect and client workflow. The media request is an optional,
human-reviewed draft **only after verified customer interest**, and only
when approved images are insufficient for the proposed visual design.
Never auto-ask cold prospects or assume they own rights to public pictures.

- [ ] Owner/client pictures are requested *only after explicit interest*
      and a documented image gap. Offer a no-photo alternative; never
      delay a free speculative demo because the prospect hasn't supplied images.
- [ ] The client has authorized website image use, purpose and licensing
      scope; identifiable people and separate portfolio/public-demo
      usage are checked where relevant.
- [ ] Images follow a coherent creative direction, not random stock; if
      no genuine photo assets exist, prefer fewer coordinated illustrations
      and premium typographic/layout/motion design over misleading filler.
- [ ] Raising visual richness MUST NOT reintroduce manufactured AI
      symbols, repeated number badges, decorative arrow spam, false
      testimonial imagery, overlong scroll or duplicated content.
- [ ] Check primary CTA and obvious click styling in the first viewport.
      "De-AI-ifying" must not replace a useful `Kysy arviota` or
      `Soita` path with only `Palvelut` / `Hinnasto` buttons.
      A plain text link must look clearly interactive without arrows.
- [ ] Confirm CTA, secondary link, text contrast and useful business facts
      in a real mobile browser. No invented service area, reviews,
      tax-deduction claims, awards or metrics.
- [ ] Record what the external reviewer actually saw, including mobile-only
      evidence and missing context of client approvals, before accepting
      suggestions. A score cannot replace owner preference and functionality.

## Discovery and brand — BLOCKERS

- [ ] VERIFIED real business identity, logo file or written approval for
      text-only logotype; never assemble a fake customer logo from generic SVGs,
      houses, tools, stars, first-letter icons or brandless stickers.
- [ ] Confirm real colors, existing slogans and licensed/owned photographs.
      Keep approved brand DNA while redesigning layout **substantially**;
      preserving the brand DOES NOT mean retaining outdated page design.
- [ ] Verify company-specific services, contact details, hours, pricing,
      service area and customer benefits from trustworthy sources / owner.
      No invented credentials, reviews, promises or staff photos.
- [ ] Compare THREE real same-sector websites for observed UX/design patterns;
      write down what to learn, what to avoid, and original adaptations.
      Don't reproduce their copyrighted imagery or interface.

## First impression, usability, content — BLOCKERS

- [ ] **Five-second comprehension:** first mobile viewport clearly answers
      what company does, who it helps and what the next logical action is.
      No abstract slogan as the ONLY explanation of the service.
- [ ] Put the core verified services where customers immediately find them,
      without needing a long scroll through decorative content.
- [ ] Main navigation matches the real agreed page architecture; if sold as a
      multi-page site, it has genuine separate URLs and accurate active states.
      A long landing page can be appropriate **only when scoped as such**.
- [ ] Main CTA uses a consistent, plain-language destination and valid business
      contact/booking details; do not include competing primary actions.
      Actual form delivery, if promised, must be tested end-to-end.
- [ ] Headings, copy and service descriptions contain no repetitive filler:
      remove duplicate paragraphs, vague empty adjectives, needless slogans,
      confusing jargon and template-looking recurring section intros.
- [ ] Eliminate decorative numbers and repeating micro-labels from every card,
      hero and heading. Number only a **genuine ordered sequence**.
- [ ] Audit every editorial photo across **all pages**, not just one page:
      prevent accidental reuse of the same stock photo in hero, cards and
      detail content. Intentional editorial reuse requires a documented
      reason (logos and identity assets are exempt). Record a sitewide
      duplicate-image count before client presentation.
- [ ] Audit the navigation journey as real user tasks (service → price →
      contact), avoiding circular clicks, unnecessary intermediate pages
      and multiple vague "Learn more" / "Tutustu" links with similar
      destinations. Give meaningful link names and remove redundant CTAs.
- [ ] Imagery is directly relevant to actual company work and target users,
      plausible for the specific sector, legally usable and visually coherent.
      A luxury interior / stock lifestyle scene must not displace evidence of
      practical services. Use client's own photos if available and authorized.
- [ ] Every external URL (especially **pricing**, contact and conversion links)
      has been visited/tested, labeled honestly and points to the intended
      current destination. Old-site links may be intentional, but must not be
      misleading or silently replace the new site's own promised content.

## Shared V6 client-feedback guard: coherent imagery, restrained affordances, truthful forms

- Each site's imagery MUST be art-directed as one coherent collection in
  lighting, season, color grade, subject matter and composition. Mixing random
  unrelated stock photos / branded employees from unrelated businesses is a
  client-facing blocker. Owner-supplied licensed photos always take priority.
  If real client photos are unavailable, prefer **fewer**, high-quality,
  stylistically consistent illustrative images, accurately labeled; never
  imply depicted models are the client's staff.
- Assume **no decorative arrows** in every button, service card, contact
  row or CTA. Only use an arrow when it conveys a genuine navigation/interaction
  need and is selectively approved. Explicit destinations and actual click
  styling are better than repeating arrow glyphs.
- Contact UX must be task-based: visitors see services and optional prices,
  then one clear enquiry path. Do not spam identical contact CTA buttons in
  each card and content block; keep a single main CTA in each meaningful view.
- Never ship a form that claims it sends the request but opens a prefilled
  mailto composer. A form must POST to a tested backend and show confirmed
  success/failure, or be explicitly replaced with honest direct phone/email
  contact links. Draft/demo test endpoints must identify the recipient and
  privacy context, and MUST NOT silently forward leads to a client.
- Verify all form behaviors in a real browser and run a controlled synthetic
  submission to confirm server-side receipt; do not claim functional form
  delivery based only on CSS, JS tests, form validation or HTML.
- Preserve real brand identity and locked slogans without using the
  same tagline in repeated boxes/sections; preserve original client photos
  by default unless explicitly approved otherwise. For customer-owned editing,
  verify a real CMS editor independently; demos are not CMS deliveries.

## Quality of execution — BLOCKERS

- [ ] Test with the **actual browser** on 320, 390, 768 and 1440 px,
      not PDF alone: menu toggle, real page navigation, scroll, buttons,
      form, image crop, text overflow, keyboard/tab focus and reduced-motion.
- [ ] Motion provides carefully staged navigation, meaningful feedback
      and depth where beneficial. No mandatory 3D gimmicks, incessant
      motion, heavy scroll hijacking, delayed readability or script-dependent
      blank pages. Static/reduced-motion path remains usable.
- [ ] Check mobile data and first open on realistic hosting. A cold-starting
      free preview host is NOT a polished customer experience. Record
      actual load time and cold-start behavior; choose adequate production
      hosting before making performance claims.
- [ ] Test site URLs and assets in deployed environment. An unlisted/noindex
      link is publicly accessible if shared; private content requires real
      access control. Distinguish preview vs published client site.
- [ ] Accessibility: meaningful landmarks/headings, correct alt text,
      keyboard controls, readable color contrast, usable tap targets.
      Automated passing is not WCAG certification.

## Delivery truthfulness — BLOCKERS for real client handover

- [ ] Client's own approved CMS, roles, live edit of text/image/services,
      backup/rollback and owner acceptance actually demonstrated. HTML-only
      and a mock editor do NOT count.
- [ ] Correct domain, HTTPS, contact form delivery, SEO indexing,
      legal/privacy/cookies as applicable and real hosting tested
      **only after client authorizes a production release**.
- [ ] Independently reviewed: not by same generating model only.
      Include weaknesses, concrete fixes and evidence; never invent a
      second-AI or human expert evaluation.
- [ ] Customer receives agreed documentation and scope; release is explicitly
      approved. No unsolicited outbound email or changes to an existing
      customer site without authorization.

## Decision log (one record PER client build)

Client/project: ______  Version/commit: ______  Scope (landing / multi-page): ______
Audited by: ______  Date: ______  Viewports/browsers: ______
Brand assets approved: ______  Core CTA & destinations: ______
Reference sites/evidence: ______  Motion/performance notes: ______
Issues (severity, owner, verification): ______
Result: PASS / FIX / NOT TESTED
Customer permission to share preview: ______
Owner approval for publication (separate): ______

**Release principle:** "looks premium" or "passed AI QA" is never by itself
proof of brand fidelity, current links, functional CMS, real user performance,
successful contact delivery or customer approval. Keep unverified items
as NOT TESTED and block the relevant release.
