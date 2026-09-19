"""
Scout-agentti Website Builder Agentille.

DRY-RUN:
- Käyttää OpenStreetMap / Overpass APIa.
- EI käytä Tavilyä.
- EI käytä OpenRouteria.
- EI tallenna yrityksiä.

NORMAALI AJO:
- Tavily voidaan ottaa käyttöön myöhemmin.
- OpenRouteria käytetään vasta AI-analyysissä.
"""

import re
from urllib.parse import urlparse

import requests

import config
from utils.fetch import analyze_url
from utils.state import load_companies, make_slug, save_companies
from utils.claude_client import ask_claude_json


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

HEADERS = {
    "User-Agent": (
        "WebsiteBuilderAgent/1.0 "
        "(https://github.com/K4K33/website-builder-agent)"
    ),
    "Accept": "application/json",
}


BLOCKED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
    "google.com",
    "google.fi",
    "maps.google.com",
    "tripadvisor.com",
    "yelp.com",
    "wikipedia.org",
}


def _clean_url(url: str) -> str | None:
    if not url:
        return None

    url = url.strip()

    if not url:
        return None

    if not url.lower().startswith(("http://", "https://")):
        url = "https://" + url

    try:
        parsed = urlparse(url)

        if parsed.scheme not in ("http", "https"):
            return None

        if not parsed.netloc:
            return None

        return url.rstrip("/")

    except Exception:
        return None


def _is_blocked_domain(url: str) -> bool:
    try:
        domain = urlparse(url).netloc.lower()
        domain = domain.replace("www.", "")

        for blocked in BLOCKED_DOMAINS:
            if domain == blocked or domain.endswith("." + blocked):
                return True

        return False

    except Exception:
        return True


def _normalize_website(value: str | None) -> str | None:
    if not value:
        return None

    value = value.strip()

    if not value:
        return None

    value = value.split(";")[0].strip()

    url = _clean_url(value)

    if not url:
        return None

    if _is_blocked_domain(url):
        return None

    return url


def _build_overpass_query(location: str, industry: str) -> str:
    """
    Rakentaa Overpass QL -kyselyn.

    Kampaamot ja parturit:
    shop=hairdresser
    craft=hairdresser
    """

    location = location.strip()
    industry_lower = industry.lower().strip()

    if "kampa" in industry_lower or "parturi" in industry_lower:
        tags = """
          nwr["shop"="hairdresser"](area.searchArea);
          nwr["craft"="hairdresser"](area.searchArea);
        """
    else:
        tags = """
          nwr["shop"](area.searchArea);
          nwr["craft"](area.searchArea);
          nwr["office"](area.searchArea);
        """

    return f"""
[out:json][timeout:30];

area
  ["name"="{location}"]
  ["boundary"="administrative"]
  ->.searchArea;

(
{tags}
);

out center tags;
""".strip()


