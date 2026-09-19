"""
Scout-agentti Website Builder Agentille.

Scout tekee kaksi eri asiaa:

1. DRY-RUN
   - löytää yrityksiä OpenStreetMapista
   - tarkistaa verkkosivut
   - analysoi teknisiä ominaisuuksia
   - analysoi sisältöä ja käytettävyyden signaaleja
   - ottaa desktop- ja mobiilikuvakaappaukset
   - EI käytä Tavilyä
   - EI käytä OpenRouteria
   - EI tallenna yrityksiä

2. NORMAALI KÄYTTÖ
   - tekee saman perustason analyysin
   - ottaa kuvakaappaukset
   - käyttää myöhemmin OpenRouteria syvempään AI-arvioon
   - tallentaa yritykset data/companies.json-tiedostoon

Visuaalinen AI-analyysi lisätään seuraavassa vaiheessa.
"""

import re
import requests

import config

from utils.fetch import analyze_url
from utils.screenshot import capture_website
from utils.state import load_companies, save_companies, make_slug


OVERPASS_URL = "https://overpass-api.de/api/interpreter"

HEADERS = {
    "User-Agent": (
        "WebsiteBuilderAgent/1.0 "
        "(https://github.com/K4K33/website-builder-agent)"
    ),
    "Accept": "application/json",
}


