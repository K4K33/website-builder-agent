"""
Website Builder Agent - Scout.

Scout:
- hakee yrityksiä OpenStreetMapista
- kokeilee useita Overpass-palvelimia
- tarkistaa verkkosivut
- ottaa desktop- ja mobiilikuvakaappaukset
- tekee teknisen analyysin
- käyttää OpenRouterin vision-AI:ta oikeassa ajossa
- ei käytä OpenRouteria dry-runissa
"""

import json
import os
import time

import requests

import config
from utils.fetch import analyze_url
from utils.screenshot import capture_website
from utils.claude_client import ask_claude_json


OVERPASS_SERVERS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]

OVERPASS_TIMEOUT = 45
OVERPASS_RETRIES = 2

OSM_HEADERS = {
    "User-Agent": (
        "WebsiteBuilderAgent/1.0 "
        "(business website research tool)"
    )
}


def _build_overpass_query(
    industry: str,
    location: str,
) -> str:

    return f"""
[out:json][timeout:40];

area
  ["name"="{location}"]
  ["boundary"="administrative"]
  ->.searchArea;

(
  nwr
    ["shop"="hairdresser"]
    (area.searchArea);

  nwr
    ["craft"="hairdresser"]
    (area.searchArea);

  nwr
    ["amenity"="beauty"]
    (area.searchArea);
);

out center tags;
"""


def _request_overpass(
    server: str,
    query: str,
) -> dict | None:

    for attempt in range(
        1,
        OVERPASS_RETRIES + 1,
    ):

        try:

            print(
                f"  [OSM] Yritys "
                f"{attempt}/{OVERPASS_RETRIES}:"
            )

            response = requests.post(
                server,
                data=query.encode("utf-8"),
                headers=OSM_HEADERS,
                timeout=OVERPASS_TIMEOUT,
            )

            print(
                f"  [OSM] HTTP-status: "
                f"{response.status_code}"
            )

            if response.status_code == 200:

                try:
                    return response.json()

                except ValueError as error:

                    print(
                        "  [OSM] JSON-vastausta "
                        f"ei voitu lukea: {error}"
                    )

            else:

                print(
                    "  [OSM] Palvelin palautti "
                    f"virheen: {response.status_code}"
                )

                if response.text:
                    print(
                        response.text[:1000]
                    )

        except requests.Timeout:

            print(
                "  [OSM] Palvelin aikakatkaisi."
            )

        except requests.RequestException as error:

            print(
                "  [OSM] Verkkovirhe: "
                f"{error}"
            )

        if attempt < OVERPASS_RETRIES:

            wait = 2 * attempt

            print(
                f"  [OSM] Odotetaan {wait}s..."
            )

            time.sleep(wait)

    return None


def _fetch_osm_companies(
    industry: str,
    location: str,
) -> list[dict]:

    print(
        "  [OSM] Haetaan yrityksiä "
        "OpenStreetMapista..."
    )

    print(
        f"  [OSM] Sijainti: {location}"
    )

    print(
        f"  [OSM] Ala: {industry}"
    )

    query = _build_overpass_query(
        industry,
        location,
    )

    for index, server in enumerate(
        OVERPASS_SERVERS,
        start=1,
    ):

        print(
            f"  [OSM] Palvelin "
            f"{index}/{len(OVERPASS_SERVERS)}:"
        )

        print(
            f"  [OSM] {server}"
        )

        data = _request_overpass(
            server,
            query,
        )

        if data is None:

            print(
                "  [OSM] Palvelin epäonnistui. "
                "Kokeillaan seuraavaa..."
            )

            continue

        elements = data.get(
            "elements",
            [],
        )

        print(
            f"  [OSM] Löydettyjä kohteita: "
            f"{len(elements)}"
        )

        companies = []
        seen = set()

        for element in elements:

            tags = element.get(
                "tags",
                {},
            )

            name = (
                tags.get("name")
                or tags.get("brand")
                or ""
            ).strip()

            if not name:
                continue

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
                tags.get("addr:street", ""),
                tags.get("addr:housenumber", ""),
                tags.get("addr:postcode", ""),
                tags.get("addr:city", ""),
            ]

            address = " ".join(
                part.strip()
                for part in address_parts
                if part and part.strip()
            )

            key = (
                name.lower(),
                website.lower(),
            )

            if key in seen:
                continue

            seen.add(key)

            companies.append(
                {
                    "name": name,
                    "website": website,
                    "phone": phone,
                    "email": email,
                    "address": address,
                    "osm_type": element.get("type"),
                    "osm_id": element.get("id"),
                    "tags": tags,
                }
            )

        print(
            f"  [OSM] Yrityksiä yhteensä: "
            f"{len(companies)}"
        )

        with_websites = [
            company
            for company in companies
            if company.get("website")
        ]

        print(
            "  [OSM] Yrityksiä, joilla "
            f"verkkosivu: {len(with_websites)}"
        )

        return companies

    print(
        "[OSM] Kaikki Overpass-palvelimet "
        "epäonnistuivat."
    )

    return []


