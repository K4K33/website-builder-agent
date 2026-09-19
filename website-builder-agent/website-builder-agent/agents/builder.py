"""
Website Builder -agentti.

Tehtävä:
1. Ottaa Research-agentin tuottaman design briefin.
2. Generoi oikean, toimivan ja responsiivisen yhden sivun verkkosivun.
3. Tallentaa sivun output/<slug>/index.html.
4. Tukee luonnollisen kielen revise-kutsuja.
5. Tukee preview-toimintoa.
"""

import os
import webbrowser

from utils.claude_client import ask_claude
from utils.state import (
    get_company,
    load_companies,
    upsert_company,
    set_status,
)
import config


BUILD_SYSTEM_PROMPT = """Olet kokenut web-suunnittelija ja frontend-kehittäjä.

Rakennat yritykselle UUDEN, AMMATTIMAISEN, modernin ja responsiivisen
yhden sivun verkkosivun HTML/CSS/JS:llä.

EHDOTTOMAT SÄÄNNÖT:

1. SISÄLTÖ
- ÄLÄ kopioi tekstiä, kuvatekstejä, logoja tai koodia miltään
  toiselta oikealta yritykseltä tai referenssisivulta.
- Kaikki tekstit kirjoitetaan itse kohdeyrityksen omien
  company_facts-tietojen pohjalta.
- Älä keksi yritykselle palveluita, tuotteita, ominaisuuksia,
  palkintoja, asiakaslupauksia tai muita faktoja.
- Käytä vain annettuja ja todennettuja yhteystietoja.
- Jos jokin yhteystieto puuttuu, käytä selkeää placeholderia:
  "[Puhelinnumero tähän]"
  "[Sähköposti tähän]"
  "[Osoite tähän]"
- Älä keksi puhelinnumeroita, sähköposteja tai osoitteita.

2. REFERENSSIT
- design_inspiration sisältää vain yleisiä suunnitteluperiaatteita.
- Älä kopioi referenssien tekstejä, kuvia, logoja tai koodia.
- Älä käytä referenssiyritysten nimiä uudella sivulla.
- Älä yritä jäljitellä yhtä tiettyä olemassa olevaa sivustoa.

3. VISUAALINEN TOTEUTUS
- Käytä annettua color_palette-värimaailmaa.
- Käytä annettua font_style-tyyliä.
- Käytä annettua tone-sävyä.
- Tee sivusta visuaalisesti viimeistelty ja moderni.
- Käytä CSS-pohjaisia elementtejä, gradientteja ja inline SVG-kuvakkeita.
- Älä linkitä ulkoisiin kuvatiedostoihin joita ei ole olemassa.
- Älä käytä ulkopuolisia stock-kuvia.

4. RESPONSIVUUS
- Sivun pitää toimia mobiilissa, tabletissa ja desktopissa.
- Lisää:
  <meta name="viewport"
        content="width=device-width, initial-scale=1.0">
- Navigaation pitää toimia mobiilissa.
- Tekstin pitää pysyä luettavana pienellä näytöllä.
- Painikkeiden pitää olla helposti klikattavia mobiilissa.

5. RAKENNE
Sisällytä tilanteeseen sopivassa muodossa:

- navigaatio
- Hero
- yrityksen arvolupaus
- palvelut/tuotteet
- miksi valita tämä yritys
- mahdollinen prosessi tai toimintatapa
- yhteydenotto / CTA
- yhteystiedot
- footer

Käytä semanttista HTML5:tä.

6. ACCESSIBILITY
- Käytä semanttisia HTML-elementtejä.
- Lisää aria-label tarvittaessa.
- Inline SVG-kuvakkeille sopivat accessibility-attribuutit.
- Varmista riittävä kontrasti.
- Älä käytä pelkästään väriä informaation välittämiseen.

7. TEKNINEN TOTEUTUS
- Koko sivu pitää olla yhdessä index.html-tiedostossa.
- CSS tulee <style>-tagiin.
- JavaScript tulee <script>-tagiin.
- Sivun pitää toimia avaamalla index.html suoraan selaimessa.
- Älä tarvitse build systemiä, npm:ää tai ulkoisia riippuvuuksia.

Palauta VASTAUKSENA AINOASTAAN valmis HTML-tiedoston koko sisältö,
alkaen '<!DOCTYPE html>'-rivistä.

Älä lisää selityksiä.
Älä lisää markdown-koodilohkoa.
"""


REVISE_SYSTEM_PROMPT = """Olet kokenut web-suunnittelija ja frontend-kehittäjä.

Saat:
1. olemassa olevan index.html-tiedoston
2. käyttäjän muutospyynnön.

Tee pyydetyt muutokset.

SÄÄNNÖT:
- Palauta KOKO päivitetty HTML-tiedosto.
- Älä palauta diffiä.
- Säilytä kaikki muu ennallaan, ellei muutospyyntö koske sitä.
- Älä poista toimivaa responsiivisuutta.
- Älä keksi uusia yrityksen faktoja.
- Älä keksi yhteystietoja.
- Älä lisää ulkoisia kuvia tai riippuvuuksia.
- Pidä HTML/CSS/JS yhdessä tiedostossa.
- Noudata accessibility- ja responsiivisuusperiaatteita.

Palauta VASTAUKSENA AINOASTAAN koko HTML-tiedoston sisältö.
Älä lisää selityksiä.
Älä lisää markdown-koodilohkoa.
"""


