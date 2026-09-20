"""
Website Builder -agentti.

Rakentaa research-datan perusteella yhden sivun verkkosivun.

Tärkeä periaate:
AI ei saa keksiä yrityksen faktoja.
Faktat validoidaan myös ohjelmallisesti ennen tallennusta.
"""

import os
import re
import webbrowser

from utils.claude_client import ask_claude
from utils.state import (
    get_company,
    upsert_company,
    set_status,
)
import config


BUILD_SYSTEM_PROMPT = """
Olet kokenut frontend-kehittäjä.

Rakennat tutkimusdatan perusteella ammattimaisen,
responsiivisen yhden sivun verkkosivun.

TÄRKEIN SÄÄNTÖ:

ÄLÄ KEKSI YHTÄÄN YRITYKSEN FAKTAA.

Sallittuja yrityksen faktoja ovat VAIN käyttäjän
antamassa VERIFIED FACTS -osiossa olevat tiedot.

Älä keksi:
- palveluita
- tuotteita
- hintoja
- toimialaa
- sijaintia
- osoitetta
- puhelinnumeroa
- sähköpostia
- aukioloaikoja
- asiakkaita
- referenssejä
- kokemusta
- henkilöstömäärää
- perustamisvuotta
- sertifikaatteja
- palkintoja
- yrityksen toimintaa kuvaavia väitteitä.

ÄLÄ päättele yrityksen toimintaa:
- nimestä
- domainista
- target audience -kentästä
- design-suosituksista
- hakutuloksista
- yleisestä tiedosta.

TARGET AUDIENCE EI OLE YRITYKSEN PALVELU.

DESIGN-RECOMMENDATIONS EIVÄT OLE YRITYKSEN FAKTOJA.

Jos tieto puuttuu, jätä se pois.

Älä täytä tyhjää kohtaa markkinointitekstillä.

Jos yrityksestä on hyvin vähän tietoa, tee tarkoituksella
yksinkertainen mutta visuaalisesti hyvä sivu.

TAGLINE:

Jos VERIFIED FACTS sisältää vahvistetun taglinen,
saat käyttää sitä.

Älä muuta taglinen merkitystä uudeksi yrityksen
toimintaa kuvaavaksi väitteeksi.

Jos tagline puuttuu, käytä yrityksen nimeä otsikkona
ja neutraalia tekstiä, joka kertoo vain että saatavilla
oleva tutkimustieto on rajallinen.

META DESCRIPTION:

Sen pitää perustua vain vahvistettuihin tietoihin.

Älä kirjoita keksittyä markkinointikuvausta.

CTA:

Älä käytä "Ota yhteyttä" -painiketta ilman vahvistettua
yhteystietoa.

Älä tee kuvitteellista sähköpostia, puhelinnumeroa tai
yhteydenottolomaketta.

YHTEYSTIEDOT:

Näytä vain VERIFIED FACTS -osiossa olevat yhteystiedot.

DESIGN:

Noudata design-suosituksia vain visuaalisesti.

Väripaletti voidaan ottaa design-suosituksista.

Fonttisuositusta voidaan käyttää, mutta älä lataa
ulkoisia fontteja tai muita ulkoisia resursseja.

Älä lisää ulkoisia JavaScript-kirjastoja.

Älä lisää ulkoisia kuvia.

TEKNIIKKA:

Kaikki yhdessä index.html-tiedostossa.

Käytä:
- <!DOCTYPE html>
- <html lang="fi">
- <head>
- <meta charset>
- viewport
- title
- meta description
- style
- header
- nav
- main
- footer
- script vain tarvittaessa.

Sivun pitää olla responsiivinen.

Navigaation ankkurien pitää osoittaa oikeasti olemassa
oleviin osioihin.

ACCESSIBILITY:

Käytä semanttista HTML:ää.
Varmista riittävä kontrasti.
Käytä selkeitä otsikkotasoja.
Älä käytä pelkkiä koriste-elementtejä sisältönä.

KIELI:

Kirjoita luonnollista suomea.

Jos vahvistettu tagline on englanniksi, sitä ei tarvitse
kääntää eikä sen merkitystä saa muuttaa.

PALAUTUS:

Palauta VAIN koko HTML-tiedosto.

Älä käytä markdown-koodilohkoa.
Älä lisää selityksiä.
"""


