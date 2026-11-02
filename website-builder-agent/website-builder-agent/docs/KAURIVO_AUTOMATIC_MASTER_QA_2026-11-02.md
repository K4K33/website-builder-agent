# KAURIVO — EVERY-WEBSITE AUTOMATIC QUALITY GATE
Date: 2026-11-02. Applies to ALL future companies and redesign revisions.

## Core contract

- Owner's universal feedback becomes a universal candidate **immediately**; a known
  recurring defect in QA is added to the local cross-company ledger automatically.
  If the same category affects 2 different companies, the Builder sees the
  cross-project problem in its next prompt. It is NOT falsely presented as fixed.
- A rule becomes "active" only when an appropriate tested checker exists;
  new unknown issues remain `needs_implementation` and block final QA approval.
  Client-specific tastes are local, never copied onto unrelated client brands.
- Every site is researched from its genuine old pages and at least three leading
  sites in the SAME industry. Industry references are design inspiration, never
  a cloned template or evidence of the target company's facts.
- Automatic detection is only one layer. Final quality is independently
  reviewed on the exact rendered build; a model's own claimed "9.5/10"
  cannot substitute for such evidence.

## QA matrix and evidence expectations

| Rule | Free automated verification | Evidence NOT automatically asserted |
| --- | --- | --- |
| Original source inventory | Same-site multi-page crawl, failed / important unvisited links flagged | True exhaustive coverage, dynamic/PDF subpages |
| 3 industry leaders | Three independently sourced benchmark URLs and desktop/mobile captures | Quality and artistic suitability of reference ideas |
| Original layout | Different-company DOM/style comparison; no recycled skeleton | Human comparison of overall visual DNA |
| Company identity | Verified original logo URL, lockable brand data | Actual logo license, customer brand approval |
| Sponsors and partners | Footer source logo/image and URLs inventoried; explicit required-assets manifest | Ongoing relationship, role and reuse rights |
| Contents & services | Compare verified services, phone, email, address and explicit source-backed requirements | Complete nuanced paraphrases and every changing fact; source snapshot reviewed |
| Copywriting | Decorative 01/02/03 and repeated AI phrases, contrast-pair boilerplate, fabricated review indicators | Full natural Finnish editorial quality |
| Prices, opening hours, menus | Original pages collected; explicit required fields matched | Current prices, legal/tax changes and all kitchen allergen details |
| Real references & media | Before–after widget requires verified original pair, no broken image loads | Image ownership, rights and whether photos belong to same job |
| Forms & CTAs | Link/anchor checks, no dead forms, aria controls and browser click behavior | Real backend lead received and secure handling |
| Accessibility | HTML structure, labels, reduced-motion check; browser WCAG AA contrast on solid colors | Color overlays and text over photography require visual review |
| Responsive | Offline screenshots 320/390/768/1440, overflow, JS errors, basic menu controls | Other devices and true field network performance |
| Performance/motion | Native scroll blocking, abnormal layout and broken assets | Physical touchpad smoothness and live web vitals |
| Production CMS | Evidence fields and existing client_handover gate | Successful client editor login, publish and rollback |
| Production release | Branded HTTPS, permissions, source and independent review recorded | Actual domain, signed-off material and lawful outreach proof |

The detailed universal registry has 18 categories in `utils/universal_quality.py`.
A category is **fail**, **pending**, or **no_static_defect** (which means
no static issue found, NOT an overall verified pass).

## Installed entry points

1. `utils.industry_workflow`: industry-specific visitor tasks and multi-page
   source evidence; no cross-industry visual template.
2. `utils.design_distinctness`: repeated-layout hard stop before Builder save.
3. `utils.content_parity`: verified source facts and pending full-inventory review.
4. `utils.universal_quality.audit_universal_standards`: all-site static
   standards + release-evidence status. Called by Builder on every regular
   build, imported external code response and revision, and by QA.
5. `utils.browser_qa.inspect_site`: offline Chromium checks, screenshots,
   solid-background measured WCAG contrast and blocked scrolling.
6. `utils.global_feedback`: writes identified QA categories and owner-wide
   feedback to the local global ledger; repeat patterns are fed into future
   Builder prompts. This is a **local** ledger, not a guarantee of cross-host
   durable cloud storage until synchronized to the Git repository or DB.
7. `agents.qa.run_qa`: retains content, browser, independent AI and universal
   evidence separately, logs repeated issues and blocks final QA acceptance
   when unresolved universal rules have no implementation or test.
8. `main.py pipeline --max-revisions 0..3`: bounded *optional* internal
   repair loops. Default 0 avoids automatic paid credit usage. Human source
   approval, rights and unknown rule implementation are NOT retryable via
   endless AI regeneration.

Free commands:
- `python main.py global-quality-issues`
- `python main.py learn-global-rule --text "An owner-approved general issue"`
- `python main.py learn-global-rule --text "Avoid decorative card numbering" --checker no_decorative_numbering --regression-test tests/test_design_distinctness.py`
- `python -m unittest discover -s tests -v`

The GitHub Actions workflow `.github/workflows/quality.yml` runs unit
tests and Chromium on pushes to main and pull requests. Presence of this
workflow alone does NOT prove any particular CI run passed: verify its
actual result before claiming it.

## Non-negotiable release statuses

`internal_demo`: an owner can review an honest labeled draft if automatic
checks find no defect; unsupported source and rights details remain explicit.

`client_release`: cannot pass unless all missing and pending evidence,
including editable CMS, real contact delivery, explicit client approval,
branded HTTPS and media/legal permissions, is verified.

No live customer outreach, purchases or paid browsing are triggered by
these offline checks. Future universal issues must be registered and
enforced for subsequent projects, but no untested self-generated code or
fabricated test success is permitted.
