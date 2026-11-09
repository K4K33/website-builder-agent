# Kaurivo — mandatory feedback-to-standard workflow

## 2026-11-09 — Woodtool: single overall score, no synthetic moving photo light

Owner feedback rejected the pointer-following light wash on a real carpentry
photograph as non-premium. Use the source photograph's real materials,
composition and authentic depth instead; do not layer an automatic spotlight
on client work photos. An effect with a demonstrated brand rationale can be
considered, but must receive actual desktop/mobile visual review and
reduced-motion testing.

**Assessment:** provide one overall website grade (x/10), with premium
quality integrated into it, not a separate premium grade alongside the
overall. Specific visual deficiencies can be explained in prose and the
current build's proof stated explicitly. Release blockers remain binary.
No independent rating is claimed for this code revision.



## 2026-11-02 — Kotifixi V15 owner design approval, stop unnecessary iterations

User approved V15's appearance ("tämä on jo hyvä mielestäni") with a 31.4-second desktop walkthrough. Videos show the principal pages and contact test UI, but don't independently establish mobile readiness, production CMS access, direct customer lead routing or an external >=9.5 score. Decision: freeze V15 visual design as the owner-accepted *internal demo reference*; do not invent a V16 or score-chase. Carry forward learned universal rules and measure repeatability on three unrelated industry projects. Keep truthful demo labels, client content permission and branded-domain/outreach gates independent from design approval.

## 2026-11-02 — final Kotifixi art-direction pass (V15)

User approved the V14 design and asked for the last version. Scope intentionally restricted to small crop/typography/micro-interaction improvements previously discussed: responsive srcset/sizes and intrinsic dimensions for editorial photos, balanced image composition with CSS object-position, readable 15px service-card copy and softer hover lift/zoom without reintroducing heavy scroll effects. Header/button system, page architecture, main headline, prices, example-photo disclosures and demo-only backend are unchanged. Final snapshot is a **design-review candidate**; it is not a new customer production deployment or proof of external 9.5.

Policy for future clients: do internal iterations before first owner-facing preview; test multiple unrelated sectors to validate first-pass ~9/10 aspirations instead of iterating one demo forever. Keep all factual client approval and outreach gates.

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

## 2026-11-02 — V11 desktop review + brief Claude review → V12

**User input:** desktop screen recording (~34.8 s) and Claude Sonnet 5.5 Medium critique (~8.4 s). Owner likes V11 overall but sees the header as asymmetrical (unused whitespace toward the right) and feels the typography does not form a premium, coherent system.

**Reviewed site:** public Kaurivo-owned GitHub Pages V11 internal concept, not client production. Desktop footage reveals a large logo-to-menu gap caused by the `margin-left:auto` flex pattern and visually forceful navigation lettering. User feedback demands layout/typographic refinement, not a wholesale redesign.

**Claude critique:** 9/10-level subjective rating (not independent verified >=9.5 on all devices). Video notes browser Chrome Translate bar; claims that means `lang=fi` failed, which is unsupported because V11 source declares `<html lang="fi">` and UTF-8. It also suggests a more branded visual accent, additional mobile/motion QA, and variants of a headline including the previously rejected phrase "kotona tai pihalla". Retain the owner's preferred naturally worded specific question rather than automatically accepting a conflicting AI suggestion. Indicative external price estimates are not verified Kaurivo pricing and are not adopted.

**Universal V12 action:** real 3-column CSS grid with equally sized outer tracks and center nav, right-aligned contact actions, consistent centered gutters, desktop 16–17px DM Sans menu at weight 600 and deliberate Manrope 700 headings. Active underline refined. At narrower desktop widths hide only the header phone and keep it in the mobile nav. Add Playwright geometry/text-style regression coverage and compare width variants before calling complete. Keep native scroll and pointer-only 3D as already implemented. No automatic customer outreach, no invented founder history.

## 2026-11-02 — V12 → V13: empty header zone, real mouse walkthrough and Claude

**Evidence:** owner uploaded a 65.5-second desktop walkthrough at 1916×874 and a 3.0-second Claude Sonnet 5.5 Medium response screen recording at 1386×762. Near the end of the owner video the pointer deliberately circles a blank horizontal region between the Kotifixi logo and the first navigation link. This is the real issue, not a missing navbar item or an inactive button. Owner prefers redistributing existing links across the empty space without reducing their font sizes.

**Claude findings:** service/process/price area was judged coherent and broadly ready aesthetically, but the review recommends a different three-line headline using the previously rejected wording "kotona tai pihalla", more unique brand identity, and a mobile review it explicitly has not done. It sees a private WhatsApp notification overlay in the owner's screen recording; this is capture/browser UI, not a defect in Kotifixi HTML. Claude's speculative €1,300–€3,000 implementation prices and monthly maintenance estimates are not evidence of Kaurivo's prices. Screenshot blur during fast scroll is not proof that on-page type is blurred.

