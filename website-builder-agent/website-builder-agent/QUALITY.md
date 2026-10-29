# Builder quality foundation

The pipeline discovers redesign candidates, researches their real business, builds
an independent HTML website, and evaluates the rendered result before human approval.
This change does not establish parity with any particular frontier model.

## Discovery

Scout now uses the requested industry instead of always querying hairdressers.
Supported OSM categories: hairdressers, beauty salons, restaurants, cafes, car repair,
dentists, fitness centres, hotels, electricians and plumbers (see scout.py for Finnish
CLI names). Missing/unsupported search inputs fail before API calls. It evaluates at
most min(3 × requested count, 30) new candidates, ranks eligible candidates, and returns
up to the requested count. This can increase Scout AI calls relative to the old code.
Resource-manager limits still apply. Dry-run uses no AI/Tavily and saves no candidates.

Eligibility requires successful technical analysis, desktop/mobile screenshots,
redesign_recommended=true, opportunity >=6/10 and confidence >=0.7. Failure is unknown,
not a poor-site finding. URLs are canonicalized; social-only profiles are excluded;
previous work is preserved. These scores are model judgments, not validated sales
conversion estimates. OSM remains the only discovery source: coverage and real
identity/location matching still need representative live validation.

## Models and costs

Set explicit provider model IDs with BUILDER_MODEL and QA_MODEL; both must be fixed
non-free models. QA must support images; structured output support is also required.
SCOUT_MODEL and RESEARCH_MODEL can be set separately; otherwise OPENROUTER_MODEL
applies. No model ID is invented or hardcoded here. A fixed model selection is not
itself a quality guarantee. Required credentials: OPENROUTER_API_KEY, TAVILY_API_KEY.
The full pipeline checks model/credential configuration before discovery.

BUILDER_MAX_TOKENS defaults to 16000; AI_MAX_OUTPUT_TOKENS caps retry output at 24000.
Truncated nonempty outputs are rejected. Each retry still reserves a request against
the existing resource manager. This limits requests/tokens, not actual euro spend.
Set provider-side spend limits before running a paid model.

Example after setting the four model environment variables and credentials:

    python main.py pipeline --count 1 --industry ravintola --location Tampere

Optional `--max-revisions 1` enables one repair followed by fresh QA (default 0,
maximum 3). No auto-publish, automatic approval, or customer contact is performed.
Revisions receive actual rendered screenshots plus actionable QA findings. Initial
builds receive actual reference images plus existing-site screenshots where available.

## Build and QA

Research's design pass cannot replace the extracted business facts. Both historical
contact schemas are normalized. Source text and URL are retained, but extracted
claims still require independent factual review: storing a source is not proof of
every claim. Design briefs specify business tasks, section purpose/fact dependencies,
visual concept, typography, spacing, interactions and mobile behavior.

Static QA rejects broken anchors, fake forms, missing structure, invalid dependencies
and unverified mailto/tel links during generation. Browser QA renders 1440, 768, 390
and 320 px views with network blocked, records screenshots, checks overflow, broken
images, runtime errors, small controls and disclosure keyboard behavior. It does not
exhaustively prove every interaction, contrast ratio or keyboard path.

Visual QA receives all four rendered screenshots in the same request as the content
review. Every score dimension must be >=85/100, with strict Boolean/content checks
and no blockers. These are internal acceptance scores, not an external benchmark.
Browser absence or failed visual review cannot pass. Approval must match the current
build version. Output stays a single self-contained HTML file; production backend
features (real forms, ecommerce, bookings) require separate implementation.

## Verification

    python -m unittest discover -s tests -v
    REQUIRE_BROWSER_TESTS=1 python -m unittest discover -s tests -v

Tests use mocked AI/discovery to avoid charges. The browser test renders real local
fixtures and deliberately broken variants. CI installs Chromium and requires that
test; local execution skips it only if Chromium is absent.

Before claiming commercial build quality, use a fixed-model benchmark across several
real industries, save before/after desktop/mobile images, check original source
facts and all key interactions, and obtain human review against a written rubric.
No live AI benchmark has been run as part of this initial foundation change.

## External coding-agent completions

