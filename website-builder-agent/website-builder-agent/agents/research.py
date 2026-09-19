"""
Research-agentti.

Tehtävä:
1. Lukee Scoutin löytämän yrityksen nykyisen verkkosivun.
2. Tunnistaa yrityksen toimialan, palvelut, sijainnin ja muut faktat.
3. Hakee Tavilylla 3-5 modernia referenssisivustoa samalta tai läheiseltä
   toimialalta.
4. Käyttää referenssejä vain design-inspiraation lähteenä.
5. Tuottaa design briefin Builder-agentille.

Tärkeää:
- Referenssisivustoilta ei kopioida tekstejä, kuvia tai logoja.
- Yrityksen omat faktat tulevat ensisijaisesti sen omalta verkkosivulta.
- Tavilyä käytetään vain silloin, kun Research oikeasti tarvitsee
  ulkopuolista tietoa.
"""

import os

import requests

from utils.claude_client import ask_claude_json
from utils.fetch import analyze_url
from utils.state import (
    load_companies,
    upsert_company,
    set_status,
)


TAVILY_URL = "https://api.tavily.com/search"


FACT_EXTRACTION_PROMPT = """
Olet verkkosivujen tutkimukseen erikoistunut Research-agentti.

Analysoi yrityksen nykyisen verkkosivun sisältö.

Tavoitteet:
1. Tunnista yrityksen todellinen toimiala mahdollisimman tarkasti.
2. Poimi vain sivulta löytyvät faktat:
   - yrityksen nimi
   - palvelut tai tuotteet
   - sijainti
   - puhelin
   - sähköposti
   - osoite
   - aukioloajat
   - slogan tai arvolupaus
   - kohderyhmä
3. Tunnista nykyisen verkkosivun tärkeimmät heikkoudet.
4. Luo lyhyt hakulause, jolla voidaan etsiä moderneja
   referenssisivustoja samalta toimialalta.

Älä keksi yhteystietoja.
Jos tietoa ei löydy, käytä tyhjää merkkijonoa.

Palauta VAIN validi JSON:

{
  "company_facts": {
    "name": "",
    "industry": "",
    "services": [],
    "location": "",
    "contact": {
      "phone": "",
      "email": "",
      "address": ""
    },
    "opening_hours": "",
    "tagline_or_value_prop": "",
    "target_audience": ""
  },
  "current_site_weaknesses": [],
  "reference_search_query": ""
}
"""


FINAL_RESEARCH_PROMPT = """
Olet Research-agentti verkkosivujen uudistusprojektissa.

Sinulle annetaan:
1. Kohdeyrityksen faktat.
2. Nykyisen verkkosivun heikkoudet.
3. Hakutuloksia moderneista verkkosivuista samalta tai läheiseltä
   toimialalta.

Tehtäväsi on tuottaa Builder-agentille selkeä design brief.

Referenssisivustoja saa käyttää VAIN inspiraationa:
- värimaailma
- typografia
- layout
- visuaalinen hierarkia
- tunnelma
- CTA-ratkaisut
- palveluiden esittelytapa

ÄLÄ kopioi:
- tekstejä
- kuvia
- logoja
- brändi-identiteettiä
- yritysten nimiä

Uuden sivuston sisällön pitää perustua kohdeyrityksen omiin faktoihin.

Ole erityisen tarkka siinä, ettet keksi yritykselle palveluita,
yhteystietoja tai muita faktoja.

Palauta VAIN validi JSON tässä muodossa:

{
  "company_facts": {
    "name": "",
    "industry": "",
    "services": [],
    "location": "",
    "contact": {
      "phone": "",
      "email": "",
      "address": ""
    },
    "opening_hours": "",
    "tagline_or_value_prop": "",
    "target_audience": ""
  },
  "current_site_weaknesses": [],
  "design_inspiration": [
    {
      "reference_note": ""
    }
  ],
  "design_recommendations": {
    "color_palette": [
      "#hexcode"
    ],
    "font_style": "",
    "tone": "",
    "key_sections": []
  }
}

Sääntöjä:
- design_inspiration sisältää 3-5 lyhyttä yleistä havaintoa.
- Älä kirjoita referenssiyritysten nimiä.
- Älä kirjoita referenssien URL-osoitteita.
- color_palette sisältää 3-5 väriä.
- key_sections sisältää Builder-agentille hyödylliset sivuston pääosiot.
"""


