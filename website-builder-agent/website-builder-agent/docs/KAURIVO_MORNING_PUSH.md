# Kaurivo — morning leads & iPhone PWA notifications

## Status (2026-10-31)

Implementation committed on GitHub main. Server function
\`kaurivo-daily-push\` v2 deployed to the Kaurivo-only Supabase project
\`xhsfbcwpwbgdbatrcyuk\`. Data tables have RLS enabled and explicitly
revoke anonymous/authenticated access. No other project (including OAVIR)
shares this data or credentials.

**Live device subscription and the first real schedule run are not yet
verified.** A browser-specific test on the user's physical iPhone is
required before claiming end-to-end delivery.

## Morning sequence

1. 04:13 local Europe/Helsinki: existing
   \`.github/workflows/kaurivo-national-prh.yml\` downloads PRH/YTJ public
   registry data (one bounded official source request), selects up to
   50 unverified candidate businesses and uploads an OIDC-authenticated
   packet to \`kaurivo-prh-ingest\`.
2. The RLS-protected \`kaurivo_crm_prospects\` table stores each candidate
   with \`discovery_date\`. Duplicate business IDs are not overwritten.
3. 08:00 local Europe/Helsinki: \`kaurivo-morning-push.yml\` obtains a
   short-lived GitHub Actions OIDC token, not a static key.
4. The separate \`kaurivo-daily-push\` Edge Function validates issuer,
   audience, workflow path, repository and owner numeric IDs, branch and
   event. It checks whether **actual** prospect records exist for
   that local date. If none exist, it does not send a misleading push.
5. Up to eight opted-in admin devices per user receive a Web Push message
   that opens the morning list. Last-notified date is stored per device
   for deduplication. 08:27 is a backup workflow; no repeated alerts
   on already-notified devices.

GitHub Actions cron is best effort and can be delayed or dropped. 08:00
is a target, **not an exact delivery SLA**; external push providers and
iOS may also delay presentation. A failed early PRH job cannot truthfully
be replaced by invented companies.

## iPhone setup (one time)

1. Open <https://k4k33.github.io/website-builder-agent/kaurivo/admin/>
   in **Safari** on the iPhone.
2. Use Share > **Add to Home Screen**, then open the new Kaurivo icon
   from the Home Screen (iOS 16.4 or later).
3. Sign in with a confirmed Kaurivo administrator email:
   \`hello.kaurivo@gmail.com\` or \`kaarlo.kaukko1@gmail.com\`.
4. Open **Aamun yritykset** > **Salli ilmoitukset** and accept the Apple
   permission dialog. Use **Testaa ilmoitus** to confirm on-device delivery.
5. The date selector shows that day's batch; older batches remain
   accessible by choosing their day. Push-click deep links to its day.

A browser tab on iPhone cannot subscribe to iOS Web Push. Permission
must be requested by the user tapping a control in the installed PWA.
Turning notifications off in iOS Settings or signing out unsubscribes
on that device when the app can reach the server.

## Website evidence and compliance

The prospect UI displays the company's registry-listed HTTPS URL as an
external link. If PRH has no website, the UI says **"Ei verkkosivua
löytynyt · ei vielä vahvistettu"**. It never claims verified website
absence based only on a blank registry field.

No marketing emails, demo publication, contact collection or AI-credit
requests run from these notifications. A human must confirm active
business status, website, financial/solvency signals, and outreach
legality before a demo or contact.

## Diagnostics

- GitHub Actions > Kaurivo national business discovery (PRH bulk):
  check the 04:13 run. If empty, inspect the official registry source.
- GitHub Actions > Kaurivo morning lead notifications:
  check the 08:00 and backup 08:27 executions. \`workflow_dispatch\`
  may be used to test a manual OIDC invocation without real notifications
  when there is no fresh date-stamped batch.
- Supabase (Kaurivo project): \`kaurivo_crm_prospects\`,
  \`kaurivo_push_subscriptions\` (private), Edge Function logs.
- PWA: use its **Testaa ilmoitus** button after subscribing.

VAPID keys are created once inside the Edge Function and stored only
in RLS-protected service-role database rows; **never commit the private
key to GitHub**.
