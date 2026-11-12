# Kaurivo: optional Workers Free backup and resumable research

## Current production

Kaurivo's owner laptop is not capable of running local Ollama. Default
production therefore stays **GitHub Actions + OpenRouter :free**. No Codex
CLI, paid AI route or local GPU is required.

## New research checkpoints

The same private, authenticated and SHA-256-verified per-job storage is
extended with a **research_partial** stage. It is NOT a finished design brief.

For original websites, the research worker now saves:
1. `source`: actual same-business homepage, up to 24 source pages, source
   content and browser-based original-brand/visual observations before AI.
2. `facts`: factual AI extraction after its structured result is received.
3. `references`: the three real industry references and screenshot evidence
   when they have actually been collected.

If a later free provider 429 fails the subprocess, the parent saves that
partial stage into the private checkpoint storage, and a new GitHub worker
restores it after verifying the exact same job, original site URL, source
identity and current Master Prompt digest. The unfinished Research step
still runs and all existing content, visual and QA gates remain mandatory.
The same URL/source facts are not silently extrapolated, and a partial
checkpoint can never be published as a site. Jobs without original websites
still use the existing verified no-site path; no fabricated source is used.

## Opt-in second independent FREE provider

Cloudflare Workers AI has a Workers Free plan with 10,000 Neurons per day.
Only the official, currently Free-accessible model IDs below are used:
- Research: `@cf/google/gemma-4-26b-a4b-it`
- Builder: `@cf/google/gemma-4-26b-a4b-it`
- Independent image-aware QA: `@cf/qwen/qwen3.8-27b`

This option is **disabled until the account owner explicitly confirms**
the Cloudflare account has **Workers Free** and no paid/overage settings.

After the owner sets up a Workers Free account and verifies zero-charge
billing in its dashboard, set GitHub Actions repository Secrets:
- `KAURIVO_CLOUDFLARE_ACCOUNT_ID`: 32-character Cloudflare account ID
- `KAURIVO_CLOUDFLARE_API_TOKEN`: restricted Workers AI invocation token

Then set GitHub Actions repository Variable:
- `KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED=1`

**Do not put tokens into HTML, chat messages, repository files, logs or CRM.**
Free-only configuration does not guarantee Cloudflare Free if the owner
has subsequently upgraded the account to Workers Paid. Confirm the provider
plan and usage controls again before enabling it. If the variable is not 1,
or the credentials are missing/malformed, absolutely no Cloudflare request
is made. There is NO paid-model escalation, no arbitrary user-supplied model
ID and no unbounded retry. At most six Cloudflare fallback API calls are
made during one GitHub process. On Cloudflare 429/403/503 or unsupported
response, the *original job stays queued* with its checkpoints intact.

### Quality caveat

Free Gemma/Qwen and Cloudflare are independent capacity pools, not guaranteed
production availability. Tests with mocks establish the security routing,
not the real account's quota or a 9.5/10 visual result. The owner must
validate a complete real demo (original website, generated preview, responsive
interactions, sourced facts, browser QA) before sending it to prospects.

### Source and policy documentation

- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/
- https://developers.cloudflare.com/workers-ai/models/gemma-4-26b-a4b-it/
- https://developers.cloudflare.com/workers-ai/models/qwen3.8-27b/
- https://developers.cloudflare.com/changelog/post/2026-07-28-models-require-workers-paid/
