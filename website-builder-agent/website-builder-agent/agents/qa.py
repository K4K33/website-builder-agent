"""
QA-agentti.

Tarkistaa rakennetun index.html-tiedoston automaattisesti ja AI:n avulla.

Tarkistukset:
- viewport-meta
- HTML-rakenne
- puuttuvat alt-tekstit
- puuttuvat aria-labelit tarvittaessa
- rikkinäiset sisäiset ankkurilinkit
- placeholder-tekstit
- http://-ulkoiset linkit
- tyhjät linkit ja painikkeet
- research-faktojen ja sivun sisällön vastaavuus
- tekstin laatu
- sivun kokonaisuuden uskottavuus

QA:n pitää läpäistä ennen kuin sivusto voidaan hyväksyä.
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


QA_SYSTEM_PROMPT = """Olet QA-agentti, joka tarkistaa juuri rakennetun
yrityksen verkkosivun laadun.

Saat:
1. alkuperäisen research-briefin
2. rakennetun HTML-sivun

Tarkista erityisesti:

1. FAKTAT
- Vastaavatko sivun väitteet research-briefin faktoja?
- Onko sivulle keksitty palveluita, ominaisuuksia, numeroita,
  palkintoja, kokemusta tai muita faktoja joita brief ei tue?
- Ovatko yhteystiedot research-briefin mukaisia?

2. TEKSTI
- Onko teksti ammattimaista?
- Onko siinä ilmeisiä kielioppivirheitä?
- Onko teksti luonnollista suomea tai briefin käyttämää kieltä?
- Onko tekstissä kesken jääneitä lauseita?
- Onko tekstissä AI:n selviä jäänteitä?

3. RAKENNE
- Onko sivu looginen?
- Onko tärkeät osiot toteutettu?
- Onko CTA ymmärrettävä?
- Onko navigaatio järkevä?

4. DESIGN
- Noudattaako sivu researchin design recommendations -ohjeita?
- Onko design yhtenäinen?
- Vaikuttaako sivu valmiilta eikä keskeneräiseltä?

5. RESPONSIVE
- Onko HTML toteutettu niin, että se voi toimia mobiilissa,
  tabletissa ja desktopissa?

Jos löydät ongelman, kuvaile se lyhyesti.

Ole konservatiivinen:
jos tieto ei löydy research-briefistä, älä automaattisesti merkitse
sitä virheeksi, jos kyseessä on normaali markkinointiteksti.
Merkitse virheeksi selvästi keksityt faktat.

Palauta VAIN validi JSON:

{
  "content_ok": true,
  "issues": [],
  "notes": "Lyhyt yleisarvio"
}
"""


def _automated_checks(
    html: str,
) -> dict:
    """
    Tekee deterministiset HTML-tarkistukset ilman AI-kutsua.
    """

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

    # ---------------------------------------------------------
    # DOCTYPE
    # ---------------------------------------------------------

    if not html.lstrip().lower().startswith(
        "<!doctype html"
    ):
        issues.append(
            "HTML-tiedostosta puuttuu <!DOCTYPE html>."
        )

    # ---------------------------------------------------------
    # TITLE
    # ---------------------------------------------------------

    title = soup.find("title")

    if not title or not title.get_text(
        strip=True
    ):
        issues.append(
            "Sivulta puuttuu <title>-elementti."
        )

    # ---------------------------------------------------------
    # VIEWPORT
    # ---------------------------------------------------------

    viewport = soup.find(
        "meta",
        attrs={
            "name": "viewport"
        },
    )

    has_viewport = viewport is not None

    if not has_viewport:
        issues.append(
            "Puuttuva viewport-meta -> "
            "mobiilioptimointi voi olla puutteellinen."
        )

    # ---------------------------------------------------------
    # H1
    # ---------------------------------------------------------

    h1_elements = soup.find_all(
        "h1"
    )

    if len(h1_elements) == 0:
        issues.append(
            "Sivulta puuttuu H1-otsikko."
        )

    elif len(h1_elements) > 1:
        issues.append(
            f"Sivulla on {len(h1_elements)} H1-otsikkoa. "
            "Suositeltavaa on käyttää yhtä pää-H1-otsikkoa."
        )

    # ---------------------------------------------------------
    # IMAGES
    # ---------------------------------------------------------

    imgs_without_alt = [
        img
        for img in soup.find_all("img")
        if not img.get("alt")
    ]

    if imgs_without_alt:
        issues.append(
            f"{len(imgs_without_alt)} "
            "<img>-elementtiä ilman alt-tekstiä."
        )

    # ---------------------------------------------------------
    # ANCHOR LINKS
    # ---------------------------------------------------------

    ids = {
        tag.get("id")
        for tag in soup.find_all(
            id=True
        )
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

        if href.startswith(
            "#"
        ) and len(href) > 1:

            target = href[1:]

            if target not in ids:
                broken_anchors.append(
                    href
                )

    if broken_anchors:
        issues.append(
            "Rikkinäisiä ankkurilinkkejä: "
            + ", ".join(
                broken_anchors
            )
        )

    # ---------------------------------------------------------
    # EMPTY LINKS
    # ---------------------------------------------------------

    empty_links = []

    for anchor in soup.find_all(
        "a"
    ):
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
            empty_links.append(
                anchor
            )

    if empty_links:
        issues.append(
            f"{len(empty_links)} tyhjää linkkielementtiä."
        )

    # ---------------------------------------------------------
    # BUTTONS
    # ---------------------------------------------------------

    empty_buttons = []

    for button in soup.find_all(
        "button"
    ):
        text = button.get_text(
            " ",
            strip=True,
        )

        aria = button.get(
            "aria-label",
            "",
        ).strip()

        if not text and not aria:
            empty_buttons.append(
                button
            )

    if empty_buttons:
        issues.append(
            f"{len(empty_buttons)} tyhjää button-elementtiä."
        )

    # ---------------------------------------------------------
    # PLACEHOLDERS
    # ---------------------------------------------------------

    text = soup.get_text(
        " ",
        strip=True,
    )

    placeholder_patterns = [
        r"lorem ipsum",
        r"\[.*?tähän.*?\]",
        r"\[.*?täytä.*?\]",
        r"\[.*?lisää.*?\]",
        r"placeholder",
        r"your company",
        r"company name here",
        r"example\.com",
    ]

    for pattern in placeholder_patterns:

        if re.search(
            pattern,
            text,
            re.IGNORECASE,
        ):
            issues.append(
                "Löytyi täyttämätöntä "
                f"placeholder-tekstiä "
                f"(kuvio: '{pattern}')."
            )

    # ---------------------------------------------------------
    # HTTP LINKS
    # ---------------------------------------------------------

    insecure_links = []

    for anchor in soup.find_all(
        "a",
        href=True,
    ):
        href = anchor.get(
            "href",
            "",
        ).strip()

        if href.startswith(
            "http://"
        ):
            insecure_links.append(
                href
            )

    if insecure_links:
        issues.append(
            f"{len(insecure_links)} ulkoista linkkiä käyttää "
            "http:// eikä https://."
        )

    # ---------------------------------------------------------
    # REQUIRED STRUCTURE
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # MAIN CONTENT
    # ---------------------------------------------------------

    main = soup.find("main")

    if main is not None:

        main_text = main.get_text(
            " ",
            strip=True,
        )

        if len(main_text) < 100:
            issues.append(
                "Main-sisällössä on poikkeuksellisen vähän tekstiä."
            )

    # ---------------------------------------------------------
    # EXTERNAL RESOURCES
    # ---------------------------------------------------------

    external_resources = []

    for tag in soup.find_all(
        ["script", "link"],
    ):

        source = (
            tag.get("src")
            or tag.get("href")
            or ""
        )

        if source.startswith(
            "http://"
        ):
            external_resources.append(
                source
            )

    if external_resources:
        issues.append(
            "HTML käyttää http://-muotoisia ulkoisia resursseja."
        )

    # ---------------------------------------------------------
    # RESULT
    # ---------------------------------------------------------

    return {
        "has_viewport_meta": has_viewport,
        "automated_issues": issues,
        "automated_pass": len(issues) == 0,
    }


def run_qa(
    slug_or_name: str,
) -> dict:
    """
    main.py:n käyttämä QA-käynnistys.

    Yrityksen voi antaa slugina tai nimenä.
    """

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

    if not output_path or not os.path.exists(
        output_path
    ):
        raise RuntimeError(
            f"Rakennettua HTML-tiedostoa ei löytynyt: "
            f"{output_path}"
        )

    print()
    print("=== QA ===")
    print(
        f"Yritys: {company.get('name', '')}"
    )

    # ---------------------------------------------------------
    # READ HTML
    # ---------------------------------------------------------

    with open(
        output_path,
        "r",
        encoding="utf-8",
    ) as file:
        html = file.read()

    # ---------------------------------------------------------
    # AUTOMATED CHECKS
    # ---------------------------------------------------------

    print(
        "  [QA] Tehdään automaattiset tarkistukset..."
    )

    automated = _automated_checks(
        html
    )

    print(
        f"  [QA] Automaattisia ongelmia: "
        f"{len(automated['automated_issues'])}"
    )

    # ---------------------------------------------------------
    # AI CONTENT REVIEW
    # ---------------------------------------------------------

    research = company.get(
        "research",
        {},
    )

    user_prompt = f"""
