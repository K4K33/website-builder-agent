"""
Website Builder Agent

Pääohjelma, jonka kautta eri agentteja voidaan ajaa.
"""

import argparse

from agents import scout
from agents import research
from agents import builder
from agents import qa
from agents import outreach

from utils.state import load_companies


def cmd_scout(args):
    print(
        f"[Scout] Etsitään {args.count} yritystä..."
    )

    results = scout.run_scout(
        count=args.count,
        industry=args.industry,
        location=args.location,
        dry_run=args.dry_run,
    )

    if not results:
        print(
            "Ei löytynyt uusia yrityksiä "
            "(tai kaikki löydetyt olivat jo pidemmällä)."
        )
        return

    print()
    print(
        f"[Scout] Käsitelty {len(results)} yritystä."
    )

    if args.dry_run:
        print(
            "[Scout] DRY-RUN: mitään yrityksiä ei tallennettu."
        )


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


def cmd_research(args):
    research.run_research(args.company)


def cmd_build(args):
    builder.run_build(args.company)


def cmd_revise(args):
    builder.run_revise(
        args.company,
        args.instructions,
    )


def cmd_qa(args):
    qa.run_qa(args.company)


def cmd_preview(args):
    builder.run_preview(args.company)


def cmd_approve(args):
    qa.approve_company(args.company)


def cmd_outreach(args):
    outreach.run_outreach(args.company)


def cmd_approve_outreach(args):
    outreach.approve_outreach(args.company)


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
        print(
            f"{key}: {value}"
        )


def build_parser():
    parser = argparse.ArgumentParser(
        description="Website Builder Agent"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # ---------------------------------------------------------
    # LIST
    # ---------------------------------------------------------

    parser_list = subparsers.add_parser(
        "list",
        help="Näytä tallennetut yritykset.",
    )

    parser_list.set_defaults(
        func=cmd_list
    )

    # ---------------------------------------------------------
    # ADD
    # ---------------------------------------------------------

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

    parser_add.set_defaults(
        func=cmd_add
    )

    # ---------------------------------------------------------
    # SCOUT
    # ---------------------------------------------------------

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

    parser_scout.set_defaults(
        func=cmd_scout
    )

    # ---------------------------------------------------------
    # RESEARCH
    # ---------------------------------------------------------

    parser_research = subparsers.add_parser(
        "research",
        help="Tutki yritystä.",
    )

    parser_research.add_argument(
        "company"
    )

    parser_research.set_defaults(
        func=cmd_research
    )

    # ---------------------------------------------------------
    # BUILD
    # ---------------------------------------------------------

    parser_build = subparsers.add_parser(
        "build",
        help="Rakenna verkkosivusto.",
    )

    parser_build.add_argument(
        "company"
    )

    parser_build.set_defaults(
        func=cmd_build
    )

    # ---------------------------------------------------------
    # REVISE
    # ---------------------------------------------------------

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

    parser_revise.set_defaults(
        func=cmd_revise
    )

    # ---------------------------------------------------------
    # QA
    # ---------------------------------------------------------

    parser_qa = subparsers.add_parser(
        "qa",
        help="Tarkista verkkosivusto.",
    )

    parser_qa.add_argument(
        "company"
    )

    parser_qa.set_defaults(
        func=cmd_qa
    )

    # ---------------------------------------------------------
    # PREVIEW
    # ---------------------------------------------------------

    parser_preview = subparsers.add_parser(
        "preview",
        help="Näytä verkkosivuston esikatselu.",
    )

    parser_preview.add_argument(
        "company"
    )

    parser_preview.set_defaults(
        func=cmd_preview
    )

    # ---------------------------------------------------------
    # APPROVE
    # ---------------------------------------------------------

    parser_approve = subparsers.add_parser(
        "approve",
        help="Hyväksy yrityksen verkkosivusto.",
    )

    parser_approve.add_argument(
        "company"
    )

    parser_approve.set_defaults(
        func=cmd_approve
    )

    # ---------------------------------------------------------
    # OUTREACH
    # ---------------------------------------------------------

    parser_outreach = subparsers.add_parser(
        "outreach",
        help="Luo yhteydenottoluonnos.",
    )

    parser_outreach.add_argument(
        "company"
    )

    parser_outreach.set_defaults(
        func=cmd_outreach
    )

    # ---------------------------------------------------------
    # APPROVE OUTREACH
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # SHOW
    # ---------------------------------------------------------

    parser_show = subparsers.add_parser(
        "show",
        help="Näytä yrityksen tiedot.",
    )

    parser_show.add_argument(
        "company"
    )

    parser_show.set_defaults(
        func=cmd_show
    )

    return parser


def main():
    parser = build_parser()

    args = parser.parse_args()

    args.func(args)


if __name__ == "__main__":
    main()