REVISE_SYSTEM_PROMPT = """
Olet kokenut frontend-kehittäjä.

Saat nykyisen HTML-sivun, tutkimusdatan ja muutospyynnön.

Palauta koko päivitetty HTML.

TÄRKEIN SÄÄNTÖ:

ÄLÄ KEKSI uusia yrityksen faktoja.

Sallittuja yrityksen faktoja ovat VAIN VERIFIED FACTS
-osiossa annetut tiedot.

Älä lisää ilman vahvistettua tietoa:
- palveluita
- tuotteita
- hintoja
- sijaintia
- osoitetta
- puhelinta
- sähköpostia
- asiakkaita
- kokemusta
- perustamisvuotta
- palkintoja
- sertifikaatteja
- markkinointiväitteitä.

TARGET AUDIENCE ei ole palvelu.

DESIGN-RECOMMENDATIONS eivät ole yrityksen faktoja.

Jos tieto puuttuu, jätä se pois.

Säilytä:
- semanttinen HTML
- nav
- main
- footer
- title
- meta description
- responsiivisuus
- accessibility
- vahvistetut faktat.

Älä lisää ulkoisia fontteja, kuvia tai JavaScript-kirjastoja.

Palauta VAIN koko HTML.
"""


def _output_dir(slug: str) -> str:
    return os.path.join(config.OUTPUT_DIR, slug)


def _output_path(slug: str) -> str:
    return os.path.join(_output_dir(slug), "index.html")


def _clean_html(html: str) -> str:
    cleaned = (html or "").strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    return cleaned


