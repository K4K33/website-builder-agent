# Preserve separately hosted shopping journeys

Before redesign, follow every shop entry, including external commerce domains. A link in the header does not demonstrate that product discovery survived. Record each shop, timestamp, exact product URLs, names, source images, observed prices, category structure and complete observed count in `commerce_inventory`. Keep the raw snapshot for review.

Map the catalogue to a local route. Preserve all captured products in real HTML, with `data-product-source` on each card, matching visible name, image, observed price and exact merchant product link. Keep a real local shop entry and labelled search/category/price/sort controls. Exercise filters, empty results, reset and sorting in browser at mobile and desktop widths. Unknown/custom prices must never appear as free products.

`validate_source_plan` blocks Builder spending if a discovered shop is uninspected or partially captured. `audit_source_fidelity` blocks generated sites with missing products. The changed-demo publishing audit applies the same checks to hand-coded sites. Tests include secondary external shops, omitted cards, altered price/image/name, generic shop buttons replacing product links and false local entry markers.

These structural checks cannot prove checkout integration, current stock, current prices, visual quality or client approval. A captured catalogue with original product handoff is explicitly labelled as such. Use the merchant's existing basket and checkout until a real integration is implemented and tested. Never show a simulated cart as a working store. Browser QA and independent editorial review remain separate requirements.

Castanum correction: 87 source products captured from its public eKukka catalogue; 3 parent groups and 7 subgroups in the current response. All 87 appear in the new catalogue. Custom phone product displays “Hinta sovitaan liikkeen kanssa”.