=== RESEARCH BRIEF ===

Company facts:
{research.get("company_facts", {})}

Current site weaknesses:
{research.get("current_site_weaknesses", [])}

Design recommendations:
{research.get("design_recommendations", {})}

=== RAKENNETTU HTML ===

{html[:16000]}
"""

    print(
        "  [QA] Tehdään AI-sisältötarkistus..."
    )

    content_review = ask_claude_json(
        QA_SYSTEM_PROMPT,
        user_prompt,
        use_web_search=False,
        max_tokens=1800,
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

    # ---------------------------------------------------------
    # SAVE QA RESULT
    # ---------------------------------------------------------

    qa_result = {
        "automated": automated,
        "content_review": content_review,
        "overall_pass": overall_pass,
    }

    upsert_company(
        slug,
        {
            "qa": qa_result
        },
    )

    if overall_pass:
        set_status(
            slug,
            "qa_passed",
        )

        print(
            "  [QA] PASS"
        )

    else:
        set_status(
            slug,
            "built",
        )

        print(
            "  [QA] FAIL"
        )

        if automated.get(
            "automated_issues"
        ):
            print(
                "  [QA] Automaattiset ongelmat:"
            )

            for issue in automated[
                "automated_issues"
            ]:
                print(
                    f"    - {issue}"
                )

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
        f"Tulos: "
        f"{'PASS' if overall_pass else 'FAIL'}"
    )

    return qa_result


def approve_company(
    slug_or_name: str,
) -> dict:
    """
    Hyväksyy QA:n läpäisseen verkkosivun.

    Sivua ei voi hyväksyä, jos QA ei ole mennyt läpi.
    """

    slug, company = get_company(
        slug_or_name
    )

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    qa = company.get(
        "qa",
        {},
    )

    if not qa.get(
        "overall_pass",
        False,
    ):
        raise RuntimeError(
            "Sivustoa ei voi hyväksyä, koska QA ei ole läpäisty."
        )

    upsert_company(
        slug,
        {
            "approval": {
                "approved": True,
            }
        },
    )

    set_status(
        slug,
        "approved",
    )

    print(
        f"[QA] Sivusto hyväksytty: "
        f"{company.get('name', slug)}"
    )

    return company
