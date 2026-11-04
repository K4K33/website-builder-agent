# Kaurivo: transaction and commerce parity is a permanent release blocker

**Source:** 4 November 2026, Castanum original store/user-recorded old-vs-new comparison, observed and reproduced. Applies to **all industries and all future demos**.

## Failure (regression Castanum V1)

- Original public website `castanum.fi` links to the existing live `castanum.ekukka.fi` store.
- Browser-verified eKukka store had 87 catalog products, image/price cards, seasonal and celebration/sympathy categories, basket, delivery-address/date checks, cart and actual payment-provider flow. Source capture: GH Actions run 41816989351.
- Rebuilt website displayed a generic "Verkkokauppa" outbound link but no first-class on-site catalogue with actual products or pricing. V1 passed previous static checks because external href existence was erroneously equated with complete **transactional journey**.
- Customer-facing 9.5/10 review is **invalid** while the business's primary commercial workflow is missing.

## New every-company mandatory contract

1. **Research all original operational surfaces**, not just the official main domain: e-commerce provider, booking engine, menu ordering, memberships, gift cards, appointment forms, customer portal. Record **live browser** behavior, URLs, counts, category labels, product data, price variations, basket, delivery options, checkout, languages, mobile behavior, and date of observation.
2. **Feature inventory > page inventory:** each revenue-critical visitor task has a source-bound destination page and a verifiable end-to-end route; generic redirect, email button or text mention does not automatically count as equivalent.
3. If a source shop is documented, a new demo needs a real **browseable storefront** with documented product images, names, prices, categories, and direct links to the corresponding *real* product purchase page. A checkout must never be simulated or invented.
4. **Live inventory vs static sample:** mark a sampled snapshot as such (Castanum: 30 examples out of 87 observed 2026-11-04), preserve the full live provider shop, avoid claiming stale seasonal products/prices or stock as real-time.
5. **Money flow must be genuine:** never create fake baskets or simulate a payment processor; keep checkout safely at existing merchant payment provider until an authorized real integration and domain/auth/cookie/payment QA are complete. Verify merchant permissions before embedding third-party shops or sending real transactions.
6. **Customer release cannot pass** without ownership/merchant approval, operator access, a real test order path (without charging real cards unless separately authorized), current delivery prices and dates, refund terms, security/privacy, and accessible mobile checkout.
7. **QA must fail closed** when original commerce is seen and either an observed source product snapshot, a browsable store route, source price/image/URL cards, or validated checkout evidence is absent.
8. Check independent source/full-site screenshots as well as numerical tests. Aesthetic review alone cannot authorize revenue regression.

## New code gate

`utils/commerce_parity.py`: source commerce discovery, exact source product card proof, minimum meaningful sampling, category navigation and blocked fake native carts. Called by `utils/universal_quality.py` across every future hand-authored/agent-generated demo.

`tests/test_commerce_parity.py`: unit regressions for missing store, missing shop capture, fake products/prices, fake cart, verified preview, and client-release evidence.

**Honest present status:** The new Castanum storefront is a demo product browser. Actual shopping-cart/session/delivery-price/payment flow still lives at eKukka, as in the merchant's existing store. A fully seamless store embedded or natively integrated into a new site requires documented eKukka/merchant approval, supported integration specification and end-to-end checkout testing. Do not claim that this is done.
