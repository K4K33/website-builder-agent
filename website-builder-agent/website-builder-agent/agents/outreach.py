"""
Outreach-agentti.

Tehtävä:
1. Luo henkilökohtainen sähköpostiluonnos yritykselle.
2. Varmistaa, että verkkosivu on ensin QA-tarkistettu ja hyväksytty.
3. Tallentaa luonnoksen companies.json-tiedostoon.
4. Ei koskaan lähetä sähköpostia automaattisesti.

Todellinen lähetys lisätään myöhemmin erillisenä vaiheena,
kun käyttäjä antaa siihen nimenomaisen hyväksynnän.
"""

from utils.claude_client import ask_claude_json
from utils.state import (
    get_company,
    upsert_company,
    set_status,
)


OUTREACH_SYSTEM_PROMPT = """Olet myynti- ja viestintäassistentti.

Kirjoita lyhyt, henkilökohtainen ja ei-tyrkyttävä sähköpostiluonnos
yritykselle, jolle on rakennettu uusi esimerkkiverkkosivu.

Sävy:
- ystävällinen
- ammattimainen
- konkreettinen
- luonnollinen
- ei aggressiivista myyntipuhetta
- ei kliseistä markkinointikieltä

Sähköpostin pitää:

1. Mainita yksi konkreettinen havainto yrityksen nykyisestä sivustosta.
2. Kertoa lyhyesti, että yritykselle on rakennettu MAKSUTON
   esimerkkiversio modernimmasta verkkosivusta.
3. Korostaa, ettei esimerkki aiheuta sitoumusta.
4. Sisältää matalan kynnyksen CTA:n.
   Esimerkiksi lyhyt 10 minuutin keskustelu.
5. Olla enintään 150 sanaa.
6. Olla suomeksi.
7. Päättyä:

Ystävällisin terveisin,
[Oma nimesi tähän]

Älä:
- keksi yrityksestä faktoja
- keksi yhteystietoja
- väitä tietäväsi asioita joita brief ei tue
- väitä, että yrityksen sivusto on "huono"
- käytä loukkaavaa tai alentavaa kieltä
- lupaa tuloksia joita ei ole todistettu
- painosta vastaanottajaa

Palauta VAIN validi JSON:

{
  "subject": "sähköpostin otsikko",
  "body": "sähköpostin runko-teksti"
}
"""


