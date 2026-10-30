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

A separately authorized `pipeline --benchmark-mode --confirm-live-run` is an
**internal model-quality experiment**, so it can use an unscreened design
candidate without treating that business as commercially suitable. It still
requires the normal real browsing/AI usage and safety checks. No outreach,
financial qualification or customer deployment is implied. The manual GitHub
workflow uses benchmark mode only for its explicitly approved live test.


## Free PRH financial-period enrichment and no-website research (2026-10-29)

New zero-AI-credit CLI flow (real official PRH HTTP requests require explicit
consent; bounded to ten prospects per invocation):

    python main.py scout --count 10 --industry ravintola --location Tampere --discovery-only
    python main.py enrich-free --max-companies 5 --confirm-public-lookups
    python main.py leads --project-price 1500

`enrich-free --company SLUG --confirm-public-lookups` targets one existing
lead. It looks up the PRH/YTJ business identity using a valid business ID or
an exact company name and city. Ambiguous identity never becomes a match.
It then checks the PRH XBRL API `/financials?businessId=...` for actual
reported iXBRL periods. This is a **period availability lookup** only, not
automated revenue/operating profit analysis. The normalized amounts are
not present in the period listing. The taxonomies in XML reports must be
verified before interpreting an individual report's turnover or profit.
No amount is invented. Roughly 5% of annual statements are in this open
iXBRL feed; others remain `needs_review`, not a negative verdict.
An official PRH company website is stored as a candidate; if it conflicts
with an earlier claim of no website, that claim is invalidated and must
be rechecked. PRH attribution: Patentti- ja rekisterihallitus (PRH),
Creative Commons BY 4.0, https://avoindata.prh.fi/ .

The new `leads` command generates a deterministic ranking of saved records
according to source-reviewed reputation, financial status, and website
verification. This is a worklist for a person; it never sends communications.

### Verified business without a website

When a candidate's absent website has been **independently confirmed**
through `screen-lead`, its real business identity, industry, services
and contact details may be assembled from documented third-party sources.
Example (schema illustration, **not** facts about a real firm):

    {
      "verified_by_human": true,
      "verified_at": "2026-10-29",
      "company_facts": {
        "name": "Example Oy",
        "industry": "restaurant",
        "services": ["Lunch service"],
        "location": "Tampere"
      },
      "fact_sources": {
        "name": ["https://example.org/official-registry"],
        "industry": ["https://example.org/official-registry"],
        "services": ["https://example.org/verified-menu"]
      }
    }

Save as `verified-profile.json` with true inspected references, then:

    python main.py attach-profile SLUG --profile verified-profile.json
    python main.py research SLUG --confirm-paid-apis

The profile must be dated within 180 days, manually verified, have
source URLs and validated services, and belong to the correct company.
For a business without a website, the Research agent now **does not
fetch or invent a target website**. Instead it uses the approved profile
as immutable target facts, observes three genuine independent same-industry
websites, and creates the same audited design plan used for redesigns.
The subsequent Builder/QA process is unchanged.

A paid commercial `pipeline --company SLUG --confirm-live-run` checks
live reputation and financial evidence again before using any credits.
No-site commercial work requires strong source-reviewed ratings, a
verified no-site profile, and promising financial suitability evidence.
An internal `--benchmark-mode` experiment is separately authorized;
it is not a sales lead or customer acceptance.

Direct `scout` (except `--discovery-only` / `--dry-run`),
`research`, `build`, `revise`, `qa` and `outreach` now require
`--confirm-paid-apis`. This protects accidental manual credit usage.
`pipeline` continues to use the explicit `--confirm-live-run`.
These are consent gates, **not monetary spending caps**: keep
provider-side hard limits configured.

### Remaining blockers

- Review ratings/counts still need a permitted, traceable manual or
  licensed provider source; Google Maps scraping is not enabled.
- PRH XBRL values are not yet mapped from signed/dated reporting
  concepts. An iXBRL period does not imply a profitable company.
- No-site profile fact verification still requires human review.
- No live multi-sector autonomous builder benchmark or commercial
  publishing/invoicing review has been completed.


## PRH XBRL document inspection (2026-10-29, safe preview)

The official PRH open-data financial API describes:
- `GET /financials?businessId=...` returning reporting period metadata (JSON).
- `GET /financial?businessId=...&financialDate=YYYY-MM-DD` returning an XML financial statement.

Reference: https://avoindata.prh.fi/opendata-xbrl-api/v3/schema?lang=fi
Data source: Finnish Patent and Registration Office (PRH), CC BY 4.0.

To inspect **one** PRH digital statement after confirming legal company identity
and fetching the real reporting periods:

