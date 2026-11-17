# Kaurivo website work

Before designing, building, revising or sharing any Kaurivo customer website or demo, read and follow [the current Kaurivo master prompt](website-builder-agent/website-builder-agent/docs/KAURIVO_MESTARI_PROMPT.md). This applies to automated builds, manual work, Sites and previews hosted outside this repository. A conversation, tool choice or hosting change does not replace the project rules.

## Before building

- Verify the company, original site, actual business tasks, service information, contact paths, planned site languages, visual identity and available source media. Record the source and any material gaps.
- Stop at research if the known material cannot support a useful, truthful site. Registry facts and a decorative image are insufficient when users still cannot tell what the company offers or how to reach it. Do not invent specifics or stretch sparse facts into filler pages. Report what must be confirmed before proceeding.
- Render and compare the three source-grounded concepts required by the master prompt. Record the selection and actual mobile and desktop evidence before building the full site.

## Before opening access

- Run the existing concept evidence check in `utils/demo_origin_gate.py` and validate the current release with `utils/release_safety.py` from the application directory. Require the current master-prompt hash, exact-build evidence and all applicable checks. Run the independent visual review and verify the deployed build and business journeys in a real browser.
- Before providing an open link, removing a sign-in gate or marking a demo ready in the CRM, confirm that the evidence requirements already passed for that exact version. Owner-only staging may be used to obtain live verification. Missing evidence means HOLD.
- An access request such as “open link” specifies who should be able to view the demo. It is not a quality approval. If a demo is on HOLD, keep any existing draft restricted and report which requirement is missing.
