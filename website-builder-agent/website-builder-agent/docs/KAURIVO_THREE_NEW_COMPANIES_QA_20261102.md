# Kaurivo: three unseen-company demo trials (2 November 2026)

## Goal
Validate design individuality beyond the previous TE-Service, Rosanne and RI-LI snapshots.
These examples are separate source-backed concept sites, not templates. Every site
has a home page, a practical services page and contact details, with CSS/JS
isolated per business. They are internal Kaurivo trials, not client-approved sites.

## Companies and actual websites
| Company | Sector | Actual website | Kaurivo preview |
| --- | --- | --- | --- |
| Visan polkupyörähuolto, Turku | Bicycle maintenance | https://visainen.com/ | https://k4k33.github.io/website-builder-agent/kaurivo/demos/visan-pyorahuolto-v1/ |
| Kukkakauppa Villiviini, Lahti | Florist | https://www.kukkakauppavilliviini.com/ | https://k4k33.github.io/website-builder-agent/kaurivo/demos/kukkakauppa-villiviini-v1/ |
| Verhoomo Kudelma, Tampere | Upholstery | https://www.kudelma.fi/home | https://k4k33.github.io/website-builder-agent/kaurivo/demos/verhoomo-kudelma-v1/ |

## Confirmed source facts, 2026-11-02
- Visan: Yliopistonkatu 8, interior courtyard, Turku; 02 231 1191;
  weekday hours 10-17; bicycle maintenance and repairs, parts/accessories,
  used/new bicycles, Rohloff gearbox information. Direct links retained
  to original product and Rohloff pages. Original source https://visainen.com/
- Villiviini: Koritie 2, Villähde, Lahti; 040 7577 790; Wed–Fri 10-17,
  Sat 9-15, Sun 10-14; wedding, sympathy, business/event floral work,
  weekly bouquets and eKukka checkout. Original source
  https://www.kukkakauppavilliviini.com/
- Kudelma: Hiedanrannan Paja, Tehdaskartanonkatu 46, 2nd floor, 33400
  Tampere as shown on its home page; 040 151 6577;
  verhoomo@kudelma.fi; master upholsterer Anna; traditional and modern
  upholstery; pre-estimate by email photo, appointment by agreement.
  **Important**: Kudelma's older contact/service pages show an earlier address.
  Demo uses newest observed homepage address and warns users to confirm.
  Original sources https://www.kudelma.fi/home and https://www.kudelma.fi/verhoilu

## Distinct creative decisions
- Bicycle shop: crisp utilitarian grotesk, black/acid-lime, mechanical typographic
  energy, wide workshop photos, no fake booking calendar.
- Florist: expressive old-style editorial serif, cream/clay/forest, arch-shaped
  floral imagery, real eKukka destination and correct opening hours.
- Upholsterer: soft linen/burgundy, large bookish serif, dimensional paper/fabric
  layering and editorial object images, photo-first inquiry via mailto.
All components are responsive, honor reduced-motion and maintain real links.

## Content/image integrity and release status
- Concept labels and robots noindex/nofollow on every route.
- Bicycle and upholstery photography and a portion of florist photography
  use freely published Unsplash images. All are labeled **illustration images,
  not the business's work**. Source pages must be checked for trademark/model issues.
- Villiviini images and logo link to the company's own public Wix image URLs.
  Their continued availability and **reuse rights are not confirmed**, so
  these images are not cleared for an approved business release.
- Kudelma original decorative mark is a remote Wix logo, right not confirmed.
- External image hotlinks and original-domain links require live HTTP/browser check.
  The owner should supply original high-quality licensed files before delivery.
- No customer contacted, no outreach emails sent, no commercial sales claim,
  no payment or customer CMS deployed. Static demo does not establish customer editability.
- An independent reviewer 9.5+ score was not gathered. No claim of 10/10.
- New code paths are purpose-built static demo trials. The generic Builder
  media gate in PR #35 remains the production process; remote images used
  in this clearly segregated concept stage are pending production verification.

## QA / usage
Run: `python -m unittest tests.test_kaurivo_three_new_demos_20261102 -v`.
After deploy, verify all nine routes and three remote hero image endpoints with
public-URL smoke checks. Don't email these companies without human review.