When a trusted coding agent generates HTML outside the API client, import it through
`python main.py complete-build COMPANY --response /path/to/response.html --producer "Work agent"`.
This runs the same factual and static validation as an API build, records explicit
external-agent provenance, increments the build version and clears stale QA. It
does not claim autonomous API generation or visual-AI acceptance. Use this mode for
reviewable examples when API credentials are unavailable.

## Required industry comparison

Every new build, external completion and revision now requires three independent
same-industry operator domains with desktop AND mobile screenshots and specific observations,
applicable ideas and things to avoid. The research stage captures three
reference sites and gives their images/text to the existing final design-brief
request. Unavailable references do not become fabricated evidence. Existing
research without this evidence must be refreshed before generation.

QA receives generated-page images first and reference images afterward. Its
structured comparison must name the observed reference URLs, find the result
company-specific, and report no material remaining gaps before acceptance.
These are reasoned internal comparisons, not proof of industry leadership or
an objective model-quality ranking. Extra reference fetching/screenshots and
larger vision inputs add time and may increase token costs. Reference discovery now
uses two bounded search requests (five results each; eight unique domains inspected)
and one additional Research-model selection request. Model selection is source-backed,
not an objective proof of relevance. Fewer than three verified operators stops research.

Before build, a validated design_decisions plan must trace exact observations to
original target-specific adaptations, section IDs and visible acceptance checks.
It covers first view, service hierarchy, contact path and mobile and uses all three
references. Initial generation AND revision receive the actual six reference images
with an ordered URL/viewport manifest. Previously the builder only received target
screenshots, a material gap now covered by regression tests. QA sees both views of
every reference and must give evidence for every planned decision. Missing planned
section IDs or missing/failed decision checks prevent acceptance. Art direction,
imagery and motion join the scored dimensions. Static design may score well where
appropriate; animation quality is not proven by screenshots. Manual interaction and
reduced-motion review are still needed for demanding showcase builds.

The supplied visual target is an art-directed product showcase with bold typography,
a coherent palette and meaningful scroll choreography. Its visual ambition informs
the contract; its product, branding and claims are not copied to client businesses.
Single-file output still limits assets and advanced 3D; do not claim parity with a
showcase or autonomous commercial quality without a live fixed-model benchmark.


## Production-readiness gates (2026-10-29)

**Default is offline and no paid provider calls.** GitHub Actions workflow
`Website Builder Agent (controlled run)` now has an `offline` option, which
runs the real Playwright/Chromium fixture suite without OpenRouter/Tavily
credentials. The `live` option requires exact confirmation
`I AUTHORIZE PAID API CALLS`. Direct CLI pipelines require
`--confirm-live-run`. This is a consent guard, not a model-spend cap.
The live workflow uses conservative per-run request allowances; they are **not**
a monetary cap or a lifetime allowance because Actions runners are ephemeral.
Set hard provider-side spending limits before enabling live runs.

A successful live run never auto-approves a site, publishes a customer
website or sends outreach. The workflow archives the generated state, HTML,
screenshots and resource usage for 7 days even on QA failure. GitHub-hosted
filesystem changes are temporary; to retain results beyond artifact expiry,
download the workflow artifact and restore it to durable private storage.
Do not upload confidential customer information to public repositories.

### Approval / publication integrity

QA stores the SHA-256 of the checked HTML. Manual `approve` records the
current build version and file digest. Subsequent rebuilds/revisions invalidate
QA, approval, outreach and stale demo status. `publish` requires fresh QA
and explicit approval; it refuses stale/mutated files and unexpected paths.
Publishing to `docs/demos` still requires a manual Git commit to deploy.
This is a public **demo** mechanism, not automated commercial domain hosting.

### Evidence required before claiming autonomous production quality

Run independently authorized live tests for **at least three different
industries** on real, permission-respecting business sites. Each must have:
- verified company facts and three independent same-industry references with
  source-backed quotes and actual desktop/mobile screenshots;
- traceable design decisions and an actual API-generated (not externally
  authored or fixture) site;
- passing static, browser (four viewports) and comparative visual/content QA;
- an unchanged checked HTML file and explicit human approval of that version;
- human review of actual copy, facts, imagery rights, accessibility,
  interactions and business-specific needs.