**Fix and reusable standard:** V12's CSS Grid `1fr auto 1fr` centered the middle nav mathematically, but left a visibly dead region between the logo and the first link. V13 uses `max-content minmax(0,1fr) max-content`, distributed link positions and measured maximum actual gaps. Keep 16–17px DM Sans semibold, right-aligned cohesive contact buttons and native scroll/3D performance. Extend no-credit Chromium coverage to 12 viewport widths and verify menu interactions and overflow. Preserve the user-approved direct question headline and factual/nonfictional About content.

**Gates:** release is still an internal review candidate; do not conflate passing tests with external independent >=9.5, an on-device mobile review or a customer-ready branded domain. Include direct link automatically after publishing.

## 2026-11-02 — V13 review, independent Gemini and V14 header refinement

Owner uploaded an 84.5-second desktop recording of the V13 site (1910×868) and a 17.3-second Gemini feedback recording (1484×878). Owner likes V13 but reports that the two top-right buttons do not fit the overall site styling. Full-width review shows a small neutral-outline "Soita 044 363 2429" button placed immediately beside a separate bright square blue "Kysy arviota" button. Although the layout gaps are better than V12, this pair still looks like unrelated UI pieces.

**V14 change:** wrap the existing two real actions in a common `header-action-set` with subtle cool-grey-blue backing and unified border/radius/height, keep the call link visually secondary and the quote button as the single strong cobalt primary. Maintain separate tap targets and real destinations. At small screens keep one branded quote CTA plus visible hamburger while phone remains in menu and contact page. Respect the native scrolling and existing pointer-only 3D interactions. Add regression checks for five-page structure, link destinations and group styling.

**Gemini observations and limits:** the third-party reviewer notes good minimal visual hierarchy, clear task/service navigation, transparent prices, straightforward contact details and honest tax information; it calls generic stock and openly labelled Kaurivo/test demos signs of a template. Those legal/truthful preview notices **must not** be removed from an unapproved demo. Use client-owned authorized photos, truthful service details and an actual approved production build rather than pretending stock is company work or inventing a founder story, photos, reviews or unrealistic time promises. It also suggested sales pitches, hypothetical price ranges, QR marketing and package offers; these are advisory and not adopted as actual Kaurivo terms or external client outreach instructions. This recording did not provide an authenticated V14 score, mobile audit or real trackpad performance measurements.

**Universalization:** added actionable header consistency, responsive interaction checks, truthful demo vs production distinctions and evidence boundaries into global QA/design/builder systems. New versions must include preview URL automatically. Hold customer release pending branded domain, owner approval, independent quality proof and working CMS.

## 2026-11-02 — Owner selective approval of Gemini's V14 → "10/10" feedback

**Evidence and scope:** user-uploaded 63.97-second screen recording of Gemini Auto discussion of Kotifixi V14, first an 8.5/10 **sales-demo** overall summary (visual first impression 9/10; sales/conversion 8.5/10; personalization before purchase 7.5/10), then a reply to "mikä veisi tämän 10/10 tasolle". The user considers V14 already good, agrees only with SOME suggestions and explicitly rejects blind execution of the full list. These ratings are not verified current-version independent >=9.5 ratings, nor a user conversion study.

**Accept conditionally:** for a future actual prospect, source and verify their approved company brand, contacts and actual operating area; never invent location ("Turun alueella" was only the reviewer example). In authorized sales conversations, demonstrate the real mobile view, clickable phone action and other practical interactions. Confirm real form success/error states offline and their truthful destination; this is worth testing regardless of site design. Continue real client photo and permission intake after genuine interest, not before.

**Reject:** Gemini proposed sample reviews with made-up 5-star quotes to be replaced later: fabricated testimonials are still misleading and cannot appear even in a public sales demo. Don't add review sections without verified testimonials, fake customers, inflated performance metrics or empty content. The suggestion to replace "Kotifixi" with a different prospect's branding confuses the **subject company** with the agency's next lead; Kotifixi V14 appropriately depicts Kotifixi and its actual verified details. Do not quietly erase Kaurivo concept/testing disclosure, send the technical GitHub Pages link to customers, or activate a test-only form as production. A "10/10" sales-demo promise has no proven causal relation to signed sales.

**Decision:** Keep V14 website design unchanged on this review; no V15 exists. Fold evidence-based presentation and QA lessons into the universal Builder, design standard and global QA. Later changes only if the owner identifies a concrete issue or a genuine independent current-version audit finds a material blocker. Formal >=9.5 multi-project release gate still applies.

## QA note for this revision

The V8 branch upgrades the existing V7 GitHub Pages preview, not the client production site. The earlier external **~8.5/10 iPhone-video review** does **not** transfer to this build. Until a real independent review with the required scope has evaluated the new commit, it remains **HOLD**. Static tests cannot certify a final 9.5.
