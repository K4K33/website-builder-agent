"""
Website Builder -agentti.

Tehtävä: research-briefin pohjalta generoida oikea, toimiva, responsiivinen
yhden sivun verkkosivu (HTML+CSS+JS samassa tiedostossa, jotta esikatselu
on mahdollisimman helppoa - vain avaa index.html selaimessa).

Tukee myös "revise"-kutsua, jolla käyttäjä voi pyytää muutoksia
luonnollisella kielellä (esim. "tee väreistä tummemmat").
"""
import os

from utils.claude_client import ask_claude
from utils.state import upsert_company, set_status
import config

BUILD_SYSTEM_PROMPT = """Olet kokenut web-suunnittelija ja frontend-kehittäjä.

Rakennat yritykselle UUDEN, AMMATTIMAISEN, moderin ja responsiivisen
yhden sivun (single-page) verkkosivun HTML/CSS/JS:llä.

EHDOTTOMAT SÄÄNNÖT:
- ÄLÄ kopioi mitään tekstiä, kuvatekstejä, logoja tai koodia miltään
  toiselta, oikealta yritykseltä tai referenssisivulta. Kaikki teksti
  pitää kirjoittaa itse annettujen faktojen (company_facts) pohjalta.
- ÄLÄ käytä minkään olemassa olevan yrityksen tuotemerkkiä, logoa tai
  tekijänoikeuksin suojattua materiaalia.
- Käytä VAIN annettuja, todennettuja yhteystietoja. Jos jotain tietoa
  puuttuu (esim. puhelinnumero), käytä selkeää placeholderia kuten
  "[Puhelinnumero tähän]" äläkä keksi lukuja.
- Kuvien sijaan käytä tyylikkäitä CSS-pohjaisia elementtejä, gradientteja
  tai yksinkertaisia SVG-muotoja/ikoneita (inline SVG). Älä linkitä
  ulkoisiin kuvatiedostoihin joita ei ole olemassa.
- Sivun pitää olla täysin responsiivinen (mobiili, tabletti, desktop).
- Käytä annettua värimaailmaa ja tyyliohjeita design_recommendations-kentästä.
- Koodin pitää olla yhdessä itsenäisessä index.html-tiedostossa
  (CSS <style>-tagissa, JS <script>-tagissa samassa tiedostossa).
- Sisällytä oikea navigaatio ankkurilinkeillä (#palvelut, #yhteystiedot jne.),
  Hero-osio arvolupauksella, palvelut/tuotteet-osio, "Miksi meidät"-osio,
  yhteystieto-osio ja footer.
- Käytä semanttista HTML5:tä ja lisää perus-accessibility-attribuutit
  (alt-tekstit SVG:ille rooleineen, aria-labelit navigaatiolle).
- Lisää <meta name="viewport" content="width=device-width, initial-scale=1.0">.

Palauta VASTAUKSENA AINOASTAAN valmis HTML-tiedoston koko sisältö,
alkaen '<!DOCTYPE html>' -rivistä. Älä lisää selityksiä äläkä
markdown-koodilohkomerkintöjä (```) vastauksen ympärille."""

REVISE_SYSTEM_PROMPT = """Olet kokenut web-suunnittelija. Saat käyttöösi olemassa olevan
index.html-tiedoston koko sisällön sekä käyttäjän muutospyynnön luonnollisella kielellä.

Tee PYYDETYT muutokset ja palauta KOKO päivitetty HTML-tiedosto kokonaisuudessaan
(et pelkkää diffiä). Säilytä kaikki muu ennallaan ellei muutospyyntö koske sitä.
Noudata samoja sääntöjä kuin alkuperäisessä rakentamisessa: ei kopioitua sisältöä,
ei keksittyjä yhteystietoja, responsiivisuus säilytettävä.

Palauta VASTAUKSENA AINOASTAAN koko päivitetty HTML-tiedoston sisältö,
ilman selityksiä tai markdown-koodilohkomerkintöjä."""


def _output_dir(slug: str) -> str:
    return os.path.join(config.OUTPUT_DIR, slug)


def _output_path(slug: str) -> str:
    return os.path.join(_output_dir(slug), "index.html")


def _write_html(slug: str, html: str) -> str:
    out_dir = _output_dir(slug)
    os.makedirs(out_dir, exist_ok=True)
    path = _output_path(slug)
    # Siivotaan mahdolliset jäänteet markdown-koodilohkoista varmuuden vuoksi
    cleaned = html.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        if cleaned.rstrip().endswith("```"):
            cleaned = cleaned.rstrip()[:-3]
    with open(path, "w", encoding="utf-8") as f:
        f.write(cleaned)
    return path


def build_site(slug: str, company: dict) -> str:
    research = company.get("research")
    if not research:
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy research-dataa. Aja ensin: "
            f"python main.py research {slug}"
        )

    user_prompt = f"""Rakenna uusi verkkosivu näiden tietojen pohjalta:

COMPANY_FACTS:
{research.get('company_facts')}

CURRENT_SITE_WEAKNESSES (korjaa nämä uudessa versiossa):
{research.get('current_site_weaknesses')}

DESIGN_RECOMMENDATIONS:
{research.get('design_recommendations')}
"""

    html = ask_claude(BUILD_SYSTEM_PROMPT, user_prompt, use_web_search=False, max_tokens=8000)
    path = _write_html(slug, html)

    version = company.get("build", {}).get("version", 0) + 1
    upsert_company(slug, {
        "build": {
            "output_path": path,
            "version": version,
        }
    })
    set_status(slug, "built")
    return path


def revise_site(slug: str, company: dict, feedback: str) -> str:
    path = _output_path(slug)
    if not os.path.exists(path):
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy vielä rakennettua sivua. Aja ensin: "
            f"python main.py build {slug}"
        )
    with open(path, "r", encoding="utf-8") as f:
        current_html = f.read()

    user_prompt = f"""Nykyinen index.html:

{current_html}

---
Käyttäjän muutospyyntö: "{feedback}"
"""
    new_html = ask_claude(REVISE_SYSTEM_PROMPT, user_prompt, use_web_search=False, max_tokens=8000)
    new_path = _write_html(slug, new_html)

    version = company.get("build", {}).get("version", 1) + 1
    upsert_company(slug, {
        "build": {
            "output_path": new_path,
            "version": version,
            "last_feedback": feedback,
        }
    })
    # Uusi versio pitää hyväksyä uudelleen, joten palautetaan status "built"
    set_status(slug, "built")
    return new_path