`python main.py readiness --min-industries 3` checks available local evidence
without paying for API calls. It fails unless three independent sectors have
complete evidence. This is a *metadata audit*, not cryptographic provider
attestation; screenshots, models and customer facts still need human verification.
It does **not** validate real backend forms, payment processing, web accessibility
in full, GDPR compliance, customer domain hosting, sales conversion, or model
pricing.

No actual paid multi-industry benchmark has been executed as part of this
change, so **production ready is not yet proven**. The fixture tests exercise
orchestration and browser gates, not independent frontier model creative quality.
Outreach and Kaurivo's own website remain deliberately outside this phase.


## Prospect discovery: businesses without listed websites and financial screening

The Scout now supports two tracks: **existing websites needing improvement** and
**companies without a website listed in OpenStreetMap**. OSM omitting a website
is not proof of no website. The second track is saved in
`verification_pending` without screenshots or paid AI; it must never be
misrepresented as a confirmed no-site company or sent automatically to outreach.

Use a zero-AI **persistent first-pass discovery**:

    python main.py scout --count 10 --industry ravintola --location Tampere --discovery-only

This uses OpenStreetMap's publicly accessible Overpass API only. It does not
use OpenRouter, Tavily or the browser. `--dry-run` still makes no saves.
A later manual website check may reveal that OSM simply missed a real website.
The standard Scout route still supports existing-site visual redesign discovery.

### Official identity and financial evidence

The optional `python main.py verify-registry COMPANY` performs an explicit
free PRH/YTJ open-data lookup: first by known business ID, otherwise by exact
company name and saved city. If PRH identity is ambiguous or the names conflict,
verification stops pending human checking. The official API does not provide
all company types (including sole proprietors), nor does its basic company
record establish revenue, profit, cash, business budget or ability to pay.
For a strict Y-tunnus use `--business-id 0116297-6`; name mismatches require
deliberate `--confirm-name-mismatch` after real-world inspection.

Financial statement and reviewed reputation enrichment is **source-driven**:
create an evidence JSON yourself, using figures from legally accessible
verified source material, then run:

    python main.py screen-lead COMPANY --evidence evidence.json --project-price 1500

Example shape (illustrative data, NOT a factual business record):

    {
      "reputation": {"rating": 4.8, "review_count": 60,
        "source_url": "https://example.org/verified-provider-page",
        "checked_at": "2026-10-29", "verified_by_human": true},
      "site_verification": {"confirmed_absent": true,
        "source_url": "https://example.org/verified-directory-page",
        "verified_by_human": true},
      "financials": {"business_id": "0116297-6",
        "business_id_verified": true, "registry_source_url": "https://avoindata.prh.fi/opendata-ytj-api/v3/companies?businessId=0116297-6",
        "legal_status": "active", "insolvency_proceeding": false,
        "revenue_eur": 245000, "operating_profit_eur": 17000,
        "financial_year": 2025,
        "financial_source_url": "https://example.org/verified-statement",
        "financial_verified_by_human": true}
    }

The example URLs/numbers above are **fictitious schema examples**.
Never mark evidence verified without checking the source, legal entity,
location, date and data-use rights. Strong reviews default to >=4.5/5 with
>=20 ratings checked within 180 days. A commercial "promising" budget signal
requires a positive reported operating profit, suitable sales scale,
registered active status, verified business ID and a recent source-backed
financial statement. It is **not** a solvency test or a claim of likely
purchase. Missing data is `needs_review` (not "broke") and stops expensive
build/outreach. Registry-based bankruptcy, liquidation, restructuring or
termination is exclusionary for prospecting.

The default full paid pipeline now prevents spending on unresolved lead
finances, including `--company COMPANY` runs. Fully automatic finance
statements are NOT implemented: PRH's free iXBRL data covers only ~5% of
reports. Google Places ratings/website fields require billing, and
Google's API has storage/attribution restrictions; no unauthorized Google
scraping or fee-incurring integration is enabled here. Review values remain
manually verified in this phase. Accordingly **do not claim the system
automatically discovers only highly reviewed financially qualified firms
yet**.

This phase does not change the no-send outreach policy. Human approval
is still required for website completion and customer contact.
PRH open data attribution: Patentti- ja rekisterihallitus (PRH),
CC BY 4.0, https://avoindata.prh.fi/fi/info/swagger-ui.
