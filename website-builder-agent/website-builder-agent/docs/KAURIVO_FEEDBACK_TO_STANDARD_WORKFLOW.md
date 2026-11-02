# Kaurivo — mandatory feedback-to-standard workflow

Applies to every customer, demo, template, agent-generated draft, QA iteration and published project. Owner/customer feedback takes precedence over generic model taste unless it conflicts with verified facts, accessibility, legal requirements or another explicitly approved constraint.

## For EVERY new feedback item

1. **Capture evidence:** date, project, build/commit, screenshot/video or precise quoted issue, location in the page, reviewer identity and actual scope. A review of one iPhone recording must not masquerade as a desktop or whole-site assessment.
2. **Classify scope:** (a) genuinely universal usability/copy/design/delivery lesson, (b) customer-brand or one-project content requirement, (c) unsupported suggestion. Record the classification and reasoning; don't impose one client's colors/photos/brand on everybody.
3. **Generalize the failure mode:** phrase the reusable rule so a later generator can obey it in another industry. A new negative example belongs in regression coverage where deterministic testing is possible. For visual taste, use a mandatory human/independent-review checklist; regex alone never certifies premium appearance.
4. **Apply at source:** update the shared builder guidance, QA instructions/checklists and relevant reusable components, not only the current demo. Add a focused no-credit regression test where feasible. Keep brand-specific changes in the project itself.
5. **Fix the actual site:** check current version, preview at 320/390/768/1440 px, navigate all pages and use real CTA destinations and evidence. Confirm that the cure does not break the previous design, branding, form, phone links or accessibility.
6. **Retest consistency:** don't certify quality from one impressive page. For final customer-facing release the exact current build needs an authentic independent >=9.5/10 review on mobile + desktop, at least three pages, plus the same proven threshold on the latest three distinct client-demo projects. External review is evidence, not an absolute measure of taste.
7. **Log result:** source, change, test result, regressions, remaining blockers, publication/customer permission. Never fabricate review scores, approvals or completed browser runs. Unreviewed = HOLD, not PASS.

## Current defaults from 2026-11-02 Kotifixi V7 → V8

- **Copy:** 0 template-sounding contrast/antithesis slogans by default; one sitewide only with documented editorial justification, never a quota per page. Ban formulaic two-beat constructions like “Vähemmän X. Enemmän Y.” and “Yksi yhteydenotto. Monenlaisia…”, fake inspirational slogans and repeating the same proposition in successive sections. Keep customer-locked genuine slogans unchanged.
- **First screen:** plain Finnish, immediate proof of services, clearly clickable “Kysy arviota” or real phone route. Do not invent lead counts, speed claims or testimonials.
- **Demo truth:** the notice that a concept is not the business’s own published website stays readable even on <=390px phones. A public GitHub Pages preview remains public; do not call it private.
- **Photos:** approved real company images first; otherwise coherent licensed example imagery with subtle, clear source disclosure, never misrepresented as staff or completed client work.
- **Pricing:** show verified price information with date/source/qualification, direct link to the official current source; never promise an unverified total or tax benefit.
- **Release:** maintain factual/rights/legal checks, real client-editing proof for CMS deliverables and owner approval separately from an AI quality score.

## External video review received 2026-11-02 (V7 mobile capture; not V8 certification)

The reviewed V7 design was estimated at about **8/10** by an external model based on a mobile recording; assessment was not a full direct site audit. Positive observations: service clarity, obvious contact action, functional and honest test form, real multi-page structure and subtler example-photo disclosures. Criticisms: forced hyphenation in large headings, too much italic serif, repetitive/impersonal copy, example images that imply an implausibly different service scale, and missing authentic proof.

