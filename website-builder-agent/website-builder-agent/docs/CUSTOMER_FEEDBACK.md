# Kaurivo: customer wishes, feedback and continuous improvement

## Two distinct moments

### 1. Sending a customer-specific website demo
Keep the sales email short and individual. Show the real, QA-approved company-specific demo, and ask: "Mitä lopullisella sivustolla pitää ehdottomasti olla?"

Only after the FormSubmit recipient mailbox has been activated and end-to-end delivery tested, also include the optional feedback page link:
https://k4k33.github.io/website-builder-agent/kaurivo/demo-review/

Always make the lowest-friction alternative prominent: "Voitte myös vastata suoraan tähän sähköpostiin." No login, phone number, booking call or long questionnaire. Record client must-haves in a PRIVATE project brief, confirm final scope and price with the customer, and never treat these ideas as an accepted order, marketing consent or permission to rebrand.

The first sales message must follow all outreach legal and human-review gates in OUTREACH.md. No autonomous sends.

### 2. One day after a confirmed sale: Gmail stars + short comment

The primary feedback request is due **one day after the confirmed purchase**.
It covers the quotation, purchasing process, communication and getting started,
NOT the quality of a website that has not been delivered.

A private sale record needs a genuine confirmed timestamp, verified customer,
recipient email and unique project reference. Calculate the review due datetime
from the confirmed sale in Europe/Helsinki local time. The offline function
`feedback_due_at()` and `draft_after_sale_feedback()` enforce this timing.

The Gmail email is deliberately very short:

Subject: Miten asiointi Kaurivon kanssa alkoi?

Hei [nimi],

Kiitos luottamuksesta! Miltä tarjous, yhteydenpito ja kaupanteko
tuntuivat tähän asti?

Anna 1–5 tähteä ja halutessasi yksi lyhyt kommentti. Voit vastata
suoraan tähän viestiin esimerkiksi: 4/5, asiointi sujui hyvin,
mutta aikataulut voisivat olla selkeämmät.

Kiitos!
Kaarlo Kaurivolta

The optional polished HTML version places five clickable star choices inside
the Gmail message. Each star choice opens an email draft addressed to
hello.kaurivo@gmail.com with a prefilled rating and a blank one-line feedback
field. **Clicking a star is NOT a submission.** The client confirms and sends
the reply. The plain-text fallback is simply replying in the original Gmail
thread with e.g. "4/5 – hyvä, mutta..." — no website or login required.

Each sent request should be marked in a PRIVATE customer record so the same
purchase does not produce duplicate requests. No automatic sender is currently
installed; the helper only prepares a draft after a real sale. When Gmail
sending is connected to verified private sale records, require sender account
verification, applicable privacy rules, deduplication, and an authorized
sending policy. Do not send an email to a prospect who has not purchased.

### 3. After the actual website is delivered (optional second feedback)

The website's real usability and result can only be reviewed after actual
handover. If appropriate, ask for that project-specific feedback later,
without pestering the same client. It is separate from the first-day
purchase/onboarding rating, and it must not be represented as a verified
website quality assessment until the site exists and is used.

Do not demand a review, redirect to the website, presume consent to public
testimonials, or pressure customers to leave five stars. At most one considerate
reminder, depending on the relationship. The sender MUST be
hello.kaurivo@gmail.com with verified account and approval before actual send.

## Reliability and quality triage

The offline helper utils/customer_feedback.py can parse explicitly written 1–5 stars and suggest categories and urgency. It NEVER determines authenticity based on tone, star rating, AI-style writing or whether criticism is favorable. Low ratings are never discarded. Negative, short, anonymous or unverified feedback remains worth reviewing.

Verify that the person and project actually match private records. The email address by itself is NOT proof of identity. Preserve unknown-sender feedback with source_status unverified and ask for necessary context. Categorize as mobile, usability, technical fault, speed, content and brand, editability/CMS or communication. Distinguish a verified client-specific design preference from a reproducible problem worth fixing for all future customers.

A single serious bug, accessibility failure, broken contact form, lost content or security concern can justify immediate review even without many similar reports.

## Closed-loop improvements

Keep the actual customer records private, NOT in the public GitHub repository:
project_ref, sale_confirmed_at, feedback_due_at, feedback_sent_at, verified_source_evidence, received_at, original_message_location, rating_1_to_5,
category, reproduced_issue, impact, priority, human_owner, status, change_link,
next_review_date, customer_confirmation.

Track stages: received -> source verified or marked unverified -> triaged ->
approved for change -> implemented -> retested -> customer-confirmed.

Review feedback after each handover and in a weekly internal review. Address recurring issues by updating Kaurivo's Builder, quality checklist, tests and project handover process, not merely replying with "thanks." Before generalizing a preference, check that it applies to other clients; do not override distinctive brand identities. Owner approves production changes. No public GitHub issues containing raw customer messages or personal details.

## Tested HTML email appearance (2026-10-30)

Two real TEST emails were sent using the verified Kaurivo Gmail account to the user-supplied test mailbox (one sample sales email, one purchase-experience feedback request). The feedback email uses KAURIVO as the generic sender identity instead of a person's signature, 1–5 clickable star options, and a rectangular clickable writing prompt beneath the text-feedback label. Both clickable elements use mailto links and open a compose view: **clicking does not transmit or store feedback; the recipient must send the resulting message**. The plain reply-in-thread alternative remains available. Sent-folder verification does not establish inbox delivery. No customer was contacted by this test.

## Privacy and publication

Demo review submissions use the site's existing third-party FormSubmit endpoint and follow its privacy notice. Recipient activation and delivery are NOT yet verified. Until activation, invite replies to the original Gmail message instead of advertising the page as fully operational.

Private feedback is not automatically a public testimonial or a license to disclose client details. A separately documented, informed authorization is needed before publishing a quote, company name or logo as endorsement. Store only needed data and follow legal privacy retention rules.

## Reuse in outreach

Once the form passes activation and end-to-end delivery checks, add its confirmed link below the actual QA-approved demo link and include the same form link in the email sending workflow. If not confirmed, use direct email reply. Do not add a fake review widget to fictional Kaurivo portfolio concepts or demand it in the middle of a sales pitch.

The Python helpers create drafts and suggested triage only. They do not read Gmail, schedule reminders, spend AI credits, send mail, publish testimonials or apply code changes.
