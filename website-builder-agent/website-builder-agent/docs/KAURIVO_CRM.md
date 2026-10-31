# Kaurivo — private studio CRM

**Status:** Free-tier implementation in Kaurivo's separate Supabase project
`xhsfbcwpwbgdbatrcyuk`, organization `ocglllovgdlilgcpdmon`.
No OAVIR resources are used.

## Open the UI

<https://k4k33.github.io/website-builder-agent/kaurivo/admin/>

Only the exact, confirmed Supabase Auth email `hello.kaurivo@gmail.com`
is an administrator. The database checks authenticated user ID against
`auth.users` and its email confirmation timestamp. The UI and its
public publishable key **do not provide authorization**: row-level
security on every CRM table is the enforcement layer.
The page is marked noindex but the HTML itself is public.

**One-time Supabase Auth setup:** In the Kaurivo project, go to
Authentication → URL Configuration and add exactly:

`https://k4k33.github.io/website-builder-agent/kaurivo/admin/`

to Redirect URLs. Set the Site URL to the Kaurivo website, if the default
is still localhost. Magic-link email authentication needs to be enabled
for Kaurivo; the initial request can create the verified admin Auth user
at that email. No customer needs a login for the feedback form.

## Workflow

1. **Yritykset** — add an active prospect or client, their verified
   business email, website and contact notes. Keep private notes private.
2. **Projektit** — create a company-specific web design project, its
   demo URL, must-have requirements, CMS/WordPress editability and status.
3. **Kaupat** — create a proposal, then verify a genuinely concluded
   sale with a clear evidence note. Clicking Verify marks it won,
   source_verified and timestamps the confirmed purchase.
4. PostgreSQL automatically creates exactly one feedback queue row per
   verified sale, due one Finland-local calendar day after confirmation.
   One queue row per sale is enforced by a unique index.
5. Once due, **Palautepyynnöt** → Valmistele palautekutsu generates
   a secure random 32-byte one-time token *in the authenticated browser*.
   The browser sends SHA-256(token) to a service-free SQL RPC.
   An atomic database transaction locks the queue row, ensures the
   sale is truly verified and due, inserts the invitation and marks
   the queue as prepared. This prevents duplicate invitations.
6. Copy the one-time-only message and send it from the verified Kaurivo
   Gmail account to the specified customer. The UI NEVER sends email
   automatically or claims to have sent anything.
7. Click **Merkitse lähetetyksi** only after actually sending.
   The customer submits a 1–5 rating and written comment using
   Kaurivo's original interactive feedback form; it is saved into
   Kaurivo's private Supabase tables without FormSubmit.
8. **Palaute** shows ratings, comments and machine-tagged urgency.
   Raw customer reviews are never published without separate consent.
   Serious bugs require human verification; no automatic customer-site edits.

## Security and cost

The Frontend contains only the Supabase *publishable* browser API key;
never add `service_role` or other secrets. Supabase Auth sessions are
handled by the pinned Supabase JS client.

All admin tables require database-level RLS authorization.
The private schema `kaurivo_internal` contains the email-verified
admin predicate. The transactional invitation RPC is SECURITY INVOKER
and executable only by authenticated users (but rejects non-admins).
The review submission Edge Function uses a separate service_role secret,
never sent to the browser. None of these features require AI credits.

The existing test feedback remains a synthetic test record and must
not be represented as a verified customer review.

## Not yet automated / production limits

- **Automatic actual sending** one day after sale is NOT enabled: no
  background sender with audited Gmail authorization is installed.
  The database reliably creates the due queue, but preparation
  and sending are a human-reviewed step. Don't claim otherwise.
- Supabase's default authentication email capacity and project
  bandwidth limits are subject to its Free-tier quotas.
- No paid Supabase plan or external AI runtime is required for CRM.
- Until real customer identities, lawful privacy terms, confirmation
  and payment processes are verified, keep prospect and customer data
  restricted to the intended business need.
- Onboarding may require one account-side redirect allowlist edit.
- When real sales automation is connected, use idempotent sender
  status and reliable email provider callbacks before sending.