```bash
python main.py enrich-free --company COMPANY --confirm-public-lookups
python main.py inspect-financial COMPANY --confirm-public-lookups --limit 15
python main.py leads
```

The inspector makes **one explicit, bounded PRH HTTP request** only; it refuses
redirects, non-XML replies, documents over 2 MB, malformed XML, DTD/entity
constructs, invalid IDs, future dates and unverifiable reporting periods.
It saves just a bounded sample of original XML data facts, the official source
address and a SHA-256 digest for independent human verification.

**WARNING:** An XML concept like `fi_met:mi53` and a displayed figure are NOT
an automatically verified financial result. Correct identification requires
an exact taxonomy and financial reporting context, unit, scale, sign,
consolidation scope and relevant period. This feature deliberately records
`financial_figures_verified: false`, never writes `revenue_eur` or
`operating_profit_eur` and does not change the commercial budget gate.
Final financial qualifications must still use independently reviewed and
source-linked evidence. The iXBRL open dataset covers only a minority of
Finnish statements.

Review priorities now include `inspect_available_prh_statement`,
`review_xbrl_taxonomy_facts` and `verify_financial_budget`, helping the
operator focus on verified, highly regarded website-less businesses without
spending any model credits. The review sources still need lawful access;
Google Maps ratings scraping is *not* enabled because Place API content has
license, caching and billing restrictions.

The change has been validated using fully mocked HTTP and XML fixtures only.
It is not proof that all current PRH live responses use the same taxonomy,
nor proof of the autonomous site-builder production quality.


## Indicative purchasing-capacity prioritization, not solvency (2026-10-29)

Kaurivo no longer requires actual turnover and operating profit to consider a
business for a paid website build. It uses a transparent **0..100 internal lead
priority index** from independently verified signals, not purchase probability,
a credit rating or actual cash availability.

Default additive heuristic (caps at 100):
- +55: recent, source-verified turnover scale and *positive* operating profit
  compared with the project's estimated EUR price. This remains optional.
- +10: matched official company identity in PRH/YTJ.
- +10: independently documented active registry status.
- +25: human-verified recent high customer ratings (>=4.5 with >=20 reviews).
- +20: verified business operation at two or more locations.
- +15: independently verified staff count of five or more.

Registry identity, reputation and operational size are proxies only. All signals
require source links and, where relevant, human confirmation; no fabricated
reviews and no automated Google Maps scraping. An absent signal adds zero
**without meaning that the firm is poor**. Closed, insolvent or officially
terminated businesses remain excluded from commercial targeting. Any valid
score of at least 25 is eligible for *manual consideration*, not automatic
solicitation. Confidence reports `limited`, `moderate` or `higher`;
scores are NOT calibrated probabilities.

Businesses with no reliable financial statement can therefore proceed when
they have other verifiable indicators (e.g. established good reviews or a
proven operating footprint). Website-less firms still need verified website
absence, a sourced company profile and strong reviews. Those checks concern
factual accuracy and relevance, not exact solvency.

The `leads` command and local UI both display these heuristic indicators.
Commercial pipelines compute them again on each run, so stale saved scoring
cannot bypass a gate. If a particular business is worth testing despite
missing source evidence, the operator can explicitly authorize a single
known-company experiment:

    python main.py pipeline --company SLUG --allow-low-evidence-lead --confirm-live-run

This manual exception does NOT bypass official inactive/insolvency exclusions,
company identity/site verification, provider cost restrictions, QA, or human
approval. It is only usable for a named saved company. Standard discovery and
automated outreach draft creation still require indicative signals; customer
emails are never sent automatically. `screen-lead` also accepts optional
source-checked `operational_scale` evidence (location_count, employee_count,
source_url, checked_at, verified_by_human) for the index.

Do not present these numbers as the firm's assets, revenue, profit, available
spending, creditworthiness, or likelihood of purchasing. The thresholds are
initial operational heuristics that should eventually be evaluated against
consented, actual customer outcomes rather than asserted as predictive.


## Commercial search policy: NO WEBSITE FIRST + ACTIVE BUSINESS (2026-10-29)

**New user-approved priority order**:
1. A company **verified to be currently operating** and **verified to have no existing website**.
2. A company whose website field is **not listed** (needs manual/authorized verification), even if it has no ratings or public accounts.
3. An active company with an existing website that might benefit from redesign, as a secondary market.
4. Companies with unknown activity status stay in the research queue; registered ended/insolvent businesses are excluded.

Star ratings, multiple locations, five employees, revenue and reported profit are
**NOT mandatory**. A single active sole-location business is just as eligible.
There are **zero bonus points for multiple locations**. Good reviews and
financials remain optional supporting context, not lead selection gates.

