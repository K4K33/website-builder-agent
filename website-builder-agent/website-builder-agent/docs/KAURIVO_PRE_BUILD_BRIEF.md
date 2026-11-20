# Kaurivo pre-build brief

Before any concept or page is authored, the builder answers six questions
(`utils/pre_build_brief.py`, no AI call):

| # | Question | Answered from | Blocks when |
| --- | --- | --- | --- |
| 1 | The one signature moment and its technique | selected creative direction `first_view` + material that exists | no moment |
| 2 | Which real material exists | source photos, videos, 3D models; staged files decide what a page can use | never (technique adapts) |
| 3 | Brand feel and 2-3 reference sites | selected direction, verified colours/logo, reference comparison | fewer than 2 references |
| 4 | The visitor's primary action | source booking/phone/email journeys, then verified contact | no verified action |
| 5 | Mobile performance budget | fixed budget per technique | never |
| 6 | Verified facts | company facts and the primary offering quote | no company name |

Technique by material, strongest first: `video_scrub` (own video),
`product_3d` (own GLB/GLTF), `photo_sequence_scrub` (3+ photos),
`cinematic_photo_scroll` (1 photo), `typographic_statement` (none).

The reference sites look premium because of real video, real 3D models and
real photography. A hand-coded procedural 3D stand-in for the company's
product, building or premises is therefore forbidden, as is a second
competing signature effect.

Research stores `pre_build_brief`. The concept stage and the builder
re-derive it with the staged media and stop with
`pre_build_brief_incomplete` before spending a model request.

## Signature hero engine (`utils/scroll_scrub.py`)

For `video_scrub`, `photo_sequence_scrub` and `cinematic_photo_scroll` the
model writes only plain HTML in `data-kaurivo-scrub` (poster, up to three
more staged photos, h1, chapter texts with `data-at`, primary action). The
builder then, without any AI call:

1. renders WebP frames from the staged material: a video's frames, or a slow
   camera move with crossfades through 1-4 real photos (desktop 1280x800 up
   to 96 frames, phone 540x960 up to 60), inside 6 MB / 2.5 MB budgets;
2. pins the hero (300-460 svh) and draws the frame for the scroll position on
   a canvas, eased toward the target frame without hijacking native scroll;
3. reveals each chapter at its scroll point, in the DOM;
4. keeps the poster as the first view (fetchpriority high), shows poster and
   all text for reduced motion or without JavaScript, loads 20 frames first
   and the rest in idle batches, and caps the pixel ratio at 2.

Over budget or invalid markup leaves the authored static hero. Verified
20.11.2026 in Chromium at 1440x900 and 390x844: first frame drawn in
0.2-0.5 s, chapters switch at their points, no console errors or overflow.

Not yet automated: video intake (only images are staged today), Three.js
for a real GLB model, and the pointer shader surface.
