"""
QA-agentti.

Tekee automaattisia tarkistuksia rakennetulle index.html-tiedostolle:
- Onko viewport-meta mobiilioptimointia varten
- Puuttuvatko alt-tekstit / aria-labelit
- Onko rikkinäisiä sisäisiä ankkurilinkkejä (esim. href="#yhteystiedot"
  jolle ei löydy vastaavaa id:tä)
- Onko jäänteitä placeholder-tekstistä ("Lorem ipsum", "[Puhelinnumero...]")
- Onko ulkoisia linkkejä jotka eivät ala https://

Lisäksi pyytää Claudelta laadullisen tarkistuksen (copy-tekstin
uskottavuus, faktojen yhtenevyys research-briefin kanssa).
"""
import os
import re
from bs4 import BeautifulSoup

from utils.claude_client import ask_claude_json
from utils.state import upsert_company, set_status
import config

QA_SYSTEM_PROMPT = """Olet QA-agentti, joka tarkistaa juuri rakennetun yrityksen
verkkosivun laadun. Saat sivun HTML-sisällön ja alkuperäisen research-briefin.

Tarkista:
1. Vastaako sivun sisältö research-briefin faktoja (ei ristiriitoja,
   ei keksittyjä väitteitä joita ei brief tue).
2. Onko teksti ammattimaista, virheetöntä suomea (tai kieltä jolla brief on)
   ilman ilmeisiä kielioppivirheitä.
3. Onko sivu looginen ja täydellinen (ei kesken jääneitä lauseita tai osioita).

Palauta VAIN JSON:
{
  "content_ok": true/false,
  "issues": ["lyhyt kuvaus ongelmasta", "..."],
  "notes": "lyhyt yleisarvio"
}"""


def _automated_checks(html: str) -> dict:
    issues = []
    soup = BeautifulSoup(html, "html.parser")

    has_viewport = soup.find("meta", attrs={"name": "viewport"}) is not None
    if not has_viewport:
        issues.append("Puuttuva viewport-meta -> sivu ei todennäköisesti ole mobiilioptimoitu.")

    # kuvien alt-tekstit (jos <img> elementtejä käytetty)
    imgs_without_alt = [img for img in soup.find_all("img") if not img.get("alt")]
    if imgs_without_alt:
        issues.append(f"{len(imgs_without_alt)} <img>-elementtiä ilman alt-tekstiä.")

    # sisäiset ankkurilinkit vs. olemassa olevat id:t
    ids = {tag.get("id") for tag in soup.find_all(id=True)}
    broken_anchors = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("#") and len(href) > 1:
            target = href[1:]
            if target not in ids:
                broken_anchors.append(href)
    if broken_anchors:
        issues.append(f"Rikkinäisiä ankkurilinkkejä: {', '.join(broken_anchors)}")

    # placeholder-jäänteet
    text = soup.get_text(" ", strip=True)
    placeholder_patterns = [r"lorem ipsum", r"\[.*?tähän.*?\]", r"placeholder"]
    for pattern in placeholder_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            issues.append(f"Löytyi täyttämätön placeholder-teksti (kuvio: '{pattern}').")

    # ei-https ulkoiset linkit
    insecure_links = [
        a["href"] for a in soup.find_all("a", href=True)
        if a["href"].startswith("http://")
    ]
    if insecure_links:
        issues.append(f"{len(insecure_links)} linkkiä käyttää http:// eikä https://.")

    return {
        "has_viewport_meta": has_viewport,
        "automated_issues": issues,
        "automated_pass": len(issues) == 0,
    }


def run_qa(slug: str, company: dict) -> dict:
    build_info = company.get("build")
    if not build_info or not os.path.exists(build_info.get("output_path", "")):
        raise RuntimeError(
            f"Yritykselle '{slug}' ei löydy rakennettua sivua. Aja ensin: "
            f"python main.py build {slug}"
        )

    with open(build_info["output_path"], "r", encoding="utf-8") as f:
        html = f.read()

    automated = _automated_checks(html)

    research = company.get("research", {})
    user_prompt = f"""RESEARCH_BRIEF (faktat joita sivun pitäisi noudattaa):
{research.get('company_facts')}

--- SIVUN HTML (tekstisisältö tärkein, rakenne toissijainen) ---
{html[:12000]}
"""
    content_review = ask_claude_json(QA_SYSTEM_PROMPT, user_prompt, use_web_search=False, max_tokens=1500)

    qa_result = {
        "automated": automated,
        "content_review": content_review,
        "overall_pass": automated["automated_pass"] and content_review.get("content_ok", False),
    }

    upsert_company(slug, {"qa": qa_result})
    set_status(slug, "qa_passed" if qa_result["overall_pass"] else "built")
    return qa_result
