# Kaurivo outreach standard: distinct, evidence-led, human first

Customer communication is not a generic website sales pitch. A real company
with a ready demo deserves a fully individualized note.

## Customer-visible preview URL policy — mandatory

- **Never** place `raw.githack.com`, `rawgit.hack`, `github.io`, GitHub repository/file URLs, GitHub Pages developer domains, or public deployment-provider subdomains in a prospect's email, HTML demo card, QR code or sales deck.
- These can be used in **internal technical review only**. The raw.githack warning/interstitial in the 2026-11-02 Kotifixi review is a customer-trust blocker even though the HTML looked sound after clicking through.
- Client demos must have a clean **company-appropriate Kaurivo-controlled HTTPS custom domain** (or separately approved client-owned domain), verified ownership, verified no-warning initial load, approved demo contents and a real landing page. DNS/domain fees must wait until launch is authorized; do not invent a domain or imply that it exists.
- If no branded demo URL is ready, **do not send a demo URL or sales email claiming it is ready**. Continue internal QA for free; no automatic send.
- Run the `customer_safe_preview_url` / `assess_pitch_packet` checks and a real human first-open check on the exact link, including mobile. Link shorteners and redirect chains do not bypass the policy.

## Review before drafting

1. Confirm that the company is still operating, that its identity and
   website status are correct, and that this recipient is a lawful target
   for the proposed B2B commercial message.
2. Record the specific source, date and wording for one verified positive
   fact about this business. Do not confuse the business's own facts with
   those found on a competitor site.
3. If the company has a website, record one observed, accurate friction
   point in the real customer journey, with the relevant source/URL and
   viewport evidence. For a verified no-website company, never invent an
   existing site or criticize it.
4. Record the actual design change shown in the QA-approved demo. The
   suggested benefit should reflect a customer action, such as checking
   opening hours, booking, finding directions, requesting a quote or
   contacting the operator. Never promise more customers or revenue
   without genuine evidence.
5. Verify that every personalized claim is true and that the screenshot
   corresponds to the exact approved demo and real public HTTPS link.
6. Review the recipient name, greeting, headline and the complete draft.
   The owner separately authorizes *each actual sending action*.

## Email narrative: direct personal sales from Kaarlo at Kaurivo

The user wants a **commercially direct** message, not a soft 'design idea'
pitch. Before the second sentence ends, the recipient should know who
Kaarlo is and why this business has been contacted.

1. Short recipient-specific subject, e.g. "Verkkosivuidea [Company]lle".
2. Answer **"Mikä Kaurivo on?"** immediately and in plain language:
   "Olen Kaarlo Kaurivolta. Kaurivo on uuden sukupolven
   verkkosivustudio, joka toteuttaa yrityksille uusia verkkosivuja
   ja uudistaa nykyisiä." Follow with one concrete, verifiable benefit
   (a site reflecting their brand, straightforward mobile use and
   content the company can maintain itself). Don't describe Kaurivo
   vaguely as a "teknologiayritys" or imply an established client roster,
   staff size, revenue results, or completed commissions without evidence.
   Write the same clear answer in **Swedish or English** when the
   prospect's reviewed contact language requires it. Do not assume
   that a company has an existing website merely because its name
   appears in search results.
3. State why THIS company was contacted; for an existing site, reference
   one or two factual, specific modernization opportunities. Connect
   the observation to an actual customer's practical task without
   inventing lost sales or conversion statistics. Avoid gratuitous flattery.
4. State that a company-specific demo has been built and show a genuine
   approved demo link/card. Never invent a URL or pretend mockups are
   a complete production launch.
5. **Media note immediately below the demo image/card or demo URL:**
   favor existing company-owned photos with confirmed rights; otherwise
   use coherent, licensed example photos. When demo contains example
   photos, show the short Finnish note:
   "Demon kuvat ovat esimerkkikuvia. Halutessanne voitte lähettää
   meille omia kuvia, joita toivoisitte käytettävän lopullisilla
   verkkosivuilla." For a mixed demo say "Osa demon kuvista...".
   This is an optional invitation, not a compulsory content request;
   no extra follow-up or uploading required before the firm replies.
   The outreach draft stores this as `demo_card_caption` and also
   inserts it beneath the demo link/mention in plain-text email.
   HTML renderers must display that caption directly below the demo
   card. Do not invent client ownership or assert permissions
   when the final image sources are unverified.
6. Make a clear commercial offer: "Jos pidätte ehdotuksesta,
   voin toteuttaa uuden sivuston teille kokonaan."
7. End with a **direct sales question**, for example "Olisiko teillä
   kiinnostusta uudistaa nykyisiä verkkosivujanne?" or, for a
   verified no-website business, "Olisiko oman verkkosivun
   toteuttaminen ajankohtaista?"
8. Close as Kaarlo at Kaurivo with the Kaurivo contact details. Never add a founder or CEO title.

