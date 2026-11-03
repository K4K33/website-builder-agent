"""
Website Builder Agent

Pääohjelma, jonka kautta eri agentteja voidaan ajaa.

Pipeline:
Scout → Research → Build → QA

Outreach vaatii erillisen käyttäjän hyväksynnän.
"""

import argparse
import config
import os
import json
from pathlib import Path

from agents import scout
from agents import research
from agents import builder
from agents import qa
from agents import outreach

from utils import publisher
from utils.production_readiness import readiness_report
from utils.client_handover import inspect_client_delivery
from utils.kaurivo_premium_site import inspect_site_file
from utils.kaurivo_premium_sales import (
    demo_improvement_packet, agreement_gate, delivery_gate, funnel_metrics,
)
from utils.pitch_quality import assess_pitch_packet
from utils.lead_intelligence import evaluate_prospect, site_signal
from utils.company_registry import lookup_by_business_id, lookup_by_name_and_location
from utils.free_enrichment import enrich_queue
from utils.verified_profile import validate_verified_profile
from utils.lead_queue import rank_leads
from utils.human_review_queue import shortlist as build_review_shortlist, record_decision, format_markdown
from utils.prh_statement_inspector import inspect_latest_statement
from utils.state import get_company, upsert_company

from utils.state import (
    load_companies,
)


# =========================================================
# EXPLICIT CONSENT FOR COMMANDS THAT MAY USE PAID AI
# =========================================================

def _require_paid_consent(args):
    # A loopback-only local model needs no paid-model authorization.
    # External search APIs (if any) remain independently quota-limited.
    if config.ai_backend() == "ollama":
        return
    if not getattr(args, "confirm_paid_apis", False):
        raise RuntimeError(
            "This command may consume paid AI/search credits. "
            "Pass --confirm-paid-apis only after checking provider spending caps."
        )


# =========================================================
# SCOUT
# =========================================================

def cmd_scout(args):
    if not (args.dry_run or getattr(args, "discovery_only", False)):
        _require_paid_consent(args)
    print(f"[Scout] Etsitään {args.count} yritystä...")

    results = scout.run_scout(
        count=args.count,
        industry=args.industry,
        location=args.location,
        dry_run=args.dry_run,
        discovery_only=getattr(args, "discovery_only", False),
    )

    if not results:
        print(
            "Ei löytynyt uusia yrityksiä "
            "(tai kaikki löydetyt olivat jo pidemmällä)."
        )
        return

    print()
    print(f"[Scout] Käsitelty {len(results)} yritystä.")

    if args.dry_run:
        print(
            "[Scout] DRY-RUN: mitään yrityksiä ei tallennettu."
        )


# =========================================================
# LIST
# =========================================================

def cmd_list(args):
    companies = load_companies()

    if not companies:
        print("Yrityksiä ei ole vielä tallennettu.")
        return

    print()
    print("=== YRITYKSET ===")

    for slug, company in companies.items():
        print(
            f"{slug} | "
            f"{company.get('name', '')} | "
            f"{company.get('status', '')} | "
            f"{company.get('url', '')}"
        )


# =========================================================
# ADD
# =========================================================

def cmd_add(args):
    companies = load_companies()

    from utils.state import make_slug, save_companies

    slug = make_slug(args.name)

    companies[slug] = {
        "name": args.name,
        "url": args.url,
        "status": "found",
    }

    save_companies(companies)

    print(
        f"Lisätty: {args.name} ({slug})"
    )


# =========================================================
# RESEARCH
# =========================================================

def cmd_research(args):
    _require_paid_consent(args)
    research.run_research(args.company)


# =========================================================
# BUILD
# =========================================================

def cmd_build(args):
    _require_paid_consent(args)
    builder.run_build(args.company)


def cmd_complete_build(args):
    print(builder.run_build_from_response(args.company, args.response, args.producer))


# =========================================================
# REVISE
# =========================================================

def cmd_revise(args):
    _require_paid_consent(args)
    builder.run_revise(
        args.company,
        args.instructions,
    )


# =========================================================
# QA
# =========================================================

def cmd_learn_global_rule(args):
    """Record owner-wide feedback for all subsequent clients without AI calls."""
    from utils.global_feedback import (
        load_ledger, save_ledger, record_owner_feedback,
        universal_rules_pending_implementation,
    )
    ledger_path = Path(config.OUTPUT_DIR) / "_kaurivo_global_quality.json"
    ledger = load_ledger(ledger_path)
    result = record_owner_feedback(
        ledger, text=args.text, applies_to_all=True,
        checker=args.checker, regression_test=args.regression_test
    )
    save_ledger(ledger_path, ledger)
    print(json.dumps({
        "feedback": result,
        "pending_checker": universal_rules_pending_implementation(ledger),
        "note": "Local QA ledger updated. Changes to code/checkers must be "
                "tested and committed for durable deployment.",
    }, ensure_ascii=False, indent=2))