def _normalize_url(
    url: str,
) -> str:

    if not url:
        return ""

    url = url.strip()

    if not url.startswith(
        (
            "http://",
            "https://",
        )
    ):
        url = "https://" + url

    return url


def _technical_analysis(
    company: dict,
) -> dict:

    url = _normalize_url(
        company.get("website", "")
    )

    if not url:

        return {
            "success": False,
            "issues": [],
            "positives": [],
            "problem_signals": 0,
            "priority": "unknown",
            "redesignable": False,
            "confidence": 0.0,
        }

    try:

        result = analyze_url(url)

    except Exception as error:

        print(
            "  [site] Analyysi epäonnistui: "
            f"{error}"
        )

        return {
            "success": False,
            "issues": [
                f"verkkosivun analyysi epäonnistui: {error}"
            ],
            "positives": [],
            "problem_signals": 3,
            "priority": "medium",
            "redesignable": True,
            "confidence": 0.5,
        }

    # analyze_url() voi joissain tilanteissa
    # palauttaa None ilman exceptionia.
    # Muutetaan se hallituksi epäonnistumiseksi,
    # jotta yksi huono verkkosivu ei kaada Scoutia.
    if result is None:

        print(
            "  [site] Analyysi palautti tyhjän "
            "tuloksen."
        )

        return {
            "success": False,
            "issues": [
                "verkkosivun analyysi palautti tyhjän tuloksen"
            ],
            "positives": [],
            "problem_signals": 3,
            "priority": "medium",
            "redesignable": True,
            "confidence": 0.5,
        }

    # Varmistetaan vielä, että tulos on sanakirja.
    if not isinstance(result, dict):

        print(
            "  [site] Analyysi palautti "
            "virheellisen tietotyypin."
        )

        return {
            "success": False,
            "issues": [
                "verkkosivun analyysi palautti virheellisen tietotyypin"
            ],
            "positives": [],
            "problem_signals": 3,
            "priority": "medium",
            "redesignable": True,
            "confidence": 0.5,
        }

    return result


def _ai_analyze_company(
    company: dict,
    technical: dict,
) -> dict:

    screenshots = technical.get(
        "screenshots",
        {},
    )

    if not isinstance(screenshots, dict):
        screenshots = {}

    image_paths = []

    desktop = screenshots.get(
        "desktop"
    )

    mobile = screenshots.get(
        "mobile"
    )

    if desktop and os.path.exists(desktop):
        image_paths.append(desktop)

    if mobile and os.path.exists(mobile):
        image_paths.append(mobile)

    system = """
Olet verkkosivujen UX/UI-asiantuntija.

Arvioi verkkosivua oikean asiakkaan näkökulmasta.

Arvioi:
- ensimmäinen vaikutelma
- visuaalinen modernius
- selkeys
- luettavuus
- navigointi
- tietojen löydettävyys
- CTA:n näkyvyys
- luottamusta lisäävät elementit
- mobiilikokemus
- visuaalinen hierarkia
- mahdollinen sekavuus
- todellinen tarve verkkosivun uudistamiselle

Älä keksi asioita, joita kuvissa ei voi havaita.

Pelkkä tekninen puute ei yksin tarkoita,
että koko sivu pitäisi uudistaa.

Käytä pisteitä 0-10.

overall_opportunity_score:
0 = erittäin pieni uudistusmahdollisuus
10 = erittäin suuri uudistusmahdollisuus.
"""

    prompt = f"""
Yritys:
{company.get("name", "")}

Verkkosivu:
{company.get("website", "")}

Tekninen analyysi:
{json.dumps(
    technical,
    ensure_ascii=False,
    indent=2,
)[:12000]}

Mukana olevat kuvat ovat:
- desktop-kuvakaappaus
- mobiilikuva

Palauta AINOASTAAN validi JSON:

{{
  "visual_score": 0,
  "usability_score": 0,
  "mobile_score": 0,
  "content_score": 0,
  "conversion_score": 0,
  "overall_opportunity_score": 0,
  "redesign_recommended": false,
  "confidence": 0.0,
  "visual_problems": [],
  "usability_problems": [],
  "mobile_problems": [],
  "conversion_problems": [],
  "strengths": [],
  "recommended_improvements": [],
  "reasoning": ""
}}
"""

    print(
        "  [AI] Analysoidaan "
        "verkkosivua visuaalisesti..."
    )

    return ask_claude_json(
        system=system,
        user_prompt=prompt,
        max_tokens=3000,
        image_paths=image_paths,
    )


