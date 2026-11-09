# Premium execution: evidence contract

This development gate checks recorded evidence integrity. It does not run a browser, certify a reviewer, send messages, prove CMS behavior or produce independent approval. Synthetic unit fixtures are not field evidence.

## Before Builder

New research is marked `premium_execution_protocol: v1`. Supply `premium_execution_plan.protocol: premium-execution-v1` and explicit lists `galleries`, `images`, `case_studies`, `motion`. Every scope needs a unique `id`, actual architecture `route`, and CSS `selector` matching exactly one rendered element. Empty categories remain explicit.

- Galleries: `last_row_strategy`, `responsive_strategy`, `purpose`, and `states` with unique `id` and verified positive `expected_count`. Include each filter/group. `service_brief.gallery_layout_recipes` offers lossless desktop/mobile row arrangements, not mandatory shared templates or rendered proof.
- Images: one scope per main image, observed `source_src`, `display_strategy`; identify the actual img. Owner-controlled rendered image files must be captured in the review bundle. Unsupported image formats remain unverified.
- Case studies: `facts.context`, `.work`, `.result`, each with `source_url`, exact `source_text`, and actual `rendered_text`; `missing_information` lists client intake gaps. Never manufacture facts to satisfy the gate.
- Motion: `purpose`, `material_strategy`, and explicit `states` for its real interactions.

The complete plan is part of the contract hash. A plan or master change invalidates prior approval. Reusing the same company does not count as a new-company generalization trial.

## After actual independent observation

`company.delivery.premium_execution` binds `artifact_sha256`, `contract_sha256`, `deployment_reference`, `reviewer_id`, `independent_of_builder: true`, `checked_at`, and `observations` to the exact deployment and private bundle. Observations are recent, after deployment, and recorded separately for each kind/scope/state on desktop and mobile. Never fill these fields from generated code or assumptions.

Each observation has `kind`, `scope_id`, `route`, `state`, `viewport`, `capture_paths`, and `checks`. Non-stateful image/story scopes use `state: default`. Required checks are defined by `utils.premium_execution.CHECKS`; each needs `result` and a concrete `observation`. Current failures block acceptance. Missing/stale evidence remains pending.

Gallery `layout` records `container_width` and all visible image rectangles in `items`, with x/y relative to the gallery container and width/height in CSS pixels, after layout settles. Record filter states separately. This detects the known right-edge orphan; the independent last-row check also covers other imbalance and blank space. Image `display` records measured content width/height in CSS pixels and actual `dpr`. The gate compares required pixels against captured file headers. Numeric sufficiency still requires visual sharpness and crop inspection.

Use actual screenshots/videos via permitted capture roots and regenerate the private review bundle. Bundle items preserve scope, route, viewport, state and actual media source; generated report JSON cannot substitute for captures. Never put private messages or CMS captures in public site files.

## Contact and editing

`published_experience.contact.mode: demo_storage` or `draft_only` with actual verified disclosure can support a reviewable demo, never lead-delivery acceptance. For new-protocol live-form acceptance, an authorized test recipient and hashed private `backend_receipt` JSON are required in addition to validation/success/error observations. The receipt contains `protocol: contact-receipt-v1`, `scope: authorized_delivery_test`, `channel` (email/crm/merchant_inbox), `destination`, `message_reference`, `deployment_reference`, `received_at`. These must match the test and deployment, with receipt time between deployment and completed test. A self-authored export is not proof of receipt; obtain the actual receiver/backend record. No permission to message a company is implied.

New-protocol shared CMS evidence binds `artifact_sha256` to `company.qa.site_sha256`, not just HTML. Include text, image, navigation, header/footer and applicable source contact/hour fields. Each task records before/after, saved/published/restored values, actual captures, and observed login/edit/save/publish/verify_desktop/verify_mobile/restore/verify_restored steps. An available login screen or ZIP is insufficient. Runtime testing remains pending until actually performed.

## Offline regression checks

Run the premium_execution, published_experience, review_bundle, service_quality, premium_experience_acceptance, shared_cms_editing, universal_quality, master_contract and commerce suites. These checks consume no API credits and do not establish the 9.5 visual target. Whole-site preflight/public_demo/client_release checks in AGENTS.md remain mandatory for every implementation path, including manual Sites.
