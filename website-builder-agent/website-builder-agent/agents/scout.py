"""
Scout-agentti.

Dry-run-tila:
- hakee hakutuloksia
- poimii oikeita verkkosivuja
- tarkistaa verkkosivut
- ei käytä OpenRouteria

Normaali tila:
- tekee samat vaiheet
- käyttää OpenRouteria verkkosivujen AI-arviointiin
"""

from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

import config
from utils.claude_client import ask_claude_json
from utils.fetch import analyze_url
from utils.state import load_companies, save_companies, make_slug


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )
}


SCOUT_SYSTEM_PROMPT = """
Olet Website Builder Agentin Scout-agentti.

Arvioi oikeita yrityksiä ja niiden verkkosivuja.

Kiinnitä huomiota esimerkiksi:
- puuttuuko viewport-meta
- näyttääkö sivusto teknisesti vanhalta
- onko sisältö epäselvää tai vanhentunutta
- onko title tai meta description puutteellinen
- onko sivusto erittäin suppea
- onko sivustolla muita selviä merkkejä siitä,
  että uudistus voisi olla hyödyllinen

Älä päättele vanhentuneisuutta pelkästään
yksinkertaisesta ulkoasusta.

Palauta VAIN JSON-lista:

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

Älä keksi yrityksiä tai URL-osoitteita.
"""


def _clean_url(url: str) -> str:
    url = (url or "").strip()

    if not url:
        return ""

    if url.startswith("//"):
        url = "https:" + url

    if not url.startswith(("http://", "https://")):
        return ""

    if "javascript:" in url.lower():
        return ""

    if url.lower().startswith(
        (
            "https://javascript:",
            "http://javascript:",
        )
    ):
        return ""

    try:
        parsed = urlparse(url)

        if not parsed.netloc:
            return ""

        host = parsed.netloc.lower()

        if host in {
            "javascript",
            "void(0)",
        }:
            return ""

    except Exception:
        return ""

    return url


def _is_blocked_domain(url: str) -> bool:
    try:
        host = urlparse(url).netloc.lower()
        host = host.replace("www.", "")
    except Exception:
        return True

    blocked = {
        "google.com",
        "bing.com",
        "duckduckgo.com",
        "facebook.com",
        "instagram.com",
        "linkedin.com",
        "youtube.com",
        "tiktok.com",
        "yelp.com",
    }

    return host in blocked


def _search_web(
    query: str,
    max_results: int = 20,
) -> list[dict]:

    print(f"  [search] Haetaan: {query}")

    try:
        response = requests.get(
            "https://www.bing.com/search",
            params={
                "q": query,
                "count": max_results,
                "setlang": "fi",
                "cc": "fi",
            },
            headers=HEADERS,
            timeout=20,
        )

        print(
            f"  [search] HTTP-status: "
            f"{response.status_code}"
        )

        response.raise_for_status()

    except requests.RequestException as e:
        print(
            f"  [search] Haku epäonnistui: {e}"
        )
        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser",
    )

    results = []

    items = soup.select("li.b_algo")

    print(
        f"  [search] Bingin b_algo-tuloksia: "
        f"{len(items)}"
    )

    for item in items:

        link = item.select_one(
            "h2 a[href]"
        )

        if not link:
            continue

        href = _clean_url(
            link.get("href", "")
        )

        title = link.get_text(
            " ",
            strip=True,
        )

        if not href or not title:
            continue

        if _is_blocked_domain(href):
            continue

        description_node = item.select_one(
            ".b_caption p"
        )

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

    # Jos Bingin rakenne ei anna meille oikeita linkkejä,
    # älä käytä vaarallista yleistä a[href]-varahakua.
    #
    # Se voisi poimia esimerkiksi javascript:void(0)
    # -linkkejä, jotka eivät ole yritysten verkkosivuja.

    unique = []
    seen_domains = set()

    for result in results:

        url = result["url"]

        if not _clean_url(url):
            continue

        if _is_blocked_domain(url):
            continue

        try:
            domain = urlparse(
                url
            ).netloc.lower()

            domain = domain.replace(
                "www.",
                "",
            )

        except Exception:
            continue

        if not domain:
            continue

        if domain in seen_domains:
            continue

        seen_domains.add(domain)

        unique.append(result)

    print(
        f"  [search] Oikeita verkkosivutuloksia: "
        f"{len(unique)}"
    )

    return unique


def _extract_company_name(
    search_result: dict,
) -> str:

    title = search_result.get(
        "title",
        "",
    ).strip()

    if not title:
        return ""

    separators = [
        " | ",
        " - ",
        " – ",
        " — ",
    ]

    for separator in separators:

        if separator in title:
            title = title.split(
                separator
            )[0].strip()
            break

    return title[:200]


