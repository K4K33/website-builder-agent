# Kaurivo database-enforced outreach safety — 31.10.2026

Applied migration: `kaurivo_outreach_suppression_db_safety` in Kaurivo Supabase project.

## Protections

- `kaurivo_marketing_suppressions` is a separate RLS-protected table, holding business IDs only. Admin read and insert are permitted; no admin deletion/update policy exists. Data is private.
- On any prospect insert/update, the `kaurivo_prospect_safety_trigger` checks suppression and retains previous opt-outs. A company previously opted out automatically remains blocked even when the name is rediscovered by a later PRH sync.
- No outreach can be marked as human-approved without a verified business activity assessment, customer need and a source URL.
- No outreach can be marked as sent/responded/won without human legal approval. This **records** a manual send; nothing sends emails automatically.
- Demobrief preparation requires real business activity evidence, a research source and substantial draft text.
- Assessment fields cannot be populated without a supporting evidence URL.
- A finite-value research score in the browser does not certify solvency or buyer intent.
- Use `docs/KAURIVO_LEGAL_COMPLIANCE.md` for applicable legal checks. A marketing opt-out is not an all-purpose GDPR consent status. No person-level email contact records should be added without a documented legal basis.

## Persistence and verification

```sql
select count(*) from public.kaurivo_marketing_suppressions;
select tgname from pg_trigger
where tgrelid='public.kaurivo_crm_prospects'::regclass
and not tgisinternal;
select tablename, policyname from pg_policies
where tablename='kaurivo_marketing_suppressions';
```

The proof of tomorrow's scheduled PRH run and Web Push remains a distinct live test. No developer should claim that a browser permission alone guarantees that the Web Push subscription reached Supabase.
