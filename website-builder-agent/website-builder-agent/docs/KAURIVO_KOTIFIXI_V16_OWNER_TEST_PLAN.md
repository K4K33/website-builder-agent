# Kotifixi V16 — source-first owner/entrepreneur acceptance pilot

**Status:** internal Kaurivo redesign concept. It is **not** the live Kotifixi
site, not owner-approved, and the public GitHub Pages preview is not a
customer-ready sales domain. Real logo, customer photos, testimonials,
customer CMS access and domain transfer require owner approval and technical
verification. No cold outreach or live customer traffic is authorized here.

## A. Tests Kaurivo can perform without the business owner

These are fully free apart from the user's normal internet/equipment use:

| Priority | Test | Concrete method | Pass criterion |
| --- | --- | --- | --- |
| P0 | Content parity | Compare the complete original 5 routes and V16, including seasonal services and every X-marked price | No silently omitted categories, ungrounded prices or wrong tax claims |
| P0 | Visual source-first | Side-by-side real first-screen and full-page screenshots, mobile 320/390, tablet 768, desktop 1440 | Real brand recognizable; no fake logos/photos/AI filler |
| P0 | Every link | Open internal routes, tabs, anchors, phone/email actions, tax source | Actual destination, no dead controls |
| P0 | Responsive/keyboard | 12 viewport Chromium checks, menu Escape, focus and reduced-motion | No overflow, no hidden vital CTA |
| P0 | Form security | Validate required fields; mock success, failure and double-click; run harmless fake test submission only with admin consent | Error does not impersonate success; no real Kotifixi mail |
| P1 | Price/tax updates | Verify Verohallinto 21.10.2026 rules and source site date; check 40%, €2,100 and €150 | No blanket tax-deductibility promise |
| P1 | Performance | Lighthouse lab/mobile on hosted custom preview; normal phone on 4G | No jank, legible media, image load fallback |
| P1 | Sharing | Share a private internal review link through email and iMessage to own devices first | Correct thumbnail, clickable HTTPS link, no confusing interstitial |

## B. Tests requiring the Kotifixi entrepreneur or explicit client permission

Do not send these as an unsolicited long checklist. Schedule a **short
20-minute owner test** with only the top five questions; optionally follow up
with a CMS/form test after interest.

1. **Real brand check (P0).** Show original and V16 side by side for 10 seconds.
   Ask: "Tunnistatko heti Kotifixin? Mitkä värit, kuvat, sanat ja tunnukset
   haluat ehdottomasti pitää?" A generic blue mock wordmark is not the
   licensed original logo by itself.
2. **Service and price signoff (P0).** Ask which categories and prices are still
   sold today, which are seasonal, which are *not* tax deductible, which may
   have travel/material fees, how minimum/rounding works, whether fixed prices
   and payment methods remain current.
3. **Real lead journey (P0).** With permission, send **one** clearly labeled
   "TESTI" enquiry from a permitted test address to the entrepreneur's actual
   agreed recipient endpoint. Confirm receiving mailbox, spam folder,
   timestamp, notification on phone, reply-to accuracy, lead readability and
   the entrepreneur's response. The isolated Kaurivo demo endpoint is **not**
   proof that a Kotifixi production enquiry would be delivered.
4. **Sharing a proposal (P0).** Send the versioned preview to the entrepreneur
   on the channel they choose (email/SMS), from a recognizable Kaurivo
   identity. Ask them to open it themselves on their own phone, then answer:
   "Vaikuttaako tämä uskottavalta tarjoukselta juuri sinun yrityksellesi,
   vai tuntuuko se geneeriseltä?" Record whether any browser
   warning/interstitial appears. Never impersonate the company or silently
   replace its live domain.
5. **Customer role-play (P0).** Ask the entrepreneur to act as a customer:
   find one specific service, its correct price, and the way to order it.
   Observe without guiding. Success: correct path and price without confusion.
6. **Photo and wording approval (P1).** Agree which exact original photos,
   slogans, service text and company mark may be reused on the proposed site
   and in the demo. External Pexels photos must remain labeled illustration.
7. **Owner self-editing test (P0 before real delivery).** In a **separate**
   private, customer-authorized CMS pilot, give the owner a low-privilege
   editor account. Let them change one price, one image and the hours,
   publish and revert; check their mobile editing experience and backups.
   A static HTML preview does not meet this requirement.
8. **Ownership and compliance (P0 before real release).** Approve domain,
   hosting, data processor/retention, privacy notice, the recipient of contact
   data, backups, cookie requirements where relevant, maintenance scope,
   client acceptance and a rollback plan. Do not send live enquiries before
   those decisions.
9. **Blind customer study (P1).** Ask 3–5 real potential customers unfamiliar
   with the design to identify Kotifixi's service, price and contact action.
   Collect specific misclicks/confusions, not just a 1–10 aesthetic score.

## Specific first outreach/pilot protocol

- First send a **non-public review link to yourself** and a teammate to
  confirm the host has no scam-looking warning, broken photos or weird
  previews. Do not use raw.githack / github.io as an external sales brand.
- Ask the entrepreneur whether they'd like to review a no-obligation demo.
  If yes, send the link, state it is a *concept*, and invite **one**
  concrete response: "Mikä on tärkein asia, jonka haluaisit säilyttää
  nykyisestä sivustostasi?"
- If the entrepreneur is interested, arrange a 15–20 minute screen-share.
  Demonstrate one actual lead test and one CMS edit only after the
  necessary sandbox and ownership permissions exist.
- Observe which parts feel wrong to the owner. Write a verified
  change request to the common feedback/QA ledger; do not paste
  business-specific taste into every future client's style.

## Release blockers (must remain honest)

At V16 initial coding, **not yet proven**: actual GitHub Pages live site
publication, independent exact-build premium review >=9.5, real Kotifixi
business form delivery, original logo/photo consent, working owner CMS,
published custom branded domain and complete current owner price confirmation.

The independently testable content and browser cases are implemented
separately in tests/test_kotifixi_v16_preview.py. A green CI is functional
evidence, **not** a sales/conversion or customer-approval claim.
