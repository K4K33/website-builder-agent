# Kaurivo: customer wishes, feedback and continuous improvement

## Two distinct moments

### 1. Sending a customer-specific website demo
Keep the sales email short and individual. Show the real, QA-approved company-specific demo, and ask: "Mitä lopullisella sivustolla pitää ehdottomasti olla?"

Only after the FormSubmit recipient mailbox has been activated and end-to-end delivery tested, also include the optional feedback page link:
https://k4k33.github.io/website-builder-agent/kaurivo/demo-review/

Always make the lowest-friction alternative prominent: "Voitte myös vastata suoraan tähän sähköpostiin." No login, phone number, booking call or long questionnaire. Record client must-haves in a PRIVATE project brief, confirm final scope and price with the customer, and never treat these ideas as an accepted order, marketing consent or permission to rebrand.

The first sales message must follow all outreach legal and human-review gates in OUTREACH.md. No autonomous sends.

### 2. After the real website is delivered
Do not wait for a customer to return to Kaurivo's website. Prepare an individual feedback request in the EXISTING Gmail thread, normally 7 to 14 days after actual handover, and only when a real customer relationship and completion are confirmed.

Subject: Miten verkkosivuprojektimme sujui?

Hei [asiakas],

Nyt kun sivustonne on ollut käytössä hetken, haluaisin aidosti kuulla miten yhteistyö sujui.

Mikä meni erityisen hyvin?
Oliko jokin hankalaa tai epäselvää?
Mitä yhtä asiaa meidän pitäisi tehdä jatkossa paremmin?

Voit vastata suoraan tähän sähköpostiin, vaikka vain parilla lauseella. Myös kriittinen palaute auttaa meitä kehittymään.

Kiitos!
Kaarlo Kaurivolta

Do not demand a review, redirect to the website, assume consent to public testimonials or generate pressure for five-star ratings. At most one considerate reminder, depending on the relationship. Sender MUST be hello.kaurivo@gmail.com, account verified, with explicit owner approval for each send.

## Reliability and quality triage

The offline helper utils/customer_feedback.py can suggest categories and urgency. It NEVER determines authenticity based on tone, star rating, AI-style writing or whether criticism is favorable. Negative, short, anonymous or unverified feedback remains worth reviewing.

Verify that the person and project actually match private records. The email address by itself is NOT proof of identity. Preserve unknown-sender feedback with source_status unverified and ask for necessary context. Categorize as mobile, usability, technical fault, speed, content and brand, editability/CMS or communication. Distinguish a verified client-specific design preference from a reproducible problem worth fixing for all future customers.

A single serious bug, accessibility failure, broken contact form, lost content or security concern can justify immediate review even without many similar reports.

## Closed-loop improvements

Keep the actual customer records private, NOT in the public GitHub repository:
project_ref, verified_source_evidence, received_at, original_message_location,
category, reproduced_issue, impact, priority, human_owner, status, change_link,
next_review_date, customer_confirmation.

Track stages: received -> source verified or marked unverified -> triaged ->
approved for change -> implemented -> retested -> customer-confirmed.

Review feedback after each handover and in a weekly internal review. Address recurring issues by updating Kaurivo's Builder, quality checklist, tests and project handover process, not merely replying with "thanks." Before generalizing a preference, check that it applies to other clients; do not override distinctive brand identities. Owner approves production changes. No public GitHub issues containing raw customer messages or personal details.

## Privacy and publication

Demo review submissions use the site's existing third-party FormSubmit endpoint and follow its privacy notice. Recipient activation and delivery are NOT yet verified. Until activation, invite replies to the original Gmail message instead of advertising the page as fully operational.

Private feedback is not automatically a public testimonial or a license to disclose client details. A separately documented, informed authorization is needed before publishing a quote, company name or logo as endorsement. Store only needed data and follow legal privacy retention rules.

## Reuse in outreach

Once the form passes activation and end-to-end delivery checks, add its confirmed link below the actual QA-approved demo link and include the same form link in the email sending workflow. If not confirmed, use direct email reply. Do not add a fake review widget to fictional Kaurivo portfolio concepts or demand it in the middle of a sales pitch.

The Python helpers create drafts and suggested triage only. They do not read Gmail, schedule reminders, spend AI credits, send mail, publish testimonials or apply code changes.