def _write_html(slug: str, html: str) -> str:
    if not html:
        raise RuntimeError(
            "AI ei palauttanut HTML-sisältöä."
        )

    cleaned = _clean_html(html)

    if not cleaned.lower().startswith("<!doctype html"):
        raise RuntimeError(
            "AI:n palauttama sisältö ei ala <!DOCTYPE html>."
        )

    required = [
        "<html",
        "<head",
        "</head>",
        "<body",
        "</body>",
        "</html>",
        "<nav",
        "</nav>",
        "<main",
        "</main>",
        "<footer",
        "</footer>",
        "<title",
        'name="description"',
    ]

    lowered = cleaned.lower()

    missing = [
        item
        for item in required
        if item.lower() not in lowered
    ]

    if missing:
        raise RuntimeError(
            "AI:n HTML:stä puuttuu pakollisia rakenteita: "
            + ", ".join(missing)
        )

    # Builderin ei pidä käyttää ulkoisia resursseja.
    external_resource_patterns = [
        r'<link[^>]+href=["\']https?://',
        r'<script[^>]+src=["\']https?://',
        r'<img[^>]+src=["\']https?://',
    ]

    for pattern in external_resource_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise RuntimeError(
                "AI:n HTML sisältää ulkoisen resurssin. "
                "Sivun pitää olla täysin itsenäinen."
            )

    out_dir = _output_dir(slug)

    os.makedirs(
        out_dir,
        exist_ok=True,
    )

    path = _output_path(slug)

    with open(
        path,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(cleaned)

    return path


def _resolve_company(slug_or_name: str) -> tuple[str, dict]:
    slug, company = get_company(slug_or_name)

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    return slug, company


def _safe_fact_summary(company_facts: dict) -> str:
    allowed = {
        "name": company_facts.get("name", ""),
        "industry": company_facts.get("industry", ""),
        "services": company_facts.get("services", []),
        "location": company_facts.get("location", ""),
        "phone": company_facts.get("contact_phone", ""),
        "email": company_facts.get("contact_email", ""),
        "address": company_facts.get("contact_address", ""),
        "opening_hours": company_facts.get("opening_hours", {}),
        "tagline": company_facts.get("tagline", ""),
        "target_audience": company_facts.get(
            "target_audience",
            "",
        ),
    }

    return repr(allowed)


def _validate_generated_content(
    html: str,
    company_facts: dict,
) -> None:
    """
    Paikallinen turvatarkistus.

    Tämä ei käytä AI:ta eikä API-kutsuja.
    """

    text = re.sub(
        r"<[^>]+>",
        " ",
        html,
    )

    text = re.sub(
        r"\s+",
        " ",
        text,
    ).strip().lower()

    services = company_facts.get(
        "services",
        [],
    )

    phone = company_facts.get(
        "contact_phone",
        "",
    )

    email = company_facts.get(
        "contact_email",
        "",
    )

    address = company_facts.get(
        "contact_address",
        "",
    )

    location = company_facts.get(
        "location",
        "",
    )

    industry = company_facts.get(
        "industry",
        "",
    )

    # Jos vahvistettuja palveluita ei ole,
    # estä tyypilliset keksityt palvelulistat.
    if not services:
        forbidden_service_terms = [
            "palvelumme",
            "palveluihimme",
            "tarjoamme",
            "palveluvalikoima",
            "asiantuntijapalvelut",
            "web-suunnittelu",
            "verkkosivujen suunnittelu",
        ]

        found = [
            term
            for term in forbidden_service_terms
            if term in text
        ]

        if found:
            raise RuntimeError(
                "Builder näyttää keksineen palvelusisältöä "
                "vaikka researchissä ei ole vahvistettuja "
                f"palveluita: {', '.join(found)}"
            )

    # Älä salli yhteydenottokehotusta ilman yhteystietoa.
    if not any([phone, email, address]):
        forbidden_contact_terms = [
            "ota yhteyttä",
            "ota meihin yhteyttä",
            "contact us",
            "soita meille",
            "lähetä viesti",
            "varaa aika",
        ]

        found = [
            term
            for term in forbidden_contact_terms
            if term in text
        ]

        if found:
            raise RuntimeError(
                "Builder loi yhteydenottokehotuksen ilman "
                "vahvistettuja yhteystietoja: "
                + ", ".join(found)
            )

    # Tyypillisiä keksittyjä yritysfaktoja.
    fabricated_patterns = [
        r"\b\d+\s+vuoden kokem",
        r"perustettu\s+\d{4}",
        r"vuodesta\s+\d{4}",
        r"yli\s+\d+\s+(?:asiakka|ammattila)",
    ]

    for pattern in fabricated_patterns:
        if re.search(pattern, text):
            raise RuntimeError(
                "Builderin tuottamassa sivussa havaittiin "
                "mahdollisesti keksitty yritysfakta."
            )

    # Jos toimiala puuttuu, AI ei saa esitellä keksittyä toimialaa.
    # Emme käytä yleistä sanalistaa, koska se voisi aiheuttaa
    # vääriä hälytyksiä. Tämä tarkistus suojaa erityisesti
    # tutkimuksessa selvästi puuttuvaa location/industry-dataa
    # vain yhteystietojen osalta.

    _ = location
    _ = industry


def build_site(
    slug: str,
    company: dict,
) -> str:

    research = company.get("research")

    if not research:
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy research-dataa. "
            f"Aja ensin: python main.py research {slug}"
        )

    company_facts = research.get(
        "company_facts",
        {},
    )

    weaknesses = research.get(
        "current_site_weaknesses",
        [],
    )

    inspiration = research.get(
        "design_inspiration",
        [],
    )

    recommendations = research.get(
        "design_recommendations",
        {},
    )

    fact_summary = _safe_fact_summary(
        company_facts
    )

    user_prompt = f"""
Rakenna verkkosivu tämän research-datan perusteella.

========================================
VERIFIED FACTS
========================================

{fact_summary}

Nämä ovat AINOAT yrityksen faktat.

========================================
NYKYISEN SIVUN HEIKKOUDET
========================================

{weaknesses}

========================================
DESIGN-INSPIRAATIO
========================================

{inspiration}

========================================
DESIGN-SUOSITUKSET
========================================

{recommendations}

HUOMIO:

Design-suositukset ovat vain VISUAALISIA suosituksia.

Niitä EI saa käyttää yrityksen puuttuvien faktojen
täyttämiseen.

========================================
ERITYISEN TÄRKEÄT SÄÄNNÖT
========================================

Jos services on tyhjä:
ÄLÄ kirjoita palvelulistaa.

Jos industry on tyhjä:
ÄLÄ nimeä yrityksen toimialaa.

Jos location on tyhjä:
ÄLÄ nimeä kaupunkia tai maata.

Jos address on tyhjä:
ÄLÄ kirjoita osoitetta.

Jos phone on tyhjä:
ÄLÄ kirjoita puhelinnumeroa.

Jos email on tyhjä:
ÄLÄ kirjoita sähköpostiosoitetta.

Jos pricing-tietoa ei ole:
ÄLÄ kirjoita hintoja.

Jos opening_hours on tyhjä:
ÄLÄ kirjoita aukioloaikoja.

Jos yhteystietoja ei ole:
ÄLÄ tee "Ota yhteyttä" -painiketta.

ÄLÄ muuta target_audience-kenttää yrityksen
palveluksi tai tuotteeksi.

ÄLÄ muuta taglinea uudeksi yrityksen toimintaa
kuvaavaksi markkinointiväitteeksi.

Jos tietoa ei ole:
JÄTÄ SE POIS.

========================================
SIVUN RAKENNE
========================================

Tee visuaalisesti hyvä mutta sisällöltään rehellinen
sivu.

Jos tutkimustietoa on vähän, sivu saa olla lyhyt.

Älä lisää kuvitteellisia osioita vain siksi, että
design-suosituksessa niitä ehdotetaan.

========================================
TEKNINEN TOTEUTUS
========================================

Yksi itsenäinen index.html.

Ei:
- Google Fonts -linkkiä
- ulkoisia kuvia
- ulkoisia JavaScript-kirjastoja
- ulkoisia CSS-tiedostoja.

Kaikki CSS inline <style>-elementissä.

Tarvittaessa JavaScript inline <script>-elementissä.

Varmista:
- <!DOCTYPE html>
- <html lang="fi">
- <head>
- title
- meta description
- nav
- main
- footer
- responsiivisuus
- accessibility.

Palauta VAIN koko HTML.
"""

    print(
        "  [Builder] Generoidaan verkkosivua..."
    )

    html = ask_claude(
        BUILD_SYSTEM_PROMPT,
        user_prompt,
        use_web_search=False,
        max_tokens=8000,
    )

    cleaned = _clean_html(html)

    # Ohjelmallinen faktaturva ennen tiedoston kirjoittamista.
    _validate_generated_content(
        cleaned,
        company_facts,
    )

    path = _write_html(
        slug,
        cleaned,
    )

    old_build = company.get(
        "build",
        {},
    )

    old_version = old_build.get(
        "version",
        0,
    )

    version = old_version + 1

    upsert_company(
        slug,
        {
            "build": {
                "output_path": path,
                "version": version,
            }
        },
    )

    set_status(
        slug,
        "built",
    )

    print(
        f"  [Builder] Sivusto valmis: {path}"
    )

    return path


