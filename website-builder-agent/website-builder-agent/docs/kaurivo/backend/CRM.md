# Kaurivo private CRM — actual operating model

**Live database:** organization Kaurivo (ocglllovgdlilgcpdmon), project xhsfbcwpwbgdbatrcyuk, Stockholm/EU North, Free plan. NEVER OAVIR.

**Web UI:** `https://k4k33.github.io/website-builder-agent/kaurivo/admin/`, private only via Supabase Auth and database RLS. HTML/CSS/JS are publicly served static resources; customer data is not present in any source file, server-generated HTML, CI logs or GitHub commit.

## Database

- `public.kaurivo_crm_clients`: organizations/leads and optional notes
- `public.kaurivo_crm_projects`: client websites, industry-specific demos, mandatory requirements and self-service editing platform
- `public.kaurivo_crm_sales`: offers, verified completed sales, euro value and evidence reference
- `public.kaurivo_crm_feedback_queue`: unique one-per-sale queue, due timestamp and invitation status
- `public.kaurivo_feedback_invitations`: one-use hashed invitation tokens, associated with verified buyer email/sale
- `public.kaurivo_feedback_submissions`: private stars, written feedback, topic and urgency

**Authorization:** The private database function `kaurivo_internal.is_kaurivo_admin()` verifies the current Supabase Auth user ID against an email-confirmed Auth user belonging to exactly `hello.kaurivo@gmail.com`. The function is not in the REST-exposed public schema. Every CRM table has RLS that applies this permission to both reads and writes. The public `anon` role has no access to these tables or the token generator. The browser only contains a publishable key, never a service-role secret. This supports one administrator initially; broader staff role onboarding requires a deliberately audited separate approach.

## Sales → feedback

A sale only triggers the next-day queue when it is explicitly marked `won`, `source_verified`, contains a real `confirmed_at` and includes at least five characters of verification evidence. The private SQL trigger calculates `due_at` using the Finnish timezone's *following calendar day at the same local time*.

After due time, the admin uses the CRM's **Valmistele kutsu** button. It calls `public.kaurivo_crm_prepare_invitation(queue_id)`, which checks the caller's admin status, locks the queue, generates a high-entropy 32-byte single-use token, stores only its SHA-256 hex hash and returns a private link. Invoking the prepare action twice invalidates the previous unsent token.

The interface shows a ready-to-copy personal email and a Gmail composer link. Clicking those **does not send the email**. The admin must review the sender address/recipient, send manually, and then mark the queue as `sent`. Once sent, the queue cannot be prepared again. A verified sale has at most one invitation record.

The automatic *sending* part is intentionally disabled until an approved Gmail/OAuth integration or an authorized transactional email provider has been set up, and all opt-out, rate-limit, deduplication and legal bases have been checked. Do not falsely report it as active. The existing six-hour private ChatGPT feedback watcher can summarize new feedback; it does not replace transaction email delivery.

## One-time initial login setup

The Kaurivo Supabase Auth project has no confirmed administrator user yet. The admin web page uses email magic links, so configure this exact site in **Authentication → URL Configuration**:

- Site URL: `https://k4k33.github.io/website-builder-agent/kaurivo/admin/`
- Allowed redirect URL: `https://k4k33.github.io/website-builder-agent/kaurivo/admin/`

Then open the admin UI, enter `hello.kaurivo@gmail.com`, click **Lähetä kirjautumislinkki** and finish the email verification in the browser. Only that verified email will pass database RLS. Do not ask the user for passwords or access tokens.

## Verified tests on 31 October 2026

- CRM tables created inside Kaurivo's project, RLS enabled on all four
- Supabase Security Advisor: no lints found on creation
- Anon cannot SELECT clients, sales or feedback queue or EXECUTE invitation generator
- A rolled-back synthetic purchase created exactly one next-day feedback queue row
- No real sale or customer outreach was created by tests

Actual end-to-end UI use requires the admin's email magic-link sign-in and correct Supabase Auth redirect configuration. Synthetic database tests must remain in transactions rolled back, and web UI tests must mock external APIs to save free resources.
