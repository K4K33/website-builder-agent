"""
Scout-agentti Website Builder Agentille.

Scout:
- löytää yrityksiä OpenStreetMapista
- tarkistaa verkkosivut
- kerää teknistä dataa
- ottaa desktop- ja mobiilikuvakaappaukset
- tekee AI-analyysin normaalissa ajossa
- käyttää screenshotteja visuaalisessa AI-analyysissä

DRY-RUN:
- ei OpenRouter-kutsuja
- ei Tavily-kutsuja
- ei tallenna yrityksiä
"""

import re
import time

import requests

import config

from utils.fetch import analyze_url
from utils.screenshot import capture_website
from utils.state import (
    load_companies,
    save_companies,
    make_slug,
)


OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
]


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
[out:json][timeout:45];

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

    for index, overpass_url in enumerate(
        OVERPASS_URLS,
        start=1,
    ):

        print()
        print(
            f"  [OSM] Palvelin "
            f"{index}/{len(OVERPASS_URLS)}:"
        )

        print(
            f"  [OSM] {overpass_url}"
        )

        try:

            response = requests.post(
                overpass_url,
                data={
                    "data": query,
                },
                headers=HEADERS,
                timeout=60,
            )

            print(
                f"  [OSM] HTTP-status: "
                f"{response.status_code}"
            )

            if response.status_code >= 400:

                print(
                    "  [OSM] Palvelin palautti virheen."
                )

                print(
                    response.text[:1000]
                )

                continue

            data = response.json()

        except requests.Timeout:

            print(
                "  [OSM] Palvelin aikakatkaisi."
            )

            print(
                "  [OSM] Kokeillaan seuraavaa "
                "Overpass-palvelinta..."
            )

            continue

        except requests.RequestException as e:

            print(
                f"  [OSM] Verkkovirhe: {e}"
            )

            print(
                "  [OSM] Kokeillaan seuraavaa "
                "Overpass-palvelinta..."
            )

            continue

        except ValueError as e:

            print(
                f"  [OSM] JSON-vastausta ei voitu "
                f"lukea: {e}"
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

        if not elements:
            return []

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

    print()
    print(
        "[OSM] Kaikki Overpass-palvelimet epäonnistuivat."
    )

    return []


def _normalize_url(
    url: str,
) -> str:

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
    max_results: int,
) -> list[dict]:

    analyzed = []

    for company in candidates:

        if len(analyzed) >= max_results:
            break

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

        print()
        print(
            f"  [site] Tarkistetaan: "
            f"{name}"
        )

        print(
            f"  [site] URL: {url}"
        )

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

            if screenshots.get("desktop"):
                print(
                    f"    desktop: "
                    f"{screenshots['desktop']}"
                )

            if screenshots.get("mobile"):
                print(
                    f"    mobile: "
                    f"{screenshots['mobile']}"
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

        time.sleep(
            getattr(
                config,
                "REQUEST_DELAY",
                1.0,
            )
        )

    return analyzed


def _score_without_ai(
    company: dict,
) -> dict:

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
            "HTML-rakenne ei ole "
            "poikkeuksellisen pieni"
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
            "selkeää toimintakehotusta "
            "ei havaittu"
        )

    if contact_signals.get(
        "booking_signal",
        False,
    ):

        positive_signals.append(
            "ajanvaraus havaittu"
        )

    if image_count > 0:

        if images_without_alt_count == image_count:

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
            "  [dry-run] Kuvakaappaukset:"
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

    if result["reasons"]:

        print(
            "  [dry-run] Ongelmahavainnot:"
        )

        for reason in result["reasons"]:

            print(
                f"    - {reason}"
            )

    if result["positive_signals"]:

        print(
            "  [dry-run] Positiiviset signaalit:"
        )

        for signal in result["positive_signals"]:

            print(
                f"    + {signal}"
            )


