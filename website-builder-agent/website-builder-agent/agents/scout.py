"""
Scout-agentti Website Builder Agentille.

Dry-run:
- käyttää OpenStreetMapia yritysten löytämiseen
- tarkistaa yritysten omat verkkosivut
- pisteyttää mahdollisesti vanhentuneita sivustoja
- EI käytä Tavilyä
- EI käytä OpenRouteria
- EI tallenna yrityksiä

Normaali tila:
- käyttää samaa ilmaista löytövaihetta
- AI-analyysi voidaan ottaa käyttöön myöhemmin
"""

import re
import requests

import config

from utils.fetch import analyze_url
from utils.state import load_companies, save_companies, make_slug


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

HEADERS = {
    "User-Agent": (
        "WebsiteBuilderAgent/1.0 "
        "(https://github.com/K4K33/website-builder-agent)"
    ),
    "Accept": "application/json",
}


def _build_overpass_query(location: str, industry: str) -> str:
    """
    Rakentaa Overpass-kyselyn.

    Kampaamoille käytetään hairdresser-tageja.
    Muissa tapauksissa etsitään yleisiä yrityskohteita.
    """

    location = location.strip()
    industry_lower = industry.lower().strip()

    if "kampa" in industry_lower or "parturi" in industry_lower:
        business_filter = """
(
  nwr["shop"="hairdresser"](area.searchArea);
  nwr["craft"="hairdresser"](area.searchArea);
);
"""
    else:
        business_filter = """
(
  nwr["shop"](area.searchArea);
  nwr["craft"](area.searchArea);
  nwr["office"](area.searchArea);
);
"""

    query = f"""
[out:json][timeout:30];

area["name"="{location}"]["boundary"="administrative"]->.searchArea;

{business_filter}

out center;
"""

    return query.strip()


def _search_overpass(
    location: str,
    industry: str,
    limit: int = 20,
) -> list[dict]:
    """
    Hakee yrityksiä OpenStreetMapista.
    """

    query = _build_overpass_query(
        location,
        industry,
    )

    print("  [OSM] Haetaan yrityksiä OpenStreetMapista...")
    print(f"  [OSM] Sijainti: {location}")
    print(f"  [OSM] Ala: {industry}")

    try:
        response = requests.post(
            OVERPASS_URL,
            data={
                "data": query,
            },
            headers=HEADERS,
            timeout=45,
        )

        print(
            f"  [OSM] HTTP-status: {response.status_code}"
        )

        if response.status_code >= 400:
            print(
                "  [OSM] Palvelin palautti virheen:"
            )
            print(
                response.text[:3000]
            )

            response.raise_for_status()

        data = response.json()

    except requests.RequestException as e:
        print(
            f"  [OSM] Haku epäonnistui: {e}"
        )
        return []

    except ValueError as e:
        print(
            f"  [OSM] JSON-vastausta ei voitu lukea: {e}"
        )
        return []

    elements = data.get("elements", [])

    print(
        f"  [OSM] Löydettyjä kohteita: {len(elements)}"
    )

    companies = []

    seen_names = set()

    for element in elements:
        tags = element.get("tags", {})

        name = tags.get("name", "").strip()

        if not name:
            continue

        normalized_name = name.lower()

        if normalized_name in seen_names:
            continue

        seen_names.add(normalized_name)

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or ""
        ).strip()

        phone = (
            tags.get("phone")
            or tags.get("contact:phone")
            or ""
        ).strip()

        email = (
            tags.get("email")
            or tags.get("contact:email")
            or ""
        ).strip()

        address_parts = [
            tags.get("addr:street", "").strip(),
            tags.get("addr:housenumber", "").strip(),
            tags.get("addr:postcode", "").strip(),
            tags.get("addr:city", "").strip(),
        ]

        address = " ".join(
            part for part in address_parts if part
        )

        companies.append(
            {
                "name": name,
                "url": website,
                "phone": phone,
                "email": email,
                "address": address,
                "osm_type": element.get("type", ""),
                "osm_id": element.get("id"),
                "tags": tags,
            }
        )

        if len(companies) >= limit:
            break

    with_website = [
        company
        for company in companies
        if company.get("url")
    ]

    print(
        f"  [OSM] Yrityksiä yhteensä: {len(companies)}"
    )

    print(
        f"  [OSM] Yrityksiä, joilla verkkosivu: "
        f"{len(with_website)}"
    )

    return companies