Universal actions: headline wrapping and typographic restraint, context-specific natural copy, industry-plausible image selection, no invented testimonials, and research-backed legal/financial claims. In particular, the video's **35%** home-service tax figure was superseded by a dated Finnish Tax Administration update effective for 2026–2027 (**40%** of eligible business work, subject to conditions). Neutral tax information does not establish that Kotifixi is eligible or registered; independently verify the seller before making a positive eligibility claim. Sources: https://www.vero.fi/tietoa-verohallinnosta/uutishuone/lehdist%C3%B6tiedotteet/2026/kotitalousvahennys-nousee-takautuvasti--nain-saat-korotetun-vahennyksen-kayttoosi/ and https://www.vero.fi/henkiloasiakkaat/vahennykset/kotitalousvahennys/kotitalousvahennyksen-maara .

V8 already addressed the old contrast slogan and several repeated phrases. This follow-up must not invent reviews, publish without signoff, or treat CSS/tests as a real independent >=9.5 design review.

## 2026-11-02 — Second external V8 desktop review and owner feedback (V9 candidate)

**Observed evidence:** user shared a ~56.7-second desktop browser walkthrough of V8 through raw.githack and a ~19.9-second Claude Sonnet 5.5 review recording. Claude estimated ~8.5/10 for the reviewed desktop view. Main critic: raw.githack's warning/interstitial before the site; a sales-prospect must never see a developer host. It also identified a crowded pricing sidebar where a source link and the tax heading visually touched; persistent template-like serif accents and pale offset hero photo decoration; sparse human/business proof on About; absent genuine reviews/service area; small low-contrast copy. The owner separately reported slow trackpad scrolling and unconvincing text bands.

**Site fixes:** reduce heavy sticky/filter/blur/scroll effects; move tax guidance out of the sidebar into its own readable editorial block, restyle pricing notice and other feature bands, improve text contrast and remove the hero's decorative offset. Keep the existing real service/price facts and test-form honesty. Human image choices must reflect service; do not invent founder identity, reviews or discounts. Use the latest Verohallinto 2026 source (40% / 2100 EUR / 150 EUR), not an obsolete original-site 35% figure.

**Universal policy:** customer-facing demos must open directly on an appropriate verified HTTPS brand domain. Raw.githack, github.io and other generic developer-domain URLs remain INTERNAL only and fail the sales gate. An internal GitHub PR or test PASS does not establish customer-ready hosting.

**Evidence limitations:** a subjective user trackpad sensation is not a confirmed measured page-performance regression. CSS/JS complexity reductions are hypotheses to verify with actual device profiling. The independent reviewer saw V8, not this subsequent V9 code. Keep the ≥9.5 and three-client consistency gate on HOLD until authentic full-device assessment.

## 2026-11-02 — Third video: Claude recalibrates scope of desktop V8 assessment

User supplied a ~12.5-second iPhone screen recording of a **Claude Sonnet 5.5 Medium** conversation evaluating Kotifixi. The reviewer explicitly scopes assessment to the web agency's layout, design, usability and technical execution; client-dependent portraits, real team biography, customer testimonials and business-specific photos are not fabricated. This *scope-limited* appraisal is **about 9/10**, not an audited release certificate and not a score for the newer V9 candidate.

**Actionable design/engineering suggestions:** (1) developer/raw.githack interstitial still a blocker for customers; use verified branded HTTPS preview, (2) uniform stable photo slots with `object-fit: cover`, coordinated crop and radii, no hidden empty photo holes, (3) optional reviews, people/teams and FAQ only with genuine approved content, (4) built-in demo vs production mode so test-form labels, not-official-site badge and Kaurivo test-endpoint behavior disappear only as part of a properly approved production build, never just via CSS, (5) reduce italic headlines, offset hero decoration and crowded price sidebar, (6) readable small text, and (7) retest mobile widths. Suggested optional phone/town input fields remain **deferred** until data need, privacy notice, storage schema and permissions are proven.

**No invented business content:** sale-ready content requirements should be delivered to the customer as a checklist (work photos, operator bio/name if desired, proof/feedback with consent, service coverage, opening hours, correct quoted prices and verified eligibility if tax deductions claimed). Empty sections do not go live. The video's indicative pricing ranges are not adopted into Kaurivo's price list.

