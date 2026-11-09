# Website Builder Agent — shared operating contract

Before researching, building, revising or accepting a client website, read
`website-builder-agent/website-builder-agent/docs/KAURIVO_MESTARI_PROMPT.md`.
It is the current project master prompt; older dated quality documents are
history and supporting detail. User instructions retain precedence.

This contract applies equally to the normal pipeline, imported code, manual
implementation and Sites. Do not substitute the visual-only adapter for the
whole-site check. From the application directory run:

```
python scripts/audit_site_contract.py --research research.json --pages rendered-pages.json --stage preflight
```

`rendered-pages.json` must contain every actual rendered route, not React
source. Preflight is not approval. Use `--stage public_demo` or
`--stage client_release` with actual company/evidence records and
`--artifact` for the exact deployment archive before claiming those statuses.
The checker does not publish, send messages, run a browser/CMS, or manufacture
independent evidence. Sites hosting does not automatically execute it.

Add each general failure to the shared lesson registry and a meaningful
counterexample test. Keep first-pass reviews immutable and use a previously
unseen company for the next internal trial. Do not merge review branches or
send customer messages as part of a prompt update.

Commerce discovery requires an inspected commerce-v1 plan, including icon-only
cart/checkout entries. Do not infer an enquiry-only business from an empty cart.
For woocommerce_native use `python main.py build-commerce COMPANY` before paid
HTML/concept generation. This prepares an integration package, not a deployed
store. No commerce acceptance without the exact-backend, independent sandbox
journey evidence and sanitized paid order export required by commerce_workflow.
Offline tests and ZIP generation never prove live WordPress or gateway behavior.
