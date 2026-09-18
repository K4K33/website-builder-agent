"""
Outreach-agentti.

Tehtävä: valmistella henkilökohtainen sähköpostiluonnos yritykselle,
kun sivusto on hyväksytty. TÄRKEÄÄ: tämä agentti EI KOSKAAN lähetä
sähköpostia automaattisesti. Se ainoastaan kirjoittaa luonnoksen
data/companies.json:iin ja tulostaa sen käyttäjälle luettavaksi.

Todellinen lähetys (esim. SMTP/SendGrid-integraatio) on tarkoituksella
jätetty pois v1:stä - se lisätään myöhemmin billing-agentin yhteydessä,
kun käyttäjä on valmis automatisoimaan myös sen, ja vasta selkeän,
erillisen hyväksynnän jälkeen."""
from utils.claude_client import ask_claude_json
from utils.state import upsert_company, set_status

OUTREACH_SYSTEM_PROMPT = """Olet myynti- ja viestintäassistentti, joka kirjoittaa
lyhyen, henkilökohtaisen ja ei-tyrkyttävän sähköpostiluonnoksen yritykselle,
jolle on rakennettu uusi esimerkkiverkkosivu.

Sävy: ystävällinen, ammattimainen, konkreettinen - ei myyntipuhetta täynnä
kliseitä. Sähköpostin pitää:
- Mainita jotain konkreettista nykyisestä sivustosta (perustuen brief-tietoihin)
- Kertoa lyhyesti että olemme rakentaneet MAKSUTTOMAN esimerkin uudesta,
  modernista verkkosivusta ilman sitoumuksia
- Sisältää selkeän mutta matalan kynnyksen call-to-actionin (esim. "voisiko
  10 minuutin puhelu sopia ensi viikolla?")
- Olla max. 150 sanaa
- Päättyä kohteliaaseen allekirjoitukseen "[Oma nimesi tähän]"

Palauta VAIN JSON:
{
  "subject": "sähköpostin otsikko",
  "body": "sähköpostin runko-teksti"
}"""


def draft_outreach(slug: str, company: dict) -> dict:
    research = company.get("research", {})
    facts = research.get("company_facts", {})
    weaknesses = research.get("current_site_weaknesses", [])

    user_prompt = f"""Yritys: {facts.get('name', company.get('name'))}
Toimiala: {facts.get('industry', '')}
Nykyisen sivun heikkoudet joita voisi hienovaraisesti mainita: {weaknesses}

Kirjoita outreach-sähköposti suomeksi."""

    draft = ask_claude_json(OUTREACH_SYSTEM_PROMPT, user_prompt, use_web_search=False, max_tokens=800)

    upsert_company(slug, {
        "outreach": {
            "subject": draft.get("subject", ""),
            "body": draft.get("body", ""),
            "approved": False,
        }
    })
    set_status(slug, "outreach_drafted")
    return draft


def approve_outreach(slug: str, company: dict) -> None:
    outreach = company.get("outreach")
    if not outreach:
        raise RuntimeError(f"Yritykselle '{slug}' ei ole vielä sähköpostiluonnosta.")
    outreach["approved"] = True
    upsert_company(slug, {"outreach": outreach})
    set_status(slug, "outreach_approved")
    print(
        "  Sähköposti on merkitty hyväksytyksi. HUOM: tämä versio EI lähetä "
        "sähköpostia automaattisesti - lähetys on tietoisesti jätetty manuaaliseksi "
        "(tai tulevan billing/outreach-automaation varaan) kunnes olet valmis siihen."
    )