def _get_tavily_key():
    key = os.getenv("TAVILY_API_KEY", "")

    if not key:
        raise RuntimeError(
            "TAVILY_API_KEY puuttuu. "
            "Lisää se GitHub Secretiksi nimellä TAVILY_API_KEY."
        )

    return key


def _search_tavily(
    query: str,
    max_results: int = 5,
) -> list[dict]:
    """
    Hakee Tavillysta referenssisivustoja.

    Tätä käytetään vain Research-vaiheessa.
    """

    api_key = _get_tavily_key()

    print(
        f"  [Tavily] Hakulause: {query}"
    )

    payload = {
        "api_key": api_key,
        "query": query,
        "search_depth": "basic",
        "topic": "general",
        "max_results": max_results,
        "include_answer": False,
        "include_raw_content": False,
        "include_images": False,
    }

    try:
        response = requests.post(
            TAVILY_URL,
            json=payload,
            timeout=60,
        )

    except requests.RequestException as e:
        raise RuntimeError(
            f"Tavily-verkkovirhe: {e}"
        ) from e

    if response.status_code >= 400:
        raise RuntimeError(
            "Tavily API-virhe: "
            f"HTTP {response.status_code} "
            f"{response.text[:1000]}"
        )

    try:
        data = response.json()

    except ValueError as e:
        raise RuntimeError(
            f"Tavily palautti virheellisen JSON-vastauksen: {e}"
        ) from e

    results = data.get(
        "results",
        [],
    )

    cleaned = []

    for result in results:
        if not isinstance(result, dict):
            continue

        title = str(
            result.get("title", "")
        ).strip()

        url = str(
            result.get("url", "")
        ).strip()

        content = str(
            result.get("content", "")
        ).strip()

        if not url:
            continue

        cleaned.append(
            {
                "title": title,
                "url": url,
                "content": content[:1500],
            }
        )

    print(
        f"  [Tavily] Tuloksia: {len(cleaned)}"
    )

    return cleaned[:max_results]


def _format_search_results(
    results: list[dict],
) -> str:
    """
    Muuttaa Tavily-tulokset AI:lle sopivaksi tekstiksi.
    """

    if not results:
        return "Ei referenssihakutuloksia."

    sections = []

    for index, result in enumerate(
        results,
        start=1,
    ):
        sections.append(
            f"""
REFERENSSI {index}
Otsikko: {result.get("title", "")}
URL: {result.get("url", "")}
Sisältökuvaus:
{result.get("content", "")}
""".strip()
        )

    return "\n\n".join(sections)


def _get_company(
    slug: str,
) -> dict:
    companies = load_companies()

    company = companies.get(slug)

    if not company:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug}"
        )

    return company


