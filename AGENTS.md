# Kaurivo website work

Before designing, building, revising or sharing any Kaurivo customer website or demo, read and follow [the current Kaurivo master prompt](website-builder-agent/website-builder-agent/docs/KAURIVO_MESTARI_PROMPT.md). This applies to automated builds, manual work, Sites and previews hosted outside this repository. A conversation, tool choice or hosting change does not replace the project rules.

## Source imagery and site-wide design

- Inspect and prefer the company's existing photos and videos before generating illustrations. Match the design to suitable source images. Record rejected source-image candidates and the actual gap for each replacement.
- Put essential source service information, product details and genuine customer proof into the redesigned customer journey. Use old-site links for supplementary information and preserve real external transaction platforms.
- Compare rendered homepage, substantive service page and product/contact page with real source assets and content before extending the design. Review the complete page rhythm, hierarchy and useful interaction.
- Run the existing source-content, route-experience, media, provenance and release checks on manual and external builds too. Repair available-source omissions before handing the draft to review. Follow the current Master Prompt for approval and report actual evidence and unresolved work.

## Before building

- Verify the company, original site, actual business tasks, service information, contact paths, planned site languages, visual identity and available source media. Record the source and any material gaps.
- Stop at research if the known material cannot support a useful, truthful site. Registry facts and a decorative image are insufficient when users still cannot tell what the company offers or how to reach it. Do not invent specifics or stretch sparse facts into filler pages. Report what must be confirmed before proceeding.
- Record the main offer in the company's own words with a source URL and exact excerpt. A business classification, legal scope or contact details do not substantiate an offer. Use a current company profile or owner confirmation when the original site has too little information.
- Give each service page a customer question to answer and enough verified material to answer it. Combine thin pages. During concept comparison, inspect one full service journey as well as the homepage. Verify that service routes use relevant examples and images where available, the contact path is prominent and generic calls to action do not repeat through consecutive sections.
- Render and compare the three source-grounded concepts required by the master prompt. Record the selection and actual mobile and desktop evidence before building the full site.

## Before opening access

- Run the existing concept evidence check in `utils/demo_origin_gate.py` and validate the current release with `utils/release_safety.py` from the application directory. Require the current master-prompt hash, exact-build evidence and all applicable checks. Run the independent visual review and verify the deployed build and business journeys in a real browser.
- Before providing an open link, removing a sign-in gate or marking a demo ready in the CRM, confirm that the evidence requirements already passed for that exact version. Owner-only staging may be used to obtain live verification. Missing evidence means HOLD.
- An access request such as “open link” specifies who should be able to view the demo. It is not a quality approval. If a demo is on HOLD, keep any existing draft restricted and report which requirement is missing.