def _save_company(
    company: dict,
    output_file: str,
) -> None:

    directory = os.path.dirname(
        output_file
    )

    if directory:
        os.makedirs(
            directory,
            exist_ok=True,
        )

    companies = []

    if os.path.exists(output_file):

        try:

            with open(
                output_file,
                "r",
                encoding="utf-8",
            ) as file:

                companies = json.load(file)

        except (
            json.JSONDecodeError,
            OSError,
        ):

            companies = []

    if not isinstance(
        companies,
        list,
    ):
        companies = []

    existing_names = {
        item.get("name", "").lower()
        for item in companies
        if isinstance(item, dict)
    }

    name = company.get(
        "name",
        "",
    )

    if name.lower() not in existing_names:
        companies.append(company)

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            companies,
            file,
            ensure_ascii=False,
            indent=2,
        )


def _analyze_candidates(
    candidates: list[dict],
    max_results: int,
    dry_run: bool,
) -> list[dict]:

    analyzed = []

    for candidate in candidates:

        if len(analyzed) >= max_results:
            break

        name = candidate.get(
            "name",
            "Tuntematon",
        )

        website = _normalize_url(
            candidate.get(
                "website",
                "",
            )
        )

        if not website:

            print(
                f"  [skip] Ei verkkosivua: "
                f"{name}"
            )

            continue

        candidate["website"] = website

        print(
            f"  [site] Tarkistetaan: {name}"
        )

        print(
            f"  [site] URL: {website}"
        )

        technical = _technical_analysis(
            candidate
        )

        # Lisäsuoja: technical ei saa koskaan
        # olla None tai muu kuin dict.
        if not isinstance(technical, dict):

            print(
                "  [site] Tekninen analyysi "
                "ei palauttanut kelvollista "
                "tulosta."
            )

            continue

        candidate["technical_analysis"] = (
            technical
        )

        if not technical.get(
            "success",
            False,
        ):

            print(
                f"  [site] Analyysi epäonnistui: "
                f"{name}"
            )

            continue

        print(
            "  [site] OK | "
            f"title='{technical.get('title', '')}' "
            f"| viewport="
            f"{technical.get('viewport', False)}"
        )

        print(
            f"  [site] Otetaan kuvakaappaukset: "
            f"{name}"
        )

        try:

            screenshots = capture_website(
                website,
                name,
            )

        except Exception as error:

            print(
                "  [site] Kuvakaappausten "
                f"ottaminen epäonnistui: {error}"
            )

            screenshots = None

        candidate["screenshots"] = (
            screenshots or {}
        )

        if screenshots:

            print(
                "  [site] Kuvakaappaukset: OK"
            )

            if screenshots.get("desktop"):
                print(
                    "    desktop: "
                    f"{screenshots['desktop']}"
                )

            if screenshots.get("mobile"):
                print(
                    "    mobile: "
                    f"{screenshots['mobile']}"
                )

        else:

            print(
                "  [site] Kuvakaappausten "
                "ottaminen epäonnistui."
            )

        technical["screenshots"] = (
            screenshots or {}
        )

        if not dry_run:

            try:

                ai_analysis = _ai_analyze_company(
                    candidate,
                    technical,
                )

                if not isinstance(
                    ai_analysis,
                    dict,
                ):

                    raise RuntimeError(
                        "AI palautti virheellisen "
                        "tietotyypin."
                    )

                candidate["ai_analysis"] = (
                    ai_analysis
                )

                print(
                    "  [AI] Analyysi valmis."
                )

                opportunity_score = (
                    ai_analysis.get(
                        "overall_opportunity_score",
                        "N/A",
                    )
                )

                redesign_recommended = (
                    ai_analysis.get(
                        "redesign_recommended",
                        "N/A",
                    )
                )

                print(
                    "  [AI] Opportunity score: "
                    f"{opportunity_score}"
                )

                print(
                    "  [AI] Redesign recommended: "
                    f"{redesign_recommended}"
                )

            except Exception as error:

                print(
                    "  [AI] Analyysi epäonnistui: "
                    f"{error}"
                )

                candidate["ai_analysis"] = {
                    "error": str(error)
                }

        analyzed.append(
            candidate
        )

    return analyzed