def run_research(
    slug: str,
) -> dict:
    """
    Tutkii yhden Scoutin löytämän yrityksen.

    Main.py kutsuu tätä muodossa:

        research.run_research(args.company)
    """

    company = _get_company(slug)

    name = company.get(
        "name",
        "",
    )

    url = company.get(
        "url",
        "",
    )

    if not url:
        raise RuntimeError(
            f"Yrityksellä {slug} ei ole verkkosivun URL-osoitetta."
        )

    print()
    print("=== RESEARCH ===")
    print(
        f"Yritys: {name}"
    )
    print(
        f"URL: {url}"
    )

    # ---------------------------------------------------------
    # 1. Hae nykyinen verkkosivu
    # ---------------------------------------------------------

    print(
        "  [Research] Haetaan nykyinen verkkosivu..."
    )

    site_data = analyze_url(url)

    if not site_data:
        raise RuntimeError(
            f"Yrityksen sivua ei saatu analysoitua: {url}"
        )

    if not site_data.get(
        "success",
        True,
    ):
        error = site_data.get(
            "error",
            "Tuntematon virhe",
        )

        raise RuntimeError(
            f"Yrityksen sivun analyysi epäonnistui: {error}"
        )

    print(
        "  [Research] Nykyinen sivu haettu."
    )

    # ---------------------------------------------------------
    # 2. Ensimmäinen AI-analyysi
    # ---------------------------------------------------------

    user_prompt = f"""
Yrityksen nimi:
{name}

Yrityksen URL:
{url}

--- Sivun otsikko ---
{site_data.get("title", "")}

--- Meta-kuvaus ---
{site_data.get("meta_description", "")}

--- Sivun näkyvä teksti ---
{site_data.get("visible_text", "")[:10000]}

--- Tekniset tiedot ---
Viewport-meta:
{site_data.get("has_viewport_meta", "")}

HTTP-status:
{site_data.get("status_code", "")}

Raaka HTML:
{site_data.get("raw_html_length", "")} merkkiä
"""

    print(
        "  [Research] Tunnistetaan yrityksen faktat..."
    )

    extracted = ask_claude_json(
        FACT_EXTRACTION_PROMPT,
        user_prompt,
        max_tokens=2500,
    )

    if not isinstance(
        extracted,
        dict,
    ):
        raise RuntimeError(
            "AI ei palauttanut Researchin faktatietoja JSON-objektina."
        )

    company_facts = extracted.get(
        "company_facts",
        {},
    )

    if not isinstance(
        company_facts,
        dict,
    ):
        company_facts = {}

    industry = company_facts.get(
        "industry",
        "",
    )

    search_query = extracted.get(
        "reference_search_query",
        "",
    )

    if not search_query:
        search_query = (
            f"modern {industry} website design"
        )

    # ---------------------------------------------------------
    # 3. Tavily-referenssihaku
    # ---------------------------------------------------------

    print(
        "  [Research] Etsitään design-referenssejä..."
    )

    references = _search_tavily(
        search_query,
        max_results=5,
    )

    # ---------------------------------------------------------
    # 4. Lopullinen design brief
    # ---------------------------------------------------------

    final_prompt = f"""
KOHDEYRITYS
Nimi: {name}
URL: {url}

--- YRITYKSEN FAKTAT ---
{company_facts}

--- NYKYISEN SIVUN HEIKKOUDET ---
{extracted.get("current_site_weaknesses", [])}

--- TAVILYN REFERENSSIT ---
{_format_search_results(references)}

Muodosta nyt lopullinen design brief.
"""

    print(
        "  [Research] Rakennetaan design brief..."
    )

    brief = ask_claude_json(
        FINAL_RESEARCH_PROMPT,
        final_prompt,
        max_tokens=3500,
    )

    if not isinstance(
        brief,
        dict,
    ):
        raise RuntimeError(
            "AI ei palauttanut lopullista Research-briefiä JSON-objektina."
        )

    # ---------------------------------------------------------
    # 5. Tallenna Research yrityksen tietoihin
    # ---------------------------------------------------------

    research_data = {
        **brief,
        "reference_sources": [
            {
                "title": result.get(
                    "title",
                    "",
                ),
                "url": result.get(
                    "url",
                    "",
                ),
            }
            for result in references
        ],
        "reference_search_query": search_query,
    }

    updated_company = upsert_company(
        slug,
        {
            "name": (
                brief.get(
                    "company_facts",
                    {},
                ).get(
                    "name"
                )
                or name
            ),
            "url": url,
            "research": research_data,
            "current_site_raw": {
                "has_viewport_meta": site_data.get(
                    "has_viewport_meta",
                    False,
                ),
                "raw_html_length": site_data.get(
                    "raw_html_length",
                    0,
                ),
                "status_code": site_data.get(
                    "status_code",
                    "",
                ),
            },
        },
    )

    set_status(
        slug,
        "researched",
    )

    print()
    print("=== RESEARCH VALMIS ===")
    print(
        f"Yritys: {name}"
    )
    print(
        f"Toimiala: {industry}"
    )
    print(
        f"Referenssejä: {len(references)}"
    )
    print(
        "Status: researched"
    )

    return updated_company
