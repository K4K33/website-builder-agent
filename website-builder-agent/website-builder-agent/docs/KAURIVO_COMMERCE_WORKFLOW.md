# Native commerce workflow — development status, 8 November 2026

Master contract: KAURIVO_MESTARI_PROMPT.md v4. Applies to automatic, imported,
manual and Sites implementations. This change prepares integration and adds
acceptance gates. It does not establish verified automatic store delivery.

## Routing

Research preserves commerce signals before stripping scripts: icon/ARIA carts,
checkout URLs, purchase actions and Product/Offer JSON-LD. Read-only source
inspection includes the actual catalogue, not just an empty cart. Mutating
add-to-cart queries are evidence, never crawler targets.

`research.commerce_plan` requires `protocol: commerce-v1`, an inspected mode,
and `inspection` containing inspected_urls, catalogue_url, captured_at,
observed_product_count, catalogue_inspected and a source-backed reason.

- `inquiry_catalogue`: purchasing_enabled=false and checkout_observed=false;
  cannot override a discovered purchase action or commerce_required=true.
  Independent source_classification captures on both viewports remain required.
- `preserve_existing`: real HTTPS backend_url and catalogue_strategy; preserve
  the complete sourced catalogue and verify the actual checkout/backend flow.
- `woocommerce_native`: same backend/inspection requirements; generated static
  HTML cannot stand in for native product/cart/checkout pages.

`python main.py build-commerce COMPANY` prepares a native WP plugin, setup
instructions and a manifest. Normal build routes here before paid concept/HTML
calls. State is prepared_not_runtime_verified; no built/client-ready status.
It does not provision WordPress, activate WooCommerce, import products or
configure a gateway. Install only on authorized staging. Native product IDs
must map back to the complete verified source catalogue; no invented stock,
prices, variants, tax, delivery or returns.

## Runtime evidence

Use the same editable WordPress/theme/backend for preview and delivery. Follow
COMMERCE_SETUP.md in the prepared package. Run every manifest required_test on
desktop/mobile using the actual gateway's test mode. Cover catalogue, variants,
cart edits, totals, success/failure/cancellation, order confirmation, stock,
duplicate callback, out-of-stock and customer product editing. Use authorized
staging test products for absent source variant types, never live inventory.

Store `delivery.commerce_runtime` with artifact_sha256, contract_sha256,
deployment_reference, backend_url, checked_at, reviewer_id,
independent_of_builder=true, environment=sandbox and payment_mode=test.
Each tests entry has case, viewport, result, observation and capture_paths.
An observed failure blocks; a missing test/capture remains pending.

Export the actual paid test order using
`wp kaurivo commerce-order-evidence ORDER_ID`, saving JSON privately as
transaction_capture_path. Collect review-material, then reference the actual
commerce_backend_trace item ID as transaction_evidence_id. Required order fields
include backend, environment, order ID, payment transaction reference, paid
status, timestamp, positive total/currency and product/quantity. The paid time
must fall between the exact deployment and completed review. Screenshots/videos
must exist as hashed private files; a generated JSON report is not a capture.

Bundle hashes establish file integrity, not truth or gateway identity. Actual
independent observation, source comparison and existing CMS/premium acceptance
are still required. Do not include customer details or credentials in evidence.
Never substitute fixtures, a success URL or a prepared ZIP for a paid test order.

## Validation and remaining limits

220 targeted offline tests passed across commerce, extraction/crawling,
source/brand continuity, review integrity, quality scorecard, published
experience and editable-delivery acceptance. Python syntax and diff checks pass.
These are synthetic/local regression tests, not merchant runtime evidence.
PHP and Docker are absent here: PHP lint, an installed WordPress/WooCommerce
backend, actual gateway tests and real editor save/publish/restore are unverified.
The next unseen-company trial must demonstrate those before commerce acceptance.
Lasitaivas retains its original self-review (65/9), not independent acceptance.

Native API references:
https://woocommerce.com/document/woocommerce-shortcodes/
https://woocommerce.com/document/woocommerce-shortcodes/page-shortcodes/
