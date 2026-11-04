# Service-wide quality changes — 4 November 2026

Owner feedback on any demo describes a service-level problem by default. Explicit client-specific choices (such as one client's purple palette) remain local. These changes apply to Research, every Builder/revision entry, generated multi-page validation, hand-coded demo publication checks and final approval. No Castanum HTML is modified by this change.

## Workflow and actual enforcement

1. Research receives a deterministic list of original business tasks. Distinct booking destinations, external platforms and contact forms remain distinct. The brief records `business_task_plan`, `media_purpose_plan` and `company_voice_brief`; it cannot overwrite the captured source inventory or verified facts. New research is marked `service_quality_protocol: v1`.
2. Before any new Builder/rebuild/revision request, `validate_service_plan` rejects unmapped, duplicated or invented task ids, invalid routes, unsupported destinations and unknown completion modes. Legacy briefs remain readable, but their output and release evidence are still checked. The Builder receives the actual service contract and the service-wide lesson register.
3. Generated-site and hand-coded-demo QA use the same universal service audit. Known lost external booking/quotation/application destinations and broken planned links are objective blockers. A full original contact form cannot be silently replaced by a mailto draft or a search box. Existing commerce catalogue checks remain in force.
4. Lead photography gets an explicit source, rendered image, observed subject, route-specific visitor task and rationale. A genuine source image, filename or alt attribute does not prove subject relevance. Missing subject evidence stays pending for visual review. This is a structured inspection requirement, not automated image understanding.
5. Company voice is grounded in exact excerpts and source-backed facts. Invented source quotations or unsupported voice facts block QA. Whether the copy sounds natural and specific still requires content review. Source narration and repetitive copy remain covered by the existing checks.
6. Originality now also compares combined split-hero, italic-title and actual CSS font-family patterns across unrelated clients. This is a review flag, not a style ban, AI detector or subjective score. Prior-client signatures are supplied to the reviewer. One common design feature alone does not fail a site.
7. Client acceptance has four separate decisions: technical, content, visual and commercial. Each review references all current routes, the complete bundle digest and the current source/design contract digest, reviewer identity, evidence and open issues. Commercial review needs actual journey results for every task. Visual review covers the media decisions and source/new/prior-client comparisons. Technical success never substitutes for the other three decisions. Existing premium reviewer, brand, CMS and rights requirements remain applicable.

## Evidence fields

`business_task_plan`: `task_id` (from the deterministic source manifest), `source_route`, `destination`, `completion_mode` (`existing_platform`, `local_flow`, `form_submission`). Preserve the exact original external booking destination. Additional browser acceptance instructions belong in the plan.

`media_purpose_plan`: `route`, `src`, `source_src` when the rendered URL differs, `observed_subject`, `visitor_task`, `rationale`. The first content photo of each route must have a matching decision. Rights and redistribution are separate existing checks. If imagery is unknown, record the gap rather than inventing its contents.

`company_voice_brief`: `tone`, `company_specific_facts` (exact source-backed statements), `source_excerpts` with `source_url` and exact `text`. These are internal planning fields and must not leak into customer copy.

`service_quality_reviews`: separate `technical`, `content`, `visual`, `commercial` records. Each has `approved`, `artifact_sha256`, `contract_sha256`, `reviewer_id`, `independent_of_builder`, `checked_at`, `evidence_reference`, `routes_reviewed`, `open_issues`. Technical/commercial records list `task_ids_tested`. Commercial additionally has `journey_results` with task id, completion mode, result and actual completion evidence. Visual additionally has `media_decisions_reviewed`, `source_new_comparison` and `prior_client_comparison`. Content additionally has the reviewed source excerpts. These records must come from actual review; Builder must never fabricate them. Test fixture review records are not real approvals.

## Learning and validation status

`data/service_quality_lessons.json` records each root cause, concrete implementation files, regression test and a distinct real-new-company validation status. It is loaded into the Builder's service contract. New owner rules default to universal scope; active checkers are labelled `implemented_not_field_validated` until supported by separate real-project evidence.

The new regression fixtures use an instrument workshop and hospitality booking, not Castanum. They validate enforcement mechanics with no external API calls or credits. They do **not** prove a new real company's visual quality. Every real-new-company validation in the register remains **pending**. The next real company must be evaluated without correcting these lessons specifically for that company first.
