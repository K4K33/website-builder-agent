# Kaurivo V9 — use genuine free quotas, zero accidental paid API requests

Source verified 2026-11-03:
- Tavily [official pricing](https://www.tavily.com/pricing): Researcher Free
  **1,000 API credits per month**, card not needed. Basic search consumes
  one credit. Other actions/search depths can cost more.
- OpenRouter [official pricing](https://openrouter.ai/pricing): `:free`
  model variants currently have **50 requests/day**, **20/min**, or up to
  1,000/day for accounts with the qualifying historical credit purchase.
  The local default does **not** assume the larger quota. Failed cloud
  attempts may also count. `openrouter/free` is a free router but changes
  the selected model; do not use it for Builder or visual QA.
- OpenStreetMap/Overpass: public access subject to fair-use/availability,
  **not an unlimited service or a contractual volume guarantee**.
- Local Ollama/browser QA: no paid API credits but local power, computer,
  bandwidth, capacity and any hosting still have costs.

## Safety contract

**Default:** `FREE_ONLY=1`, `AI_BACKEND=ollama`. Paid OpenRouter models
are forbidden before HTTP, even with a paid OpenRouter API key installed.
Only exact `author/model:free` IDs or `openrouter/free` for research are
allowed under FREE_ONLY. Stage-specific backend selection lets one job
use the free Research cloud allowance while Builder/QA stay local:

```powershell
$env:FREE_ONLY = "1"
$env:AI_BACKEND = "ollama"
$env:RESEARCH_AI_BACKEND = "openrouter"
$env:RESEARCH_MODEL = "ACTUAL_VERIFIED_OPENROUTER_MODEL_ID:free"
$env:OPENROUTER_API_KEY = "YOUR_FREE_MODEL_KEY"
$env:OLLAMA_BUILDER_MODEL = "LOCALLY_INSTALLED_CODE_MODEL"
$env:OLLAMA_QA_MODEL = "LOCALLY_INSTALLED_VISION_MODEL"
$env:OLLAMA_RESEARCH_MODEL = "LOCALLY_INSTALLED_FALLBACK"
python main.py free-readiness
python main.py free-batch --allow-public-lookups --limit 0
```

Replace model placeholders with *actually available* verified IDs and installed
models; the example is intentionally not a claim of availability or model
quality. There is NO model download/installation, no automatic paid endpoint.
An explicitly configured exact `:free` code or vision model may also be used,
but only after checking its multimodal input support and actual premium QA
scores. The 9.5/10 independent audit, source parity and media permissions
are never bypassed.

OpenRouter local resource budget defaults to **45 of the first 50**
requests/day and **18 of 20** requests/minute. A quota denial/HTTP 429
immediately switches to explicitly configured local Ollama inference,
or fails closed. No cloud paid retry. For keys used outside Kaurivo,
provider-wide quotas may be lower: provider always has the final say.

## Tavily Researcher — free plan, **no paid spill**

A local counter is not a billing limit. **Use Tavily only on an account
verified to be no-card, free Researcher, with no automatic pay-as-you-go,
or a separately enforced $0 billing hard stop.**

```powershell
$env:FREE_ONLY = "1"
$env:TAVILY_API_KEY = "YOUR_FREE_RESEARCHER_KEY"
$env:TAVILY_FREE_PLAN_CONFIRMED = "1"
```

When the above is true, Research first uses real cached OSM/previous
references. For a sector with fewer than eight source candidate URLs,
it can spend **one Tavily basic-search credit** to find additional
real operators. Every operator still needs independent source/industry
validation, non-fabricated quotes and screenshots before it is accepted.
Local free-tier budget is limited to **750 basic searches/month**, leaving
a safety reserve against the official 1,000-credit free limit. The cap is
independent of other clients and computers; use a separate account/key from
the scheduled national-search service **or** one central quota ledger.
If the account can bill, do NOT set the confirmation flag.

## Scheduled national PRH website suggestions

`KAURIVO_TAVILY_API_KEY` remains a GitHub Secret. Separately, a human
must configure repository variable
`KAURIVO_TAVILY_FREE_PLAN_CONFIRMED=1` **only** after verifying that this
specific account does not have pay-as-you-go billing.

The existing Supabase claim endpoint must atomically reserve a credit
**before every request**; the server has a separate hard **750/month**
limit, and the job caps use to **12 basic queries per scheduled batch**.
The PRH shortlist still contains up to 50 leads; with no free-plan
verification, provider key or quota reservation, these 12 searches are
skipped without affecting the free source lead scan. Site ownership
and website presence are never marked verified from a search suggestion.

## More companies without compromising quality

`free-batch --limit 0` still has no **programmatic per-company count
ceiling**. Free external quotas are finite and real; unused work can use
locally installed inference and cached content. It remains a sequential,
checkpointed queue to avoid GPU contention. It does NOT mean unlimited
completed sites per day. Test and publish actual elapsed time and human
visual acceptance rate on real projects before quoting any numerical
capacity or 9.5/10 promise.

Other providers may be added only if there is **a documented verifiable
free allowance, endpoint-specific zero price, and a billing hard stop**.
Do not infer that a provider's promotional trial credit permits unpaid,
unlimited, commercial production. No automatic paid fallback, no
cross-account quota evasion, and no fabricated evidence.
