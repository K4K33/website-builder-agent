# Customer feedback: brand preservation and editable websites

Updated from first-hand feedback from an owner of an actual business shown a
Kaurivo redesign demo. The owner liked the layout but would not necessarily
approve changing company colors, photographs or slogans. They also asked
how the business could edit its own site after delivery.

## Default policy for **every** future client

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
6. Keep the original identity while improving mobile hierarchy, services,
   navigation, speed, forms and clarity. Large visual brand changes require
   explicit client signoff.
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

When a client wants to update text, headlines, services, hours, prices or
photos:

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

### Hand-off acceptance

- [ ] Client reviewed original identity, images and protected wording
- [ ] Desktop and mobile proposal retains approved assets/content
- [ ] Client approved any requested brand, photo or copy changes
- [ ] CMS is actually installed and access controlled (if sold)
- [ ] Client can edit one real text field and one real image
- [ ] Saved change shows up at published URL without code editing
- [ ] Permissions, backups and rollback tested
- [ ] Written responsibilities for maintenance and hosting agreed
- [ ] Final owner approval before public launch

This is a design & delivery policy, not an assertion that CMS support has
already been deployed to Kotifixi or another customer's site.