**Quality status:** independent designer's scope-limited ~9/10 is useful qualitative evidence. It cannot count as full ≥9.5/10 exact-commit desktop+mobile evaluation or three-distinct-client consistency. Current candidate release remains **HOLD**.

## 2026-11-02 — V9 review, friend feedback and Claude Sonnet 5.5 Medium

**Source evidence:** owner provided a 52.9-second 1916x880 walk-through of the currently published internal V9 review and a 38.4-second recording of an external AI critique. A friend who independently saw the site identified excessively small top-navigation options and a loose, unintegrated phone number. Owner finds the repeated "kotona tai pihalla" phrasing unnatural and agrees on adding purposeful motion.

**External AI observations:** navigation was around 12–13px and some card text felt too small; Meistä wording was third-person and explicitly reported what the company's own website said; unrelated product branding was visible on the About photograph; motion was almost absent except hover. It suggested one-shot subtle scroll entrances and better focus/click states. It also recommended not inventing reviews, client stories, staff or optional pages until real content is supplied. The AI's indicative site sale-price estimates were **not** adopted as Kaurivo pricing.

**V10 fixes:** replace the repetitive home headline with direct natural Finnish, simplify service title and About passage; group the contact phone with a clear "Soita" label and a bordered header action; raise desktop nav text to 15px, improve contrast and focus; replace branded handbook stock with a neutral, source-checked Pexels furniture-assembly photo; use small IntersectionObserver reveals only for below-the-fold sections, with native scroll, no hidden first viewport and full reduced-motion fallback.

**Scope:** outcomes are code and offline browser checks, not an independent current V10 >=9.5/10 certification. Link users proactively after successful publishing; never send raw GitHub Pages to a prospect.

## 2026-11-02 — V10 desktop and Claude review → V11

**Sources:** owner supplied two screen recordings: V10 desktop walkthrough (~41.9 s, 1914×884) and a separate Claude Sonnet 5.5 Medium text-review recording (~17.1 s, 1480×882). Owner reports top navigation still looks small, would welcome *more* layered movement and 3D that does not slow scrolling, and rejects generic headline "Kotifixiltä apua arjen töihin." A better direction is a concrete customer-question headline about household and yard tasks.

**Reviewer positives:** the internal Pages link opens without raw.githack interstitial; the caller/button group and no-longer-third-person text improved; services, price guidance and honest sample photography are clear. **Reviewer criticisms:** the new business-name-repeat headline is weaker than the prior question, Meistä page is actually a contact-process page, style is too plain after stripping every serif accent, desktop Chrome translation popup is seen, animated transitions are not obvious on their reduced movement or narrow capture, mobile view was not evaluated. Reviewer prices are not adopted into Kaurivo offers.

**Changes in V11 candidate:** "Tarvitsetko apua kotitöissä tai pihatöissä?" on the home hero; increase wide-screen nav to 17–18px (keep 16px for narrower desktop); change visible "Meistä" menu label to factual "Näin toimimme" and rewrite the corresponding page without invented owner history. Add branded cobalt image-backplate depth, 3D image frame and cursor-limited hero tilt on desktop, CSS card hover depth, paced small entrance transitions and focus feedback. All heavy work is isolated to transform/opacity and pointer hover; browser scroll stays native. Reduced motion/touch/no-JS fallbacks and no-credit tests are compulsory. In HTML, `lang=fi` and UTF-8 are already present; Chrome's toolbar is user/browser UI, not page code.

**Generalization:** update universal QA and builder prompts, not only this source. Distinguish verified owner-reviewed usability from an unmeasured performance assertion. HOLD for exact-version external >=9.5, measured real hardware performance and customer branded URL.

## QA note for this revision

The V8 branch upgrades the existing V7 GitHub Pages preview, not the client production site. The earlier external **~8.5/10 iPhone-video review** does **not** transfer to this build. Until a real independent review with the required scope has evaluated the new commit, it remains **HOLD**. Static tests cannot certify a final 9.5.