def _ai_analyze_company(
    company: dict,
) -> dict:

    from utils.claude_client import (
        ask_claude_json,
    )

    data = company.get(
        "site_analysis",
        {},
    )

    screenshots = company.get(
        "screenshots",
        {},
    )

    technical_score = (
        _score_without_ai(
            company
        )
    )

    image_paths = []

    desktop_path = screenshots.get(
        "desktop"
    )

    mobile_path = screenshots.get(
        "mobile"
    )

    if desktop_path:
        image_paths.append(
            desktop_path
        )

    if mobile_path:
        image_paths.append(
            mobile_path
        )

    system = """
Olet pienten yritysten verkkosivustojen
auditointiin erikoistunut asiantuntija.

Tavoitteena on tunnistaa verkkosivustoja,
joiden uudistamisesta voisi olla yritykselle
todellista hyötyä.

Sinulle annetaan:
- verkkosivuston desktop-kuvakaappaus
- verkkosivuston mobiilikuvasivu
- teknisiä tietoja
- sivun tekstiä
- CTA- ja yhteystietoja

Arvioi sivustoa erityisesti tavallisen
potentiaalisen asiakkaan näkökulmasta.

Katso kuvista erityisesti:

1. Ensivaikutelma
2. Visuaalinen modernius
3. Selkeys
4. Luettavuus
5. Navigoinnin ymmärrettävyys
6. Tärkeän tiedon löytyminen
7. CTA:n näkyvyys
8. Luottamusta lisäävät elementit
9. Mobiilikokemus
10. Visuaalinen hierarkia
11. Sivun mahdollinen sekavuus
12. Vaikutelma siitä, tarvitseeko sivusto
    oikeasti suuremman uudistuksen

Älä pidä yksittäistä teknistä ongelmaa
automaattisesti merkkinä huonosta sivustosta.

Esimerkiksi puuttuva meta description
ei yksin tarkoita, että sivusto pitäisi
uudistaa.

Jos sivusto näyttää hyvältä ja toimii hyvin,
sano se myös analyysissä.

Palauta AINOASTAAN validi JSON:

{
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
}

Score-arvot ovat välillä 0-10.

Korkeampi overall_opportunity_score tarkoittaa,
että verkkosivustossa on enemmän havaittavaa
uudistamispotentiaalia.

redesign_recommended saa olla true vain,
jos kokonaisuus antaa siihen järkevän perusteen.

Älä keksi asioita, joita kuvissa tai annetuissa
tiedoissa ei voi havaita.
"""

    user_prompt = f"""
YRITYS

Nimi:
{company.get('name', '')}

URL:
{company.get('url', '')}

---

TEKNINEN ANALYYSI

Ongelmasignaalit:
{technical_score.get('score', 0)}

Tekninen prioriteetti:
{technical_score.get('priority', '')}

Teknisen analyysin havainnot:
{technical_score.get('reasons', [])}

Positiiviset tekniset signaalit:
{technical_score.get('positive_signals', [])}

---

SIVUN TIEDOT

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

---

SIVUN TEKSTI

{data.get('visible_text', '')[:8000]}

---

KUVAT

Ensimmäinen kuva on desktop-kuvakaappaus,
jos se on saatavilla.

Toinen kuva on mobiilikuvasivu,
jos se on saatavilla.

Arvioi kuvat yhdessä muun datan kanssa.
"""

    print(
        "  [AI] Lähetetään tekninen data + "
        f"{len(image_paths)} screenshotia "
        "OpenRouterille..."
    )

    result = ask_claude_json(
        system,
        user_prompt,
        use_web_search=False,
        max_tokens=2500,
        image_paths=image_paths,
    )

    return result


def run_scout(
    count: int = 10,
    industry: str = "",
    location: str = "",
    dry_run: bool = False,
):

    print(
        f"[Scout] Etsitään {count} yritystä..."
    )

    print()
    print(
        "=== SCOUT ==="
    )

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

        print()

        print(
            "[scout] OpenStreetMapista "
            "ei löytynyt yrityksiä."
        )

        return []

    analyzed = _analyze_candidates(
        candidates,
        max_results=count,
    )

    if not analyzed:

        print()

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
