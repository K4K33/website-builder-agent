# Kaurivo: customer wishes, feedback and continuous improvement

## Two distinct moments

### 1. Sending a customer-specific website demo
Keep the sales email short and individual. Show the real, QA-approved company-specific demo, and ask: "Mitä lopullisella sivustolla pitää ehdottomasti olla?"

Only after the FormSubmit recipient mailbox has been activated and end-to-end delivery tested, also include the optional feedback page link:
https://k4k33.github.io/website-builder-agent/kaurivo/demo-review/

Always make the lowest-friction alternative prominent: "Voitte myös vastata suoraan tähän sähköpostiin." No login, phone number, booking call or long questionnaire. Record client must-haves in a PRIVATE project brief, confirm final scope and price with the customer, and never treat these ideas as an accepted order, marketing consent or permission to rebrand.

The first sales message must follow all outreach legal and human-review gates in OUTREACH.md. No autonomous sends.

### 2. One day after a confirmed sale: private Kaurivo database

The customer receives a polished, generic Kaurivo / Asiakaskokemus Gmail
request ONE Finnish calendar day after a genuinely verified purchase. A
unique cryptographically random 32-byte customer invitation is stored
only as a SHA-256 digest and tied to the verified recipient, project and
expiration in the dedicated Kaurivo Supabase database. A text or HTML
email draft MUST NOT be offered for sending without a corresponding,
valid private invitation in the database.

The five star links and a writing-field link open:
https://k4k33.github.io/website-builder-agent/kaurivo/feedback/?lang=fi&rating=4#invite=TOKEN
where TOKEN is a real one-time private invitation (never a public
placeholder), inside the URL fragment rather than the HTTP request path.
The user may change the highlighted stars, write a comment, fill the
company and matching verified customer email, acknowledge privacy
information and submit. Only a successful POST via Kaurivo's own Supabase
Edge Function counts as a saved review. The Edge Function verifies
request origin, data format and token before calling an atomic,
single-use SQL function. Invalid, expired or repeated links do not
create customer feedback. The browser never receives the database
service-role key.

The **Kaurivo Supabase project is separate from OAVIR**: project
xhsfbcwpwbgdbatrcyuk in organization ocglllovgdlilgcpdmon, EU North,
Free plan. The two private feedback tables are RLS-protected and do not
permit anonymous reading. The server categorizes urgency and subject.
All reviews remain unverified statements until human review; they are
not automatically posted as testimonials or turned into client changes.

The FormSubmit-based Gmail archive reader is now LEGACY, not the
customer feedback collection path; its GitHub workflow remains disabled.
The already connected Gmail watcher can separately process direct
email feedback; it does not read Supabase table rows automatically.
A verified sales/purchase source and admin invitation issuance are
still required before automatic customer invitations can be sent.
No real customer emails are sent by the code itself.

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

Two real TEST emails were sent using the verified Kaurivo Gmail account to the user-supplied test mailbox (one sample sales email, one purchase-experience feedback request). The feedback email uses KAURIVO as a generic sender identity. The star links and feedback prompt now open Kaurivo's interactive /feedback/ page; they no longer open Gmail drafts. The choice is recorded only when the form is submitted and provider delivery is confirmed. Sent-folder verification does not establish inbox delivery. No customer was contacted by this test.

## Privacy and publication

Demo review submissions use the site's existing third-party FormSubmit endpoint and follow its privacy notice. Recipient activation and delivery are NOT yet verified. Until activation, invite replies to the original Gmail message instead of advertising the page as fully operational.

Private feedback is not automatically a public testimonial or a license to disclose client details. A separately documented, informed authorization is needed before publishing a quote, company name or logo as endorsement. Store only needed data and follow legal privacy retention rules.

## Reuse in outreach

Once the form passes activation and end-to-end delivery checks, add its confirmed link below the actual QA-approved demo link and include the same form link in the email sending workflow. If not confirmed, use direct email reply. Do not add a fake review widget to fictional Kaurivo portfolio concepts or demand it in the middle of a sales pitch.

The Python helpers create drafts and suggested triage only. They do not read Gmail, schedule reminders, spend AI credits, send mail, publish testimonials or apply code changes.


## October 31, 2026: deployment and remaining verification

Kaurivo's separate Supabase database and server submission function are
installed, and database tests have confirmed accepted one-use token,
rejected duplicate token, wrong email and invalid star rating (all
transaction-rolled-back synthetic tests). The static website now uses
the dedicated endpoint. CI browser tests and one real browser submission
with a synthetic invitation are still part of deployment verification.
FormSubmit activation is no longer required for this customer-review
flow; it remains relevant to the separate demo-wishes form.
