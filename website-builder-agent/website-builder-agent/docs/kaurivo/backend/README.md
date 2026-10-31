# Kaurivo customer feedback backend

Status on 31 October 2026: INSTALLED into the separate Kaurivo Supabase
organization, NOT OAVIR. Organization ID: ocglllovgdlilgcpdmon.
Project ID: xhsfbcwpwbgdbatrcyuk (Free, EU North).

## Live components

- PostgreSQL tables: public.kaurivo_feedback_invitations and
  public.kaurivo_feedback_submissions, both with RLS enabled and no
  anonymous read/write access.
- Service-role-only SQL function:
  public.kaurivo_submit_invited_feedback_v2.
  It uses SECURITY INVOKER, row locking and a unique invitation ID.
- Supabase Edge Function kaurivo-feedback-submit, public JWT check disabled
  because the request carries a 43-character, one-use customer invitation.
  The Edge Function checks exact origin, validates form fields and hashes
  the invitation token before calling service-only RPC.
- GitHub Pages /kaurivo/feedback/ page uses the Edge Function, not FormSubmit.
  The same visual 1–5 stars and written feedback UI remains unchanged.

## Issuing an invitation

Only after verifying a genuine customer purchase, generate a cryptographically
secure 32-byte random token and deliver it solely to the correct customer's
email address one Finnish calendar day after the purchase. The token's
SHA-256 hex digest, recipient email, verified company, sale timestamp,
expiry and internal project reference go in the private invitations table.

The customer-facing URL includes #invite=<base64url-token> after the language
and optional preselected rating query parameters, e.g.
https://k4k33.github.io/website-builder-agent/kaurivo/feedback/?lang=fi&rating=4#invite=TOKEN

Do not put real tokens, customer names, emails, project metadata or raw
comments into a public GitHub repository, URL query analytics, CI logs or
source-control artifacts. HTML email drafts and copyable form links must only
be created after a valid private invitation exists.

The customer must enter their matching verified email when submitting.
The database validates that the token has not expired, has never been used
before, belongs to the claimed email and is after the confirmed purchase.

## Operations

The classification occurs in the SQL transaction, producing a topic and
priority without using AI credits. A critical bug is flagged for human
review. All feedback remains private and no review is automatically
published or used to modify real customer sites.

The FormSubmit GitHub Actions monitor is LEGACY and disabled.
Direct Gmail feedback is separately checked by the scheduled email watcher.
To automatically send invitation emails after genuine new purchases, a
trusted and confirmed purchase/sales source is still required; there is no
live payment-driven trigger yet.

Security verification: validated the SQL function with rollback-only
synthetic cases for valid, duplicate, invalid email and invalid rating.
The full browser-to-Edge-to-database live submission with a synthetic
invitation remains the next integration test.

Never add the customer feedback data to OAVIR's project.
