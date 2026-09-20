"""
QA-agentti.

Tarkistaa rakennetun index.html-tiedoston:
1. paikallisilla/automaattisilla tarkistuksilla
2. AI-pohjaisella sisältö- ja laatutarkistuksella

Tärkeä periaate:
Puuttuva tutkimustieto EI ole virhe.

QA ei saa vaatia esimerkiksi palveluita, hintoja,
yhteystietoja tai sijaintia, jos research-data ei
sisällä niitä.
"""

import os
import re

from bs4 import BeautifulSoup

from utils.claude_client import ask_claude_json
from utils.state import (
    get_company,
    upsert_company,
    set_status,
)


QA_SYSTEM_PROMPT = """
Olet verkkosivuston QA-tarkastaja.

Tarkistat tutkimusdatan perusteella rakennetun
verkkosivuston.

========================================
TÄRKEIN QA-SÄÄNTÖ
========================================

PUUTTUVA TIETO EI OLE VIRHE.

Jos research-datassa ei ole:
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
- perustamisvuotta

sivun EI tarvitse sisältää niitä.

ÄLÄ merkitse puuttuvaa tietoa ongelmaksi.

ÄLÄ vaadi sivulle osiota vain siksi, että
design-recommendations suosittelee sitä.

========================================
DESIGN-RECOMMENDATIONS
========================================

Design-recommendations kertoo ensisijaisesti
VISUAALISISTA ja rakenteellisista ideoista.

Se EI ole lista pakollisista yrityksen faktoista.

Esimerkiksi jos design recommendations sisältää:

- Services
- Pricing
- Contact
- About
- Events

mutta company facts ei sisällä näiden sisältöä,
sivuston EI tarvitse keksiä tai lisätä niitä.

Builder toimii oikein, jos se jättää tällaisen
sisällön pois.

========================================
FAKTAT
========================================

Tarkista erityisesti:

- Onko sivulla keksittyjä yrityksen faktoja?
- Onko keksitty palveluita?
- Onko keksitty yhteystietoja?
- Onko keksitty sijainti?
- Onko keksitty hintoja?
- Onko keksitty kokemusta?
- Onko keksitty asiakkaita?
- Onko keksitty perustamisvuosi?
- Onko keksitty yrityksen toimintaa kuvaavia väitteitä?

Yrityksen väitteiden pitää perustua VERIFIED COMPANY
FACTS -tietoihin.

TARGET AUDIENCE ei automaattisesti tarkoita,
että yritys tarjoaa kyseiselle kohderyhmälle palvelua.

DESIGN-RECOMMENDATIONS eivät ole yrityksen faktoja.

========================================
TAGLINE
========================================

Jos researchissä on tagline, tarkista ettei builder
ole muuttanut sen merkitystä niin, että yritykselle
syntyy uusi toimintaa kuvaava väite.

Jos tagline on esimerkiksi:

"This domain is for use in documentation examples
without needing permission. Avoid use in operations."

sitä ei saa muuttaa esimerkiksi muotoon:

"Tarjoamme dokumentaatiopalveluita."

========================================
META DESCRIPTION
========================================

Meta description saa olla lyhyt ja neutraali.

Sen ei tarvitse sisältää kaikkia research-faktoja.

Se ei kuitenkaan saa sisältää keksittyjä yrityksen
ominaisuuksia tai markkinointiväitteitä.

========================================
CTA
========================================

CTA ei ole pakollinen.

Jos yhteystietoja ei ole researchissä,
"ei yhteydenotto-CTA:ta" EI ole ongelma.

Jos CTA kuitenkin väittää esimerkiksi:

"Ota yhteyttä"

sen pitää johtaa oikeaan yhteydenottosisältöön
tai vahvistettuun yhteystietoon.

========================================
SISÄLTÖ
========================================

Lyhyt sivu ei automaattisesti ole huono sivu.

Jos tutkimustietoa on vähän, myös rakennettu sivu
saa olla lyhyt.

Älä merkitse sivua FAILiksi vain siksi, että se
ei muistuta laajaa yrityksen markkinointisivustoa.

Testidomainit ja dokumentaatioesimerkit voivat
sisältää hyvin vähän tietoa.

========================================
TEKSTIN LAATU
========================================

Merkitse ongelmaksi:

- selvä kielioppivirhe
- erittäin epäluonnollinen teksti
- keskeneräinen lause
- ilmeinen AI-roska
- Lorem ipsum
- placeholder-teksti
- ristiriitainen yritysfakta.

Yksinkertainen tai lyhyt teksti ei yksinään ole ongelma.

========================================
RAKENNE
========================================

Tarkista:

- selkeä rakenne
- navigaatio
- main-sisältö
- footer
- otsikot
- responsiivinen rakenne
- accessibility
- ettei HTML ole selvästi katkennut.

========================================
DESIGN
========================================

Tarkista, että sivu käyttää researchin design-suosituksia
järkevästi.

Älä kuitenkaan vaadi tiettyä sisältöosiota, jos sen
sisältöä ei ole researchissä.

========================================
PALAUTUS
========================================

Ole konservatiivinen.

FAIL vain todellisesta ongelmasta.

Jos sivu on tutkimustiedon määrään nähden tarkoituksella
yksinkertainen ja siinä ei ole keksittyjä faktoja,
sen pitää saada PASS.

Palauta VAIN validi JSON:

{
  "content_ok": true,
  "issues": [],
  "notes": "Lyhyt arvio"
}

Jos löydät todellisen ongelman:

{
  "content_ok": false,
  "issues": [
    "..."
  ],
  "notes": "..."
}

issues saa sisältää enintään 8 tärkeintä ongelmaa.

Älä kirjoita analyysia ennen JSONia.
Älä kirjoita JSONin jälkeen mitään.
"""


