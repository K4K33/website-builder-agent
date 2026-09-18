"""
Scout-agentti.

Etsii oikeita yrityksiä hakutuloksista ja tarkistaa niiden verkkosivut
ennen kuin ne annetaan OpenRouterin arvioitavaksi.

Prosessi:
1. Muodostetaan hakukysely.
2. Haetaan hakutuloksia.
3. Poimitaan yritys- ja verkkosivuehdokkaat.
4. Haetaan ehdokkaiden omat verkkosivut fetch.py:n avulla.
5. OpenRouter arvioi, vaikuttaako sivusto vanhentuneelta.
6. Hyväksytyt yritykset tallennetaan companies.json-tiedostoon.
"""

import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import config
from utils.claude_client import ask_claude_json
from utils.fetch import analyze_url
from utils.state import load_companies, save_companies, make_slug


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; WebsiteBuilderAgent/1.0; "
        "+https://github.com/K4K33/website-builder-agent)"
    )
}


SCOUT_SYSTEM_PROMPT = """
Olet Website Builder Agentin Scout-agentti.

Tehtäväsi on arvioida OIKEITA yrityksiä ja niiden verkkosivuja.

Saat yrityksestä:
- yrityksen nimen
- verkkosivun URL-osoitteen
- toimialan ja sijainnin
- verkkosivulta kerättyä sisältöä ja teknisiä tietoja

Arvioi, vaikuttaako verkkosivu aidosti vanhentuneelta tai heikkolaatuiselta.

Kiinnitä huomiota esimerkiksi:
- puuttuuko viewport-meta mobiililaitteita varten
- onko sivu erittäin vanhan oloinen
- puuttuuko selkeä yrityksen palvelukuvaus
- onko sisältö epäselvää tai vanhentunutta
- näyttääkö rakenne teknisesti vanhalta
- onko title tai meta description puutteellinen
- onko sivusto erittäin suppea
- onko sivustolla muita selviä merkkejä siitä, että uudistus voisi olla hyödyllinen

ÄLÄ päättele vanhentuneisuutta pelkästään siitä, että sivu on yksinkertainen.
Yksinkertainen mutta toimiva sivusto ei automaattisesti ole huono.

Palauta VAIN JSON-lista tässä muodossa:

[
  {
    "name": "Yrityksen nimi",
    "url": "https://example.fi",
    "industry_guess": "toimiala",
    "location": "paikkakunta",
    "old_site": true,
    "confidence": 0.85,
    "reason": "Lyhyt konkreettinen perustelu."
  }
]

confidence pitää olla välillä 0 ja 1.

Jos sivusto vaikuttaa hyvältä, älä merkitse sitä old_site=true.
Älä koskaan keksi yritystä tai URL-osoitetta.
"""


def _clean_url(url: str) -> str:
    """Normalisoi URL:n mahdollisimman turvallisesti."""

    url = (url or "").strip()

    if not url:
        return ""

    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    parsed = urlparse(url)

    if not parsed.netloc:
        return ""

    return url


def _is_probably_search_result_url(url: str) -> bool:
    """
    Suodattaa pois yleisiä hakukoneiden, some-palveluiden ja hakemistojen
    URL-osoitteita. Tavoitteena on löytää yrityksen oma verkkosivu.
    """

    try:
        host = urlparse(url).netloc.lower()
    except Exception:
        return False

    blocked_hosts = {
        "google.com",
        "www.google.com",
        "bing.com",
        "www.bing.com",
        "duckduckgo.com",
        "www.duckduckgo.com",
        "facebook.com",
        "www.facebook.com",
        "instagram.com",
        "www.instagram.com",
        "linkedin.com",
        "www.linkedin.com",
        "youtube.com",
        "www.youtube.com",
        "tiktok.com",
        "www.tiktok.com",
        "yelp.com",
        "www.yelp.com",
    }

    return host not in blocked_hosts


