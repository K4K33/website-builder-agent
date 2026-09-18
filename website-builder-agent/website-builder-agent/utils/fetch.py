"""
Yksinkertaiset apufunktiot yrityksen omien verkkosivujen hakemiseen ja
niiden sisällön puhdistamiseen analyysiä varten.
"""
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; WebsiteBuilderAgent/1.0; "
        "+https://github.com/) research bot"
    )
}


def fetch_html(url: str, timeout: int = 15) -> str | None:
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        print(f"  [fetch] Sivun haku epäonnistui ({url}): {e}")
        return None


def extract_text_and_meta(html: str, base_url: str = "") -> dict:
    """
    Palauttaa sanakirjan:
      - title, meta_description
      - visible_text (siivottu, rajattu pituus)
      - has_viewport_meta (mobiiliystävällisyyden karkea indikaattori)
      - links (sisäiset linkit, karkealla suodatuksella)
      - raw_html_length
    """
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""
    meta_desc_tag = soup.find("meta", attrs={"name": "description"})
    meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else ""

    has_viewport_meta = soup.find("meta", attrs={"name": "viewport"}) is not None

    text = soup.get_text(separator=" ", strip=True)
    text = " ".join(text.split())  # normalisoi whitespacet
    visible_text = text[:8000]  # rajataan promptin kokoa varten

    links = []
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if href and not href.startswith("#") and not href.lower().startswith("javascript:"):
            links.append(href)

    return {
        "title": title,
        "meta_description": meta_description,
        "visible_text": visible_text,
        "has_viewport_meta": has_viewport_meta,
        "links": links[:100],
        "raw_html_length": len(html),
    }


def analyze_url(url: str) -> dict | None:
    html = fetch_html(url)
    if html is None:
        return None
    data = extract_text_and_meta(html, base_url=url)
    data["url"] = url
    return data
