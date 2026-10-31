# Separate Kaurivo customer feedback backend

**Status: prepared, NOT deployed.** The only connected Supabase project belongs to OAVIR. No Kaurivo data or schemas may be added there.

## Why

FormSubmit.co is temporary: its archive lasts 30 days, and the mailbox must first confirm activation. The one-time GitHub activation request was rejected by FormSubmit's Cloudflare challenge (403). A durable private database is more appropriate for real EU client reviews.

## Architecture

1. When a genuine sale is confirmed, an authorized Kaurivo administrator creates a random one-use token (32 cryptographically random bytes, encoded in base64url). Only its SHA-256 hash is stored with the verified recipient, project and expiry in the dedicated Kaurivo database. Never commit real invitation links or tokens.
2. A customer receives the private feedback link one day after sale, with the invitation token in the URL query parameter. The browser submits rating and written comment to a Kaurivo Edge Function, not directly to an exposed table.
3. The Edge Function validates an exact allowed origin, token length, rating, comment and body size; computes token SHA-256; then calls a privileged atomic SQL RPC. The token is consumed once. Invalid, expired or reused tokens do not create reviews.
4. The tables have row-level security enabled and no anonymous read/write policies. A verified buyer review remains private and is not automatically a public testimonial. Every serious issue requires human review, even if automatically tagged.
5. The backend stores private feedback for authorized Kaurivo review. It is completely separate from OAVIR.

## Activation checklist

- First, the owner must choose which Supabase organization should own the new project. The assistant must verify costs and seek approval for nonzero charges. Name the distinct project **Kaurivo** (EU North preferred). No shared OAVIR resources.
- Review relevant privacy and data-processing terms and complete the data-controller identity/privacy notice.
- Apply schema.sql in the NEW project only. Check both RLS tables, restrict RPC EXECUTE to service_role, verify no anonymous select/insert access and inspect Supabase security advisors.
- Deploy edge_function.ts as an Edge Function named kaurivo-feedback-submit with verify_jwt=false. Visitors are authenticated with one-use high-entropy invitation tokens. The service key stays entirely server-side.
- Wire the existing Kaurivo /feedback/ form to the new Edge Function only after this project exists. Keep star selection and desktop/mobile appearance identical.
- In a PRIVATE admin workflow, create an invitation tied to a genuinely verified purchase. Test a synthetic valid invitation, duplicate submit rejection, invalid/expired tokens, invalid star ratings, preflight CORS denial and mobile/desktop layout. Never print secret tokens or actual customer messages in public GitHub Actions output.
- Disable the FormSubmit polling once the new backend is verified end-to-end; keep Gmail as an optional second feedback intake channel.
- Feed categorized, privacy-safe improvements into the Builder QA checklist. Never auto-apply client design changes or publish endorsements.

## Security and business rules

One subjective color preference is not necessarily a global design change. Repeated, reproducible usability problems should become QA regression checks. A critical functional or security incident should be reviewed promptly, even if only reported once. Never infer message truthfulness or client identity from stars or sentiment.

No billable service was created by preparing this source code.