def _automated_checks(html: str) -> dict:
    issues = []

    if not html or not html.strip():
        return {
            "has_viewport_meta": False,
            "automated_issues": [
                "HTML-tiedosto on tyhjä."
            ],
            "automated_pass": False,
        }

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # DOCTYPE
    if not html.lstrip().lower().startswith(
        "<!doctype html"
    ):
        issues.append(
            "HTML-tiedostosta puuttuu <!DOCTYPE html>."
        )

    # TITLE
    title = soup.find("title")

    if not title or not title.get_text(strip=True):
        issues.append(
            "Sivulta puuttuu <title>-elementti."
        )

    # META DESCRIPTION
    description = soup.find(
        "meta",
        attrs={"name": "description"},
    )

    if (
        description is None
        or not description.get("content", "").strip()
    ):
        issues.append(
            "Sivulta puuttuu meta description."
        )

    # VIEWPORT
    viewport = soup.find(
        "meta",
        attrs={"name": "viewport"},
    )

    has_viewport = viewport is not None

    if not has_viewport:
        issues.append(
            "Puuttuva viewport-meta."
        )

    # H1
    h1_elements = soup.find_all("h1")

    if len(h1_elements) == 0:
        issues.append(
            "Sivulta puuttuu H1-otsikko."
        )

    elif len(h1_elements) > 1:
        issues.append(
            f"Sivulla on {len(h1_elements)} H1-otsikkoa."
        )

    # IMAGE ALT
    imgs_without_alt = [
        img
        for img in soup.find_all("img")
        if img.get("alt") is None
    ]

    if imgs_without_alt:
        issues.append(
            f"{len(imgs_without_alt)} img-elementtiä ilman alt-tekstiä."
        )

    # ANCHOR LINKS
    ids = {
        tag.get("id")
        for tag in soup.find_all(id=True)
        if tag.get("id")
    }

    broken_anchors = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        href = anchor.get(
            "href",
            "",
        ).strip()

        if href.startswith("#") and len(href) > 1:
            target = href[1:]

            if target not in ids:
                broken_anchors.append(href)

    if broken_anchors:
        issues.append(
            "Rikkinäisiä ankkurilinkkejä: "
            + ", ".join(broken_anchors)
        )

    # EMPTY LINKS
    empty_links = []

    for anchor in soup.find_all("a"):
        href = anchor.get(
            "href",
            "",
        ).strip()

        text = anchor.get_text(
            " ",
            strip=True,
        )

        aria = anchor.get(
            "aria-label",
            "",
        ).strip()

        if not href and not text and not aria:
            empty_links.append(anchor)

    if empty_links:
        issues.append(
            f"{len(empty_links)} tyhjää linkkielementtiä."
        )

    # EMPTY BUTTONS
    empty_buttons = []

    for button in soup.find_all("button"):
        text = button.get_text(
            " ",
            strip=True,
        )

        aria = button.get(
            "aria-label",
            "",
        ).strip()

        if not text and not aria:
            empty_buttons.append(button)

    if empty_buttons:
        issues.append(
            f"{len(empty_buttons)} tyhjää button-elementtiä."
        )

    # PLACEHOLDERS
    text = soup.get_text(
        " ",
        strip=True,
    )

    placeholder_patterns = [
        r"lorem ipsum",
        r"\[.*?täytä.*?\]",
        r"\[.*?lisää.*?\]",
        r"placeholder",
        r"your company",
        r"company name here",
    ]

    for pattern in placeholder_patterns:
        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            issues.append(
                f"Löytyi placeholder-tekstiä: '{pattern}'."
            )

    # INSECURE HTTP LINKS
    insecure_links = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        href = anchor.get(
            "href",
            "",
        ).strip()

        if href.startswith("http://"):
            insecure_links.append(href)

    if insecure_links:
        issues.append(
            f"{len(insecure_links)} ulkoista linkkiä käyttää http://."
        )

    # REQUIRED HTML ELEMENTS
    required_elements = {
        "header": soup.find("header"),
        "nav": soup.find("nav"),
        "main": soup.find("main"),
        "footer": soup.find("footer"),
    }

    for element_name, element in required_elements.items():
        if element is None:
            issues.append(
                f"Sivulta puuttuu <{element_name}>-elementti."
            )

    # MAIN CONTENT
    main = soup.find("main")

    if main is not None:
        main_text = main.get_text(
            " ",
            strip=True,
        )

        # Hyvin lyhyt sisältö voi olla hyväksyttävää,
        # jos research-data on vähäistä.
        # Siksi emme tee lyhyestä sisällöstä automaattista FAILia.

        if not main_text:
            issues.append(
                "Main-elementti on täysin tyhjä."
            )

    # EXTERNAL RESOURCES
    external_resources = []

    for tag in soup.find_all(
        ["script", "link"],
    ):
        source = (
            tag.get("src")
            or tag.get("href")
            or ""
        ).strip()

        if source.startswith(
            (
                "http://",
                "https://",
            )
        ):
            external_resources.append(source)

    if external_resources:
        issues.append(
            "HTML käyttää ulkoisia resursseja: "
            + ", ".join(
                external_resources[:5]
            )
        )

    return {
        "has_viewport_meta": has_viewport,
        "automated_issues": issues,
        "automated_pass": len(issues) == 0,
    }