def run_build(
    slug_or_name: str,
) -> str:

    slug, company = _resolve_company(
        slug_or_name
    )

    return build_site(
        slug,
        company,
    )


def revise_site(
    slug: str,
    company: dict,
    feedback: str,
) -> str:

    path = _output_path(slug)

    if not os.path.exists(path):
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy rakennettua sivua. "
            f"Aja ensin: python main.py build {slug}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        current_html = file.read()

    research = company.get(
        "research",
        {},
    )

    company_facts = research.get(
        "company_facts",
        {},
    )

    user_prompt = f"""
========================================
VERIFIED FACTS
========================================

{_safe_fact_summary(company_facts)}

========================================
NYKYINEN HTML
========================================

{current_html}

========================================
MUUTOSPYYNTÖ
========================================

{feedback}

========================================
SÄÄNNÖT
========================================

Tee pyydetyt muutokset.

ÄLÄ keksi yrityksen faktoja.

Jos tieto puuttuu:
jätä se pois.

TARGET AUDIENCE ei ole yrityksen palvelu.

DESIGN-RECOMMENDATIONS eivät ole yrityksen faktoja.

Älä lisää ilman vahvistettua tietoa:
- palveluita
- tuotteita
- hintoja
- yhteystietoja
- sijaintia
- asiakkaita
- kokemusta
- vuosilukuja
- markkinointiväitteitä.

Älä lisää ulkoisia resursseja.

Säilytä:
- nav
- main
- footer
- title
- meta description
- responsiivisuus
- accessibility.

Palauta koko HTML.
"""

    print(
        "  [Builder] Muokataan verkkosivua..."
    )

    new_html = ask_claude(
        REVISE_SYSTEM_PROMPT,
        user_prompt,
        use_web_search=False,
        max_tokens=8000,
    )

    cleaned = _clean_html(new_html)

    _validate_generated_content(
        cleaned,
        company_facts,
    )

    new_path = _write_html(
        slug,
        cleaned,
    )

    old_build = company.get(
        "build",
        {},
    )

    old_version = old_build.get(
        "version",
        1,
    )

    version = old_version + 1

    upsert_company(
        slug,
        {
            "build": {
                "output_path": new_path,
                "version": version,
                "last_feedback": feedback,
            }
        },
    )

    set_status(
        slug,
        "built",
    )

    print(
        f"  [Builder] Sivusto päivitetty: {new_path}"
    )

    return new_path


def run_revise(
    slug_or_name: str,
    feedback: str,
) -> str:

    slug, company = _resolve_company(
        slug_or_name
    )

    return revise_site(
        slug,
        company,
        feedback,
    )


def preview_site(
    slug: str,
    company: dict,
) -> str:

    path = _output_path(slug)

    if not os.path.exists(path):
        raise RuntimeError(
            f"Esikatseltavaa sivua ei löydy: {path}"
        )

    absolute_path = os.path.abspath(path)

    print(
        f"  [Preview] {absolute_path}"
    )

    try:
        webbrowser.open(
            "file://" + absolute_path
        )
    except Exception:
        pass

    return absolute_path


def run_preview(
    slug_or_name: str,
) -> str:

    slug, company = _resolve_company(
        slug_or_name
    )

    return preview_site(
        slug,
        company,
    )
