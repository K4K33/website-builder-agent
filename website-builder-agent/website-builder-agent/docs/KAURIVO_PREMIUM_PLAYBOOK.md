# Kaurivo — premium customer delivery standard (zero new subscriptions)

**Status:** engineering checks and procedures; NOT evidence that a particular
customer website, a live CMS or real paid delivery is operational. Applies to
website-builder-agent and the Kaurivo website. Implemented in
`utils/kaurivo_premium_site.py` and `utils/kaurivo_premium_sales.py`.
Existing human gates remain mandatory: `utils/pitch_quality.py`,
`utils/client_handover.py`, `utils/marketing_compliance.py`.

## 1. Discovery to customer, no unapproved contact

1. The night job may acquire public business candidates into the *private*
   Kaurivo CRM. A missing registry website URL is **not** proof that no
   website exists, and a registry entry is not proof of an active business.
2. A person verifies the actual business, relevant existing site and real
   business facts. Only create a lead profile after those checks.
3. For a redesign, collect **three independent, genuinely same-industry**
   live design references with observable strengths/weaknesses and permission-
   safe screenshots. Never copy competitors' assets or claims.
4. Record three concrete, human-verified observations from the target site in
   `research.verified_improvements` with `before`, `after_proposal`,
   `source_url` and `human_verified: true`. An improvement proposal is
   explicitly **not** proof of better SEO, leads or revenue. If a company has
   no verifiable existing site, first verify the business's web presence with
   multiple independent sources; do not invent an "old site" comparison.
5. `python main.py demo-evidence COMPANY` produces an audit/brief, not
   a personalized email or sent outreach. Ensure the existing premium
   `python main.py premium-pitch-check COMPANY` gate passes and inspect
   the actual 320/390/768/1440 browser screenshots for quality and errors.
6. A human reviews company-specific offer, client recipient and business-
   marketing legal basis, including a simple opt-out mechanism and suppression
   register. Drafting or selecting never authorizes sending. Send individually
   only after explicit approval. No invented testimonials or market outcomes.
7. Keep weekend research and drafts in the queue; release on a suitable
   weekday *after* the same legal and human review. No automatic bulk sends.

## 2. Design direction (brand first, never template first)

- Start from the real brand, assets owned/licensed by the customer and locked
  phrases. Existing sites must receive a clearly substantial redesign of
  navigation, typography, section hierarchy and mobile experience, while
  preserving client identity unless permission says otherwise.
- Use references for **structure and interaction quality**, not their names,
  copy, images or branding. Compare the same sector's strongest sites,
  document which choices to adapt and which to avoid.
- Each section answers a customer question. Make the offer, location,
  verified services and next appropriate step clear in the first view.
- Prioritize native scroll, accessible interaction, responsive typography,
  `transform`/`opacity` animation only when useful, and reduced-motion
  alternatives. Avoid generic AI-looking filler, fake awards, reviews,
  statistics and unnecessary continuous 3D loops.
- Responsive visual inspection on mobile, tablet and desktop, both normal and
  reduced-motion. Test real taps, inputs, copy and link destinations.

## 3. Static preflight and performance / accessibility checks

```bash
cd website-builder-agent/website-builder-agent
python main.py premium-audit --html docs/kaurivo/index.html --root docs/kaurivo
python main.py premium-audit --html path/to/client/index.html --root path/to/client --production
python -m unittest tests.test_kaurivo_premium_standard -v
```

The static audit covers:
- HTML5, lang, title, description, viewport, exactly one main and H1,
- duplicate IDs, broken fragment links, missing local assets, path escape,
- basic labels/alt text, and possible responsiveness/reduced-motion omissions,
- noindex **blocking only** in `--production` mode.

A static pass is **not** Lighthouse, measured Core Web Vitals,
WCAG conformance, visual QA, real contact form delivery, cookie consent,
security, CMS operation or browser-based validation. They require separate
documented tests. Targets: field p75 LCP <= 2.5 s, INP <= 200 ms,
CLS <= 0.1, and WCAG 2.2 AA intent. Treat mobile Lighthouse 90+ as a
stretch target only when actually measured on a reproducible URL/device.
Do not publish invented scores. Fix failures before a production release.

