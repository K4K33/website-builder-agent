# Penny Lane (2026-11-04) — source-rich vintage business critique

Reviewed 94-second user-supplied screen recording showing the actual original
business site and a Kaurivo five-route concept. This is an independent-of-builder
USER comparison recording, but the judgement written here is still the builder
assistant's subjective review, NOT an independent audited numerical score.

## What improved vs previous company

- The real combined wordmark and illustrated dress symbol remain in the header.
- The warm cream/chocolate source character is recognizable.
- Five original source photographs were retained in some form (three product,
  one shop interior, one satin-item presentation).
- The user can find separate inventory, consignment, rental and contact routes.
- Existing real details such as two-month consignment, two-storey shop history,
  and the source's physical store address are visible.
- Prior browser 20/20 width/navigation/media-load checks and 656 project tests
  were real technical evidence, but none was a visual quality rating.

## STILL unacceptable before a 9.5 claim

1. **Every subpage starts like the same editorial magazine mockup.**
   The rental page uses a giant, nearly full-width two-line serif heading,
   with a large empty region before any useful apparel image. Inventory and
   shop pages have similarly giant text-only first views. A page for an actual
   rental dress store should typically lead with dresses; a store/contact
   page should lead with location, opening hours or actual people/shop.
   Do not enforce a universal hero layout; derive the first fold from the
   route-specific real visitor task.
2. **Photographic coverage is shallow despite nominal 100% asset preservation.**
   The source satin clothes/shoes photo is reused for homepage, consignment,
   inventory and contact. Three tiny source product images are blown up as
   large catalogue tiles; browser image-load success cannot detect softness.
   Count both unique on-brand photo assets, repeat exposure across routes,
   native-vs-displayed pixel dimensions, and contextual placement. Do not
   hide poor photo availability behind repetitions or AI-generated replacements.
3. **Recognizable agency house styling remains.** Repeated enormous
   Cormorant-like headings, cream/pink sections, rotated postcard frames,
   thin decorative outlines and identical full-width CTA strips make even
   distinct real companies resemble one portfolio. A source-matched palette
   and real logo don't automatically preserve the source site's layered,
   eclectic boutique environment.
4. **The demo still hotlinks photos from the company's OLD WordPress host.**
   Reusing genuine source photos within a labelled internal concept is
   traceable, but a real commercial replacement cannot assume old-site
   hosting remains available. If the original domain/assets are later
   switched off, the new site loses its pictures. Secure rights and store
   licensed originals in owner-controlled hosting before handover.
5. **Content architecture is too thin.** Five routes look like a long
   editorial landing page chopped into five short pages, not five
   task-focused destinations. A product gallery with only three sample
   photographs and vague product headings is not sufficient to show a
   varied secondhand boutique. Never invent stock availability or prices,
   but identify evidence gaps and design around them. Compare the source
   'Uutuuksia liikkeessämme' content area with the new static gallery and
   social link; verify whether the source widget is dynamic before claiming
   feature parity.
6. **Conversion paths are weak.** A visitor contemplating consignment needs
   exact steps, time window, contact and any verified terms where those
   terms were published. A rental visitor needs the clothes visible,
   inquiry details and truthful sizing/availability policy. A customer
   looking for the physical shop should see opening hours/directions
   promptly. Decorative headings should not postpone the primary task.
7. **Some phrasing is template-like.** 'Valikoima elää', 'Jokaiselle
   vuosikymmenelle on oma hetkensä', and repeated formulaic vintage mottos
   may be elegant individually but become filler alongside repeated
   visual templates. Copy must sound like the original store and explain
   actual visitor decisions.

## Mandatory future general tests

- Use SOURCE -> ROUTE -> USER TASK -> CONTENT -> PHOTO -> CTA mapping before
  choosing layout; reject a plan that treats all pages as text-only giant
  headline templates.
- Compare every route's first desktop/mobile viewport with the correct
  original content. Product-rich retail routes need early genuine merchandise,
  unless there is a documented brand-specific reason to be text-first.
- Surface warning when an original shop/work photo is reused on >=3 pages,
  or when there are >=3 text-only short-heading intros despite a photo-rich
  original, or when the same lengthy CTA heading repeats on >=3 routes.
  Those are **editorial review flags** rather than universal aesthetic bans.
- Detect photo hotlinks to the old website. They are fragile under a real
  site migration, and reuse still requires rights clearance.\n- Use actual Chromium naturalWidth/Height versus display geometry to flag
  low-resolution enlarged content photos. 'All images loaded' is not a
  substitute for image quality inspection.
- Verify source dynamic feed, galleries, booking widgets, current offers
  and practical shopping flows before replacing them with static text.
  Unknown behaviour remains REVIEW REQUIRED, not assumed absent.
- Maintain the real shop's existing symbol, palette, personality and content.
  Original brand-media reuse, external photo rights, and customer editability
  remain open until owner permission and CMS demonstration.
- Never present passing automated tests as a 9.5/10 premium aesthetic grade.
  Invite a separate human to review the complete original/new recordings
  and exact code hash before client-ready approval.

## Code changes made because of the recording

- \`utils/cross_route_editorial_risks.py\`: cross-route repeated images,
  text-only intros and duplicated large CTA headings.
- \`utils/browser_qa.py\`: browser-native media resolution review flag.
- \`utils/universal_quality.py\`: cross-route risk evidence included in
  the standard premium QA decision.
- \`tests/test_cross_route_editorial_risks.py\`: business-neutral regression
  cases for repeated-photo templates and valid diverse layouts.

These changes are intended for FUTURE sites; this critique does not claim
Penny Lane V1's layout was revised or that permission for its assets exists.
