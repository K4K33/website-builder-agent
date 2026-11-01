# Kaurivo — customer photography and asset intake (ALL client projects)

**Status:** universal operating rule for prospecting, demos, interested
customers, site production, CMS handover and maintenance. No automated email,
photo upload portal, publishing, or consent collection is implemented by this
document alone. The helper `client_photo_intake_plan` returns an offline,
non-sending decision and a **draft**, never sends it.

## When to request company pictures

**Before demonstrated interest:** research and create a compelling initial
demo using existing assets ONLY if licensed and permitted, otherwise use
coherent illustration, thoughtful type and original graphical composition.
DO NOT ask every cold prospect to send photographs. DO NOT claim the firm
has approved demo reuse or that no image means permission to scrape one.

**After the company expressly responds with interest** and a human checks
that the agreed design needs more actual, suitable images: ask courteously
for **optional** customer-owned photos. One request is enough unless the
company asks for a follow-up. Don't insist on an arbitrary number; list
the relevant *types* based on their actual business and design requirements.
Offer a cohesive licensed alternative if they have no suitable pictures.

Suggested photo categories, only when truly relevant:
- authentic work and completed projects with permission;
- workspace/premises, tools, equipment, vehicles or materials;
- team portraits ONLY with proper permission and privacy review;
- logo in original vector/high-resolution form, if available.

Do not include fake photos of other firms' employees or misleading
before/after examples. Don't demand client photo sessions or new
professional photography as a hidden prerequisite.

## Non-sending customer reply draft (Finnish)

Kiitos kiinnostuksesta! Saisimme uudesta sivustosta vielä paremmin
yrityksenne näköisen, jos teiltä löytyisi muutama hyvä kuva esimerkiksi
tehdyistä töistä, työtiloista, kalustosta tai tiimistä.
Olisiko teillä kuvia, joita voisimme käyttää verkkosivuilla?
Käyttöoikeudet ja mahdollisten kuvissa esiintyvien henkilöiden
julkaisuluvat varmistetaan ennen käyttöä. Jos kuvia ei ole,
suunnittelemme teille mielellämme yhtenäisen vaihtoehdon hyväksyttäväksi.

**Human gate:** personalize for the firm's actual industry, review legal
basis and actual intended recipient; this is NOT automatically sent.

## Rights and approval checklist before an image is usable

- Record the source/owner, the photographer/licensor and license scope:
  website, domain, social, geographic limitations, attribution, duration.
- Check the firm's authorization to supply/use the image, and additional
  photographer/third-party permissions when required.
- If a person is identifiable, verify the relevant permission, privacy
  obligations and purpose. Avoid images of minors without appropriate approval.
- Confirm whether the owner wants original brand photos and fixed slogans
  kept even if they aren't trendy. Don't replace them on an assumption.
- Mark every candidate `rights_verified_by_human`, `client_approved`,
  `identifiable_people` and, when relevant, `subject_consent_verified`.
  These flags describe evidence; **the flags themselves are not evidence**.
- Never copy raw images, personal portraits or private permissions into
  public GitHub repos. Store originals and permissions in a scoped private
  client-approved location; do not expose via public demo paths.
- Confirm cropping, consistent visual tone, mobile clarity and accessibility
  descriptions before delivery. Obtain consent for any image transformations.
- Ask permission for public demo/portfolio use SEPARATELY from the client's
  production website image rights. Do not imply the same authorization covers
  both.
- Include client self-service media-edit workflow in the real approved CMS.

## Image and premium visual design if photos are scarce

Resist forcing many unrelated stock photos into the design. Build a
cohesive **art direction**, with consistent color grade, lighting,
subject, photo crop, scale and context. Use only enough imagery for
the actual content. Raise premium quality through typography,
clear visual hierarchy, precise alignment, spacing, strong authentic
brand accents, original diagrams/pictograms ONLY where suitable,
measured hover/focus transitions, motion choreography, and service-led
composition. Don't fill space with generic AI phrases, decorative
numbers, arrows, invented logos, distracting heavy 3D or repetitive
cards. Unrelated stock style is an acceptance blocker.

**Functional affordance is still required:** no decorative-arrow spam,
but clickable controls MUST look clickable (color, border, contrast,
underlining or button treatment, focus/hover). Removing arrows is
not permission to remove accessible link styling.

## Conversion/navigation check after "de-AI-ifying" a page

A simpler page must not become *less useful*. First mobile view
needs a clear, genuine next action. Make a suitably prominent
`Kysy arviota` / `Soita` main CTA where contact drives the business,
with contextual `Palvelut` and `Hinnasto` as secondary links;
choose only options the business actually supports.
Avoid multiple equivalent links in each section. Preserve the
short task path from service to contact, with verified contact details.
Assess short copy repetition, important service area, verified trust
proof, pricing conditions and relevant Finnish tax information only
if supported by sources and legally applicable. Never invent ratings,
before/after photos, reviews or tax entitlement.

## Practical planning data (offline only)

`client_preferences.interest_confirmed`: explicit human confirmation;
no guess from company discovery, CRM candidate status, or page view.

`client_preferences.planned_photo_slots`: a nonnegative integer based
on approved visual layout, NOT an obligatory photo quota.

`client_preferences.media_assets`: optional private metadata list,
each `{kind: "photo", rights_verified_by_human: true,
client_approved: true, identifiable_people: false}` (or if a
person is identifiable, `subject_consent_verified: true`).
Do not put source image files or clients' private PII in public state.

`client_photo_intake_plan(company)` includes `request_owner_photos`
only when interest is explicit AND verified approved photo count is
short of planned photo slots. Its draft is never dispatched.
The normal client brief also includes that plan under `photo_intake`.

## Documentation of independent review

Log the actual reviewer and model, version, date, **what media they saw**
(e.g. iPhone video only), and supported positives/negatives.
The reviewer does not know any unpublished client licensing, brand
agreements or owner restrictions unless supplied. Its rating is not a
market appraisal, legal clearance, real performance benchmark or
desktop QA. When external reviewers and the owner disagree, resolve
which context explains the difference rather than blindly copying
suggestions. Keep a dated learning log of changes that raised
authenticity while preserving business conversion usability.

**Release gate:** source brand and media approvals, real browser QA
(320/390/768/1440), accessible navigation/link affordances, genuine
CTA and tested form path, coherent art direction, owner acceptance.
If any essential evidence is missing, report NOT TESTED/BLOCKED.
