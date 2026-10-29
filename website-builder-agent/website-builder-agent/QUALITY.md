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
builds receive existing-site screenshots where available.

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
