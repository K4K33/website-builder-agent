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

## Depth scene and touchable product (free 3D from real photos)

`utils/depth_estimation.py` runs two open models locally with onnxruntime,
downloaded once from GitHub releases and verified by SHA-256 (cached in the
worker with actions/cache): Depth Anything V2 Small (Apache-2.0) for depth
and U2-Net-p (Apache-2.0, rembg) for product masks. About 1.3 s per photo on
a CPU; no API, account or cost. Failure of either keeps the fallback.

- Depth scene (default for photo heroes): each hero photo gets a depth map
  (about 40 KB). A WebGL shader dollies the camera into the photo (near
  pixels move more than far ones), dissolves to the next photo front to back,
  and tilts and lifts a lens where the pointer or finger is. Pitskun test:
  3 photos in 4.9 s and 120 KB, against 48 s and 6.8 MB for frames. Frames
  remain the fallback, and the path for a company video.
- Touchable product (`utils/product_relief.py`, `data-kaurivo-product`): a
  product photo is cut out and given depth; the product floats as a lit
  relief with a soft shadow and turns toward pointer, finger and scroll.
  Only clean cut-outs are accepted (coverage 6-75 %, little contact with the
  frame edge, few uncertain mask pixels); otherwise the photo stays.

Not yet automated: video intake (only images are staged today) and full
360-degree models; the relief turns convincingly up to roughly 25 degrees.

## Sales demos: stock illustrations, own photos later

A sales demo for a prospect with fewer than four own photos may use licensed
stock photos (`utils/stock_media.py`): Pexels when a key exists (new keys
are paused), Pixabay with the free `KAURIVO_PIXABAY_API_KEY` secret, and
Openverse without a key (CC0, Public Domain Mark or CC BY only). Every stock
image is captioned "Havainnekuva, kuva: <creator> / <source>" plus the
licence for Creative Commons, the draft note states that the
images are illustrations and not the company's projects, and no project-like
caption is kept. The final customer site uses the company's own photos and
before/after pairs, requested once the company is interested.

## Sales demo in production (`mode=sales`)

The demo worker accepts `workflow_dispatch` input `mode: sales` together with
`job_id`. For that job it skips the full pipeline and runs
`utils/sales_demo_pipeline.py`:

1. fetches up to six public pages of the source site (same safe-URL rules as
   the readiness gate) and collects visible text, own photos, phone and e-mail
2. one free model call fills the sales demo content plan
3. every field is checked against the source text: unverifiable services,
   chapters, captions and reference lines are dropped (numbers must match
   exactly); an unverifiable headline or no verified service is a HOLD
4. fewer than four own photos are topped up with labelled stock illustrations
5. one page is rendered (shared photo grade, proof section from references),
   published to the internal preview host and verified in Chromium at 390,
   768 and 1440 px, then marked `internal_preview`

Free-model rate limits defer the job like the full pipeline. Nothing is sent
to the company.
