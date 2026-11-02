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


## 2026-11-02 — Kotifixi V10 human + independent AI feedback

- Every release note automatically includes a published, verified preview URL.
- Independently gathered human observations count equally with AI: desktop navigation must be readable, typically 15–16px, and not tiny 12px links.
- Phone and contact CTA must be a visually integrated header action group.
- Plain, authentic Finnish; reject repeated awkward phrases such as "kotona tai pihalla" and outside-reporter descriptions of a business.
- Restrained animation: one-shot below-the-fold reveals via IntersectionObserver, native scrolling, reduced-motion and content shown when JS is off; intentional hover/focus/click feedback.
- Example photos must be on-topic, licensed and free of misleading third-party brands in visible print; no fake business facts, reviews or staff.
- Customer-sales links STILL require a separately verified branded HTTPS domain without an interstitial. Public GitHub Pages is for the owner review only.

**Internal review link:** https://k4k33.github.io/website-builder-agent/kaurivo/demos/kotifixi-v10/

## V11 owner-review snapshot — 2026-11-02

New version: https://k4k33.github.io/website-builder-agent/kaurivo/demos/kotifixi-v11/

Every version gets its working direct link in the completion reply automatically. The GitHub Pages technical host is permitted for **owner/internal preview only**, never for emails to prospective customers. See the latest 2026-11-02 V11 QA/feedback standards for the natural-Finnish headline, 17–18px desktop menu, page-title honesty and optional pointer-only CSS 3D effects with uncompromised native scroll. Every new implementation must pass device/browser tests and independent review; none of this represents an accepted >=9.5 score or production/CMS readiness.
