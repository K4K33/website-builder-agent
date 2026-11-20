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
