"""
Scout-agentti.

Prosessi:

1. Hakee yritysehdokkaita web-haulla.
2. Poimii oikeat verkkosivujen URL-osoitteet.
3. Tarkistaa yritysten verkkosivut.
4. Dry-run-tilassa ei käytä OpenRouteria.
5. Normaalitilassa OpenRouter arvioi löydetyt sivustot.

Tärkeä periaate:
OpenRouteria ei kutsuta ennen kuin oikeita yritysten
verkkosivuja on löydetty ja niiden lataus on onnistunut.
"""

from urllib.parse import parse_qs, unquote, urlparse

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
    ),
    "Accept-Language": "fi-FI,fi;q=0.9,en;q=0.8",
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
    """
    Puhdistaa hakutuloksesta saadun URL-osoitteen.
    """

    url = (url or "").strip()

    if not url:
        return ""

    # HTML-entiteettejä voi esiintyä osoitteessa.
    url = unquote(url)

    # Poistetaan lainausmerkit ja ympäröivä whitespace.
    url = url.strip(" \"'")

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):
        return ""

    # JavaScript-linkit eivät ole verkkosivuja.
    if "javascript:" in url.lower():
        return ""

    try:
        parsed = urlparse(url)

        if not parsed.netloc:
            return ""

        if parsed.scheme not in (
            "http",
            "https",
        ):
            return ""

        host = parsed.netloc.lower()

        if host in (
            "javascript",
            "void(0)",
        ):
            return ""

    except Exception:
        return ""

    return url


def _is_blocked_domain(url: str) -> bool:
    """
    Estää hakukoneet, some-sivut ja muut sivut,
    joita emme halua pitää yrityksen omana verkkosivuna.
    """

    try:
        host = urlparse(url).netloc.lower()
        host = host.replace(
            "www.",
            "",
        )
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
        "x.com",
        "twitter.com",
        "yelp.com",
        "tripadvisor.com",
    }

    return host in blocked


def _unwrap_duckduckgo_url(url: str) -> str:
    """
    DuckDuckGo voi käyttää /l/?uddg=... -muotoisia
    välitysurleja. Yritetään purkaa ne alkuperäiseksi URL:ksi.
    """

    try:
        parsed = urlparse(url)

        if parsed.path == "/l/":
            query = parse_qs(
                parsed.query
            )

            target = query.get(
                "uddg",
                [""],
            )[0]

            if target:
                return unquote(target)

    except Exception:
        pass

    return url


def _search_web(
    query: str,
    max_results: int = 20,
) -> list[dict]:
    """
    Hakee DuckDuckGo HTML -hakutuloksia.

    Tämä ei käytä OpenRouteria.
    """

    print(
        f"  [search] Haetaan: {query}"
    )

    try:
        response = requests.post(
            "https://html.duckduckgo.com/html/",
            data={
                "q": query,
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

    # DuckDuckGo HTML -hakutulokset.
    result_nodes = soup.select(
        ".result"
    )

    print(
        f"  [search] Hakutuloslohkoja: "
        f"{len(result_nodes)}"
    )

    results = []

    for node in result_nodes:

        link = node.select_one(
            ".result__a"
        )

        if not link:
            continue

        raw_url = link.get(
            "href",
            "",
        )

        raw_url = _unwrap_duckduckgo_url(
            raw_url
        )

        url = _clean_url(
            raw_url
        )

        if not url:
            continue

        if _is_blocked_domain(url):
            continue

        title = link.get_text(
            " ",
            strip=True,
        )

        if not title:
            continue

        description_node = node.select_one(
            ".result__snippet"
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
                "url": url,
                "description": description,
            }
        )

        if len(results) >= max_results:
            break

    # Poistetaan saman domainin toistot.
    unique = []
    seen_domains = set()

    for result in results:

        url = result["url"]

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
    print(
        f"Hakukysely: {query}"
    )
    print(
        f"Tavoite: {count} yritystä"
    )

    if dry_run:
        print(
            "TILA: DRY-RUN"
        )
        print(
            "OpenRouteria EI käytetä."
        )
    else:
        print(
            "TILA: NORMAALI"
        )
        print(
            "OpenRouteria käytetään "
            "AI-arviointiin."
        )

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

        _print_candidate(
            candidate
        )

        candidates.append(
            candidate
        )

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
        "[scout] Verkkosivujen analyysi onnistui: "
        f"{len(candidates)}"
    )

    if dry_run:

        print()
        print(
            "=== DRY-RUN VALMIS ==="
        )

        print(
            "OpenRouter-kutsuja tehtiin: 0"
        )

        print(
            "Yritysten verkkosivuja analysoitu: "
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

        slug = make_slug(
            name
        )

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

    save_companies(
        companies
    )

    print()

    print(
        "[scout] Tallennettu potentiaalisia "
        f"yrityksiä: {len(saved)}"
    )

    return saved
