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
from utils.lead_intelligence import evaluate_prospect, site_signal
from utils.company_registry import lookup_by_business_id, lookup_by_name_and_location
from utils.free_enrichment import enrich_queue
from utils.verified_profile import validate_verified_profile
from utils.state import get_company, upsert_company

from utils.state import (
    load_companies,
)


# =========================================================
# SCOUT
# =========================================================

def cmd_scout(args):
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
    research.run_research(args.company)


# =========================================================
# BUILD
# =========================================================

def cmd_build(args):
    builder.run_build(args.company)


def cmd_complete_build(args):
    print(builder.run_build_from_response(args.company, args.response, args.producer))


# =========================================================
# REVISE
# =========================================================

def cmd_revise(args):
    builder.run_revise(
        args.company,
        args.instructions,
    )


# =========================================================
# QA
# =========================================================

def cmd_qa(args):
    qa.run_qa(args.company)


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
# BUSINESS INTELLIGENCE / LEAD SCREENING
# =========================================================

def cmd_screen_lead(args):
    slug, company = get_company(args.company)
    if company is None:
        raise RuntimeError("Lead not found; run Scout first.")
    evidence = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
    if not isinstance(evidence, dict) or not any(
        item in evidence for item in ("reputation", "financials", "site_verification")
    ):
        raise ValueError("Evidence must include reputation, financials or site_verification.")
    updates = {}
    for key in ("reputation", "financials", "site_verification"):
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
    for key in ("OPENROUTER_API_KEY", "TAVILY_API_KEY"):
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
        raise RuntimeError("No financially screened and buildable company available; verify business facts first.")

    # -----------------------------------------------------
    # SELECT COMPANY
    # -----------------------------------------------------

    companies = load_companies()

    selected_slug = None
    selected_company = None

    for result in results:
        candidate_slug = result.get("slug")
        if candidate_slug in companies:
            selected_slug = candidate_slug
            selected_company = companies[candidate_slug]
            break

    if selected_company is None:
        raise RuntimeError("Scout returned no company with a saved record.")
    website_state = site_signal(selected_company)
    if website_state != "has_website":
        # A confirmed site-less company can be built from a manually reviewed,
        # source-backed profile; unknown OSM website listings are still blocked.
        if website_state != "confirmed_no_website":
            raise RuntimeError("No-site lead needs independent website and business verification.")
        validate_verified_profile(selected_company)
    intelligence = selected_company.get("lead_intelligence") or {}
    if (intelligence and intelligence.get("financial", {}).get("status") != "promising"
            and not getattr(args, "benchmark_mode", False)):
        raise RuntimeError("Financial screening not passed; do not spend build credits on this commercial lead.")

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
    for attempt in range(args.max_revisions):
        if qa_result.get("overall_pass") is True:
            break
        if qa_result.get("content_review", {}).get("notes") == "AI review failed":
            break
        if any("Browser QA unavailable" in issue for issue in qa_result.get("browser", {}).get("issues", [])):
            break
        import json
        feedback = {
            "static": qa_result.get("automated", {}).get("automated_issues", []),
            "browser": qa_result.get("browser", {}).get("issues", []),
            "review": qa_result.get("content_review", {}),
        }
        print(f"[Pipeline] Korjauskierros {attempt + 1}/{args.max_revisions}")
        builder.run_revise(selected_slug, json.dumps(feedback, ensure_ascii=False))
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

    parser_revise.set_defaults(func=cmd_revise)

    # -----------------------------------------------------
    # QA
    # -----------------------------------------------------

    parser_qa = subparsers.add_parser(
        "qa",
        help="Tarkista verkkosivusto.",
    )

    parser_qa.add_argument(
        "company"
    )

    parser_qa.set_defaults(func=cmd_qa)

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
        help="Run a previously financially screened saved lead (skips Scout discovery).")
    parser_pipeline.add_argument("--benchmark-mode", action="store_true",
        help="Explicitly use unscreened leads ONLY for an internal quality benchmark; no customer outreach.")
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
