# Kaurivo: customer wishes, feedback and continuous improvement

## Two distinct moments

### 1. Sending a customer-specific website demo
Keep the sales email short and individual. Show the real, QA-approved company-specific demo, and ask: "Mitä lopullisella sivustolla pitää ehdottomasti olla?"

Only after the FormSubmit recipient mailbox has been activated and end-to-end delivery tested, also include the optional feedback page link:
https://k4k33.github.io/website-builder-agent/kaurivo/demo-review/

Always make the lowest-friction alternative prominent: "Voitte myös vastata suoraan tähän sähköpostiin." No login, phone number, booking call or long questionnaire. Record client must-haves in a PRIVATE project brief, confirm final scope and price with the customer, and never treat these ideas as an accepted order, marketing consent or permission to rebrand.

The first sales message must follow all outreach legal and human-review gates in OUTREACH.md. No autonomous sends.

### 2. One day after a confirmed sale: interactive stars on Kaurivo's website

After a verified sale, prepare a private, customer-specific Kaurivo Gmail
feedback email ONE calendar day later in Finland time. It must rate the
quotation and onboarding, not a website that hasn't been delivered.

The email's five star links and the rectangular writing prompt now open
the dedicated Kaurivo page:
https://k4k33.github.io/website-builder-agent/kaurivo/feedback/?lang=fi

Each star link passes an integer preselection in the URL, but does not
record anything by itself. On the page, the client can change the lit
stars, enter a short written review, company and contact email, consent
to private submission and press **Lähetä palaute**.

The page uses the documented FormSubmit JSON AJAX endpoint and receives
a success state only if FormSubmit explicitly reports success. It does
NOT open Gmail or claim success based only on HTTP 200.

**Activation:** Confirm hello.kaurivo@gmail.com in FormSubmit's first
activation email, then test end-to-end submission. Before the receiving
address is activated, the UI displays a failure/activation status; do
not claim that customer reviews have been accepted.

**Storage:** As currently configured, reviews are retained by the
external FormSubmit service (with 30-day archival retention) and
delivered into the Kaurivo Gmail inbox. This is NOT yet a durable
first-party Kaurivo database. We must not add any private review
contents to the public GitHub repository.

**Optional automatic classification:** The private GitHub workflow
kaurivo-feedback.yml is installed, but remains inert until an API
secret named KAURIVO_FORMSUBMIT_API_KEY is configured. The workflow
checks up to four times daily (under the provider's five-call free API
quota), filters the last 24 hours and publishes only anonymous topic,
rating and urgency counters to a GitHub Actions run. It sends no emails
and makes no website edits. Individual reviews remain unverified until
checked against private customer/project records. Duplicate provider
entries in a single archive response are coalesced. The rolling window
may overlap across runs; treat those counts as snapshots, not additive
new-review notifications.

A durable, real-time customer-feedback system requires a SEPARATE
Kaurivo backend, database and verified purchase invitation tokens.
The only connected existing Supabase project belongs to OAVIR; do not
touch or reuse it. Creating a distinct project needs the user's explicit
choice of Supabase organization and any cost confirmation. Until then,
the FormSubmit archive remains the temporary store.

The email sender and signoff are generic: Kaurivo / Asiakaskokemus.
No personal name or title. No true client is contacted in tests.

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


## October 31, 2026: verified setup status and activation blocker

- The live Kaurivo feedback form and its 1–5 stars passed browser tests. The AJAX request has been updated to regular URL-encoded form data to reduce cross-origin preflight issues.
- GitHub datacenter POST to activate FormSubmit was **blocked by Cloudflare HTTP 403** with a JavaScript challenge. No activation confirmation was received by Kaurivo's Gmail. The one-time GitHub activation workflow has been removed. Activation requires one normal browser submission on the real Kaurivo form, then confirmation in hello.kaurivo@gmail.com. Do not describe delivery as live until a post-activation end-to-end submission arrives.
- A recurring ChatGPT automation was created to check the connected Kaurivo Gmail every 6 hours, classify new non-test review messages and alert on significant issues. It does not send mail, publish customer data or modify any client websites. This operates independently of FormSubmit's archive API.
- The FormSubmit GitHub workflow is now guarded by the repository variable KAURIVO_FEEDBACK_ENABLED == true; before activation it schedules no runner work and consumes no archive API credits. When later enabled, it needs the KAURIVO_FORMSUBMIT_API_KEY GitHub Actions secret. Maximum 4 archive requests daily, under the 5/day free cap. Do not enable until key and activation are both proven.
- A dedicated Kaurivo-only Supabase schema and Edge Function package is prepared under docs/kaurivo/backend/. This is **not deployed**. It must go into a new Kaurivo organization-selected project, never OAVIR. Confirm any project costs and privacy terms before production deployment. The private backend uses cryptographically random one-time invitation tokens, atomic database consumption, RLS and no public access.