def _build_candidate_data(
    search_result: dict,
    industry: str,
    location: str,
) -> dict | None:

    url = _clean_url(
        search_result.get(
            "url",
            "",
        )
    )

    if not url:
        return None

    print(
        f"  [site] Tarkistetaan: {url}"
    )

    site_data = analyze_url(url)

    if not site_data:
        print(
            "  [site] Sivustoa ei voitu lukea."
        )
        return None

    return {
        "name": _extract_company_name(
            search_result
        ),
        "url": url,
        "industry": industry,
        "location": location,
        "search_title": search_result.get(
            "title",
            "",
        ),
        "search_description": search_result.get(
            "description",
            "",
        ),
        "site": site_data,
    }


def _print_candidate(
    candidate: dict,
) -> None:

    site = candidate["site"]

    print()
    print("  --- EHDOKAS ---")
    print(
        f"  Yritys: {candidate['name']}"
    )
    print(
        f"  URL: {candidate['url']}"
    )
    print(
        f"  Title: {site.get('title', '')}"
    )
    print(
        "  Viewport-meta: "
        f"{site.get('has_viewport_meta', False)}"
    )
    print(
        "  HTML-koko: "
        f"{site.get('raw_html_length', 0)}"
    )


def _ask_ai_to_evaluate(
    candidates: list[dict],
) -> list[dict]:

    prompt_parts = [
        "Arvioi seuraavat yritykset.",
        "",
    ]

    for index, candidate in enumerate(
        candidates,
        start=1,
    ):

        site = candidate["site"]

        prompt_parts.append(
            f"""
YRITYS {index}

Nimi:
{candidate['name']}

URL:
{candidate['url']}

Toimiala:
{candidate['industry']}

Sijainti:
{candidate['location']}

Hakutuloksen otsikko:
{candidate['search_title']}

Hakutuloksen kuvaus:
{candidate['search_description']}

Sivuston title:
{site.get('title', '')}

Meta description:
{site.get('meta_description', '')}

Viewport-meta:
{site.get('has_viewport_meta', False)}

HTML-koko:
{site.get('raw_html_length', 0)}

Sivuston teksti:
{site.get('visible_text', '')[:5000]}
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

    return ask_claude_json(
        SCOUT_SYSTEM_PROMPT,
        "\n".join(prompt_parts),
        use_web_search=False,
        max_tokens=4000,
    )


def run_scout(
    count: int = None,
    industry: str = "",
    location: str = "",
    dry_run: bool = False,
) -> list[dict]:

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

    if dry_run:
        print("TILA: DRY-RUN")
        print("OpenRouteria EI käytetä.")
    else:
        print("TILA: NORMAALI")
        print("OpenRouteria käytetään AI-arviointiin.")

    print()

    search_results = _search_web(
        query,
        max_results=max(
            count * 5,
            20,
        ),
    )

    if not search_results:
        print()
        print(
            "[scout] Hakupalvelusta ei saatu "
            "käyttökelpoisia yrityssivustoja."
        )
        return []

    candidates = []

    for result in search_results:

        candidate = _build_candidate_data(
            result,
            industry,
            location,
        )

        if not candidate:
            continue

        if not candidate["name"]:
            continue

        _print_candidate(candidate)

        candidates.append(candidate)

        if len(candidates) >= count:
            break

    print()

    if not candidates:
        print(
            "[scout] Hakutuloksia löytyi, "
            "mutta verkkosivuja ei voitu analysoida."
        )
        return []

    print(
        f"[scout] Verkkosivujen analyysi onnistui: "
        f"{len(candidates)}"
    )

    if dry_run:

        print()
        print("=== DRY-RUN VALMIS ===")
        print("OpenRouter-kutsuja tehtiin: 0")
        print(
            f"Yritysten verkkosivuja analysoitu: "
            f"{len(candidates)}"
        )

        return candidates

    print()
    print(
        "[scout] Lähetetään ehdokkaat "
        "OpenRouterille arvioitavaksi..."
    )

    evaluated = _ask_ai_to_evaluate(
        candidates
    )

    companies = load_companies()

    saved = []

    for item in evaluated:

        if not isinstance(item, dict):
            continue

        name = str(
            item.get(
                "name",
                "",
            )
        ).strip()

        url = _clean_url(
            str(
                item.get(
                    "url",
                    "",
                )
            ).strip()
        )

        if not name or not url:
            continue

        old_site = bool(
            item.get(
                "old_site",
                False,
            )
        )

        try:
            confidence = float(
                item.get(
                    "confidence",
                    0,
                )
            )
        except (
            TypeError,
            ValueError,
        ):
            confidence = 0.0

        confidence = max(
            0.0,
            min(
                1.0,
                confidence,
            )
        )

        if not old_site:
            continue

        if confidence < 0.60:
            continue

        slug = make_slug(name)

        if (
            slug in companies
            and companies[slug].get(
                "status"
            ) != "found"
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
        "[scout] Tallennettu potentiaalisia "
        f"yrityksiä: {len(saved)}"
    )

    return saved
