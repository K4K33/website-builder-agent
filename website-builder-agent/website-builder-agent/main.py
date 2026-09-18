#!/usr/bin/env python3
"""
Website Builder Agent - pääohjelma (CLI).

Käyttö (aja projektin juuresta):

    python main.py scout --count 10 --industry "putkiliike" --location "Tampere"
    python main.py list
    python main.py research koivuranta
    python main.py build koivuranta
    python main.py preview koivuranta
    python main.py revise koivuranta "tee väreistä tummemmat ja ammattimaisemmat"
    python main.py qa koivuranta
    python main.py approve koivuranta
    python main.py outreach koivuranta
    python main.py approve-outreach koivuranta

Katso README.md tarkemmat selitykset ja käyttöesimerkit.

HUOM: Tämä v1 käyttää selkeitä komentoja (ei vapaata luonnollista kieltä
suoraan terminaalissa). Jos haluat myöhemmin kirjoittaa Claudelle suoraan
"Analysoi Koivuranta" ja Claude päättelee mitä komentoa ajaa, seuraava
kehitysaskel on lisätä tämän päälle kevyt NLU-kerros (esim. oma
"agent_runner.py", joka tulkitsee vapaan tekstin näiksi samoiksi
komennoiksi). Katso README:n "Seuraavat kehitysaskeleet".
"""
import argparse
import sys

from agents import scout, research, builder, qa, outreach
from utils import state


def cmd_scout(args):
    print(f"[Scout] Etsitään {args.count} yritystä...")
    results = scout.run_scout(count=args.count, industry=args.industry, location=args.location)
    if not results:
        print("Ei löytynyt uusia yrityksiä (tai kaikki löydetyt olivat jo pidemmällä).")
        return
    print(f"\nLöytyi {len(results)} yritystä:\n")
    for slug, c in results:
        print(f"  - {c['name']}  ({c['url']})  [slug: {slug}]")
        print(f"      Syy: {c['scout']['reason']}")
    print("\nJatka seuraavaksi: python main.py research <slug>")


def cmd_list(args):
    companies = state.load_companies()
    if not companies:
        print("Ei vielä yhtään yritystä. Aloita: python main.py scout --count 10")
        return
    print(f"{'SLUG':<25} {'NIMI':<30} {'STATUS':<20} URL")
    print("-" * 100)
    for slug, c in companies.items():
        print(f"{slug:<25} {c.get('name', ''):<30} {c.get('status', ''):<20} {c.get('url', '')}")


def _require_company(name_or_slug):
    slug, company = state.get_company(name_or_slug)
    if company is None:
        print(
            f"Yritystä '{name_or_slug}' ei löytynyt (slug: {slug}). "
            f"Käytä 'python main.py list' nähdäksesi tunnetut yritykset, "
            f"tai lisää yritys manuaalisesti: python main.py add \"Nimi\" https://url.fi"
        )
        sys.exit(1)
    return slug, company


def cmd_add(args):
    slug = state.make_slug(args.name)
    state.upsert_company(slug, {"name": args.name, "url": args.url, "status": "found"})
    print(f"Lisätty: {args.name} [{slug}] -> {args.url}")
    print(f"Jatka: python main.py research {slug}")


def cmd_research(args):
    slug, company = _require_company(args.slug)
    print(f"[Research] Analysoidaan {company['name']} ({company['url']})...")
    research.run_research(slug, company["name"], company["url"])
    print(f"Valmis. Katso data/companies.json (avain: '{slug}') tai:")
    print(f"  python main.py show {slug}")
    print(f"Jatka: python main.py build {slug}")


def cmd_build(args):
    slug, company = _require_company(args.slug)
    print(f"[Builder] Rakennetaan sivusto yritykselle {company.get('name', slug)}...")
    path = builder.build_site(slug, company)
    print(f"Valmis! Sivusto tallennettu: {path}")
    print(f"Esikatsele: python main.py preview {slug}")
    print(f"Tarkista laatu: python main.py qa {slug}")


def cmd_revise(args):
    slug, company = _require_company(args.slug)
    print(f"[Builder] Muokataan sivustoa palautteen perusteella: \"{args.feedback}\"")
    path = builder.revise_site(slug, company, args.feedback)
    print(f"Valmis! Päivitetty sivusto: {path}")
    print(f"Esikatsele: python main.py preview {slug}")


