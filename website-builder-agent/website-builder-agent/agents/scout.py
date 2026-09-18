"""
Scout-agentti.

Tehtävä: etsiä yrityksiä, joiden verkkosivut vaikuttavat vanhentuneilta
tai heikkolaatuisilta, ja tallentaa ne data/companies.json-tiedostoon
statuksella "found".

HUOM (v1 rajoitus): Claude ei voi "selata" koko internetiä satunnaisesti,
vaan käyttää web-hakutyökalua kohdennettuihin hakuihin (esim.
"putkiliike Tampere" tai "kampaamo Turku"). Käyttäjä ohjaa hakua
toimialalla ja/tai sijainnilla. Tulokset ovat ehdotuksia, jotka
kannattaa aina silmäillä itse ennen jatkokäsittelyä.
"""
import config
from utils.claude_client import ask_claude_json
from utils.state import load_companies, save_companies, make_slug

SCOUT_SYSTEM_PROMPT = """Olet Scout-agentti, joka etsii pieniä ja keskisuuria yrityksiä,
joiden verkkosivut ovat vanhentuneita, huonosti toimivia tai visuaalisesti heikkoja.

Käytä web-hakutyökalua löytääksesi oikeita, olemassa olevia yrityksiä käyttäjän
antaman toimialan ja/tai sijainnin perusteella. Vieraile (hae tietoa) yritysten
verkkosivuilla tunnistaaksesi merkkejä vanhentuneesta sivustosta, esimerkiksi:
- ei mobiilioptimointia
- vanha muotoilu, table-pohjainen layout, Flash-elementit
- vanhentunut copyright-vuosi (esim. 2015 tai vanhempi mainittuna)
- rikkinäisiä linkkejä tai puuttuvaa sisältöä
- ei HTTPS:ää

Palauta VAIN JSON-lista objekteja, ei mitään muuta tekstiä:
[
  {
    "name": "Yrityksen nimi",
    "url": "https://yrityksen-sivu.fi",
    "industry_guess": "arvioitu toimiala",
    "location": "kaupunki tai paikkakunta jos tiedossa",
    "reason": "lyhyt perustelu miksi sivu vaikuttaa vanhentuneelta (1-2 lausetta)"
  }
]
Jos et löydä varmoja tuloksia, palauta silti parhaat arvauksesi äläkä tyhjää listaa
ilman erittäin hyvää syytä.
"""


def run_scout(count: int = None, industry: str = "", location: str = "") -> list[dict]:
    count = count or config.SCOUT_MAX_RESULTS

    query_parts = []
    if industry:
        query_parts.append(f"toimiala: {industry}")
    if location:
        query_parts.append(f"sijainti: {location}")
    context = ", ".join(query_parts) if query_parts else "mikä tahansa toimiala Suomessa"

    user_prompt = f"""Etsi {count} yritystä ({context}), joiden verkkosivut vaikuttavat
vanhentuneilta tai heikkolaatuisilta. Käytä web-hakua oikeiden yritysten löytämiseen
äläkä keksi yrityksiä. Suosi pieniä/keskisuuria paikallisia yrityksiä
(esim. käsityöläiset, remonttifirmat, kampaamot, ravintolat, kirjanpitotoimistot),
joilla on todennäköisesti vanha, itse tai kauan sitten teetetty verkkosivu."""

    results = ask_claude_json(SCOUT_SYSTEM_PROMPT, user_prompt, use_web_search=True, max_tokens=3000)

    if not isinstance(results, list):
        raise RuntimeError(f"Scout-agentti palautti odottamattoman muodon: {results}")

    companies = load_companies()
    saved = []
    for item in results:
        name = item.get("name", "").strip()
        url = item.get("url", "").strip()
        if not name or not url:
            continue
        slug = make_slug(name)
        # Älä ylikirjoita jo pidemmällä olevaa yritystä (esim. jo "built")
        if slug in companies and companies[slug].get("status") != "found":
            continue
        companies[slug] = {
            "name": name,
            "url": url,
            "status": "found",
            "scout": {
                "industry_guess": item.get("industry_guess", ""),
                "location": item.get("location", ""),
                "reason": item.get("reason", ""),
            },
        }
        saved.append((slug, companies[slug]))

    save_companies(companies)
    return saved
