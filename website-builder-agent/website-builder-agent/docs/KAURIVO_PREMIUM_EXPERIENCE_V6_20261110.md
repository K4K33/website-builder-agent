# Kaurivo – Premium-experience quality precedence, 10 November 2026

Universal scope: every researched, generated, manually produced, static, CMS, e-commerce and client demo. Applied as V6 runtime addendum. Not an independent visual certificate.

## Documented failure and why existing master text was insufficient

The owner compared the original dark brown/black Verhoomo 3 Ässää site (photo-rich craft layout, sand typography, authentic in-image image-comparison handle) with the later Kaurivo beige/pink editorial split layout. The rewrite materially changed the original identity and made key interaction worse: CSS-projected flat colored rectangles as material 3D, decorative in-image handle with functional slider in a separate strip, and repeated colored text bands. The exact deployed site passed 18/18 multi-width technical checks and six concept screenshots. Those tests proved HTTP/CSS/keyboard but NOT source aesthetic parity or intuitive drag. The preview branch ran an ad-hoc workflow, not the universal provenance gate.

This is a systematic defect in **evidence scope and builder art direction**, not a demand for more adjectives in prompts. Fixes require both art-direction evidence and fail-closed tests.

## A. Three grounded design references – principles only

1. [De Troupe by L'Étude](https://letude.group/work/atelier-de-troupe-website): showroom-like product presentation, brand-specific editorial style and clean information architecture. For real furniture/upholstery: products and details lead; do not force default pastel agency layout.
2. [Impronta by ET Studio](https://www.e-t.studio/works/impronta-website): movement, whitespace, and light chosen from the product's actual properties. For materials: use genuine light and surface, not simulated decorative halos.
3. [Sundae Creative by Locomotive](https://locomotive.ca/en/work/sundae-creative): visual rhythm, serif/sans and colors chosen from that brand's identity; transitions support narrative rather than decorate every strip.
4. [Kvadrat/Raf Simons](https://kvadratrafsimons.com/): large authentic textile/product photography and readable material context, compared with exaggerated fake swatches. Not evidence that Kaurivo may copy assets.
5. [GSAP ScrollTrigger docs](https://gsap.com/docs/v3/Plugins/ScrollTrigger/) and [Motion/Lenis docs](https://motion.dev/docs/lenis): scroll-synced motion, sticky sequences, and reduced-motion guidance. Only use on user-beneficial sequences; do not capture scrolling unnecessarily.
6. [web.dev animation performance](https://web.dev/articles/animations-overview): favor transform and opacity, measure rendering and real devices. [MDN pointer capture](https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture): direct drag/capture. Reduced motion must remain functional.

## B. Mandatory research-to-art-direction document before HTML

Source `visual_experience_brief` MUST describe at least: first 2 viewport screenshots desktop/mobile; authentic logo/typography, color roles, photography and background texture, primary and secondary motion, image compare/store/gallery existing behavior, source's 3 most successful moments, current drawbacks, changes that would IMPROVE each, rights risk, and the primary business conversion path.

The baseline cannot be assumed bad simply because the company is an SME. If the original site tried premium, identify where it succeeds and why it still needs an upgrade. Preserve strengths first. If no trustworthy visual capture, status HOLD, not a guessed minimalist direction.

Write a 6–10 sentence **company-specific visual thesis**, not just three themes. Reserve a large proportion of screen time/space for the business's most distinctive evidence. Sketch navigation+hero+key inner page with genuinely different internal structures. When the company has existing dark craft imagery, defaulting to beige/pink is a source-composition rejection unless defended with exact image evidence and review.

## C. Layout rhythm and navigation rules

Before building, draw the full page as a silhouette, with composition types for each major section. Reject the same cadence of: colored full-width background → eyebrow label → huge heading → short paragraph → CTA → another colored background. Count repeated modules, but don't ban legitimate long-form reading by arbitrary section quotas. Use asymmetry, layered real photographs, overlapping whitespace, varied scale, image-led sequences, real material closeups and restrained text; only when suited to the brand. Distinct inside-pages must have distinct functions and layouts. Keep source logo and identity exact, with readable menu typography, balanced header mass and integrated contact.

External independent reviewer must answer: “Could I replace the company name and pictures and sell this unchanged to a different company?” If yes, reject and redesign.

## D. Meaningful signature motion – no fake textile 3D

Choose 1–2 signatures that directly show what business sells or makes, not mandatory WebGL on every page:
- Direct manipulation of actual before/after photos: grab handle ANYWHERE on image, pointer/touch drag with pointer capture, accessible keyboard range, same crop/registration, tested at 0/25/50/75/100, perceptually smooth. Standalone range under image is not equal to original in-image handle.
- Authentic fabric-material reveal: real licensed high-resolution macro texture/loop/shadow, tactile layered folds/shape, accurate lighting. If true interactive 3D is useful, model licensed fabric mesh with thickness and roughness, test touch/low-power fallback. Flat untextured CSS rectangles rotated like playing cards are a BLOCKER for claimed material depth.
- Nonessential small parallax/reveal 250–600ms only where it helps attention. Avoid moving lights on photos, spinning icons, everything-on-scroll, perpetual floating, scrolljacking and decorative number systems.

No material scene should be introduced without a true material reference and a visual approval. Abstract CSS samples may still be used as honest 2D palette chips; don't present them as textile 3D.

## E. Staged gates, no checklist gaming

Research lock → brand and source preservation → multiple meaningfully distinct design prototypes **with interaction** → designer visual selection → full-build → static blockers → real browser tests including pointer and touch, screenshots across interaction states and reduced motion → original-vs-new side-by-side including header, source-best feature and first-fold → independent exact-build art/UX review (one overall website score, target >=9.5) → rights, CMS/rollback and client signoff. Each stage has its own evidence, not a list marked green by the author. A screenshot hash is integrity, not approval. No production claims from tests alone.

Automated `utils/premium_experience_gate.py` catches obvious fake canvas handles and untextured CSS pseudo-3D. It intentionally leaves image alignment, genuine texture realism and repetitive strips as review-required, not “PASS”. Browser QA for pointer/touch must be performed on the deployed version; a keyboard-only 51% change is insufficient.
