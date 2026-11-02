# Kaurivo: first-pass creative quality and source-led multi-page Builder

Date: 2026-11-02. Built into generic Research → Builder → QA and the
zero-API external agent completion path. No previous client demos were altered
or used as repeated benchmark exercises.

## Why this change exists
Older demos repeatedly used text-left/photo-right, enormous split slogans,
arched/circular decorative imagery, generic luxury colors, three-card
service layouts and AI-sounding antithesis copy. Worse, important existing
partner logos, old products, languages and source content disappeared.
Passing a browser smoke test did NOT establish either creativity or content parity.

## Four non-negotiable stages

### 1. Research: three grounded directions (before any Builder request)
Research produces exactly three creative_directions objects and one
creative_selection. Each direction specifies actual customer/business rationale,
source anchor, hero/first-view composition, information architecture, navigation,
image plan, typography, original brand continuity, deliberate non-goals, mobile
behavior. They MUST differ materially in at least 3 of 4 main structural
axes. A different palette and hero headline is NOT a new proposal.
Selected idea requires comparative rationale and rejected alternative IDs.

Source inventory and 3 same-sector benchmark screenshots remain mandatory
when the business has a site. The choices are evaluated by deterministic
validators; the original Research model is NOT independently scoring itself.
The separate QA model must critically evaluate the actual built site later.

### 2. Information architecture: true content-led routes
Research outputs site_architecture.pages with a safe relative HTML path,
business purpose, user task and planned section IDs. It maps every original
source page and its significant headings to an actual new route/section.
A site with 3+ researched old pages OR >=650 captured source words MUST
have >=2 real new pages; often more are required. Up to 14 routes supported
by the bounded JSON output. Original service/product pages are not allowed
to vanish or be replaced by links to the hard-to-read old site.

Builder outputs ONE JSON object containing ALL planned complete HTML documents.
Each route has own head, title, viewport, navigation, main, footer and H1.
Deep routes reference local assets using correct relative paths.
No user-facing fake form or unknown customer claims. External coding-agent
completion and revisions are subject to exactly the same rules.

### 3. Objective gates: all routes, not only homepage
- Every route exists, has planned anchors and links to real destinations;
  homepage navigation reaches all new pages.
- All routes independently pass static HTML, safe media, company fact checks,
  source parity and existing partner/brand logo preservation.
- Whole-site editorial language checks and old-site content comparisons run
  on all documents, including services and subpages.
- Compare against prior **different** company demo compositions using
  tag/content structures rather than class or palette names.
  Repeated high-similarity structural clones or repeated generic
  antithesis copy block approval; weak style conventions alone generate
  warnings rather than arbitrary bans.
- Actual browser renders each route at 320/390/768/1440px; the independent
  reviewer sees homepage and service page evidence, original company brand,
  and three same-sector reference screenshots. A designer may choose no
  unnecessary animation or 3D when that suits the specific client.
- A dated, exact whole-bundle cryptographic digest covers all HTML routes and
  packaged local images, not only index.html. Later edits to any route or
  asset revoke the matching QA/approval. The publisher copies ALL approved
  pages and assets or refuses release.

### 4. Subjective quality: evidenced AI-genericity risk
The independent review must now include ai_style_review with:
- risk_score (0..10; target <=2; NOT an AI authorship detector)
- at least two specific visual/editorial observations
- how original business identity is communicated
- at least two earlier site patterns explicitly considered
- no unresolved material genericity concern.

Normal visually impressive 95/100 model ratings alone are insufficient.
Exact-build independent >=9.5/10, correct source coverage, true client
content, actual media rights and editable CMS are additional release criteria.
No provider rating is treated as verified unless its real evidence exists.

## Honest measurement on *new* companies
`pipeline --benchmark-mode` already refuses repeating company names/domains
and prevents repeated same-company revision attempts. After the FIRST QA,
the local ignored registry records the first-pass:
- all-page route count and source page count;
- missing old content / verified company facts;
- browser issues and original design clone risks;
- internal AI-genericity risk evidence;
- independent visual score = **NOT VERIFIED** until genuinely provided
  with exact-version evidence, separate from model self-ratings.

Never overwrite the original first-pass record after a revised build.
Compare 10–20 new, previously unseen industries/brands before claiming
reliable generalization. Keep customer editing and paid outreach separate.

## Operational caveats and costs
The preflight and CI tests use ZERO Tavily/LLM credits. Generating three
creative directions within Research JSON increases response complexity and
may require a larger single Research reply; the Builder's bounded max output
currently restricts the number of fully rendered routes it can return in
one request. If data overflows a model's output limit, fail safely rather
than truncate the site or invent an approved quality score.

The current source crawler only fetches a bounded number of URLs and may
miss JS-driven catalogs or multilingual routes. Such evidence is pending;
a human must verify unusual catalogs. Source photos/sponsor logos are not
automatically legally reusable simply because they are visible on the
original site. A real client CMS is NOT created by this HTML generator;
delivery needs separate verified editable platform integration.

The historical demo and per-company first-pass registry lives in local
`output/_kaurivo_unseen_trials.json`. Multi-run cloud workers still need
persistent data storage before cloud-wide uniqueness can be promised.

## Offline regression tests
Run on a locally prepared environment:

python -m unittest tests.test_creative_multipage_originality tests.test_site_bundle_integrity tests.test_blind_trials -v

Github CI: `kaurivo-creative-multipage-qa.yml`. Real browser source
contrast checks remain in `kaurivo-source-fidelity-blind-qa.yml`.