def cmd_qa(args):
    slug, company = _require_company(args.slug)
    print(f"[QA] Tarkistetaan sivuston laatu ({slug})...")
    result = qa.run_qa(slug, company)
    print(f"\nAutomaattitarkistukset: {'OK' if result['automated']['automated_pass'] else 'HUOMIOITAVAA'}")
    for issue in result["automated"]["automated_issues"]:
        print(f"  - {issue}")
    print(f"\nSisältötarkistus (Claude): {'OK' if result['content_review'].get('content_ok') else 'HUOMIOITAVAA'}")
    for issue in result["content_review"].get("issues", []):
        print(f"  - {issue}")
    print(f"\nKOKONAISTULOS: {'LÄPÄISI' if result['overall_pass'] else 'EI LÄPÄISSYT - tarkista yllä olevat huomiot'}")


def cmd_preview(args):
    import subprocess
    import webbrowser
    import os

    slug, company = _require_company(args.slug)
    out_dir = os.path.join("output", slug)
    path = os.path.join(out_dir, "index.html")
    if not os.path.exists(path):
        print(f"Sivustoa ei ole vielä rakennettu. Aja: python main.py build {slug}")
        sys.exit(1)

    print(f"Avataan {path} selaimessa...")
    try:
        webbrowser.open(f"file://{os.path.abspath(path)}")
    except Exception:
        pass
    print(f"Jos selain ei avautunut automaattisesti, avaa tiedosto käsin: {os.path.abspath(path)}")


def cmd_approve(args):
    slug, company = _require_company(args.slug)
    state.set_status(slug, "approved")
    print(f"'{company.get('name', slug)}' merkitty hyväksytyksi.")
    print(f"Jatka: python main.py outreach {slug}")


def cmd_outreach(args):
    slug, company = _require_company(args.slug)
    if company.get("status") not in ("approved", "outreach_drafted", "outreach_approved"):
        print(
            "HUOM: sivustoa ei ole vielä merkitty hyväksytyksi. "
            f"Suosittelemme ajamaan ensin: python main.py approve {slug}"
        )
    print(f"[Outreach] Kirjoitetaan sähköpostiluonnos ({slug})...")
    draft = outreach.draft_outreach(slug, company)
    print(f"\nAihe: {draft.get('subject')}\n")
    print(draft.get("body"))
    print(f"\nKun olet tyytyväinen, hyväksy lähetystä varten: python main.py approve-outreach {slug}")
    print("(Tämä versio ei lähetä sähköpostia automaattisesti.)")


def cmd_approve_outreach(args):
    slug, company = _require_company(args.slug)
    outreach.approve_outreach(slug, company)


def cmd_show(args):
    import json
    slug, company = _require_company(args.slug)
    print(json.dumps(company, ensure_ascii=False, indent=2))


def build_parser():
    parser = argparse.ArgumentParser(description="Website Builder Agent - CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scout", help="Etsi potentiaalisia yrityksiä")
    p.add_argument("--count", type=int, default=None)
    p.add_argument("--industry", type=str, default="")
    p.add_argument("--location", type=str, default="")
    p.set_defaults(func=cmd_scout)

    p = sub.add_parser("list", help="Listaa kaikki tunnetut yritykset ja niiden statukset")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("add", help="Lisää yritys manuaalisesti (ilman scoutia)")
    p.add_argument("name")
    p.add_argument("url")
    p.set_defaults(func=cmd_add)

    p = sub.add_parser("research", help="Analysoi yritys ja toimiala")
    p.add_argument("slug")
    p.set_defaults(func=cmd_research)

    p = sub.add_parser("build", help="Rakenna uusi verkkosivu")
    p.add_argument("slug")
    p.set_defaults(func=cmd_build)

    p = sub.add_parser("revise", help="Muokkaa rakennettua sivua luonnollisella kielellä annetulla palautteella")
    p.add_argument("slug")
    p.add_argument("feedback")
    p.set_defaults(func=cmd_revise)

    p = sub.add_parser("qa", help="Tarkista rakennetun sivun laatu")
    p.add_argument("slug")
    p.set_defaults(func=cmd_qa)

    p = sub.add_parser("preview", help="Avaa rakennettu sivu selaimessa")
    p.add_argument("slug")
    p.set_defaults(func=cmd_preview)

    p = sub.add_parser("approve", help="Hyväksy sivusto (sinä, käyttäjänä)")
    p.add_argument("slug")
    p.set_defaults(func=cmd_approve)

    p = sub.add_parser("outreach", help="Valmistele sähköpostiluonnos (ei lähetä)")
    p.add_argument("slug")
    p.set_defaults(func=cmd_outreach)

    p = sub.add_parser("approve-outreach", help="Hyväksy sähköpostiluonnos lähetettäväksi")
    p.add_argument("slug")
    p.set_defaults(func=cmd_approve_outreach)

    p = sub.add_parser("show", help="Näytä kaikki tallennettu data yhdestä yrityksestä")
    p.add_argument("slug")
    p.set_defaults(func=cmd_show)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