def _normalize_url(url: str) -> str:
    """
    Muuttaa yleisimmät OSM-URL-muodot analysoitaviksi.
    """

    url = url.strip()

    if not url:
        return ""

    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url

    return url


def _analyze_candidates(
    candidates: list[dict],
) -> list[dict]:
    """
    Hakee yritysten verkkosivut ja kerää tekniset havainnot.
    """

    analyzed = []

    for company in candidates:

        name = company.get("name", "")
        raw_url = company.get("url", "")

        if not raw_url:
            print(
                f"  [skip] Ei verkkosivua: {name}"
            )
            continue

        url = _normalize_url(raw_url)

        print(
            f"  [site] Tarkistetaan: {name}"
        )

        print(
            f"  [site] URL: {url}"
        )

        data = analyze_url(url)

        if not data:
            print(
                f"  [site] Sivua ei voitu hakea: {name}"
            )
            continue

        print(
            f"  [site] OK | "
            f"title='{data.get('title', '')}' | "
            f"viewport={data.get('has_viewport_meta', False)}"
        )

        result = dict(company)

        result["url"] = url
        result["site_analysis"] = data

        analyzed.append(result)

    return analyzed


def _score_without_ai(company: dict) -> dict:
    """
    Arvioi sivuston vanhentuneisuutta ilman AI:ta.

    Mitä enemmän teknisiä puutteita löytyy,
    sitä suurempi pisteytys.

    Tämä EI tarkoita vielä, että sivusto varmasti
    tarvitsee uuden verkkosivun.
    """

    data = company.get("site_analysis", {})

    title = data.get("title", "").strip()
    meta_description = data.get(
        "meta_description",
        "",
    ).strip()

    visible_text = data.get(
        "visible_text",
        "",
    )

    raw_html_length = int(
        data.get(
            "raw_html_length",
            0,
        )
        or 0
    )

    has_viewport = bool(
        data.get(
            "has_viewport_meta",
            False,
        )
    )

    links = data.get(
        "links",
        [],
    )

    score = 0
    reasons = []

    # 1. Meta description puuttuu.
    if not meta_description:
        score += 1
        reasons.append(
            "meta description puuttuu"
        )

    # 2. Mobiili-viewport puuttuu.
    if not has_viewport:
        score += 2
        reasons.append(
            "viewport-meta puuttuu"
        )

    # 3. Title puuttuu tai on erittäin lyhyt.
    if not title:
        score += 2
        reasons.append(
            "title puuttuu"
        )
    elif len(title) < 8:
        score += 1
        reasons.append(
            "erittäin lyhyt title"
        )

    # 4. Sivulla on hyvin vähän näkyvää sisältöä.
    if len(visible_text) < 800:
        score += 2
        reasons.append(
            "hyvin vähän näkyvää sisältöä"
        )
    elif len(visible_text) < 1500:
        score += 1
        reasons.append(
            "vähän näkyvää sisältöä"
        )

    # 5. Erittäin pieni HTML-dokumentti.
    if raw_html_length < 10000:
        score += 2
        reasons.append(
            "hyvin pieni HTML-sivu"
        )
    elif raw_html_length < 20000:
        score += 1
        reasons.append(
            "pieni HTML-sivu"
        )

    # 6. Sivustolla on hyvin vähän linkkejä.
    if len(links) < 3:
        score += 1
        reasons.append(
            "hyvin vähän linkkejä"
        )

    # Luottamus pidetään tarkoituksella maltillisena.
    confidence = min(
        0.95,
        round(
            0.25 + (score * 0.10),
            2,
        ),
    )

    # Vanhaksi ei merkitä yhden pienen puutteen perusteella.
    old_site = score >= 3

    return {
        "old_site": old_site,
        "score": score,
        "confidence": confidence,
        "reasons": reasons,
    }


def _print_dry_run_result(company: dict) -> None:
    """
    Tulostaa yhden yrityksen dry-run-analyysin.
    """

    result = _score_without_ai(company)

    print(
        f"  [dry-run] {company.get('name', '')}"
    )

    print(
        f"  [dry-run] URL: "
        f"{company.get('url', '')}"
    )

    print(
        f"  [dry-run] Pisteet: "
        f"{result['score']}"
    )

    print(
        f"  [dry-run] Mahdollisesti vanha: "
        f"{result['old_site']}"
    )

    print(
        f"  [dry-run] Luottamus: "
        f"{result['confidence']:.2f}"
    )

    if result["reasons"]:
        print(
            "  [dry-run] Havainnot: "
            + ", ".join(result["reasons"])
        )
    else:
        print(
            "  [dry-run] Havainnot: "
            "ei merkittäviä teknisiä puutteita"
        )


