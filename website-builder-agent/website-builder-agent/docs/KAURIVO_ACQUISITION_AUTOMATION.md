# Kaurivo — zero-AI-credit automated lead acquisition

## What is deployed

This automation is exclusively for Kaurivo, not OAVIR. It reuses the
existing two scheduled workflows:

- 03:17 Europe/Helsinki: small, one-request OpenStreetMap pilot
  (`.github/workflows/kaurivo-nightly.yml`).
- 04:13 Europe/Helsinki: official nationwide PRH/YTJ bulk-data daily
  download, one bounded ZIP GET followed by local streaming and
  deduplication (`.github/workflows/kaurivo-national-prh.yml`).

The nationwide job scans company-register entries and creates:
`candidates.json` (up to 5,000 unverified registry candidates),
`shortlist.md` (50 selected leads), `crm-shortlist.json`
(an admin-safe 50-company import packet), and
`research-briefs.md` (per-company research/QA checklist).

These numbers are maximums; failed downloads, incomplete registry data
and duplicates can result in fewer real candidates. Results are not
claims that an enterprise is operating, can afford a website or has
no existing website.

The job then requests a short-lived GitHub Actions **OIDC token** with
audience `kaurivo-prh-ingest-xhsfbcwpwbgdbatrcyuk`.
The separate Kaurivo Supabase Edge Function
`kaurivo-prh-ingest` verifies its signature with GitHub's fixed JWKS
and strictly checks the exact GitHub repository and immutable numeric
repository/owner IDs, main branch, national-PRH workflow file and
schedule/explicit-dispatch event. Unauthenticated, other-repository,
wrong-branch or incorrect-audience calls are rejected.

After verifying the packet fields, it inserts up to 50 source-only
public business records into Kaurivo's RLS-protected
`public.kaurivo_crm_prospects` table with
`review_status='unverified'`. The business ID is unique; repeat runs
never overwrite manual research. No client data, personal emails or
website observations from this feed are published in GitHub source.

The use of GitHub OIDC means **no Supabase secret is installed in
GitHub Actions**. The Kaurivo service-role credential stays
server-side inside the Supabase Edge Function only. GitHub's
`id-token:write` permission by itself does not enable GitHub
repository writes.

## Admin management

<https://k4k33.github.io/website-builder-agent/kaurivo/admin/>

Choose `hello.kaurivo@gmail.com` or `kaarlo.kaukko1@gmail.com`.
Both email addresses need their own confirmed Supabase Auth session.
Signing in to ChatGPT or Gmail alone does not sign into the Kaurivo
admin application.

The **Liidijono** section lists source-attributed candidates.
A reviewer must verify:
- actual business status, legal identity and solvency signals
- whether a website genuinely exists (PRH's omission is not proof)
- current visual brand, actual services and original image licensing
- three genuine same-sector design benchmarks
- a factually correct site improvement and premium-quality UI/UX
- desktop, tablet, mobile and reduced-motion QA, plus customer CMS
- recipient-specific commercial-email legality and explicit owner
  approval before sending

Only after validation should a lead become an actual CRM client record.
The public PRH feed supplies **no verified contact email**.
The import deliberately cannot turn a PRH entry into a sale or send a
message.

## Fallback if the scheduled OIDC sync fails

GitHub Actions → `Kaurivo national business discovery (PRH bulk)` →
most recent successful run → `kaurivo-national-leads-...` artifact →
`crm-shortlist.json`. In Kaurivo admin, open **Liidijono** and choose
**Tuo yön 50 yritystä**, then select this JSON file.
The importer accepts only recent official `pilot-live` packets with
no-sales/no-demo state; already known business IDs are not overwritten.

Note: GitHub Actions schedules are best effort and can be delayed, so
neither the exact minute nor a fully successful daily source download
can be guaranteed. Inspect the workflow summary to confirm actual
results. The first new OIDC sync needs a real scheduled workflow run
to prove end-to-end delivery; local source and security tests alone
are not that proof.

## Premium demo and contact release gates

The nightly job generates **research briefs**, not finished premium
websites. An unreviewed page or generic automatic email would harm
Kaurivo's quality positioning. Actual demo work is a separate,
individually researched stage with browser screenshot QA and explicit
visual review before outreach.

The agent's marketing-compliance gate must also be applied to every
contact. Finnish B2B rules distinguish a generic organization mailbox
from a natural person/direct work address. Keep a private suppression
list, observe objections and do not send unapproved marketing.

No paid AI calls, no customer messages, no claimed sales and no
external enrichment API quotas are consumed by this nightly pipeline.