def draft_outreach(
    slug: str,
    company: dict,
) -> dict:
    """
    Luo outreach-luonnoksen.

    Luonnosta ei luoda ennen kuin:
    1. QA on tehty
    2. QA on läpäisty
    3. sivusto on hyväksytty
    """

    # ---------------------------------------------------------
    # 1. Tarkista QA
    # ---------------------------------------------------------

    qa = company.get(
        "qa",
        {},
    )

    if not qa.get(
        "overall_pass",
        False,
    ):
        raise RuntimeError(
            f"Yrityksen '{slug}' verkkosivusto ei ole läpäissyt QA:ta. "
            "Aja ensin: python main.py qa "
            f"{slug}"
        )

    # ---------------------------------------------------------
    # 2. Tarkista käyttäjän hyväksyntä
    # ---------------------------------------------------------

    approval = company.get(
        "approval",
        {},
    )

    if not approval.get(
        "approved",
        False,
    ):
        raise RuntimeError(
            f"Yrityksen '{slug}' verkkosivustoa ei ole vielä hyväksytty. "
            "Hyväksy ensin: python main.py approve "
            f"{slug}"
        )

    # ---------------------------------------------------------
    # 3. Research-data
    # ---------------------------------------------------------

    research = company.get(
        "research",
        {},
    )

    facts = research.get(
        "company_facts",
        {},
    )

    weaknesses = research.get(
        "current_site_weaknesses",
        [],
    )

    if not facts:
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy research-dataa."
        )

    company_name = (
        facts.get(
            "name"
        )
        or company.get(
            "name",
            "",
        )
    )

    industry = facts.get(
        "industry",
        "",
    )

    services = facts.get(
        "services",
        [],
    )

    location = facts.get(
        "location",
        "",
    )

    user_prompt = f"""
Yritys:
{company_name}

Toimiala:
{industry}

Palvelut:
{services}

Sijainti:
{location}

Nykyisen sivuston havaitut heikkoudet:
{weaknesses}

Kirjoita näiden tietojen perusteella henkilökohtainen outreach-sähköposti.

Tärkeää:
- Mainitse vain sellainen nykyisen sivuston havainto, joka on oikeasti
  tuettavissa annetuilla tiedoilla.
- Älä keksi yrityksestä mitään.
- Älä käytä teknistä jargon-selitystä.
- Sähköpostin pitää tuntua oikean ihmisen kirjoittamalta.
"""

    # ---------------------------------------------------------
    # 4. AI-luonnos
    # ---------------------------------------------------------

    print(
        "  [Outreach] Luodaan sähköpostiluonnos..."
    )

    draft = ask_claude_json(
        OUTREACH_SYSTEM_PROMPT,
        user_prompt,
        use_web_search=False,
        max_tokens=1200,
    )

    if not isinstance(
        draft,
        dict,
    ):
        raise RuntimeError(
            "AI ei palauttanut outreach-luonnosta JSON-objektina."
        )

    subject = str(
        draft.get(
            "subject",
            "",
        )
    ).strip()

    body = str(
        draft.get(
            "body",
            "",
        )
    ).strip()

    if not subject:
        raise RuntimeError(
            "AI ei tuottanut sähköpostille otsikkoa."
        )

    if not body:
        raise RuntimeError(
            "AI ei tuottanut sähköpostille runkoa."
        )

    # ---------------------------------------------------------
    # 5. Tallenna luonnos
    # ---------------------------------------------------------

    outreach_data = {
        "subject": subject,
        "body": body,
        "approved": False,
    }

    upsert_company(
        slug,
        {
            "outreach": outreach_data
        },
    )

    set_status(
        slug,
        "outreach_drafted",
    )

    print(
        "  [Outreach] Luonnos valmis."
    )

    print()
    print("=== OUTREACH-LUONNOS ===")
    print(
        f"Aihe: {subject}"
    )
    print()
    print(body)
    print()
    print(
        "HUOM: Tätä viestiä EI lähetetty."
    )

    return outreach_data


def run_outreach(
    slug_or_name: str,
) -> dict:
    """
    main.py:n käyttämä outreach-käynnistys.
    """

    slug, company = get_company(
        slug_or_name
    )

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    print()
    print("=== OUTREACH ===")
    print(
        f"Yritys: {company.get('name', slug)}"
    )

    return draft_outreach(
        slug,
        company,
    )


def approve_outreach(
    slug_or_name: str,
) -> None:
    """
    Merkitsee outreach-luonnoksen käyttäjän hyväksymäksi.

    TÄRKEÄÄ:
    Tämä ei lähetä sähköpostia.
    """

    slug, company = get_company(
        slug_or_name
    )

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    outreach = company.get(
        "outreach"
    )

    if not outreach:
        raise RuntimeError(
            f"Yritykselle '{slug}' ei ole vielä "
            "sähköpostiluonnosta."
        )

    subject = outreach.get(
        "subject",
        "",
    ).strip()

    body = outreach.get(
        "body",
        "",
    ).strip()

    if not subject or not body:
        raise RuntimeError(
            f"Yrityksen '{slug}' outreach-luonnos on tyhjä."
        )

    outreach["approved"] = True

    upsert_company(
        slug,
        {
            "outreach": outreach
        },
    )

    set_status(
        slug,
        "outreach_approved",
    )

    print()
    print("=== OUTREACH HYVÄKSYTTY ===")
    print(
        f"Yritys: {company.get('name', slug)}"
    )
    print()
    print(
        "Sähköposti on merkitty hyväksytyksi."
    )
    print(
        "HUOM: sähköpostia EI lähetetty."
    )
    print(
        "Lähetys on tässä versiossa tarkoituksella manuaalinen."
    )