def scout(
    count: int = 10,
    industry: str = "kampaamo",
    location: str = "Tampere",
    dry_run: bool = False,
) -> list[dict]:

    print(
        f"[Scout] Etsitään {count} yritystä..."
    )

    print()
    print("=== SCOUT ===")

    print(
        f"Hakukysely: "
        f"{industry} {location}"
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

    print()

    candidates = _fetch_osm_companies(
        industry,
        location,
    )

    if not candidates:

        print(
            "[scout] OpenStreetMapista "
            "ei löytynyt yrityksiä."
        )

        print(
            "Ei löytynyt uusia yrityksiä "
            "(tai kaikki löydetyt olivat "
            "jo pidemmällä)."
        )

        return []

    analyzed = _analyze_candidates(
        candidates,
        max_results=count,
        dry_run=dry_run,
    )

    saved_count = 0

    if not dry_run:

        output_file = getattr(
            config,
            "COMPANIES_FILE",
            "data/companies.json",
        )

        for company in analyzed:

            _save_company(
                company,
                output_file,
            )

            saved_count += 1

    if dry_run:

        for company in analyzed:

            technical = company.get(
                "technical_analysis",
                {},
            )

            print()
            print(
                f"  [dry-run] "
                f"{company.get('name', '')}"
            )

            print(
                f"  [dry-run] URL: "
                f"{company.get('website', '')}"
            )

            print(
                "  [dry-run] Ongelmasignaalit: "
                f"{technical.get('problem_signals', 0)}"
            )

            print(
                "  [dry-run] Prioriteetti: "
                f"{technical.get('priority', 'unknown')}"
            )

            print(
                "  [dry-run] Mahdollisesti uudistettava: "
                f"{technical.get('redesignable', False)}"
            )

            print(
                "  [dry-run] Teknisen analyysin luottamus: "
                f"{technical.get('confidence', 0)}"
            )

            screenshots = company.get(
                "screenshots",
                {},
            )

            if screenshots:

                print(
                    "  [dry-run] Kuvakaappaukset:"
                )

                if screenshots.get("desktop"):
                    print(
                        "    - desktop: "
                        f"{screenshots['desktop']}"
                    )

                if screenshots.get("mobile"):
                    print(
                        "    - mobile: "
                        f"{screenshots['mobile']}"
                    )

            issues = technical.get(
                "issues",
                [],
            )

            if issues:

                print(
                    "  [dry-run] Ongelmahavainnot:"
                )

                for issue in issues:
                    print(
                        f"    - {issue}"
                    )

            positives = technical.get(
                "positives",
                [],
            )

            if positives:

                print(
                    "  [dry-run] Positiiviset signaalit:"
                )

                for positive in positives:
                    print(
                        f"    + {positive}"
                    )

        print()
        print(
            "=== DRY-RUN VALMIS ==="
        )

        print(
            f"Yrityksiä analysoitiin: "
            f"{len(analyzed)}"
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

    else:

        print()
        print(
            "=== SCOUT VALMIS ==="
        )

        print(
            f"Yrityksiä analysoitiin: "
            f"{len(analyzed)}"
        )

        print(
            f"Tallennettuja yrityksiä: "
            f"{saved_count}"
        )

    print(
        f"[Scout] Käsitelty "
        f"{len(analyzed)} yritystä."
    )

    if dry_run:

        print(
            "[Scout] DRY-RUN: mitään "
            "yrityksiä ei tallennettu."
        )

    return analyzed


def run_scout(
    count: int = 10,
    industry: str = "kampaamo",
    location: str = "Tampere",
    dry_run: bool = False,
    **kwargs,
):
    """
    Yhteensopivuus main.py:n kanssa.

    main.py kutsuu scout.run_scout().
    Varsinainen työ tehdään scout()-funktiossa.
    """

    return scout(
        count=count,
        industry=industry,
        location=location,
        dry_run=dry_run,
    )