def _output_dir(slug: str) -> str:
    return os.path.join(
        config.OUTPUT_DIR,
        slug,
    )


def _output_path(slug: str) -> str:
    return os.path.join(
        _output_dir(slug),
        "index.html",
    )


def _clean_html(html: str) -> str:
    """
    Poistaa mahdolliset markdown-koodilohkot AI:n vastauksesta.
    """

    cleaned = (html or "").strip()

    if cleaned.startswith("```"):
        lines = cleaned.splitlines()

        if lines:
            lines = lines[1:]

        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]

        cleaned = "\n".join(lines).strip()

    return cleaned


def _write_html(
    slug: str,
    html: str,
) -> str:
    if not html:
        raise RuntimeError(
            "AI ei palauttanut HTML-sisältöä."
        )

    cleaned = _clean_html(html)

    if not cleaned.lower().startswith(
        "<!doctype html"
    ):
        raise RuntimeError(
            "AI:n palauttama sisältö ei näytä validilta "
            "kokonaiselta HTML-tiedostolta."
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


def _resolve_company(
    slug_or_name: str,
) -> tuple[str, dict]:
    """
    Hakee yrityksen slugilla tai nimellä.
    """

    slug, company = get_company(
        slug_or_name
    )

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    return slug, company


def build_site(
    slug: str,
    company: dict,
) -> str:
    """
    Rakentaa uuden verkkosivun Research-datan perusteella.
    """

    research = company.get(
        "research"
    )

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

    user_prompt = f"""
Rakenna uusi verkkosivu seuraavien tutkimustietojen perusteella.

=== COMPANY FACTS ===

{company_facts}

=== CURRENT SITE WEAKNESSES ===

{weaknesses}

=== DESIGN INSPIRATION ===

{inspiration}

=== DESIGN RECOMMENDATIONS ===

{recommendations}

Tärkeää:

Korjaa uuden sivuston suunnittelussa nykyisen sivuston tunnistetut
heikkoudet.

Kirjoita kaikki verkkosivun tekstit itse yrityksen todellisten
company_facts-tietojen perusteella.

Älä keksi puuttuvia faktoja.
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

    path = _write_html(
        slug,
        html,
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


def revise_site(
    slug: str,
    company: dict,
    feedback: str,
) -> str:
    """
    Muokkaa olemassa olevaa verkkosivua
    käyttäjän luonnollisen kielen ohjeen perusteella.
    """

    path = _output_path(
        slug
    )

    if not os.path.exists(path):
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy vielä rakennettua sivua. "
            f"Aja ensin: python main.py build {slug}"
        )

    with open(
        path,
        "r",
        encoding="utf-8",
    ) as file:
        current_html = file.read()

    user_prompt = f"""
=== NYKYINEN INDEX.HTML ===

{current_html}

=== KÄYTTÄJÄN MUUTOSPYYNTÖ ===

{feedback}

Tee ainoastaan pyydetyt muutokset.
Palauta koko päivitetty HTML.
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

    new_path = _write_html(
        slug,
        new_html,
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
        f"  [Builder] Uusi versio valmis: {new_path}"
    )

    return new_path


def run_build(
    slug_or_name: str,
) -> str:
    """
    main.py:n käyttämä Builder-käynnistys.
    """

    slug, company = _resolve_company(
        slug_or_name
    )

    print()
    print("=== BUILD ===")
    print(
        f"Yritys: {company.get('name', '')}"
    )

    return build_site(
        slug,
        company,
    )


def run_revise(
    slug_or_name: str,
    instructions: str,
) -> str:
    """
    main.py:n käyttämä revise-käynnistys.
    """

    slug, company = _resolve_company(
        slug_or_name
    )

    if not instructions.strip():
        raise RuntimeError(
            "Muutospyyntö ei voi olla tyhjä."
        )

    print()
    print("=== REVISE ===")
    print(
        f"Yritys: {company.get('name', '')}"
    )

    return revise_site(
        slug,
        company,
        instructions,
    )


def run_preview(
    slug_or_name: str,
) -> str:
    """
    Avaa rakennetun sivuston esikatselun.

    GitHub Actionsissa selainta ei ole käytettävissä,
    joten siellä tulostetaan vain tiedoston sijainti.
    """

    slug, company = _resolve_company(
        slug_or_name
    )

    path = _output_path(
        slug
    )

    if not os.path.exists(path):
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy rakennettua sivua. "
            f"Aja ensin: python main.py build {slug}"
        )

    absolute_path = os.path.abspath(
        path
    )

    file_url = (
        "file:///"
        + absolute_path.replace(
            "\\",
            "/",
        )
    )

    print()
    print("=== PREVIEW ===")
    print(
        f"Yritys: {company.get('name', '')}"
    )
    print(
        f"Tiedosto: {absolute_path}"
    )
    print(
        f"URL: {file_url}"
    )

    # GitHub Actionsissa BROWSER-ympäristömuuttujaa
    # ei yleensä ole eikä graafista selainta ole.
    if os.getenv(
        "GITHUB_ACTIONS"
    ) == "true":
        print(
            "[Preview] GitHub Actions -ympäristössä "
            "selainta ei avata."
        )

        return absolute_path

    try:
        webbrowser.open(
            file_url
        )
    except Exception as e:
        print(
            f"[Preview] Selaimen avaaminen epäonnistui: {e}"
        )

    return absolute_path