def _search_overpass(
    location: str,
    industry: str,
    max_results: int = 20,
) -> list[dict]:
    """
    Hakee yrityksiä OpenStreetMapista.

    Tämä vaihe ei käytä Tavilyä eikä OpenRouteria.
    """

    print()
    print("  [OSM] Haetaan yrityksiä OpenStreetMapista...")
    print(f"  [OSM] Sijainti: {location}")
    print(f"  [OSM] Ala: {industry or 'yleinen yrityshaku'}")

    query = _build_overpass_query(
        location=location,
        industry=industry,
    )

    try:
        response = requests.post(
            OVERPASS_URL,
            params={
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
                f"  [OSM] {response.text[:500]}"
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

    results = []
    seen_names = set()

    for element in elements:
        tags = element.get("tags", {})

        name = (
            tags.get("name")
            or tags.get("brand")
            or ""
        ).strip()

        if not name:
            continue

        normalized_name = re.sub(
            r"\s+",
            " ",
            name.lower(),
        )

        if normalized_name in seen_names:
            continue

        seen_names.add(normalized_name)

        website = (
            tags.get("website")
            or tags.get("contact:website")
            or tags.get("url")
        )

        website = _normalize_website(website)

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

        street = (
            tags.get("addr:street")
            or ""
        ).strip()

        house_number = (
            tags.get("addr:housenumber")
            or ""
        ).strip()

        postcode = (
            tags.get("addr:postcode")
            or ""
        ).strip()

        city = (
            tags.get("addr:city")
            or location
        ).strip()

        address_parts = [
            part
            for part in [
                street,
                house_number,
                postcode,
                city,
            ]
            if part
        ]

        address = " ".join(address_parts)

        results.append(
            {
                "name": name,
                "url": website,
                "phone": phone,
                "email": email,
                "address": address,
                "source": "openstreetmap",
            }
        )

        if len(results) >= max_results:
            break

    with_website = [
        result
        for result in results
        if result.get("url")
    ]

    print(
        f"  [OSM] Yrityksiä yhteensä: {len(results)}"
    )

    print(
        f"  [OSM] Yrityksiä, joilla verkkosivu: "
        f"{len(with_website)}"
    )

    return results


def _analyze_candidates(
    candidates: list[dict],
    max_results: int,
) -> list[dict]:
    """
    Hakee löydettyjen yritysten verkkosivut ja analysoi
    niiden perustekniset ominaisuudet.

    Ei käytä Tavilyä eikä OpenRouteria.
    """

    analyzed = []

    for candidate in candidates:
        if len(analyzed) >= max_results:
            break

        url = candidate.get("url")

        if not url:
            print(
                f"  [skip] Ei verkkosivua: "
                f"{candidate.get('name', '')}"
            )
            continue

        print()
        print(
            f"  [site] Tarkistetaan: "
            f"{candidate.get('name', '')}"
        )
        print(
            f"  [site] URL: {url}"
        )

        data = analyze_url(url)

        if not data:
            print(
                "  [site] Verkkosivua ei voitu hakea."
            )
            continue

        candidate_copy = dict(candidate)
        candidate_copy["site_analysis"] = data

        analyzed.append(candidate_copy)

        print(
            f"  [site] OK | "
            f"title='{data.get('title', '')}' | "
            f"viewport={data.get('has_viewport_meta', False)}"
        )

    return analyzed


def _score_without_ai(company: dict) -> dict:
    """
    Paikallinen heuristiikka dry-run-testaukseen.

    Tämä ei ole lopullinen AI-arvio.
    """

    site = company.get("site_analysis", {})

    title = site.get("title", "")
    meta_description = site.get("meta_description", "")
    visible_text = site.get("visible_text", "")
    viewport = site.get("has_viewport_meta", False)

    issues = []

    if not title:
        issues.append("title puuttuu")

    if not meta_description:
        issues.append("meta description puuttuu")

    if not viewport:
        issues.append("viewport-meta puuttuu")

    if len(visible_text) < 200:
        issues.append("hyvin vähän näkyvää sisältöä")

    raw_html_length = site.get("raw_html_length", 0)

    if raw_html_length < 5000:
        issues.append("hyvin pieni HTML-sivu")

    score = len(issues)

    old_site = score >= 2

    return {
        "old_site": old_site,
        "confidence": min(
            0.95,
            0.40 + score * 0.15,
        ),
        "issues": issues,
        "method": "local_heuristic",
    }


def _ai_analyze_company(company: dict) -> dict:
    """
    Normaali tuotantoanalyysi OpenRouterilla.

    Tätä funktiota ei kutsuta dry-run-tilassa.
    """

    site = company.get("site_analysis", {})

    prompt = f"""
Analysoi seuraavan yrityksen nykyinen verkkosivusto.

Yritys:
{company.get("name", "")}

URL:
{company.get("url", "")}

Sivun title:
{site.get("title", "")}

Meta description:
{site.get("meta_description", "")}

Viewport:
{site.get("has_viewport_meta", False)}

Näkyvä teksti:
{site.get("visible_text", "")[:6000]}

Palauta JSON:

{{
  "old_site": true,
  "confidence": 0.0,
  "reasons": [
    "..."
  ]
}}

Arvioi erityisesti:
- vanhanaikainen rakenne
- mobiilikäytettävyys
- puuttuva tai heikko sisältö
- puuttuvat yhteydenottokehotteet
- teknisesti heikko toteutus
- selvästi parannettavissa oleva asiakaskokemus

Älä väitä sivustoa vanhaksi vain siksi, että se on yksinkertainen.
"""

    return ask_claude_json(
        system=(
            "Olet verkkosivustojen analysointiin erikoistunut "
            "AI-agentti. Ole objektiivinen ja perustele havainnot."
        ),
        user_prompt=prompt,
        max_tokens=1500,
    )


def run_scout(
    count: int = 10,
    industry: str = "",
    location: str = "",
    dry_run: bool = False,
) -> list[dict]:
    """
    Scout-agentin pääfunktio.
    """

    print()
    print("=== SCOUT ===")

    query_text = " ".join(
        part
        for part in [
            industry,
            location,
        ]
        if part
    ).strip()

    print(
        f"Hakukysely: {query_text or '(ei määritelty)'}"
    )

    print(
        f"Tavoite: {count} yritystä"
    )

    if dry_run:
        print("TILA: DRY-RUN")
        print("Tavilyä EI käytetä.")
        print("OpenRouteria EI käytetä.")
        print("Yrityksiä EI tallenneta.")

    candidates = _search_overpass(
        location=location,
        industry=industry,
        max_results=max(
            count * 3,
            10,
        ),
    )

    if not candidates:
        print()
        print(
            "[scout] OpenStreetMapista ei löytynyt yrityksiä."
        )
        return []

    analyzed = _analyze_candidates(
        candidates=candidates,
        max_results=count,
    )

    if not analyzed:
        print()
        print(
            "[scout] Löydetyillä yrityksillä ei ollut "
            "käyttökelpoisia verkkosivuja."
        )
        return []

    results = []

    for company in analyzed:
        if dry_run:
            evaluation = _score_without_ai(company)

            company["evaluation"] = evaluation
            results.append(company)

            print()
            print(
                f"  [dry-run] {company.get('name', '')}"
            )

            print(
                f"  [dry-run] URL: "
                f"{company.get('url', '')}"
            )

            print(
                f"  [dry-run] Mahdollisesti vanha: "
                f"{evaluation['old_site']}"
            )

            print(
                f"  [dry-run] Luottamus: "
                f"{evaluation['confidence']:.2f}"
            )

            if evaluation["issues"]:
                print(
                    "  [dry-run] Havainnot: "
                    + ", ".join(
                        evaluation["issues"]
                    )
                )

            continue

        evaluation = _ai_analyze_company(company)

        company["evaluation"] = evaluation

        old_site = bool(
            evaluation.get(
                "old_site",
                False,
            )
        )

        confidence = float(
            evaluation.get(
                "confidence",
                0,
            )
        )

        if not old_site:
            print(
                f"  [scout] Hylätään: "
                f"{company.get('name', '')} "
                "(sivu ei vaikuta riittävän vanhalta/puutteelliselta)"
            )
            continue

        if confidence < 0.60:
            print(
                f"  [scout] Hylätään: "
                f"{company.get('name', '')} "
                f"(luottamus {confidence:.2f})"
            )
            continue

        results.append(company)

    if dry_run:
        print()
        print("=== DRY-RUN VALMIS ===")
        print(
            f"Yrityksiä analysoitiin: {len(results)}"
        )
        print("Tavily-kutsuja: 0")
        print("OpenRouter-kutsuja: 0")
        print("Tallennettuja yrityksiä: 0")

        return results

    companies = load_companies()
    saved = []

    for company in results:
        name = company.get("name", "")
        url = company.get("url", "")

        slug = make_slug(name)

        if not slug:
            continue

        if slug in companies:
            print(
                f"  [scout] Ohitetaan jo olemassa oleva: "
                f"{name}"
            )
            continue

        companies[slug] = {
            "name": name,
            "url": url,
            "phone": company.get("phone", ""),
            "email": company.get("email", ""),
            "address": company.get("address", ""),
            "status": "found",
            "source": company.get(
                "source",
                "unknown",
            ),
            "site_analysis": company.get(
                "site_analysis",
                {},
            ),
            "evaluation": company.get(
                "evaluation",
                {},
            ),
        }

        saved.append(company)

    save_companies(companies)

    print()
    print(
        f"[Scout] Tallennettu uusia yrityksiä: "
        f"{len(saved)}"
    )

    return saved
