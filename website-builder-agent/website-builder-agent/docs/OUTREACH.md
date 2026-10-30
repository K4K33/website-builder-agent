# Kaurivo outreach standard: distinct, evidence-led, human first

Customer communication is not a generic website sales pitch. A real company
with a ready demo deserves a fully individualized note.

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
2. Introduce sender immediately: "Olen Kaarlo Kaurivolta.
   Suunnittelen ja toteutan verkkosivuja yrityksille."
3. State why THIS company was contacted; for an existing site, reference
   one or two factual, specific modernization opportunities. Connect
   the observation to an actual customer's practical task without
   inventing lost sales or conversion statistics. Avoid gratuitous flattery.
4. State that a company-specific demo has been built and show a genuine
   approved demo link/card. Never invent a URL or pretend mockups are
   a complete production launch.
5. Make a clear commercial offer: "Jos pidätte ehdotuksesta,
   voin toteuttaa uuden sivuston teille kokonaan."
6. End with a **direct sales question**, for example "Olisiko teillä
   kiinnostusta uudistaa nykyisiä verkkosivujanne?" or, for a
   verified no-website business, "Olisiko oman verkkosivun
   toteuttaminen ajankohtaista?"
7. Close as Kaarlo at Kaurivo with the Kaurivo contact details. Never add a founder or CEO title.

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