def _ai_analyze_company(company: dict) -> dict:
    """
    AI-analyysi myöhempää tuotantokäyttöä varten.

    Tätä ei kutsuta dry-run-tilassa.
    """

    from utils.claude_client import ask_claude_json

    data = company.get(
        "site_analysis",
        {},
    )

    system = """
Olet verkkosivustojen auditointiin erikoistunut analyytikko.

Arvioi, vaikuttaako pienen yrityksen verkkosivusto
aidosti vanhentuneelta ja voisiko yritykselle olla
järkevää tarjota verkkosivuston uudistusta.

Älä päättele pelkästään siitä, että sivu ei ole modernin
näköinen. Erota tekniset puutteet, sisällölliset puutteet
ja aidot myyntimahdollisuudet.

Palauta AINOASTAAN validi JSON:
{
  "old_site": true,
  "confidence": 0.0,
  "reasons": [],
  "opportunity": "",
  "priority": "low"
}
"""

    user_prompt = f"""
Yritys:
{company.get('name', '')}

URL:
{company.get('url', '')}

Title:
{data.get('title', '')}

Meta description:
{data.get('meta_description', '')}

Viewport:
{data.get('has_viewport_meta', False)}

Näkyvä teksti:
{data.get('visible_text', '')[:5000]}

HTML-koko:
{data.get('raw_html_length', 0)}

Linkkien määrä:
{len(data.get('links', []))}
"""

    return ask_claude_json(
        system,
        user_prompt,
        use_web_search=False,
        max_tokens=1000,
    )


def run_scout(
    count: int = 10,
    industry: str = "",
    location: str = "",
    dry_run: bool = False,
):
    """
    Scoutin päätoiminto.
    """

    print()
    print("=== SCOUT ===")

    print(
        f"Hakukysely: "
        f"{industry} {location}".strip()
    )

    print(
        f"Tavoite: {count} yritystä"
    )

    if dry_run:
        print(
            "TILA: DRY-RUN"
        )
        print(
            "Tavilyä EI käytetä."
        )
        print(
            "OpenRouteria EI käytetä."
        )
        print(
            "Yrityksiä EI tallenneta."
        )

    candidates = _search_overpass(
        location=location,
        industry=industry,
        limit=max(
            count * 4,
            10,
        ),
    )

    if not candidates:
        print(
            "[scout] OpenStreetMapista "
            "ei löytynyt yrityksiä."
        )
        return []

    analyzed = _analyze_candidates(
        candidates
    )

    if not analyzed:
        print(
            "[scout] Yhtään toimivaa verkkosivua "
            "ei löytynyt."
        )
        return []

    results = []

    for company in analyzed:

        if len(results) >= count:
            break

        if dry_run:
            _print_dry_run_result(
                company
            )
            results.append(company)
            continue

        try:
            ai_result = _ai_analyze_company(
                company
            )

        except Exception as e:
            print(
                f"  [AI] Analyysi epäonnistui "
                f"({company.get('name', '')}): {e}"
            )
            continue

        company["ai_analysis"] = ai_result

        results.append(company)

    if dry_run:
        print()
        print(
            "=== DRY-RUN VALMIS ==="
        )

        print(
            f"Yrityksiä analysoitiin: "
            f"{len(results)}"
        )

        print(
            "Tavily-kutsuja: 0"
        )

        print(
            "OpenRouter-kutsuja: 0"
        )

        print(
            "Tallennettuja yrityksiä: 0"
        )

        return results

    # Normaali tila: tallenna vain AI:n analysoimat kohteet.
    companies = load_companies()

    saved_count = 0

    for company in results:

        slug = make_slug(
            company.get(
                "name",
                "",
            )
        )

        if not slug:
            continue

        existing = companies.get(
            slug,
            {},
        )

        company_record = dict(existing)
        company_record.update(company)

        company_record["status"] = (
            existing.get(
                "status",
                "found",
            )
        )

        companies[slug] = company_record

        saved_count += 1

    save_companies(companies)

    print(
        f"[Scout] Tallennettuja yrityksiä: "
        f"{saved_count}"
    )

    return results
