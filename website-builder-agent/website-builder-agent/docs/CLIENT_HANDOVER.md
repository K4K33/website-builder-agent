# Customer feedback: brand preservation and editable websites

Updated from first-hand feedback from an owner of an actual business shown a
Kaurivo redesign demo. The owner liked the layout but would not necessarily
approve changing company colors, photographs or slogans. They also asked
how the business could edit its own site after delivery.

## Default policy for **every** future client

**A bold redesign does not require a rebrand.**

**Two distinct scenarios:**
- **New website:** Design a fully original, ambitious website from the ground
  up. If the business already has a real brand (logo, colors, voice) in other
  materials, carry that identity into the new website, with client approval.
  If there is no identity at all, propose a distinctive one for approval.
- **Existing website redesign:** Deliver a **major visible upgrade** in
  layout, hero, page architecture, typography, navigation, mobile experience,
  motion, services presentation and contact flow. The old layout is not
  protected. Keep the company's recognizable brand: its approved logo,
  palette, licensed real photos and protected slogans. The design should
  look new and higher quality while still unmistakably belonging to
  the same company.

Before showing the result to the customer, compare old and new screenshots:
it should be easy to see a substantial improvement beyond minor polishing,
without confusing customers about which business the site belongs to.

**Improve the website, not automatically the company's identity.**

1. Treat existing colors, logo, own photographs and recognizable messaging as
   client's brand assets, not as design flaws. Keep them by default.
2. Mark each important existing slogan, exact key passage and customer-selected
   image as **keep**, **propose an improvement**, or **client-authorized replace**.
3. Preserve the meaning and exact wording of slogans marked **keep**.
4. Never substitute competitor images, stock people presented as real staff,
   invented company photos or an AI illustration claimed to be a real job.
5. Do not take an existing site's images for reuse unless the client confirms
   permission/ownership and supplies assets or an authorized source. A public
   web image is not automatically licensed for reuse or rehosting.
6. Keep the original identity while comprehensively rebuilding layout,
   mobile hierarchy, hero, services, navigation, interaction, speed, forms
   and clarity. This should be a substantial redesign, not small adjustments.
   A brand identity change still requires explicit client signoff.
7. A demo is a **proposal**. The owner has the final say before production.

## Record the client's explicit choices

Add optional `client_preferences` data to a company record.
An example for testing (not actual Kotifixi consent):

```json
{
  "client_preferences": {
    "verified_with_client": true,
    "permission_to_rebrand": false,
    "permission_to_replace_photos": false,
    "existing_colors": ["#182B3A", "#EAE8E2"],
    "locked_copy": ["An example of wording the client explicitly wants kept"],
    "content_editing": "client_self_service"
  }
}
```

The above has **fictional choices and colors**; do not insert it as a real
client's preferences. An unverified client review results in conservative
default preservation and no strict copy lock. Only exact strings in the
client-reviewed `locked_copy` list cause a local build/revision validation
failure if the text is lost. HTML semantic source validation does not
automatically prove logo identity, color fidelity, asset rights or overall
brand quality. Those still require comparison screenshots and client approval.

## Editability after handover: real CMS required

The current Builder generates a standalone static `index.html` and **does not
have built-in login, CMS, content publishing or media upload**. Do not tell
prospects that they can self-edit an unchanged static demo through an admin
interface.

This is no longer optional. **Every future client site Kaurivo hands over
must be owner-editable by default**, including a company receiving its
first website and one whose existing site is redesigned. The client must
not need Kaurivo for routine text and photo changes. This does not mean
all layout, 3D scenes or code are exposed to nontechnical editors.

A pre-sales static HTML demo remains allowed while the customer reviews
the design. But **no final customer handover** without a working, secure,
tested CMS and the customer's own editing access.

For every customer, set up editable text, headlines, service information,
hours, prices where relevant, contact details and approved photos:

1. Agree on edit scope. Separate safe content fields from layout/CSS/animations.
2. Choose infrastructure together. A lightweight option for GitHub-backed
   static sites is Pages CMS, which provides editing UI and media management.
   Its workflow still needs GitHub repository permissions, proper content
   model, auth and a tested site build/deploy. Another choice is Decap CMS
   with its own configured authentication and editorial workflow.
   WordPress is a common choice when owners need a broader visual site editor
   and appropriate hosting/maintenance.
3. Move editable values to an appropriately structured content source;
   configure actual CMS fields, uploads and access. Protect layout and
   motion from accidental editing unless that freedom is an explicit goal.
4. Verify the owner's login, the change-preview-save-publish cycle,
   image updates, mobile rendering, rollback and backup. Agree who owns
   the domain, repository/hosting, updates and credentials.
5. Give the customer a simple short guide and demonstrate a real edit.
6. Separate one-time website creation pricing from optional hosting,
   maintenance and support; do not imply a paid tier is necessary until
   the client selects a delivery platform. Our developer test phase
   remains zero-paid-component when feasible.

Pages CMS documentation: https://pagescms.org/docs/
Decap CMS documentation: https://decapcms.org/docs/
WordPress roles and site editing: https://wordpress.org/documentation/article/roles-and-capabilities/

### Mandatory offline client handover gate

Run the zero-credit CLI audit before labelling a site delivered:

    python main.py handover-check COMPANY_SLUG

The company's delivery record must document actual verification
results: cms_platform, real HTTPS admin_url and published_url,
verified_by_human, verified_at, client_editor_login_tested,
text_edit_published_tested, image_edit_published_tested,
contact_edit_published_tested, mobile_layout_after_edit_tested,
backup_and_rollback_tested, client_owns_editor_access,
owner_guide_delivered, customer_acceptance, and the current
approved build_version and html_sha256.

**These are records of real human tests, not features automatically
implemented by this change.** The tool rejects incomplete or stale
handover records. It does not contact CMS providers, verify the truth of
checkboxes, or configure CMS and hosting.

### Hand-off acceptance

- [ ] Client reviewed original identity, images and protected wording
- [ ] Desktop and mobile proposal retains approved assets/content
- [ ] Client approved any requested brand, photo or copy changes
- [ ] CMS is actually installed and access controlled (mandatory for every client delivery)
- [ ] Client can edit one real text field and one real image
- [ ] Saved change shows up at published URL without code editing
- [ ] Permissions, backups and rollback tested
- [ ] Written responsibilities for maintenance and hosting agreed
- [ ] Final owner approval before public launch

This requirement applies to all **future** client deliveries.
It is not an assertion that CMS support has already been deployed to
Kotifixi or another demo. The current builder still produces static
index.html; real integration is required for each production site.


## Client's explicit demo must-haves

Record client wishes from the demo in the private project record; then review together: (1) must-have pages and features, (2) current logo, colours, photos and copy to keep, (3) optional ideas, (4) CMS/editor requirements, (5) scope, budget and timeline, (6) open questions. Only client-confirmed requirements become binding. Never mistake a response to an initial sales demo for permission to rebrand, publish comments or start paid work. Do not put personal customer details or raw correspondence into GitHub. See CUSTOMER_FEEDBACK.md.
