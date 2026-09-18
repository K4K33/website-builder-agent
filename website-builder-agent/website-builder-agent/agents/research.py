"""
Research-agentti.

Tehtävä:
1. Hakee ja lukee yrityksen nykyisen verkkosivun sisällön.
2. Tunnistaa yrityksen toimialan, palvelut, sijainnin ja muut faktat.
3. Etsii web-haulla 3-5 hyvää/modernia referenssisivustoa samalta
   toimialalta INSPIRAATIOKSI (ei kopioitavaksi).
4. Tuottaa "design briefin", jota builder-agentti käyttää.

TÄRKEÄÄ: Referenssisivustoja käytetään VAIN suunnitteluperiaatteiden
(värimaailma, typografia, asettelu, tunnelma) tunnistamiseen. Mitään
tekstejä, kuvia tai logoja niiltä ei kopioida - builder-agentti saa
ohjeeksi kirjoittaa kaiken sisällön itse kohdeyrityksen omien tietojen
pohjalta.
"""
from utils.claude_client import ask_claude_json
from utils.fetch import analyze_url
from utils.state import upsert_company, set_status

RESEARCH_SYSTEM_PROMPT = """Olet Research-agentti verkkosivujen uudistusprojektissa.

Saat käyttöösi yrityksen nykyisen verkkosivun tekstisisällön ja perustiedot.
Tehtäväsi:
1. Tunnista yrityksen toimiala mahdollisimman tarkasti.
2. Poimi sivulta faktat: yrityksen nimi, palvelut/tuotteet, sijainti,
   yhteystiedot (jos näkyvissä), aukioloajat (jos näkyvissä), mahdollinen
   slogan tai arvolupaus, kohderyhmä.
3. Käytä web-hakutyökalua löytääksesi 3-5 esimerkkiä MODERNEISTA ja HYVIN
   TOTEUTETUISTA verkkosivuista samalta tai läheiseltä toimialalta.
   Näitä käytetään VAIN inspiraationa design-periaatteisiin (värit, typografia,
   layout-tyyli, tunnelma) - älä poimi niiltä tekstejä tai kuvia sellaisenaan.
4. Anna konkreettisia design-suosituksia UUDELLE sivustolle: värimaailma,
   fonttityyli, tunnelma/sävy, tärkeimmät osiot (esim. Hero, Palvelut,
   Referenssit, Yhteystiedot), ja mitä nykyisessä sivussa on parannettavaa.

Palauta VAIN JSON tässä muodossa, ei muuta tekstiä:
{
  "company_facts": {
    "name": "...",
    "industry": "...",
    "services": ["...", "..."],
    "location": "...",
    "contact": {"phone": "...", "email": "...", "address": "..."},
    "opening_hours": "...",
    "tagline_or_value_prop": "...",
    "target_audience": "..."
  },
  "current_site_weaknesses": ["...", "..."],
  "design_inspiration": [
    {"reference_note": "mitä hyvää tässä tyylissä on (EI URL:ia eikä yrityksen nimeä, vain yleinen kuvaus tyylistä)"}
  ],
  "design_recommendations": {
    "color_palette": ["#hexcode", "#hexcode", "#hexcode"],
    "font_style": "esim. moderni groteski, lämmin serif, jne.",
    "tone": "esim. luotettava ja ammattimainen / lämmin ja kutsuva",
    "key_sections": ["Hero", "Palvelut", "..."]
  }
}
Jos jotain tietoa ei löydy sivulta, käytä tyhjää merkkijonoa tai parasta arviota
ja mainitse se selkeästi (älä keksi yhteystietoja tai puhelinnumeroita)."""


def run_research(slug: str, name: str, url: str) -> dict:
    print(f"  Haetaan sivusto: {url}")
    site_data = analyze_url(url)
    if site_data is None:
        raise RuntimeError(
            f"Yrityksen sivua ei saatu haettua ({url}). Tarkista URL tai yritä myöhemmin uudelleen."
        )

    user_prompt = f"""Yrityksen nimi (oletus): {name}
Yrityksen nykyinen verkkosivu: {url}

--- Sivun otsikko ---
{site_data['title']}

--- Meta-kuvaus ---
{site_data['meta_description']}

--- Sivun näkyvä teksti (rajattu) ---
{site_data['visible_text']}

--- Tekninen huomio ---
Viewport-meta löytyi: {site_data['has_viewport_meta']} (False viittaa todennäköisesti
puutteelliseen mobiilioptimointiin)
"""

    brief = ask_claude_json(RESEARCH_SYSTEM_PROMPT, user_prompt, use_web_search=True, max_tokens=3000)

    company = upsert_company(slug, {
        "name": brief.get("company_facts", {}).get("name") or name,
        "url": url,
        "research": brief,
        "current_site_raw": {
            "has_viewport_meta": site_data["has_viewport_meta"],
            "raw_html_length": site_data["raw_html_length"],
        },
    })
    set_status(slug, "researched")
    return company