def _build_ai_snapshot(html: str) -> str:
    """
    Luo HTML:stä AI-QA:lle tiiviin tarkistusmateriaalin.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    title = ""

    title_tag = soup.find("title")

    if title_tag:
        title = title_tag.get_text(
            " ",
            strip=True,
        )

    headings = []

    for tag in soup.find_all(
        ["h1", "h2", "h3"],
    ):
        text = tag.get_text(
            " ",
            strip=True,
        )

        if text:
            headings.append(
                f"{tag.name}: {text}"
            )

    links = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        text = anchor.get_text(
            " ",
            strip=True,
        )

        href = anchor.get(
            "href",
            "",
        ).strip()

        if text or href:
            links.append(
                f"{text[:100]} -> {href[:200]}"
            )

    images = []

    for img in soup.find_all("img"):
        images.append(
            f"alt={img.get('alt', '')!r}, "
            f"src={img.get('src', '')[:200]!r}"
        )

    body_text = soup.get_text(
        " ",
        strip=True,
    )

    body_text = body_text[:9000]

    html_end = html[-2500:]

    return f"""
TITLE:
{title}

HEADINGS:
{chr(10).join(headings[:30])}

LINKS:
{chr(10).join(links[:40])}

IMAGES:
{chr(10).join(images[:30])}

VISIBLE TEXT:
{body_text}

HTML END:
{html_end}
""".strip()


def run_qa(
    slug_or_name: str,
) -> dict:

    slug, company = get_company(
        slug_or_name
    )

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    build_info = company.get(
        "build"
    )

    if not build_info:
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy build-dataa. "
            f"Aja ensin: python main.py build {slug}"
        )

    output_path = build_info.get(
        "output_path",
        "",
    )

    if (
        not output_path
        or not os.path.exists(output_path)
    ):
        raise RuntimeError(
            "Rakennettua HTML-tiedostoa ei löytynyt: "
            f"{output_path}"
        )

    print()
    print("=== QA ===")
    print(
        f"Yritys: {company.get('name', '')}"
    )

    with open(
        output_path,
        "r",
        encoding="utf-8",
    ) as file:
        html = file.read()

    print(
        "  [QA] Tehdään automaattiset tarkistukset..."
    )

    automated = _automated_checks(
        html
    )

    print(
        "  [QA] Automaattisia ongelmia: "
        f"{len(automated['automated_issues'])}"
    )

    # Jos paikallinen QA epäonnistuu,
    # AI-QA:ta ei tarvitse käyttää.
    #
    # Tämä säästää ilmaista AI-kiintiötä ja estää
    # turhan AI-kutsun silloin, kun rakenne on jo
    # selvästi rikki.
    if not automated["automated_pass"]:
        qa_result = {
            "automated": automated,
            "content_review": {
                "content_ok": False,
                "issues": [],
                "notes": (
                    "AI-QA ohitettiin, koska paikallinen "
                    "QA löysi rakenteellisia ongelmia."
                ),
            },
            "overall_pass": False,
        }

        upsert_company(
            slug,
            {
                "qa": qa_result,
            },
        )

        set_status(
            slug,
            "built",
        )

        print(
            "  [QA] AI-sisältötarkistus ohitettiin."
        )

        print()
        print("=== QA VALMIS ===")
        print("Tulos: FAIL")

        print(
            "  [QA] Automaattiset ongelmat:"
        )

        for issue in automated[
            "automated_issues"
        ]:
            print(
                f"    - {issue}"
            )

        return qa_result

    research = company.get(
        "research",
        {},
    )

    company_facts = research.get(
        "company_facts",
        {},
    )

    design_recommendations = research.get(
        "design_recommendations",
        {},
    )

    ai_snapshot = _build_ai_snapshot(
        html
    )

    user_prompt = f"""