def cmd_global_quality_issues(args):
    """Inspect cross-project QA problems without any paid service."""
    from utils.global_feedback import load_ledger
    ledger_path = Path(config.OUTPUT_DIR) / "_kaurivo_global_quality.json"
    print(json.dumps(load_ledger(ledger_path), ensure_ascii=False, indent=2))


def cmd_qa(args):
    _require_paid_consent(args)
    qa.run_qa(args.company)



def cmd_visual_evidence(args):
    """No paid AI: original/new browser screenshot pairs and repair report."""
    from utils.screenshot import capture_website
    from utils.browser_qa import inspect_site
    from utils.visual_comparison import build_visual_comparison

    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Company not found: " + str(args.company))
    research_data = dict(company.get("research") or {})
    build = company.get("build") or {}
    output_path = build.get("output_path")
    if not output_path or not Path(output_path).is_file():
        raise RuntimeError("Build this site before requesting visual evidence.")
    root = Path(output_path).resolve().parent
    routes = build.get("page_paths") or ["index.html"]
    pages = {}
    for route in routes:
        file = (root / route).resolve()
        if not file.is_relative_to(root) or not file.is_file():
            raise RuntimeError("Missing or unsafe site route: " + str(route))
        pages[route] = file.read_text(encoding="utf-8")
    if args.refresh_original:
        source_url = company.get("url") or ""
        if not (research_data.get("source_inventory") or {}).get("pages"):
            raise RuntimeError("This company has no researched original website.")
        captured = capture_website(source_url, "original-client-" + slug)
        if not captured:
            raise RuntimeError("Original site could not be captured; no fake comparison generated.")
        research_data["original_screenshots"] = captured
        upsert_company(slug, {"research": research_data})
    new_browser = inspect_site(root / "index.html")
    report = build_visual_comparison(
        research_data.get("original_screenshots"), new_browser, pages,
        research_data, report_dir=Path(config.OUTPUT_DIR)/"_visual_reports"/slug,
    )
    print(json.dumps({
        "status": report["status"],
        "comparison_html": report["comparison_html"],
        "manifest": report["report_path"],
        "pairs": list(report["pairs"]),
        "repair_hints": report["repair_hints"],
        "missing": report["missing"],
        "render_errors": report["render_errors"],
        "browser_issues": new_browser.get("issues") or [],
        "note": "Offline evidence, NOT client approval or an independent 9.5 score.",
    }, ensure_ascii=False, indent=2))


# =========================================================
# PREVIEW
# =========================================================

def cmd_preview(args):
    builder.run_preview(args.company)


# =========================================================
# PUBLISH
# =========================================================

def cmd_publish(args):
    publisher.run_publish(args.company)


# =========================================================
# APPROVE WEBSITE
# =========================================================

def cmd_approve(args):
    qa.approve_company(args.company)


# =========================================================
# OUTREACH
# =========================================================

def cmd_outreach(args):
    _require_paid_consent(args)
    outreach.run_outreach(args.company)


# =========================================================
# APPROVE OUTREACH
# =========================================================

def cmd_approve_outreach(args):
    outreach.approve_outreach(args.company)


# =========================================================
# SHOW
# =========================================================

def cmd_show(args):
    companies = load_companies()

    company = companies.get(args.company)

    if not company:
        print(
            f"Yritystä ei löytynyt: {args.company}"
        )
        return

    print()
    print("=== YRITYS ===")

    for key, value in company.items():
        print(f"{key}: {value}")


# =========================================================
# OFFLINE PRODUCTION-READINESS AUDIT
# =========================================================

def cmd_readiness(args):
    report = readiness_report(load_companies(), min_industries=args.min_industries)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not report["ready_for_review"]:
        raise RuntimeError("Production evidence gate failed: the live multi-industry benchmark is incomplete.")


