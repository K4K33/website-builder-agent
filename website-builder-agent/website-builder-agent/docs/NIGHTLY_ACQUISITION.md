# Kaurivo — nightly customer discovery and premium-demo sales workflow

**Commercial objective:** Sell a great website through a genuinely impressive,
company-specific preview. The preview is the product demonstration, not a
generic website template. One exceptional candidate is more useful than 20
unconvincing pages.

## What runs autonomously now

GitHub Actions: `.github/workflows/kaurivo-nightly.yml` runs at **03:17
Europe/Helsinki** (timezone-aware DST) each night from the *default main
branch*. The workflow uses no paid AI credentials and is limited to one
public Overpass request per successful pilot attempt, with **no retries**,
at most 120 source items parsed and at most 5 unverified lead cards
retained. It rotates through 12 small city/sector combinations. It creates:

- `candidates.json` public business source records, explicitly unverified
- `shortlist.md` a human research queue, plus the source and quality gates
- `status.json` run telemetry, including paid-AI and emails = zero
- `data/nightly_seen.json` bounded, disposable de-duplication cache

The GitHub Actions run summary displays the review list. The outputs
are stored as downloadable GitHub run artifacts for 14 days. The seen-ID
cache is best effort and can be evicted; a cache miss is NOT proof that
a firm has never been reviewed. There are no automatic messages or
public client sites in this workflow.

If the Overpass public service refuses or rate-limits a query, the job
will fail cleanly, without trying additional servers or repeat requests.
This is a low-rate *feasibility pilot*, not a license for ongoing
commercial-scale extraction. Use a compliant dataset download or
approved commercial feed before scaling production. Respect source
attribution and applicable data policy. Relevant usage guide:
https://wiki.openstreetmap.org/wiki/Overpass_API

GitHub scheduled workflows are best effort: scheduled jobs can be delayed
or even dropped under load. The GitHub Actions job and daily artifacts
are evidence of what actually ran; there is no "100% on time" guarantee.
Reference: https://docs.github.com/en/actions/reference/events-that-trigger-workflows#schedule

### Manual zero-credit dry run

From `website-builder-agent/website-builder-agent/`:

    python -m utils.nightly_pipeline --mode offline
    python -m unittest tests.test_nightly_pipeline -v

To run exactly one public pilot discovery query by deliberate choice:

    python -m utils.nightly_pipeline --mode pilot-live --max-candidates 5

Neither command calls OpenRouter/Tavily, drafts email, deploys demos or
authorizes contact. The manual GitHub Action defaults to `offline`.

## The full future staged acquisition pipeline

### A. Discovery (nightly automated, pilot implemented)
- Search bounded source records, skip duplicates when possible.
- Do not infer business inactivity, poor finances, unprofessional design
  or complete absence of a website from missing third-party tags.
- Prioritize candidates for independent confirmation. Existing-site
  opportunities require a **real** desktop and mobile audit.

### B. Research (human or explicitly authorized research agent)
- Verify current operation, business identity, exact website URL/no-site
  status, actual services and contact addresses. Use traceable sources.
- Existing business: preserve approved identity, logos, palette,
  original licensed photographs and protected slogans.
- New business website: make a fresh, ambitious design while honoring
  any brand already used in other channels.
- Compare **at least three real high-quality same-industry websites**;
  collect concrete design observations and screenshots, not copy assets.

### C. Premium demo (NOT AUTOMATED BY THIS NIGHTLY JOB)
- Build a bespoke animated, fully responsive and brand-faithful demo,
  not an interchangeable "AI card" page.
- Show the firm's actual service, an immediate customer journey, and
  at least one substantial change that can help more people contact
  or understand the business. Do not promise more sales without data.
- Preserve client-owned art without inventing logos/photos/reviews.
- Validate source facts before spending any AI credit.
- Run desktop (1440), tablet (768), mobile (390), small mobile (320)
  real browser QA; check layout overflow, interactions, performance,
  all real URLs, keyboard focus and reduced motion.
- Record **human** premium review evidence. The zero-credit
  `utils.pitch_quality.assess_pitch_packet` gate requires the exact
  version/hash, source benchmarks, QA screenshots, true functional
  links, truthful email claims and explicit premium-quality acceptance.
  QA scoring alone does not substitute for a designer reviewing the
  actual render or for the user's approval.

### D. Individualized sales email (not automated without a real demo)
- Send from only Kaurivo `hello.kaurivo@gmail.com`, never from a
  personal Gmail; introduce "Olen Kaarlo Kaurivolta".
- Acknowledge one verified site detail, name a business-specific benefit,
  show the actual beautiful screenshot with one functional demo link,
  and explicitly offer to build the full website.
- If nobody's name is known, start "Hei," and name the company next.
- Refer to prior work only if genuinely approved and demonstrable; call
  concept demos concept demos, never paid client projects.
- Compliance: check the specific recipient/address, lawful marketing
  basis, suppression requests, opt-out and sending identity.
  See Finlex 917/2014 sections 200–203.

### E. Owner approval and final send (no background emailing)
- Owner reviews the identity, confirmed business need, visuals, real demo
  link, individual message, address, opt-out and exact sending account.
- Approve each recipient and message. Only then use the connected Kaurivo
  Gmail account for an actual send. Never send to all found leads.
- Stop after an objection, bounce or inaccurate website/no-site report.

## Future expansion and budget safeguards

The current live Builder pipeline uses explicitly selected AI models and
potentially paid research. Its existing runner requires deliberate paid-API
approval; it is NOT called from this nightly schedule. The repository's
OpenRouter/Tavily quotas and counters are not guaranteed to persist across
ephemeral GitHub runners. Do not add paid AI to the unattended night job
without a durable shared ledger, provider-side hard spending caps, per-demo
limits, QA failure stop, and explicit user authorization.

If building a fully unattended premium-demo generator later, start with
one manually inspected approved example at a time. Require the same
strong quality gate and never use generic templates as finished demos.
More leads should NOT reduce quality per prospect.

## User promise vs current truth

**Implemented now:** nightly limited discovery pilot, zero paid AI usage,
candidate review artifacts, dedupe cache, quality gate code, no-send safety.

**Not implemented:** independently validated nightly business research,
autonomous premium-quality demo creation, visual QA agent selecting its
own revisions and reliably passing human standards, individual Gmail
drafts for every lead, or automatic Gmail delivery.

Do not claim that clients will receive finished sites overnight until
those steps truly exist and pass end-to-end evidence.
