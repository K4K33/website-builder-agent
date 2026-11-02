# Kaurivo V3 — three different company demos and the current quality gate
Date: 2026-11-02. Repository: K4K33/website-builder-agent.

## Internal owner previews

- Auto repair / TE-Service: `/kaurivo/demos/te-service-v3/`
- Restaurant / Ravintola Rosanne: `/kaurivo/demos/ravintola-rosanne-v3/`
- Construction / Rakennuspalvelu RI-LI: `/kaurivo/demos/rakennuspalvelu-rili-v3/`

## Evidence-based changes from rejected V1

| Category | TE-Service V3 | Rosanne V3 | RI-LI V3 |
| --- | --- | --- | --- |
| Visual hierarchy | Workshop photo and practical repair accordions, white/blue | Editorial serif, lavender and full dated weekday menu | Dark construction portfolio, oversized photo mosaic and yellow |
| Company identity | TE-Service wordmark and Fixus chain badge | Actual purple logo extracted faithfully from original user screen recording | Real yellow smiling house + RI-LI logo from source site |
| Information architecture | Home, repair details, contact | Home/full menu, celebrations and meetings, contact | Home, actual projects, services, contact |
| Key old-source content | Auto repairs, diagnostics, tires, payment, loan car, schedule | Full Mon–Fri 2–6 Nov lunch, explicit G/L/M labels; cafe, grill, events and meeting prices | Six core service categories, real completed project photos, contact and partner link |
| Link handling | Official repair inquiry page, real phone/email | Real phone/email; no fake broken feedback form | Real phone/email and official quote contact |
| Numbering | No decorative 01/02/03 cards | No decorative 01/02/03 cards | No decorative 01/02/03 cards |

### Checked, not claimed

- GitHub objects: 10 HTML files plus company image/CSS/JS present on main.
- Offline structural check: each has one h1, navigation, internal noindex,
  and links to its own existing local pages.
- Bespoke structures: homepage section compositions are distinct.
- Rosanne: five source weekdays and source dietary abbreviations are present.
- No generated before/after photos; no invented live reservation or CRM forms.
- A new credit-free regression test `tests/test_kaurivo_v3_industry_previews.py`
  checks source facts and rejects cloned company layouts.

### Open before any sale/customer-facing version

1. Real browser rendering, especially image loads and page performance.
   Remote customer photos are referenced from original websites and cannot
   be considered asset-rights cleared simply because they render.
2. Contrast, mobile overflow, touch interaction, alt text, actual focus
   behavior and genuine photo/copy quality require real browser screenshots.
3. Rosanne logo is a faithfully cropped and simplified asset from owner's
   screen recording of the original site; request the true full-resolution
   logo for actual customer production. Current Rosanne food photo endpoint
   needs an explicit live load check.
4. Full source-to-new content parity across nested and dynamic pages,
   partner logo permissions, current pricing and opening-hours confirmation.
5. Real editable CMS, branded HTTPS, contact form delivery, customer approval
   and lawful customer outreach are NOT implemented by these static demos.
6. There is NO verified independent 9/10 or 9.5/10 score for V3.
   Score only exact rendered revision after verified real-device review.

Owner URLs are *internal previews* and MUST NOT be sent to sales prospects.
