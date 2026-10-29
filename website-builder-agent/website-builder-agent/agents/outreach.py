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


OUTREACH_SYSTEM_PROMPT = """Olet Kaurivon perustajan Kaarlon myyntiviestien kirjoittaja.
Kirjoita SUORA, henkilökohtainen B2B-myyntisähköposti todelliselle
yritykselle, jolle on jo rakennettu ja QA-hyväksytty demosivusto.

Älä käytä varovaista, kiertelevää 'miltä tällainen suunta tuntuu'
-tyyliä tai pelkkää myönteistä jutustelua. Tämä on myyntiviesti.
Vastaanottajan tulee ymmärtää ensimmäisessä kahdessa virkkeessä
kuka ottaa yhteyttä, mitä hän tekee ja miksi juuri heille kirjoitetaan.

Pakollinen runko, luonnollisena tekstinä ilman luetelmia:
1. Hei [vastaanottajan etunimi vain, jos se on TARKISTETTU], muuten 'Hei'.
2. 'Olen Kaarlo, Kaurivon perustaja. Suunnittelen ja toteutan
   verkkosivuja yrityksille.' Tämä on lähettäjän oikea identiteetti,
   ei tekaistu edustaja.
3. Kerro suoraan, että tutustuit nimenomaan tämän yrityksen
   verkkosivuihin ja huomasit yhden tai kaksi KONKREETTISTA
   uudistuskohdetta. Nimeä yksityiskohta ja selitä lyhyesti,
   miksi muutos palvelisi heidän asiakkaitaan. Älä kehu väkisin.
   Käytä vain lähteistä todettuja yksityiskohtia.
4. Kerro, että rakensit tätä yritystä varten valmiin
   verkkosivuehdotuksen ja näytä siihen oikea linkki vain, jos se
   on annettu tai esitetään erillisessä hyväksytyssä HTML-demokortissa.
   Älä koskaan keksi URL-osoitetta tai luvattuja ominaisuuksia.
5. Kerro SUORA kaupallinen tarjous: 'Jos pidätte ehdotuksesta, voin
   toteuttaa uuden sivuston teille kokonaan.' Tämä ei ole väite
   siitä, että valmis tuotantosivu olisi jo toimitettu.
6. Päätä selkeään kysymykseen: 'Olisiko teillä kiinnostusta uudistaa
   nykyisiä verkkosivujanne?' Voit sovittaa sanamuodon vastaanottajan
   tilanteeseen. Älä piilota myyntitarjousta epämääräiseen
   'miltä suunta tuntuu' -kysymykseen.
7. Lopeta 'Ystävällisin terveisin, Kaarlo, Kaurivon perustaja,
   hello.kaurivo@gmail.com'.

Jos yrityksellä ei ole TODETUSTI verkkosivuja, älä väitä nähneesi
nykyisiä sivuja, äläkä sano 'uudistaa nykyisiä verkkosivuja'.
Kerro sen sijaan 'Huomasin, ettei yrityksellenne löydy vielä
verkkosivua' vain jos tämä on lähteistä riippumattomasti varmistettu.
Kerro yksi rehellinen syy uuden sivun hyötyyn (esimerkiksi palvelut,
toimialue tai yhteydenotto löytyisi yhdestä paikasta), esittele
juuri heille rakennettu demo, tarjoa toteutus ja kysy suoraan:
'Olisiko oman verkkosivun toteuttaminen ajankohtaista?'

Tyyli: 85–140 sanaa, suomalaisessa yritysviestinnässä suora,
ystävällinen, itsevarma, asiakasta kunnioittava, aito ihminen.
Ei pitkiä sepustuksia, tekaistuja kehuja, yleisiä korulauseita,
psykologista painostusta, feikkituloksia, keinotekoista kiirettä,
tapaamispakkoa, puolustelevaa pehmentelyä, outoa jargonia tai
korostuksia CAPS LOCKILLA. Älä käytä pitkää tai lyhyttä ajatusviivaa
myyntiviestin lauseissa tai erotinviivarivejä.

Jokainen yritys tarvitsee oman havaintonsa ja demossaan OIKEASTI
näkyvän ratkaisun. Jos tiedot eivät tue havaintoa, älä keksi
sellaista. Tällainen keskeneräinen luonnos vaatii ihmisen
tarkistuksen ennen mahdollista lähettämistä.

Älä sisällytä kieltäytymistekstiä henkilökohtaiseen myyntirunkoon.
Mahdollisessa todellisessa suoramarkkinointisähköpostissa säilytä
selkeä ja maksuton markkinointikielto erillisessä HTML-alatunnisteessa.
Sähköposti lähetetään vain ihmisen erillisellä hyväksynnällä.

Palauta VAIN validi JSON:
{"subject":"lyhyt yrityskohtainen suora otsikko","body":"valmis sähköpostin runko"}
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

Kirjoita näiden tietojen perusteella Kaarlon omalla nimellä suora ja
henkilökohtainen MYYNTIsähköposti. Osoita lyhyesti, mikä nykyisessä
sivussa kaipaa uudistusta, miten valmis demo näyttää ratkaisun ja
tarjoa nimenomaisesti uuden sivuston toteuttamista.
Jos nykyistä sivua ei ole riippumattomasti varmistettu olemassaolevaksi,
älä väitä nähneesi sivua tai sen heikkouksia. Silloin myy uuden
sivuston toteutusta, ei uudistusta.
Vastaanottajan nimi on tiedossa vain, jos kentässä on lähteistetty
tarkistettu nimi. Älä keksi henkilön nimeä.
Valmis julkinen demolinkki (ei anneta ellei vahvistettu):
{company.get("demo_url", "")}
Jos tämä on tyhjä, viesti voi viitata kuvan ja linkin sisältävään
erilliseen hyväksyttyyn HTML-demokorttiin. Älä keksi URLia.
Jokainen asiakkaan hyöty ja havainto tarkistetaan ennen lähettämistä.
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
    # Do not silently save impersonal stock copy or user-disliked dashes.
    # AI can try again only on a new explicitly approved manual run.
    if any(mark in body for mark in ("—", "–")):
        raise RuntimeError(
            "Outreach copy contains sentence-divider dashes. "
            "Revise the draft without AI-style em/en dashes."
        )
    if "jos et toivo kaurivolta muita yhteydenottoja" in body.casefold():
        raise RuntimeError(
            "Keep the legal marketing opt-out in the separate email footer, "
            "not in the personal sales copy."
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