## 4. Sales promise and agreement

Before paid work, define exact pages, deliverables, price and VAT treatment,
deposit/final milestone, revisions, change orders, client brand/file rights,
domain/hosting renewal responsibility, actual CMS and editing scope,
privacy/forms/cookie responsibility, acceptance, support and delivery.
Save a local **private** JSON record, for example `project-terms.json`:
```json
{
  "scope_version": "offer-2026-001",
  "signed_or_explicit_written_acceptance": false,
  "fixed_scope_and_page_count": false,
  "total_price_and_vat_treatment": false,
  "deposit_and_final_payment_terms": false,
  "revision_rounds_and_change_requests": false,
  "approved_brand_and_content_rights": false,
  "hosting_domain_and_renewal_owner": false,
  "cms_platform_and_editing_scope": false,
  "privacy_cookie_and_form_responsibilities": false,
  "delivery_support_and_acceptance_terms": false
}
```
Change a flag to true **only** after independently checking and retaining
the actual agreed document privately. Then:
`python main.py project-terms --file project-terms.json`.
This is a checklist, not an electronic signature or legally binding contract.
Do not commit customer agreements, identifiers, private URLs or invoices.

First-sale finance: use a properly established Y-tunnus or qualified
invoicing intermediary; a project is **not** a won sale until accepted and
its financial status is verified. Confirm current tax/registration rules with
the authorities. A milestone such as 40% deposit + 60% delivery is an
example; always agree the real split in writing.

## 5. Actual client editing and ownership

A static public HTML page, GitHub Pages site, mock editor or screenshot is
**not** a customer's live CMS. Do not claim the client can edit until an
actual client-owned instance has passed independent testing.

Choose hosting/platform with the **client**. Example paths:
- WordPress (client's own hosting and verified editor login).
- Decap CMS with carefully scoped backend authentication, Git access and a
  secure publishing workflow; **never** put GitHub tokens in client JS.
- Another established CMS that the customer approves and can own.

Implement server-side authentication, scoped roles, backups, restricted media
upload, content preview and rollback, and a non-admin customer editor.
Test real customer login; edit text, image, service, contact details and
hours/prices where relevant; publish; verify smartphone layout; restore a
backup; then deliver a short client guide. Provide site ownership and
credentials via a secure approved channel, never in a git repository.

`python main.py handover-check COMPANY` checks the existing evidence
contract. `python main.py delivery-preflight COMPANY --html SITE/index.html
--root SITE` additionally checks the production HTML; any warning requires
recorded human resolution. Neither makes a demo into a CMS.

## 6. Measurement without intrusive tracking

Existing admin CRM includes verified sales KPIs and its own authenticated
dashboard. For local old-style company state:
`python main.py sales-funnel` summarizes discovery, owner selection,
approved demos, recorded contacts, proposals, verified wins and deliveries.
It does not send data to Google, mix OAVIR accounts or add visitor trackers.
Do not call an unsent draft a contact or proposal a won sale.

For actual client site reporting, first obtain permission and configure
first-party or consent-respecting analytics, GA4/Search Console only if
required and lawfully configured. Define lead conversion events precisely
(form submit **confirmed at server**, tapped phone link as intent, booking
confirmed by booking provider). Never promise rankings or revenue.
Report baselines and dates and use 'no data' when unavailable.

## 7. Budget and release conditions

Until first paying customer: no new AI subscription, external paid API,
marketing bulk-send service or custom portal. Use offline fixtures, mocks,
existing CI, human review and free hosting within limits.

Before taking a new project into production:
- real scope and legal readiness,
- signed/accepted terms,
- real visual and technical proof,
- working customer-owned editable CMS,
- private, verified customer acceptance,
- correct invoices/tax treatment,
- explicit release decision.

This checklist does **not** activate a paid service, start an automatic
send, modify a client domain, deploy an Edge Function or prove a live
end-to-end sale.
