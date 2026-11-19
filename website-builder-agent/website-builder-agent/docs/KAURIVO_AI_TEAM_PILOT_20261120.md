# Kaurivo AI team — first controlled 24/7 pilot (2026-11-20)

## What is implemented

- GitHub Actions Control Tower wakes at minute 17 and 47 (UTC) each hour and can be manually triggered. GitHub schedules are best-effort: they can be delayed or dropped, so this is NOT a continuously running server or a 24/7 service guarantee.
- Every heartbeat checks the last demo-builder workflow state, counts owner-approved work items, and processes at most one authorized task.
- GitHub Issues are a PUBLIC queue for non-sensitive Kaurivo briefs ONLY. Allowed role lines: Role: designer, Role: developer, Role: quality, Role: social_strategist, Role: social_editor. Issue author must be K4K33, with the label kaurivo-ai-approved.
- The existing OpenRouter key is used only for explicitly exact model IDs ending with :free. Missing key, wrong model or quota => BLOCKED, never a paid fallback. At most one AI request per heartbeat.
- The bot claims an item with kaurivo-ai-running, publishes an unapproved draft in an issue comment, then marks kaurivo-ai-review. On an inference failure it marks kaurivo-ai-blocked and does not automatically retry.
- All drafts must be reviewed by the owner. This pilot does not modify source code, publish client websites, create real edited videos, post to social media, read private CRM rows, or send sales emails.
- The existing private Supabase-backed demo builder, research and master-prompt QA pipeline remains the exclusive client demo builder. Its last workflow status is not proof that any customer site is finished.

## Setup once this PR is merged

1. Open Actions > Kaurivo AI team control tower > Run workflow on main. This bootstraps labels and writes a no-AI heartbeat summary. No AI quota is used if the queue is empty.
2. Read the Actions run Summary. Success means the monitor worked, not that a website is ready.
3. Open Issues > New issue. Example content:

    Role: social_strategist

    Task: Create a seven-post Finnish Kaurivo LinkedIn/Instagram editorial plan using only verified Kaurivo capabilities. Include video scripts and a checklist of every factual claim that needs confirmation. Do not invent clients or testimonials.

4. Add label kaurivo-ai-approved. The next heartbeat processes at most one task, or manually run the workflow again.
5. Inspect the AI draft comment on the issue. Edit task instructions if needed, remove any previous state label and re-apply kaurivo-ai-approved when you intentionally want another draft.
6. For client websites, use authenticated Kaurivo admin > Rakenna demo. NEVER put non-public customer details, customer emails, secrets, client credentials or unlicensed media into the public repo issues.

## Scope boundaries for the six roles

- Project manager: monitors current builder workflow metadata, owner-approved tasks and blocking conditions; cannot guarantee job completion or repair arbitrary infrastructure yet.
- Designer: drafts direction and requirements; a rendered browser preview and owner/independent aesthetic review are still required.
- Developer: drafts implementation requirements and tests. The actual site builder is the existing authorized private pipeline, not this Issue agent.
- Quality: audits supplied evidence and states missing proof; it cannot assign a credible visual score without seeing rendered pages.
- Social strategist: plans and scripts with unverified claims marked; does not post.
- Social editor: produces timecoded edit decisions, subtitles and export guidance. Media ingestion, rights validation and FFmpeg actual rendering are a next milestone, NOT implemented yet.

## Cost and operational guardrails

- Idle heartbeat: GitHub API calls only, no AI inference.
- Approved work: maximum one free OpenRouter call per heartbeat. Rate limits and free-model availability are external constraints.
- Workflow token: repository contents read, GitHub Actions read, Issues write. No code write, private CRM access, deployment rights, social publishing tokens or paid API.
- Interrupted jobs can remain labeled running; investigate before reapproval instead of retrying forever.
- The next upgrade after validation is a managed durable Supabase queue and Render/cloud workers, which can have separate costs. Do not turn on billing or auto-publish without explicit owner agreement.

## Acceptance test for 24h operations

Observe a full day of scheduled heartbeats (including night); count delays/missed runs; submit a sample owner-approved task; confirm correct transition to review; test missing key and paid-model guard; confirm no demo/social publishing occurred without approval. Only then describe this as a proven operational pilot.