=== VERIFIED COMPANY FACTS ===

{company_facts}

========================================
TÄRKEÄÄ
========================================

Nämä ovat ainoat vahvistetut yrityksen faktat.

Jos jokin tieto puuttuu, sen puuttuminen EI ole virhe.

Älä vaadi sivulta:
- palveluita
- hintoja
- yhteystietoja
- sijaintia
- toimialaa
- asiakkaita
- referenssejä

jos niitä ei ole VERIFIED COMPANY FACTS -datassa.

========================================
DESIGN RECOMMENDATIONS
========================================

{design_recommendations}

Design recommendations ovat visuaalisia ja
rakenteellisia suosituksia.

Ne EIVÄT ole pakollisia yrityksen sisältöjä.

Jos suositus sanoo esimerkiksi:
"palvelut-osio"

mutta VERIFIED COMPANY FACTS ei sisällä
palveluita, builder toimii oikein jättämällä
palvelut-osan pois.

ÄLÄ merkitse tätä virheeksi.

========================================
RAKENNETTU SIVU
========================================

{ai_snapshot}

========================================
TARKISTA NYT
========================================

1. Keksiikö sivu yrityksen faktoja?

2. Onko sivulla palveluita, joita research ei vahvista?

3. Onko sivulla keksittyjä yhteystietoja?

4. Onko tagline muutettu yrityksen toimintaa
   kuvaavaksi keksityksi väitteeksi?

5. Onko meta descriptionissa keksittyjä faktoja?

6. Onko sivulla selviä placeholder-tekstejä?

7. Onko teksti selvästi rikkinäistä tai
   epäluonnollista?

8. Onko rakenne keskeneräinen?

9. Onko CTA harhaanjohtava?

10. Onko sivu tutkimustiedon määrään nähden
    järkevä?

ÄLÄ FAILAA SIVUA vain siksi, että se on lyhyt.

ÄLÄ FAILAA SIVUA siksi, että siitä puuttuu
tietoja, joita research ei sisällä.

ÄLÄ FAILAA SIVUA siksi, ettei se toteuta jokaista
design recommendation -kohtaa.

FAIL vain todellisesta ongelmasta.

Jos sivu käyttää vain vahvistettua tietoa ja
rakenne on kunnossa, anna PASS.

Palauta vain JSON.
"""

    print(
        "  [QA] Tehdään AI-sisältötarkistus..."
    )

    content_review = ask_claude_json(
        QA_SYSTEM_PROMPT,
        user_prompt,
        use_web_search=False,
        max_tokens=2500,
    )

    if not isinstance(
        content_review,
        dict,
    ):
        content_review = {
            "content_ok": False,
            "issues": [
                "AI:n QA-vastaus ei ollut validi JSON-objekti."
            ],
            "notes": "",
        }

    ai_content_ok = bool(
        content_review.get(
            "content_ok",
            False,
        )
    )

    overall_pass = (
        automated.get(
            "automated_pass",
            False,
        )
        and ai_content_ok
    )

    qa_result = {
        "automated": automated,
        "content_review": content_review,
        "overall_pass": overall_pass,
    }

    upsert_company(
        slug,
        {
            "qa": qa_result,
        },
    )

    if overall_pass:
        set_status(
            slug,
            "qa_passed",
        )

        print("  [QA] PASS")

    else:
        set_status(
            slug,
            "built",
        )

        print("  [QA] FAIL")

        ai_issues = content_review.get(
            "issues",
            [],
        )

        if ai_issues:
            print(
                "  [QA] AI:n havaitsemat ongelmat:"
            )

            for issue in ai_issues:
                print(
                    f"    - {issue}"
                )

    print()
    print("=== QA VALMIS ===")
    print(
        "Tulos: "
        f"{'PASS' if overall_pass else 'FAIL'}"
    )

    return qa_result
