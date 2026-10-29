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
from utils.lead_intelligence import evaluate_prospect
from utils.state import (
    get_company,
    upsert_company,
    set_status,
)


OUTREACH_SYSTEM_PROMPT = """Olet Kaurivon asiakaslähtöinen suunnittelija, et massamarkkinoija.

Kirjoita henkilökohtainen sähköpostiluonnos suomalaiselle yritykselle,
jolle on oikeasti suunniteltu ja QA-tarkistettu uusi esimerkkisivu.

Tärkein tavoite:
Vastaanottaja ymmärtää, miten juuri hänen asiakkaansa voisi löytää
palvelun, tehdä varauksen, kysyä tarjousta tai saapua käymään
nykyistä helpommin. Älä myy 'modernia sivua' itseisarvona.
Myy konkreettista asiakaskokemuksen parannusta ja sen mahdollisuutta.

Rakenne:
1. Lyhyt, tavallinen, uskottava otsikko, joka liittyy nimettyyn yritykseen.
2. Välitön syy yhteydenottoon ja yksi AITO, tarkistettu myönteinen havainto.
   Ei geneerisiä kehuja tai yritykselle keksittyjä ominaisuuksia.
3. Yksi selkeä nykyisen asiakaspolun kitka, jos se voidaan todistaa.
   Esitä sen liiketoiminnallinen merkitys selkeästi ja maltillisesti:
   esimerkiksi ajanvarauksen, hinnan tai saapumisohjeen löytyminen
   helpommin. Älä väitä asiakkaiden jättävän ostamatta ilman näyttöä.
4. Kerro täsmällisesti, mitä suunnittelit tässä yrityksessä toisin,
   miten se helpottaisi heidän asiakkaansa seuraavaa askelta, ja
   että halutessaan he voivat tutustua valmiiseen demoon.
   Älä keksimällä keksi demolle URLia tai teknisiä ominaisuuksia.
5. Lopuksi YKSI kevyt kysymys, johon voi vastata yhdellä lauseella.
   Älä pyydä kylmässä ensiviestissä tapaamista tai puhelua.
6. Luonnollinen allekirjoitus: Kaurivo, hello.kaurivo@gmail.com.
   Lähettäjän nimeä ei saa keksiä.

Jos sivustoa ei ole riippumattomasti varmistetun tiedon mukaan olemassa:
Älä puhu vanhan sivun heikkouksista tai väitä asiakkaan menettävän myyntiä.
Puhu sen sijaan siitä, miten yrityksen vahvuudet olisivat helpommin
löydettävissä ja miten verkkosivu voisi helpottaa ostajan asiointia.

Kirjoitustyyli:
- 90–135 sanaa (ei keinotekoisesti täyteen venytetty).
- Ystävällinen, suorapuheinen, helposti lähestyttävä ja ammattimainen.
- Ei ylisanallista ihailua, turhia anteeksipyyntöjä, teknistä jargonia,
  painostusta, tekaistua kiirettä, ROI-lukuja tai tekaistuja tuloksia.
- Älä käytä ajatusviivoja, pitkää tai lyhyttä viivaa lauseiden välissä,
  äläkä luettelomaisia viivarivejä sähköpostin rungossa.
- Ei geneeristä 'innostuin niin paljon että...' -lausetta.
- Älä kirjoita mitään, mikä ei perustu annettuihin yritysfaktoihin,
  todellisiin havaintoihin ja demossa oikeasti toteutettuun ratkaisuun.
- Jos nämä tiedot puuttuvat, älä keksi niitä: kirjoita luonnos,
  joka tarvitsee faktatarkistuksen ennen lähettämistä.

Älä lisää sähköpostin runkoon erillistä kieltäytymislausetta.
Mahdollisen sähköisen B2B-suoramarkkinoinnin lain vaatima
kieltomahdollisuus sijoitetaan HTML-viestin huomaamattomaan,
mutta selkeään erilliseen alatunnisteeseen, ei myyntitekstiin.
Kieltoa ei saa jättää pois todellisessa markkinointiviestissä.

Palauta VAIN validi JSON:
{"subject":"yksilöllinen aihe","body":"täydellinen sähköpostin runko"}
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

    qa = company.get("qa") or {}

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

    approval = company.get("approval") or {}

    if (approval.get("approved") is not True
            or approval.get("build_version") != company.get("build", {}).get("version")
            or approval.get("html_sha256") != qa.get("html_sha256")):
        raise RuntimeError(
            f"Yrityksen '{slug}' nykyistä verkkosivustoversiota ei ole hyväksytty. "
            f"Aja QA ja hyväksy: python main.py approve {slug}"
        )

    intelligence = evaluate_prospect(company)
    if intelligence["financial"]["status"] == "exclude":
        raise RuntimeError("Company inactive/insolvent according to recorded official data.")
    if intelligence["business_activity"]["status"] != "active":
        raise RuntimeError("Active business operations must be independently verified before outreach drafting.")
    if intelligence["site_status"] not in {"has_website", "confirmed_no_website"}:
        raise RuntimeError("Website absence must be verified before drafting outreach.")
    # Review stars, location count, turnover and profit are OPTIONAL.

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

Yrityksen sivutilanne: {intelligence["site_status"]}

Nykyisen sivuston havaitut heikkoudet:
{weaknesses}

Yrityksen designin asiakastehtävät ja konkretia:
{research.get("design_recommendations", {}).get("customer_tasks", [])}

Uuden toteutuksen muutokset ja niiden hyväksymiskriteerit:
{research.get("design_decisions", [])}

Ihmisen mahdolliset yksilölliset, lähteistetyt havainnot:
{company.get("outreach_research", {})}

Kirjoita näiden tietojen perusteella yksilöllinen outreach-sähköposti.
Lähtökohtana vastaanottajan asiakkaan konkreettinen seuraava askel.
Kerro vain yhdestä todellisesta, nimenomaan tälle yritykselle hyödyllisestä
parannuksesta. Yksilöllinen havainto tarkistetaan ennen lähettämistä.
Jos tietoa ei ole, älä korvaa sitä keksityllä tai geneerisellä kehumisella.
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