def _build_overpass_query(
    location: str,
    industry: str,
) -> str:
    """
    Rakentaa OpenStreetMap/Overpass-kyselyn.
    """

    location = location.strip()
    industry_lower = industry.lower().strip()

    if (
        "kampa" in industry_lower
        or "parturi" in industry_lower
    ):
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

    print(
        "  [OSM] Haetaan yrityksiä OpenStreetMapista..."
    )

    print(
        f"  [OSM] Sijainti: {location}"
    )

    print(
        f"  [OSM] Ala: {industry}"
    )

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
            f"  [OSM] HTTP-status: "
            f"{response.status_code}"
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

    elements = data.get(
        "elements",
        [],
    )

    print(
        f"  [OSM] Löydettyjä kohteita: "
        f"{len(elements)}"
    )

    companies = []

    seen_names = set()

    for element in elements:

        tags = element.get(
            "tags",
            {},
        )

        name = tags.get(
            "name",
            "",
        ).strip()

        if not name:
            continue

        normalized_name = name.lower()

        if normalized_name in seen_names:
            continue

        seen_names.add(
            normalized_name
        )

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
            tags.get(
                "addr:street",
                "",
            ).strip(),

            tags.get(
                "addr:housenumber",
                "",
            ).strip(),

            tags.get(
                "addr:postcode",
                "",
            ).strip(),

            tags.get(
                "addr:city",
                "",
            ).strip(),
        ]

        address = " ".join(
            part
            for part in address_parts
            if part
        )

        companies.append(
            {
                "name": name,
                "url": website,
                "phone": phone,
                "email": email,
                "address": address,
                "osm_type": element.get(
                    "type",
                    "",
                ),
                "osm_id": element.get(
                    "id"
                ),
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
        f"  [OSM] Yrityksiä yhteensä: "
        f"{len(companies)}"
    )

    print(
        f"  [OSM] Yrityksiä, joilla verkkosivu: "
        f"{len(with_website)}"
    )

    return companies


def _normalize_url(
    url: str,
) -> str:
    """
    Varmistaa, että URL sisältää protokollan.
    """

    url = (
        url
        or ""
    ).strip()

    if not url:
        return ""

    if not re.match(
        r"^https?://",
        url,
        re.IGNORECASE,
    ):
        url = "https://" + url

    return url


def _analyze_candidates(
    candidates: list[dict],
) -> list[dict]:
    """
    Hakee yritysten verkkosivut,
    analysoi ne ja ottaa kuvakaappaukset.
    """

    analyzed = []

    for company in candidates:

        name = company.get(
            "name",
            "",
        )

        raw_url = company.get(
            "url",
            "",
        )

        if not raw_url:
            print(
                f"  [skip] Ei verkkosivua: "
                f"{name}"
            )

            continue

        url = _normalize_url(
            raw_url
        )

        print(
            f"  [site] Tarkistetaan: "
            f"{name}"
        )

        print(
            f"  [site] URL: {url}"
        )

        # ==================================================
        # HTML-ANALYYSI
        # ==================================================

        data = analyze_url(
            url
        )

        if not data:
            print(
                f"  [site] Sivua ei voitu hakea: "
                f"{name}"
            )

            continue

        print(
            f"  [site] OK | "
            f"title='{data.get('title', '')}' | "
            f"viewport="
            f"{data.get('has_viewport_meta', False)}"
        )

        # ==================================================
        # KUVAKAAPPAUKSET
        # ==================================================

        print(
            f"  [site] Otetaan kuvakaappaukset: "
            f"{name}"
        )

        screenshots = capture_website(
            url=url,
            company_name=name,
        )

        if screenshots:

            print(
                "  [site] Kuvakaappaukset: OK"
            )

            print(
                f"    desktop: "
                f"{screenshots.get('desktop', '')}"
            )

            print(
                f"    mobile: "
                f"{screenshots.get('mobile', '')}"
            )

        else:

            print(
                "  [site] Kuvakaappausten ottaminen "
                "epäonnistui."
            )

        result = dict(company)

        result["url"] = url

        result["site_analysis"] = data

        result["screenshots"] = (
            screenshots or {}
        )

        analyzed.append(
            result
        )

    return analyzed


def _score_without_ai(
    company: dict,
) -> dict:
    """
    Arvioi verkkosivun laatua ilman AI:ta.

    Tämä ei yritä väittää, että kone tietää miltä
    sivu näyttää ihmisen silmissä.

    Se kerää objektiivisia signaaleja, joita voidaan
    myöhemmin yhdistää visuaaliseen AI-arvioon.

    Korkeampi score = enemmän havaittuja ongelmasignaaleja.
    """

    data = company.get(
        "site_analysis",
        {},
    )

    title = data.get(
        "title",
        "",
    ).strip()

    meta_description = data.get(
        "meta_description",
        "",
    ).strip()

    visible_text = data.get(
        "visible_text",
        "",
    )

    visible_text_length = int(
        data.get(
            "visible_text_length",
            len(visible_text),
        )
        or 0
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

    h1_count = int(
        data.get(
            "h1_count",
            0,
        )
        or 0
    )

    link_count = int(
        data.get(
            "link_count",
            0,
        )
        or 0
    )

    button_count = int(
        data.get(
            "button_count",
            0,
        )
        or 0
    )

    form_count = int(
        data.get(
            "form_count",
            0,
        )
        or 0
    )

    image_count = int(
        data.get(
            "image_count",
            0,
        )
        or 0
    )

    images_without_alt_count = int(
        data.get(
            "images_without_alt_count",
            0,
        )
        or 0
    )

    contact_signals = data.get(
        "contact_signals",
        {},
    )

    cta_signals = data.get(
        "cta_signals",
        {},
    )

    score = 0

    reasons = []

    positive_signals = []

    if not meta_description:
        score += 1
        reasons.append(
            "meta description puuttuu"
        )
    else:
        positive_signals.append(
            "meta description löytyy"
        )

    if not has_viewport:
        score += 2
        reasons.append(
            "viewport-meta puuttuu"
        )
    else:
        positive_signals.append(
            "viewport-meta löytyy"
        )

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
    else:
        positive_signals.append(
            "sivulla on title"
        )

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
    else:
        positive_signals.append(
            "HTML-rakenne ei ole poikkeuksellisen pieni"
        )

    if visible_text_length < 500:
        score += 3
        reasons.append(
            "erittäin vähän näkyvää sisältöä"
        )
    elif visible_text_length < 1000:
        score += 2
        reasons.append(
            "vähän näkyvää sisältöä"
        )
    elif visible_text_length < 1800:
        score += 1
        reasons.append(
            "melko vähän näkyvää sisältöä"
        )
    else:
        positive_signals.append(
            "sivulla on kohtuullisesti sisältöä"
        )

    if h1_count == 0:
        score += 2
        reasons.append(
            "H1-otsikko puuttuu"
        )
    elif h1_count > 1:
        score += 1
        reasons.append(
            "sivulla on useita H1-otsikoita"
        )
    else:
        positive_signals.append(
            "yksi H1-otsikko löytyy"
        )

    if link_count == 0:
        score += 3
        reasons.append(
            "sivulla ei ole linkkejä"
        )
    elif link_count < 3:
        score += 1
        reasons.append(
            "hyvin vähän linkkejä"
        )
    else:
        positive_signals.append(
            "sivulla on navigoitavia linkkejä"
        )

    if button_count == 0:
        reasons.append(
            "selkeitä painikkeita ei löytynyt"
        )
    else:
        positive_signals.append(
            "painikkeita löytyy"
        )

    if not contact_signals.get(
        "phone_found",
        False,
    ):
        score += 1
        reasons.append(
            "puhelinnumeroa ei havaittu"
        )
    else:
        positive_signals.append(
            "puhelinnumero havaittu"
        )

    if not contact_signals.get(
        "email_found",
        False,
    ):
        score += 1
        reasons.append(
            "sähköpostiosoitetta ei havaittu"
        )
    else:
        positive_signals.append(
            "sähköpostiosoite havaittu"
        )

    if not contact_signals.get(
        "address_signal",
        False,
    ):
        score += 1
        reasons.append(
            "osoitetietoa ei havaittu"
        )
    else:
        positive_signals.append(
            "osoitetieto havaittu"
        )

    if cta_signals.get(
        "has_cta",
        False,
    ):
        positive_signals.append(
            "toimintakehotus havaittu"
        )
    else:
        score += 2
        reasons.append(
            "selkeää toimintakehotusta ei havaittu"
        )

    if contact_signals.get(
        "booking_signal",
        False,
    ):
        positive_signals.append(
            "ajanvaraus havaittu"
        )

    if image_count > 0:

        if (
            images_without_alt_count
            == image_count
        ):
            score += 1
            reasons.append(
                "kuvien alt-tekstit puuttuvat"
            )

        elif images_without_alt_count > 0:
            score += 1
            reasons.append(
                "osasta kuvista puuttuu alt-teksti"
            )

        else:
            positive_signals.append(
                "kuvien alt-tekstit löytyvät"
            )

    if form_count > 0:
        positive_signals.append(
            "yhteydenotto-/lomake-elementti löytyy"
        )

    if score >= 8:
        priority = "high"
    elif score >= 4:
        priority = "medium"
    else:
        priority = "low"

    confidence = min(
        0.95,
        round(
            0.25 + score * 0.07,
            2,
        ),
    )

    return {
        "score": score,
        "priority": priority,
        "confidence": confidence,
        "reasons": reasons,
        "positive_signals": positive_signals,
        "old_site": score >= 4,
    }


def _print_dry_run_result(
    company: dict,
) -> None:
    """
    Tulostaa yrityksen auditointituloksen.
    """

    result = _score_without_ai(
        company
    )

    screenshots = company.get(
        "screenshots",
        {},
    )

    print()

    print(
        f"  [dry-run] "
        f"{company.get('name', '')}"
    )

    print(
        f"  [dry-run] URL: "
        f"{company.get('url', '')}"
    )

    print(
        f"  [dry-run] Ongelmasignaalit: "
        f"{result['score']}"
    )

    print(
        f"  [dry-run] Prioriteetti: "
        f"{result['priority']}"
    )

    print(
        f"  [dry-run] "
        f"Mahdollisesti uudistettava: "
        f"{result['old_site']}"
    )

    print(
        f"  [dry-run] "
        f"Teknisen analyysin luottamus: "
        f"{result['confidence']:.2f}"
    )

    if screenshots:

        print(
            "  [dry-run] "
            "Kuvakaappaukset:"
        )

        if screenshots.get("desktop"):
            print(
                f"    - desktop: "
                f"{screenshots['desktop']}"
            )

        if screenshots.get("mobile"):
            print(
                f"    - mobile: "
                f"{screenshots['mobile']}"
            )

    else:

        print(
            "  [dry-run] "
            "Kuvakaappauksia ei saatu."
        )

    if result["reasons"]:

        print(
            "  [dry-run] "
            "Ongelmahavainnot:"
        )

        for reason in result["reasons"]:
            print(
                f"    - {reason}"
            )

    if result["positive_signals"]:

        print(
            "  [dry-run] "
            "Positiiviset signaalit:"
        )

        for signal in result[
            "positive_signals"
        ]:
            print(
                f"    + {signal}"
            )


def _ai_analyze_company(
    company: dict,
) -> dict:
    """
    AI:n syvempi analyysi normaalia käyttöä varten.

    Tätä EI kutsuta dry-runissa.

    Visuaalinen kuvakaappausanalyysi lisätään
    seuraavassa vaiheessa.
    """

    from utils.claude_client import (
        ask_claude_json,
    )

    data = company.get(
        "site_analysis",
        {},
    )

    technical_score = (
        _score_without_ai(
            company
        )
    )

    system = """
Olet verkkosivustojen auditointiin erikoistunut
asiantuntija.

Arvioi pienen yrityksen verkkosivustoa
potentiaalisen uuden asiakkaan näkökulmasta.

Arvioi erikseen:

1. käytettävyys
2. sisältö
3. mobiilikäytön todennäköiset ongelmat
4. tekniset ongelmat
5. toimintakehotukset
6. asiakaskokemus
7. verkkosivuston uudistamisen potentiaali

Älä arvioi visuaalista ulkoasua tämän datan perusteella
liian varmasti, koska tässä vaiheessa et näe kuvakaappausta.

Palauta AINOASTAAN validi JSON:

{
  "usability_score": 0,
  "content_score": 0,
  "mobile_score": 0,
  "technical_score": 0,
  "conversion_score": 0,
  "overall_opportunity_score": 0,
  "old_site": true,
  "confidence": 0.0,
  "reasons": [],
  "recommended_improvements": []
}

Kaikki score-arvot välillä 0-10.
Korkeampi score tarkoittaa suurempaa
uudistustarvetta.
"""

    user_prompt = f"""
Yritys:
{company.get('name', '')}

URL:
{company.get('url', '')}

Perustason ongelmasignaalit:
{technical_score.get('score', 0)}

Perustason prioriteetti:
{technical_score.get('priority', '')}

Perustason havainnot:
{technical_score.get('reasons', [])}

Title:
{data.get('title', '')}

Meta description:
{data.get('meta_description', '')}

Viewport:
{data.get('has_viewport_meta', False)}

Näkyvän tekstin määrä:
{data.get('visible_text_length', 0)}

H1-määrä:
{data.get('h1_count', 0)}

Linkkien määrä:
{data.get('link_count', 0)}

Painikkeiden määrä:
{data.get('button_count', 0)}

Lomakkeiden määrä:
{data.get('form_count', 0)}

Kuvien määrä:
{data.get('image_count', 0)}

Kuvia ilman alt-tekstiä:
{data.get('images_without_alt_count', 0)}

Yhteystietosignaalit:
{data.get('contact_signals', {})}

CTA-signaalit:
{data.get('cta_signals', {})}

Otsikot:
{data.get('headings', {})}

Näkyvä teksti:
{data.get('visible_text', '')[:6000]}
"""

    return ask_claude_json(
        system,
        user_prompt,
        use_web_search=False,
        max_tokens=1500,
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

    print(
        f"[Scout] Etsitään {count} yritystä..."
    )

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

            results.append(
                company
            )

            continue

        try:

            ai_result = (
                _ai_analyze_company(
                    company
                )
            )

        except Exception as e:

            print(
                f"  [AI] Analyysi epäonnistui "
                f"({company.get('name', '')}): "
                f"{e}"
            )

            continue

        company["ai_analysis"] = (
            ai_result
        )

        results.append(
            company
        )

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

        company_record = dict(
            existing
        )

        company_record.update(
            company
        )

        company_record["status"] = (
            existing.get(
                "status",
                "found",
            )
        )

        companies[slug] = (
            company_record
        )

        saved_count += 1

    save_companies(
        companies
    )

    print(
        f"[Scout] Tallennettuja yrityksiä: "
        f"{saved_count}"
    )

    return results