To mark a business as active for commercial building or outreach, use
source-backed official company status, or evidence of recent trading activity
reviewed within 180 days:

```json
{
  "activity_evidence": {
    "active": true,
    "verified_by_human": true,
    "source_url": "https://example.org/source-of-recent-operation",
    "checked_at": "2026-10-29"
  }
}
```

This example URL is illustrative, not evidence for any real business.
Attach the reviewed JSON using:

```bash
python main.py screen-lead COMPANY --evidence verified-activity.json
python main.py leads
```

A missing activity field is **unknown**, not a false claim that the business is
closed. But expensive commercial builds and outreach drafts require verified
activity, which prevents spending credits on long-closed businesses. Controlled
internal mock/model-quality benchmarks can still run separately.

`scout --discovery-only` now puts missing-website *candidates* first, even for
count=1, without calling AI or browser. An omitted OSM website tag is **not
proof** the company has no site. Prior to commercial no-site work, independently
verify website absence and the company's real services/contact facts through
a source-backed, human-reviewed profile. Existing-site redesign is secondary.

The 0–100 indicative capacity index continues to describe a sales-worklist
heuristic, **not** actual ability to pay. Activity evidence contributes more
than stars; multiple locations never contribute. The list order is based first
on site-status and business activity, not the highest turnover or rating.
Customers are not contacted automatically.


## Visual clarity, sharp color & purposeful motion — project-wide baseline (2026-10-30)

This applies to **every future Kaurivo-built demo and agency website**, not
just the Kaurivo brand site. It comes from direct visual feedback on V1/V2/V3.

**Color, clarity and art direction**
- Aim for deliberate, sharp color separation, true high-contrast typography,
  clear boundaries, legible small text, precise graphical detail, and a
  visually confident premium finish. Avoid washed-out, hazy, grey-on-grey,
  muddy overlays or ornamental low-contrast elements that look blurry.
- The Kaurivo agency brand currently uses deep charcoal/black, clean
  off-white and muted metallic-silver/steel accents. Avoid the electric-blue
  V3 palette and distracting pointer-following hero movement. **Do not impose
  Kaurivo's specific colors on client websites.** Match
  each client's approved identity and evaluate color fidelity against
  three high-quality sites in its actual industry.
- Text contrast must meet WCAG AA when possible: 4.5:1 for normal text
  and 3:1 for large text; maintain strong non-text affordance contrast.
- At design QA, inspect a *real render* at 1440, 768, 390 and 320px,
  including sharpness, line breaks, legibility and image asset resolution.
  Do not report "premium" solely on the basis of generated HTML or scores.

**Motion is mandatory when it adds demonstrable value, not decorative noise**
- User explicitly wants high-quality motion. Never interpret a complaint
  about lag as permission to remove all animations. Instead isolate the
  expensive mechanism, replace with purposeful, performant interactions,
  and retain high-quality entrance, hover, scroll-reveal, and contextually
  meaningful interactive moments.
- Prefer \`transform\` and \`opacity\` transitions, bounded intersection
  observers, a small number of simultaneously animated elements, limited
  pointer updates and native semantic controls. Avoid per-frame changes
  to layout-affecting style, unbounded canvas/WebGL rendering and extremely
  long sticky scroll-locked 3D assembly sequences.
- Make animation intentionally choreographed, with readable pace and no
  unexpected jumping; users should control interactive visual stories
  using buttons/tabs if scroll scrubbing would be clumsy.
- Respect \`prefers-reduced-motion\`, touch devices, keyboard navigation,
  visibility state and real-device performance. Target a smooth experience
  rather than claim "60fps" without measurements.

**Page architecture / functional usability**
- When content grows, do not put every major topic into one giant
  scrolling landing page. Split into meaningful, linked pages (e.g.,
  services, process, FAQ, contact) while keeping primary navigation clear.
- Accordions are fine *inside a dedicated FAQ page*; don't force the
  user to scroll through a full FAQ and contact form on the landing page.
- Make each nav item navigate to a real URL; test deep links, backwards
  navigation, responsive navigation and keyboard interactions.
- New site or redesign? New sites may substantially reinterpret layout;
  redesigns should remain genuinely recognisable to existing customers.
- All client projects must have an explicit handover/editability plan
  (WordPress or a suitable CMS/editor agreed per project).

**Release proof**
- Use free/offline browser testing and screen recordings where possible.
  Log motion/render issues, compare before/after at key viewports, verify
  actual links/FAQ/forms, and obtain human visual approval. Do not infer
  that no layout overflow means the user will like the art direction.
- Motion-heavy visuals are a craft demonstration, not an excuse to
  compromise readability, conversion flows, accessibility or performance.