**Sender account:** All client-facing drafts and approved commercial mail must
be created and sent using only **hello.kaurivo@gmail.com**. NEVER use
any personal Gmail account or any other sender.
Introducing Kaarlo by his first name in the body does NOT make it a
personal Gmail email. Before a send operation through Gmail, explicitly
confirm the connected account's `get_profile` address equals
`hello.kaurivo@gmail.com`; if this cannot be verified, abort.
Verify the exact recipient and message and obtain per-message owner approval.
The local Python repository has no sending ability.

Avoid vague closings such as "Miltä tällainen suunta tuntuu?", a forced
positive opening, over-explaining or asking for a meeting in the first
contact. The tone should be confident, helpful, honest and friendly,
not rude or manipulative. Don't claim an improvement that isn't actually
in the demo. Make each observation and solution truly distinct.

Use a crisp HTML mail with a company-specific approved screenshot/card
and one clear demo link, with a real text fallback when images are blocked.
Avoid newsletters, tracking pixels and large embedded base64 images.

No sentence-level em dashes, en dashes, separator lines, aggressive sales
claims, artificial urgency, boilerplate flattery or generic "inspired to
build you a website" filler.

**Compliance:** A Finnish commercial B2B email must also clearly offer a
simple and free way to opt out in every message. The awkward long opt-out
sentence should not be in the personal sales copy. The email can instead
use a concise, legible footer link labelled "Kieltäydy jatkoviesteistä"
with a working reply or unsubscribe mechanism. Suppress contacts who
object. Verify applicable recipient-specific consent rules before sending,
especially for personal addresses and sole traders. See
https://www.finlex.fi/fi/lainsaadanto/2014/917 (sections 200-203).

## Data limitations

OpenRouter/AI-generated candidate observations are not enough to claim
something is verified. A human must compare the email's exact statement
to the original source and approved demo. The prompt alone is not a
guarantee of accuracy, legal compliance or conversion. The repository
still does not send email automatically.


## Finnish B2B outbound marketing: mandatory release gate (2026-10-30)

The repository **does not send emails**. Neither GitHub schedules nor
draft approval authorize a Gmail send. Kaurivo is responsible for complying
with Finnish law and GDPR. Taxes are outside this project's scope.

The code at \`utils/marketing_compliance.py\` provides a deliberately
conservative, offline *pre-send* check. It must be integrated into and
executed by **every** future real Gmail sender; never rely on AI-generated
copy or a "B2B" label alone as evidence of permission.

1. A verified company's generic mailbox may be approached under the
   community opt-out rule unless a prior objection exists (917/2014 §202).
2. A named employee's direct work address ordinarily needs advance
   consent unless the offered service is substantially related to their
   verified actual job duties. Store source and documented role reason.
3. A natural person, including a sole trader, needs documented advance
   consent for unsolicited marketing unless a specific lawful exception
   has been independently established. If unsure, do not email (§200).
4. Clearly identify the message as commercial, sender as Kaurivo and
   actual sender mailbox. Add an easily accessible, free opt-out in
   *every* commercial message (§§202–203).
5. A reply to \`hello.kaurivo@gmail.com\` can be the opt-out method **only if
   monitored**. Every objection must enter a persistent, private suppression
   register that is checked again immediately before every send. A
   company-level \`marketing_opt_out\` or \`do_not_contact\` also blocks
   drafting in the Python agent. Do not store named email addresses or
   suppression data in public GitHub files, public artifacts or logs.
6. Comply with GDPR duties including minimization, a lawful basis,
   legitimate-interests assessment where applicable, transparency/Art. 14,
   retention limits and Art. 21 objection rights. A website privacy notice
   must be verified before public commercial launch. Public availability
   of personal data alone does not permit arbitrary marketing.
7. Verify the real demo URL, permission to use brand material, accurate
   individualized sales claims and the recipient's current business status.
8. Send only after **individual owner approval** and live sender-account
   verification. The test module cannot prove an externally connected
   Gmail sender has implemented these checks. Until one does, automated
   sending stays disabled.

Legal source: https://www.finlex.fi/fi/lainsaadanto/2014/917
(especially §§200, 202 and 203).
Regulator interpretation for employee mailboxes:
https://www.finlex.fi/fi/viranomaiset/tietosuojavaltuutettu/2020/629

Run free tests: \`python -m unittest tests.test_marketing_compliance -v\`.


## Demo must-haves and customer feedback

When emailing a QA-approved company-specific demo, include one short optional question asking what MUST be on the final website. Replying to the same Gmail thread is always possible. Only include the reusable demo-review form link when the FormSubmit recipient is activated and a real submission is delivered, and only when the private customer record has `demo_review_intake_confirmed=True` and an explicit `demo_review_url`. Wishes do not create a contractual scope. After a real client project is completed, collect feedback in an individual Gmail reply request, not via the public site. Drafting is not sending. See CUSTOMER_FEEDBACK.md.