def _search_web(query: str, max_results: int = 20) -> list[dict]:
    """
    Hakee hakutuloksia Bingin HTML-hakutuloksista.

    Tämä ei käytä maksullista AI-web-search API:a.
    """

    url = "https://www.bing.com/search"

    try:
        response = requests.get(
            url,
            params={
                "q": query,
                "count": max_results,
                "setlang": "fi",
            },
            headers=HEADERS,
            timeout=20,
        )

        response.raise_for_status()

    except requests.RequestException as e:
        print(f"  [scout] Hakupalvelun haku epäonnistui: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for item in soup.select("li.b_algo"):
        link = item.select_one("h2 a")

        if not link:
            continue

        href = link.get("href", "").strip()
        title = link.get_text(" ", strip=True)

        if not href or not title:
            continue

        href = _clean_url(href)

        if not href:
            continue

        if not _is_probably_search_result_url(href):
            continue

        description_node = item.select_one(".b_caption p")

        description = ""

        if description_node:
            description = description_node.get_text(
                " ",
                strip=True,
            )

        results.append(
            {
                "title": title,
                "url": href,
                "description": description,
            }
        )

        if len(results) >= max_results:
            break

    return results


def _same_domain(url1: str, url2: str) -> bool:
    """Tarkistaa ovatko kaksi URL-osoitetta samassa domainissa."""

    try:
        host1 = urlparse(url1).netloc.lower().replace("www.", "")
        host2 = urlparse(url2).netloc.lower().replace("www.", "")

        return host1 == host2

    except Exception:
        return False


def _extract_company_name(search_result: dict) -> str:
    """Yrittää muodostaa yrityksen nimen hakutuloksen otsikosta."""

    title = search_result.get("title", "").strip()

    if not title:
        return ""

    # Poistetaan yleisiä verkkosivujen otsikkolisäyksiä.
    separators = [
        " | ",
        " - ",
        " – ",
        " — ",
    ]

    for separator in separators:
        if separator in title:
            title = title.split(separator)[0].strip()
            break

    return title[:200]


def _build_candidate_data(
    search_result: dict,
    industry: str,
    location: str,
) -> dict | None:
    """
    Hakee ehdokkaan verkkosivun ja palauttaa analysoitavan datan.
    """

    url = _clean_url(search_result.get("url", ""))

    if not url:
        return None

    print(f"  [scout] Tarkistetaan: {url}")

    site_data = analyze_url(url)

    if not site_data:
        return None

    return {
        "name": _extract_company_name(search_result),
        "url": url,
        "industry": industry,
        "location": location,
        "search_title": search_result.get("title", ""),
        "search_description": search_result.get(
            "description",
            "",
        ),
        "site": site_data,
    }


def _ask_ai_to_evaluate(
    candidates: list[dict],
) -> list[dict]:
    """
    Antaa oikeista verkkosivuista kerätyt tiedot OpenRouterin AI:lle.
    """

    if not candidates:
        return []

    prompt_parts = [
        "Arvioi seuraavat oikeista hakutuloksista löydetyt yritykset.",
        "",
    ]

    for index, candidate in enumerate(candidates, start=1):
        site = candidate["site"]

        prompt_parts.append(
            f"""
YRITYS {index}
Nimi: {candidate["name"]}
URL: {candidate["url"]}
Toimiala: {candidate["industry"]}
Sijainti: {candidate["location"]}

Hakutuloksen otsikko:
{candidate["search_title"]}

Hakutuloksen kuvaus:
{candidate["search_description"]}

Sivuston title:
{site.get("title", "")}

Meta description:
{site.get("meta_description", "")}

Viewport-meta:
{site.get("has_viewport_meta", False)}

HTML-koko:
{site.get("raw_html_length", 0)}

Sivuston teksti:
{site.get("visible_text", "")[:5000]}
"""
        )

    prompt_parts.append(
        """
Arvioi jokainen yritys.

Palauta vain JSON-lista.
Älä keksi uusia yrityksiä.
Käytä vain annettuja yrityksiä ja URL-osoitteita.
"""
    )

    result = ask_claude_json(
        SCOUT_SYSTEM_PROMPT,
        "\n".join(prompt_parts),
        use_web_search=False,
        max_tokens=4000,
    )

    if not isinstance(result, list):
        raise RuntimeError(
            f"Scout-agentti palautti odottamattoman muodon: {result}"
        )

    return result


def run_scout(
    count: int = None,
    industry: str = "",
    location: str = "",
) -> list[dict]:
    """
    Etsii yrityksiä ja tallentaa kiinnostavat yritykset.
    """

    count = count or config.SCOUT_MAX_RESULTS

    industry = industry.strip()
    location = location.strip()

    if industry and location:
        query = f"{industry} {location}"
    elif industry:
        query = industry
    elif location:
        query = f"yritys {location}"
    else:
        query = "pieni yritys Suomi"

    print()
    print("=== SCOUT ===")
    print(f"Hakukysely: {query}")
    print(f"Tavoite: {count} yritystä")
    print()

    search_results = _search_web(
        query,
        max_results=max(count * 4, 20),
    )

    if not search_results:
        print("[scout] Hakutuloksia ei löytynyt.")
        return []

    print(
        f"[scout] Hakutuloksia löytyi: {len(search_results)}"
    )

    candidates = []

    seen_domains = set()

    for result in search_results:
        url = _clean_url(result.get("url", ""))

        if not url:
            continue

        try:
            domain = urlparse(url).netloc.lower().replace(
                "www.",
                "",
            )
        except Exception:
            continue

        # Älä analysoi samaa yrityksen domainia useita kertoja.
        if domain in seen_domains:
            continue

        seen_domains.add(domain)

        candidate = _build_candidate_data(
            result,
            industry,
            location,
        )

        if not candidate:
            continue

        if not candidate["name"]:
            continue

        candidates.append(candidate)

        if len(candidates) >= count:
            break

    if not candidates:
        print("[scout] Yhtään käyttökelpoista yritysehdokasta ei löytynyt.")
        return []

    print()
    print(
        f"[scout] Analysoitavia yrityksiä: {len(candidates)}"
    )

    evaluated = _ask_ai_to_evaluate(candidates)

    companies = load_companies()
    saved = []

    for item in evaluated:
        if not isinstance(item, dict):
            continue

        name = str(item.get("name", "")).strip()
        url = _clean_url(str(item.get("url", "")).strip())

        if not name or not url:
            continue

        old_site = bool(item.get("old_site", False))

        confidence_raw = item.get("confidence", 0)

        try:
            confidence = float(confidence_raw)
        except (TypeError, ValueError):
            confidence = 0.0

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        # Scoutin tarkoitus on löytää potentiaalisia sivustouudistuksia.
        # Emme tallenna selvästi hyviä sivustoja jatkokäsittelyyn.
        if not old_site:
            continue

        if confidence < 0.60:
            continue

        slug = make_slug(name)

        # Älä ylikirjoita jo pidemmällä olevaa yritystä.
        if (
            slug in companies
            and companies[slug].get("status") != "found"
        ):
            continue

        companies[slug] = {
            "name": name,
            "url": url,
            "status": "found",
            "scout": {
                "industry_guess": item.get(
                    "industry_guess",
                    industry,
                ),
                "location": item.get(
                    "location",
                    location,
                ),
                "reason": item.get(
                    "reason",
                    "",
                ),
                "confidence": confidence,
            },
        }

        saved.append(
            (
                slug,
                companies[slug],
            )
        )

    save_companies(companies)

    print()
    print(
        f"[scout] Tallennettu potentiaalisia yrityksiä: "
        f"{len(saved)}"
    )

    return saved
