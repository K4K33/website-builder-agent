# Kaurivo — every reviewable version gets a working preview link automatically

**Permanent agency workflow rule (2026-11-02).** Applies to all client demos and
revisions, including Kotifixi. The user must NEVER need to ask separately for
the web link after the agent reports a version is ready for review.

1. **Build first.** Complete copy, assets, responsive browser QA and tests.
2. **Publish a versioned INTERNAL preview** (e.g. `/kaurivo/demos/kotifixi-v9/`)
   to a stable deployment that opens directly to the real site, never to
   raw.githack, warning screens, GitHub code, file viewer, or zip download.
   Keep prior versions available so differences can be compared. Never
   mislabel an unmerged branch or an unverified URL as a live deployment.
3. **Verify exact real link** with HTTP 200 and the latest HTML marker plus
   CSS, JS, navigation and subpage checks; preview must include an accurate
   demo disclaimer and noindex while still a concept.
4. **Proactively put the clickable preview URL in the SAME completion response**
   without waiting for the user to request it. If deploying/verification
   fails, explain the actual blocker and provide no invented working link.
5. **Review-only vs sales are distinct gates.** A public GitHub Pages/internal
   technical-preview host may be given to the agency owner for testing only.
   It is NEVER a customer-facing sales/outreach link. Customers must see
   a direct, owner-verified branded HTTPS domain with no warning/interstitial,
   independently accepted design, correct rights and approved sending.
6. Do not buy domains or subscriptions or contact the customer without
   explicit permission. Reuse existing free preview hosting where practical.
7. For a future V10/V11 or a different client, repeat publication and
   verification **as part of** the build/QA task. Include new link by default,
   not merely a PR link. An internal version must not be described as
   a production CMS or a site accepted at >=9.5 unless independently proven.

**Kotifixi V9 owner-review preview**:
https://k4k33.github.io/website-builder-agent/kaurivo/demos/kotifixi-v9/
This is an internal design review path, NOT a client-sales URL.