# =========================================================
# CUSTOMER DELIVERY AUDIT: MUST HAVE TESTED SELF-EDITABLE CMS
# =========================================================
def cmd_handover_check(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Company not found.")
    result = inspect_client_delivery(company)
    print(json.dumps({"company": slug, **result}, ensure_ascii=False, indent=2))
    if not result["ready_to_handover"]:
        raise RuntimeError(
            "Client delivery BLOCKED: CMS self-editing is not proven. "
            "A website demo can still be reviewed without this check."
        )


# =========================================================
# PREMIUM CLIENT QUALITY — OFFLINE, NO PAID CREDITS OR CUSTOMER MESSAGES
# =========================================================

def cmd_premium_site_audit(args):
    result = inspect_site_file(args.html, site_root=args.root, production=args.production)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["pass"]:
        raise RuntimeError("Premium static preflight BLOCKED. Fix listed errors.")


def cmd_demo_evidence(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Lead not found.")
    packet = demo_improvement_packet(company)
    print(json.dumps({"company_slug": slug, **packet}, ensure_ascii=False, indent=2))
    if not packet["ready_for_human_sales_review"]:
        raise RuntimeError("Demo evidence incomplete; never send an unverified comparison.")


def cmd_premium_pitch_gate(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Lead not found.")
    packet = assess_pitch_packet(company)
    print(json.dumps({"company_slug": slug, **packet}, ensure_ascii=False, indent=2))
    if not packet["premium_demo_ready_for_outreach_review"]:
        raise RuntimeError("Premium demo pitch is not approved; do not contact the customer.")


def cmd_project_terms(args):
    terms = json.loads(Path(args.file).read_text(encoding="utf-8"))
    result = agreement_gate(terms)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ready_to_start_work"]:
        raise RuntimeError("Project terms incomplete; do not start paid customer work.")


def cmd_delivery_preflight(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Customer not found.")
    site = inspect_site_file(args.html, site_root=args.root, production=True)
    result = delivery_gate(company, site)
    print(json.dumps({"company_slug": slug, "site": site, **result}, ensure_ascii=False, indent=2))
    if not result["ready_to_deliver"]:
        raise RuntimeError("Client delivery blocked; live CMS and quality not proven.")


def cmd_sales_funnel(args):
    print(json.dumps(funnel_metrics(load_companies()), ensure_ascii=False, indent=2))


# =========================================================
# BUSINESS INTELLIGENCE / LEAD SCREENING
# =========================================================

def cmd_screen_lead(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Lead not found; run Scout first.")
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    if not isinstance(evidence, dict) or not any(
        item in evidence for item in ("reputation", "financials", "site_verification", "operational_scale", "activity_evidence")
    ):
        raise ValueError("Evidence must include reputation, financials or site_verification.")
    updates = {}
    for key in ("reputation", "financials", "site_verification", "operational_scale", "activity_evidence"):
        if key in evidence:
            value = evidence[key]
            if not isinstance(value, dict):
                raise ValueError("Evidence section must be an object: " + key)
            if key == "financials":
                known_id = company.get("business_id", "")
                provided_id = value.get("business_id", "")
                if not provided_id or (known_id and known_id != provided_id):
                    raise ValueError("Financial evidence must match the selected business ID.")
            updates[key] = value
    refreshed = {**company, **updates}
    updates["lead_intelligence"] = evaluate_prospect(refreshed, args.project_price)
    upsert_company(slug, updates)
    print(json.dumps(updates["lead_intelligence"], ensure_ascii=False, indent=2))
    if updates["lead_intelligence"]["outreach_gate"] != "priority_for_human_review":
        print("Lead remains in verification queue; no outreach permitted.")


def cmd_verify_registry(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Lead not found; run Scout first.")
    business_id = args.business_id or company.get("business_id", "")
    if business_id:
        official = lookup_by_business_id(business_id)
    else:
        city = getattr(args, "city", "") or company.get("city", "")
        official = lookup_by_name_and_location(company.get("name", ""), city)
        business_id = official["business_id"]
    official_names = [name.strip().casefold() for name in official["official_names"]]
    display_name = company.get("name", "").strip().casefold()
    # If a trading name differs from the legal business name, don't join
    # unrelated companies automatically based on a bare OSM tag.
    if not getattr(args, "confirm_name_mismatch", False) and display_name not in official_names:
        raise RuntimeError("PRH business name does not exactly match; confirm identity manually first.")
    # A free official business-ID lookup does not contain revenue or profit.
    # Do not mark an unknown business as financially qualified.
    financials = dict(company.get("financials") or {})
    if financials.get("business_id") and financials["business_id"] != business_id:
        raise ValueError("Stored financial identity conflicts with official PRH ID.")
    financials.update({
        "business_id": business_id,
        "business_id_verified": True,
        "registry_source_url": official["registry_source_url"],
    })
    if official["registration_ended"]:
        financials["legal_status"] = "ended"
    # PRH situation codes: KONK bankruptcy, SELTILA liquidation, SANE restructuring.
    current_situations = [
        item for item in official.get("company_situations", [])
        if isinstance(item, dict) and item.get("type") in {"KONK", "SELTILA", "SANE"}
        and not item.get("endDate")
    ]
    if current_situations:
        financials["insolvency_proceeding"] = True
    updates = {"business_id": business_id, "financials": financials,
               "registry_evidence": official}
    if official.get("official_website") and not company.get("website"):
        updates["website"] = official["official_website"]
        updates["url"] = official["official_website"]
        updates["lead_type"] = "redesign_candidate"
        updates["status"] = "found"
    updates["lead_intelligence"] = evaluate_prospect({**company, **updates})
    upsert_company(slug, updates)
    print(json.dumps(updates["lead_intelligence"], ensure_ascii=False, indent=2))


# =========================================================
# LEAD TRIAGE (OFFLINE, NO AI CREDITS)
# =========================================================

def cmd_leads(args):
    rows = rank_leads(load_companies(), estimated_project_eur=args.project_price)
    print(json.dumps(rows[:args.limit], ensure_ascii=False, indent=2))
    if not rows:
        print("No saved leads; run scout --discovery-only first.")


# =========================================================
# HUMAN REVIEW HANDOFF (no AI, mail or network operations)
# =========================================================

def cmd_shortlist(args):
    rows = build_review_shortlist(load_companies(), limit=args.limit,
                                  include_reviewed=args.include_reviewed)
    if args.format == "markdown":
        print(format_markdown(rows))
    else:
        print(json.dumps(rows, ensure_ascii=False, indent=2))


def cmd_review_lead(args):
    result = record_decision(args.company, args.decision, args.note)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print("No demo built, no company contacted. Selection is not website/activity verification.")


# =========================================================
# TAXONOMY-REVIEW INVENTORY FROM ONE OFFICIAL PRH STATEMENT
# =========================================================

def cmd_inspect_financial(args):
    if not args.confirm_public_lookups:
        raise RuntimeError("PRH XML statement lookup requires --confirm-public-lookups.")
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Company is missing from the saved lead queue.")
    report = inspect_latest_statement(company)
    # Safe metadata only: never copy unsupported raw numbers into financials.
    upsert_company(slug, {"financial_statement_review": report})
    summary = {**report, "fact_candidates": report["fact_candidates"][:args.limit]}
    print(json.dumps(summary, indent=2, ensure_ascii=False))


# =========================================================
# PRH FREE-SOURCE ENRICHMENT / VERIFIED NO-WEBSITE FACTS
# =========================================================

def cmd_enrich_free(args):
    if not args.confirm_public_lookups:
        raise RuntimeError("External PRH lookups require --confirm-public-lookups.")
    results = enrich_queue(
        max_companies=args.max_companies,
        pause_seconds=args.pause_seconds,
        company_slug=args.company or None,
    )
    print(json.dumps(results, indent=2, ensure_ascii=False))


def cmd_attach_profile(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Lead not found; run Scout first.")
    data = json.loads(Path(args.profile).read_text(encoding="utf-8"))
    result = validate_verified_profile(company, data)
    upsert_company(slug, {"company_profile": data})
    print("Verified no-website profile attached:", slug, result["facts"]["industry"])
    print("No AI requests were made. Research/build still require explicit authorization.")


# =========================================================
# PIPELINE
# =========================================================

def cmd_pipeline(args):
    if not getattr(args, "confirm_live_run", False):
        raise RuntimeError("Live pipeline requires --confirm-live-run to authorize external API calls.")
    # Resolve all required models before discovery can spend API requests.
    config.model_for_stage("builder")
    config.model_for_stage("qa")
    keys = ["TAVILY_API_KEY"]
    if config.ai_backend() == "openrouter":
        keys.append("OPENROUTER_API_KEY")
    for key in keys:
        if not os.getenv(key) and not getattr(config, key, ""):
            raise RuntimeError(f"{key} puuttuu. Pipelinea ei käynnistetty.")

    print()
    print("========================================")
    print(" WEBSITE BUILDER AGENT - PIPELINE")
    print("========================================")

    print()
    print("Vaiheet:")
    print("1. Scout")
    print("2. Research")
    print("3. Build")
    print("4. QA")
    print()

    # -----------------------------------------------------
    # SCOUT
    # -----------------------------------------------------

    print("========================================")
    print(" VAIHE 1/4 — SCOUT")
    print("========================================")

    if getattr(args, "company", ""):
        slug, found = get_company(args.company)
        if found is None:
            raise RuntimeError("Selected company was not found in the saved lead queue.")
        results = [{"slug": slug}]
    else:
        results = scout.run_scout(
            count=args.count,
            industry=args.industry,
            location=args.location,
            dry_run=False,
            commercial_only=not getattr(args, "benchmark_mode", False),
        )

    if not results:
        raise RuntimeError("No prequalified lead found. Use discovery-only and verify active operations first.")

    # -----------------------------------------------------
    # SELECT COMPANY
    # -----------------------------------------------------

    companies = load_companies()

    selected_slug = None
    selected_company = None

    # Blind quality trials must not repeatedly pick the first already-tested
    # lead in the queue. Search returned candidates for a previously unseen
    # identity. Real customer jobs are not subject to this experimental rule.
    seen_trials = []
    if getattr(args, "benchmark_mode", False):
        from utils.blind_trials import trial_history, assess_new_company
        seen_trials = trial_history(
            Path(__file__).resolve().parent / "docs" /
                "KAURIVO_HISTORICAL_DEMO_TRIALS.json",
            Path(config.OUTPUT_DIR) / "_kaurivo_unseen_trials.json",
        )
    for result in results:
        candidate_slug = result.get("slug")
        if candidate_slug not in companies:
            continue
        candidate = companies[candidate_slug]
        if (getattr(args, "benchmark_mode", False)
                and not assess_new_company(candidate, slug=candidate_slug,
                                           history=seen_trials)["eligible"]):
            continue
        selected_slug = candidate_slug
        selected_company = candidate
        break

    if selected_company is None:
        raise RuntimeError("Scout returned no company with a saved record.")
    if getattr(args, "benchmark_mode", False):
        # Only unseen companies are eligible for first-pass creative trials.
        # No same-client V2/V3 retuning to make a score look artificially good.
        if int(getattr(args, "max_revisions", 0) or 0) != 0:
            raise RuntimeError("Blind design benchmark allows zero same-company revision rounds.")
        from utils.blind_trials import reserve_blind_trial
        trial = reserve_blind_trial(
            selected_company, slug=selected_slug,
            history_path=Path(__file__).resolve().parent /
                         "docs" / "KAURIVO_HISTORICAL_DEMO_TRIALS.json",
            registry_path=Path(config.OUTPUT_DIR) / "_kaurivo_unseen_trials.json",
        )
        print("Reserved one unseen first-pass company: "
              + (trial.get("url") or trial.get("slug") or selected_slug))
    website_state = site_signal(selected_company)
    intelligence = evaluate_prospect(selected_company)
    if website_state != "has_website":
        # A confirmed site-less company can be built from a manually reviewed,
        # source-backed profile; unknown OSM website listings are still blocked.
        if website_state != "confirmed_no_website":
            raise RuntimeError("No-site lead needs independent website and business verification.")
        validate_verified_profile(selected_company)
        # Star ratings and multiple locations are OPTIONAL, not requirements.
    activity = intelligence["business_activity"]["status"]
    if activity == "inactive":
        raise RuntimeError("Inactive company is excluded from commercial builds.")
    if activity != "active" and not getattr(args, "benchmark_mode", False):
        raise RuntimeError(
            "Active business operations must be independently verified before commercial building. "
            "Add recent, source-checked activity_evidence through screen-lead."
        )
    capacity = intelligence["purchase_capacity"]
    # The score ranks opportunities only. For a confirmed active business,
    # ratings, revenue, profit, staff count and locations are never mandatory.
    print(f"[Pipeline] Indicative sales priority {capacity['score']}/100 "
          f"({capacity['status']}; NOT verified ability to pay).")

    print()
    print("Pipeline valitsi yrityksen:")

    print(
        f"  Nimi: {selected_company.get('name', '')}"
    )

    print(
        f"  Slug: {selected_slug}"
    )

    print(
        f"  URL: {selected_company.get('url', '')}"
    )

    # -----------------------------------------------------
    # RESEARCH
    # -----------------------------------------------------

    print()
    print("========================================")
    print(" VAIHE 2/4 — RESEARCH")
    print("========================================")

    research.run_research(selected_slug)

    # -----------------------------------------------------
    # BUILD
    # -----------------------------------------------------

    print()
    print("========================================")
    print(" VAIHE 3/4 — BUILD")
    print("========================================")

    builder.run_build(selected_slug)

    # -----------------------------------------------------
    # QA
    # -----------------------------------------------------

    print()
    print("========================================")
    print(" VAIHE 4/4 — QA")
    print("========================================")

    qa_result = qa.run_qa(selected_slug)
    if getattr(args, "benchmark_mode", False):
        from utils.blind_trials import record_first_pass_qa
        first_pass = record_first_pass_qa(
            Path(config.OUTPUT_DIR) / "_kaurivo_unseen_trials.json",
            slug=selected_slug, qa_report=qa_result
        )
        print("[Blind benchmark] First-pass result recorded; independent 9.5 score NOT verified.")
        print(json.dumps(first_pass,ensure_ascii=False))
    # All model retries are opt-in and capped by --max-revisions. A missing
    # original screenshot, owner approval or media licence is NOT a rewrite task.
    from utils.visual_revision import decide_revision
    seen_issue_signatures = set()
    for attempt in range(args.max_revisions):
        plan = decide_revision(qa_result, seen_issue_signatures)
        if not plan["revise"]:
            print("[Pipeline] No further paid revisions: " + plan["reason"])
            break
        seen_issue_signatures.add(plan["signature"])
        print(f"[Pipeline] Evidence-backed revision {attempt + 1}/{args.max_revisions}")
        builder.run_revise(
            selected_slug, json.dumps(plan["feedback"], ensure_ascii=False)
        )
        qa_result = qa.run_qa(selected_slug)

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    print()
    print("========================================")
    print(" PIPELINE VALMIS")
    print("========================================")

    print()
    print(
        f"Yritys: {selected_company.get('name', '')}"
    )

    print(
        f"Slug: {selected_slug}"
    )

    print(
        "QA: "
        + (
            "PASS"
            if qa_result.get("overall_pass", False)
            else "FAIL"
        )
    )

    print()

    if qa_result.get("overall_pass", False):

        print("Sivusto läpäisi QA:n.")
        print("Sivustoa EI ole vielä hyväksytty.")
        print("Outreachia EI ole luotu.")
        print("Mitään sähköpostia EI ole lähetetty.")
        print()
        print(
            "Seuraava vaihe on tarkistaa rakennettu sivusto."
        )

    else:

        print("Sivusto EI läpäissyt QA:ta.")
        print("Pipeline pysähtyy tähän.")
        print("Outreachia ei luoda.")
        raise RuntimeError("Pipeline failed QA; live run is not a successful build.")


# =========================================================
# ARGUMENT PARSER
# =========================================================

def build_parser():

    parser = argparse.ArgumentParser(
        description="Website Builder Agent"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # Final client-site delivery is not allowed until self-editing is verified.
    # This offline check does not publish or spend any API credits.
    handover = subparsers.add_parser(
        "handover-check",
        help="Block client delivery until CMS login, content edits and publishing are verified.",
    )
    handover.add_argument("company", help="Company name or slug")
    handover.set_defaults(func=cmd_handover_check)

    # Premium gates use only local files, never paid APIs or customer email.
    premium = subparsers.add_parser("premium-audit", help="Static HTML, SEO, accessibility and links preflight.")
    premium.add_argument("--html", required=True, help="Path to index.html.")
    premium.add_argument("--root", default=None, help="Site root containing local images/styles/pages.")
    premium.add_argument("--production", action="store_true", help="Block noindex.")
    premium.set_defaults(func=cmd_premium_site_audit)

    demo = subparsers.add_parser("demo-evidence", help="3 genuine before/after opportunities and industry references.")
    demo.add_argument("company")
    demo.set_defaults(func=cmd_demo_evidence)

    pitch = subparsers.add_parser("premium-pitch-check", help="Existing rendered demo approval gate.")
    pitch.add_argument("company")
    pitch.set_defaults(func=cmd_premium_pitch_gate)

    terms = subparsers.add_parser("project-terms", help="Check a local versioned project agreement checklist.")
    terms.add_argument("--file", required=True)
    terms.set_defaults(func=cmd_project_terms)

    delivery = subparsers.add_parser("delivery-preflight", help="Production site + real client CMS evidence.")
    delivery.add_argument("company")
    delivery.add_argument("--html", required=True)
    delivery.add_argument("--root", default=None)
    delivery.set_defaults(func=cmd_delivery_preflight)

    funnel = subparsers.add_parser("sales-funnel", help="Local aggregate counts; no public prospect data.")
    funnel.set_defaults(func=cmd_sales_funnel)

    # -----------------------------------------------------
    # LIST
    # -----------------------------------------------------

    parser_list = subparsers.add_parser(
        "list",
        help="Näytä tallennetut yritykset.",
    )

    parser_list.set_defaults(func=cmd_list)

    # -----------------------------------------------------
    # ADD
    # -----------------------------------------------------

    parser_add = subparsers.add_parser(
        "add",
        help="Lisää yritys käsin.",
    )

    parser_add.add_argument(
        "--name",
        required=True,
    )

    parser_add.add_argument(
        "--url",
        required=True,
    )

    parser_add.set_defaults(func=cmd_add)

    # -----------------------------------------------------
    # SCOUT
    # -----------------------------------------------------

    parser_scout = subparsers.add_parser(
        "scout",
        help="Etsi yrityksiä.",
    )

    parser_scout.add_argument(
        "--count",
        type=int,
        default=10,
    )

    parser_scout.add_argument(
        "--industry",
        default="",
    )

    parser_scout.add_argument(
        "--location",
        default="",
    )

    parser_scout.add_argument(
        "--dry-run",
        action="store_true",
        help=(
            "Testaa hakua ja verkkosivuja "
            "ilman OpenRouter-kutsua."
        ),
    )

    parser_scout.add_argument(
        "--discovery-only", action="store_true",
        help="Save unscreened website/no-website leads with zero AI, screenshots or Tavily calls.",
    )
    parser_scout.add_argument("--confirm-paid-apis", action="store_true",
        help="Explicitly authorize paid AI/search provider calls.")
    parser_scout.set_defaults(func=cmd_scout)

    # -----------------------------------------------------
    # RESEARCH
    # -----------------------------------------------------

    parser_research = subparsers.add_parser(
        "research",
        help="Tutki yritystä.",
    )

    parser_research.add_argument(
        "company"
    )

    parser_research.add_argument("--confirm-paid-apis", action="store_true",
        help="Explicitly authorize paid AI/search provider calls.")
    parser_research.set_defaults(func=cmd_research)

    # -----------------------------------------------------
    # BUILD
    # -----------------------------------------------------

    parser_build = subparsers.add_parser(
        "build",
        help="Rakenna verkkosivusto.",
    )

    parser_build.add_argument(
        "company"
    )

    parser_build.add_argument("--confirm-paid-apis", action="store_true",
        help="Explicitly authorize paid AI/search provider calls.")
    parser_build.set_defaults(func=cmd_build)

    parser_complete = subparsers.add_parser(
        "complete-build", help="Validate and import an external coding agent response without API calls."
    )
    parser_complete.add_argument("company")
    parser_complete.add_argument("--response", required=True)
    parser_complete.add_argument("--producer", required=True)
    parser_complete.set_defaults(func=cmd_complete_build)

    # -----------------------------------------------------
    # REVISE
    # -----------------------------------------------------

    parser_revise = subparsers.add_parser(
        "revise",
        help="Muokkaa rakennettua verkkosivustoa.",
    )

    parser_revise.add_argument(
        "company"
    )

    parser_revise.add_argument(
        "instructions"
    )

    parser_revise.add_argument("--confirm-paid-apis", action="store_true",
        help="Explicitly authorize paid AI/search provider calls.")
    parser_revise.set_defaults(func=cmd_revise)

    # -----------------------------------------------------
    # QA
    # -----------------------------------------------------

    parser_learn = subparsers.add_parser(
        "learn-global-rule",
        help="Register general owner feedback for all Kaurivo customer sites.",
    )
    parser_learn.add_argument("--text", required=True)
    parser_learn.add_argument("--checker", default="")
    parser_learn.add_argument("--regression-test", default="")
    parser_learn.set_defaults(func=cmd_learn_global_rule)

    parser_issues = subparsers.add_parser(
        "global-quality-issues",
        help="Show recurring QA problems and universal feedback (free, offline).",
    )
    parser_issues.set_defaults(func=cmd_global_quality_issues)

    parser_qa = subparsers.add_parser(
        "qa",
        help="Tarkista verkkosivusto.",
    )

    parser_qa.add_argument(
        "company"
    )

    parser_qa.add_argument("--confirm-paid-apis", action="store_true",
        help="Explicitly authorize paid AI/search provider calls.")
    parser_qa.set_defaults(func=cmd_qa)

    visual_evidence = subparsers.add_parser(
        "visual-evidence",
        help="FREE local original/new paired screenshots and repair candidates; no AI calls.",
    )
    visual_evidence.add_argument("company")
    visual_evidence.add_argument(
        "--refresh-original", action="store_true",
        help="Capture a fresh original-company website at 320,390,768,1440 (browser only).",
    )
    visual_evidence.set_defaults(func=cmd_visual_evidence)

    # -----------------------------------------------------
    # PREVIEW
    # -----------------------------------------------------

    parser_preview = subparsers.add_parser(
        "preview",
        help="Näytä verkkosivuston esikatselu.",
    )

    parser_preview.add_argument(
        "company"
    )

    parser_preview.set_defaults(func=cmd_preview)

    # -----------------------------------------------------
    # PUBLISH
    # -----------------------------------------------------

    parser_publish = subparsers.add_parser(
        "publish",
        help="Julkaise verkkosivuston demo.",
    )

    parser_publish.add_argument(
        "company"
    )

    parser_publish.set_defaults(func=cmd_publish)

    # -----------------------------------------------------
    # APPROVE
    # -----------------------------------------------------

    parser_approve = subparsers.add_parser(
        "approve",
        help="Hyväksy yrityksen verkkosivusto.",
    )

    parser_approve.add_argument(
        "company"
    )

    parser_approve.set_defaults(func=cmd_approve)

    # -----------------------------------------------------
    # OUTREACH
    # -----------------------------------------------------

    parser_outreach = subparsers.add_parser(
        "outreach",
        help="Luo yhteydenottoluonnos.",
    )

    parser_outreach.add_argument(
        "company"
    )

    parser_outreach.add_argument("--confirm-paid-apis", action="store_true",
        help="Explicitly authorize paid AI/search provider calls.")
    parser_outreach.set_defaults(func=cmd_outreach)

    # -----------------------------------------------------
    # APPROVE OUTREACH
    # -----------------------------------------------------

    parser_approve_outreach = subparsers.add_parser(
        "approve-outreach",
        help="Hyväksy yhteydenottoluonnos.",
    )

    parser_approve_outreach.add_argument(
        "company"
    )

    parser_approve_outreach.set_defaults(
        func=cmd_approve_outreach
    )

    # -----------------------------------------------------
    # SHOW
    # -----------------------------------------------------

    parser_show = subparsers.add_parser(
        "show",
        help="Näytä yrityksen tiedot.",
    )

    parser_show.add_argument(
        "company"
    )

    parser_show.set_defaults(func=cmd_show)

    # -----------------------------------------------------
    # READINESS (offline evidence audit)
    # -----------------------------------------------------

    parser_readiness = subparsers.add_parser(
        "readiness", help="Audit live multi-industry evidence without any API requests."
    )
    parser_readiness.add_argument("--min-industries", type=int, default=3)
    parser_readiness.set_defaults(func=cmd_readiness)

    # -----------------------------------------------------
    # BUSINESS INTELLIGENCE
    # -----------------------------------------------------

    parser_screen = subparsers.add_parser(
        "screen-lead", help="Attach independently verified review/financial evidence, offline."
    )
    parser_screen.add_argument("company")
    parser_screen.add_argument("--evidence", required=True)
    parser_screen.add_argument("--project-price", type=float, default=1500)
    parser_screen.set_defaults(func=cmd_screen_lead)

    parser_registry = subparsers.add_parser(
        "verify-registry", help="Perform explicit free PRH business-ID lookup (no AI credits)."
    )
    parser_registry.add_argument("company")
    parser_registry.add_argument("--business-id", default="")
    parser_registry.add_argument("--city", default="", help="Only needed when the saved lead has no city.")
    parser_registry.add_argument("--confirm-name-mismatch", action="store_true",
        help="Explicitly confirm a trading-name/legal-name difference after checking the identity.")
    parser_registry.set_defaults(func=cmd_verify_registry)

    parser_leads = subparsers.add_parser(
        "leads", help="Rank verified/unverified prospects without external API calls."
    )
    parser_leads.add_argument("--project-price", type=float, default=1500.0)
    parser_leads.add_argument("--limit", type=int, default=30)
    parser_leads.set_defaults(func=cmd_leads)

    parser_shortlist = subparsers.add_parser(
        "shortlist",
        help="Prepare a compact company-review batch, no AI or outside requests."
    )
    parser_shortlist.add_argument("--limit", type=int, default=10)
    parser_shortlist.add_argument("--format", choices=("json", "markdown"), default="markdown")
    parser_shortlist.add_argument("--include-reviewed", action="store_true")
    parser_shortlist.set_defaults(func=cmd_shortlist)

    parser_review = subparsers.add_parser(
        "review-lead",
        help="Record human choice: select, later, skip. Does NOT build or send."
    )
    parser_review.add_argument("company")
    parser_review.add_argument("--decision", choices=("select", "later", "skip"), required=True)
    parser_review.add_argument("--note", default="", help="Optional short human note.")
    parser_review.set_defaults(func=cmd_review_lead)

    parser_fin_statement = subparsers.add_parser(
        "inspect-financial",
        help="Inspect one saved PRH digital statement's raw taxonomy facts; NEVER auto-qualify finance."
    )
    parser_fin_statement.add_argument("company")
    parser_fin_statement.add_argument("--limit", type=int, default=15, choices=range(1, 81))
    parser_fin_statement.add_argument("--confirm-public-lookups", action="store_true")
    parser_fin_statement.set_defaults(func=cmd_inspect_financial)

    # -----------------------------------------------------
    # FREE PRH ENRICHMENT
    # -----------------------------------------------------
    parser_free = subparsers.add_parser(
        "enrich-free", help="Bounded PRH registry and iXBRL-period lookups without AI credits."
    )
    parser_free.add_argument("--company", default="")
    parser_free.add_argument("--max-companies", type=int, default=5)
    parser_free.add_argument("--pause-seconds", type=float, default=1.0)
    parser_free.add_argument("--confirm-public-lookups", action="store_true")
    parser_free.set_defaults(func=cmd_enrich_free)

    parser_profile = subparsers.add_parser(
        "attach-profile", help="Attach source-verified company facts for a genuinely website-less lead."
    )
    parser_profile.add_argument("company")
    parser_profile.add_argument("--profile", required=True)
    parser_profile.set_defaults(func=cmd_attach_profile)

    # -----------------------------------------------------
    # PIPELINE
    # -----------------------------------------------------

    parser_pipeline = subparsers.add_parser(
        "pipeline",
        help=(
            "Aja Scout → Research → "
            "Build → QA yhdellä yrityksellä."
        ),
    )

    parser_pipeline.add_argument("--company", default="",
        help="Run a previously researched or source-screened lead (skips Scout discovery).")
    parser_pipeline.add_argument("--benchmark-mode", action="store_true",
        help="Use ONE unseen company per quality trial. Repeats and same-company revision loops are blocked; no customer outreach.")
    parser_pipeline.add_argument(
        "--count",
        type=int,
        default=1,
    )

    parser_pipeline.add_argument(
        "--industry",
        default="kampaamo",
    )

    parser_pipeline.add_argument(
        "--location",
        default="Tampere",
    )

    parser_pipeline.add_argument(
        "--confirm-live-run", action="store_true",
        help="Explicitly authorize the paid external Scout/Research/Build/QA run.",
    )
    parser_pipeline.add_argument(
        "--max-revisions", type=int, choices=range(0, 4), default=0,
        help="Rajattu QA-korjauskierrosten määrä (0–3). Oletus 0 pitää API-kulut ennallaan.",
    )
    parser_pipeline.set_defaults(func=cmd_pipeline)

    return parser


# =========================================================
# MAIN
# =========================================================

def main():

    parser = build_parser()

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
