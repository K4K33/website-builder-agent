"""
Verkkosivujen hakeminen ja auditointiaineiston kerääminen.

Tämä moduuli ei käytä OpenRouteria eikä Tavilyä.

Se kerää:
- tekniset metatiedot
- näkyvän tekstin
- otsikot
- linkit
- painikkeet
- lomakkeet
- kuvat
- yhteystietoja
- CTA-elementtejä
- viewport-tiedon
- HTML-koon

Tärkeää:
- analyze_url() palauttaa aina dict-olion.
- Onnistuneessa haussa success=True.
- Epäonnistuneessa haussa success=False.
- Yksittäinen huono verkkosivu ei kaada koko Scout-ajokertaa.
"""

import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36 "
        "WebsiteBuilderAgent/1.0 "
        "+https://github.com/K4K33/website-builder-agent"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,image/avif,image/webp,"
        "*/*;q=0.8"
    ),
    "Accept-Language": (
        "fi-FI,fi;q=0.9,en-US;q=0.8,en;q=0.7"
    ),
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}


def normalize_url(url: str) -> str:
    """
    Varmistaa, että URL sisältää http/https-protokollan.
    """

    url = (url or "").strip()

    if not url:
        return ""

    if not re.match(
        r"^https?://",
        url,
        re.IGNORECASE,
    ):
        url = "https://" + url

    return url


def _empty_result(
    url: str,
    error: str = "",
    status_code: int | None = None,
) -> dict:
    """
    Luo turvallisen epäonnistumistuloksen.

    Näin Scout saa aina dict-olion eikä None-arvoa.
    """

    return {
        "success": False,
        "url": url,
        "final_url": url,
        "status_code": status_code,
        "error": error,
        "title": "",
        "meta_description": "",
        "has_viewport_meta": False,
        "visible_text": "",
        "visible_text_length": 0,
        "raw_html_length": 0,
        "headings": {
            "h1": [],
            "h2": [],
            "h3": [],
            "h4": [],
            "h5": [],
            "h6": [],
        },
        "h1_count": 0,
        "links": [],
        "link_count": 0,
        "internal_link_count": 0,
        "external_link_count": 0,
        "buttons": [],
        "button_count": 0,
        "forms": [],
        "form_count": 0,
        "images": [],
        "image_count": 0,
        "images_without_alt_count": 0,
        "contact_signals": {
            "email_found": False,
            "phone_found": False,
            "address_signal": False,
            "booking_signal": False,
        },
        "cta_signals": {
            "cta_links": [],
            "cta_buttons": [],
            "has_cta": False,
        },
        "issues": [
            "Verkkosivun HTML:ää ei voitu analysoida."
        ],
        "positives": [],
        "problem_signals": 1,
        "priority": "low",
        "redesignable": False,
        "confidence": 0.0,
    }


def fetch_html(
    url: str,
    timeout: int = 20,
) -> dict:
    """
    Hakee verkkosivun HTML:n.

    Palauttaa aina dict-olion.
    """

    url = normalize_url(url)

    if not url:
        return {
            "success": False,
            "html": "",
            "final_url": "",
            "status_code": None,
            "error": "Tyhjä URL.",
        }

    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        response = session.get(
            url,
            timeout=timeout,
            allow_redirects=True,
        )

        status_code = response.status_code
        final_url = response.url or url

        if status_code >= 400:
            error = f"HTTP {status_code}"

            print(
                f"  [fetch] {error}: {url}"
            )

            return {
                "success": False,
                "html": "",
                "final_url": final_url,
                "status_code": status_code,
                "error": error,
            }

        content_type = (
            response.headers.get(
                "Content-Type",
                "",
            )
            .lower()
        )

        if (
            content_type
            and "html" not in content_type
            and "xhtml" not in content_type
        ):
            error = (
                "Vastaus ei ole HTML-sivu: "
                f"{content_type}"
            )

            print(
                f"  [fetch] {error}: {url}"
            )

            return {
                "success": False,
                "html": "",
                "final_url": final_url,
                "status_code": status_code,
                "error": error,
            }

        html = response.text or ""

        if not html.strip():
            error = (
                "Palvelin palautti tyhjän "
                "HTML-vastauksen."
            )

            print(
                f"  [fetch] {error}: {url}"
            )

            return {
                "success": False,
                "html": "",
                "final_url": final_url,
                "status_code": status_code,
                "error": error,
            }

        print(
            f"  [fetch] OK: HTTP {status_code} "
            f"({len(html)} merkkiä)"
        )

        return {
            "success": True,
            "html": html,
            "final_url": final_url,
            "status_code": status_code,
            "error": "",
        }

    except requests.exceptions.SSLError as e:
        error = f"SSL-virhe: {e}"

        print(
            f"  [fetch] {error}: {url}"
        )

        return {
            "success": False,
            "html": "",
            "final_url": url,
            "status_code": None,
            "error": error,
        }

    except requests.exceptions.Timeout as e:
        error = f"Timeout: {e}"

        print(
            f"  [fetch] {error}: {url}"
        )

        return {
            "success": False,
            "html": "",
            "final_url": url,
            "status_code": None,
            "error": error,
        }

    except requests.exceptions.ConnectionError as e:
        error = f"Yhteysvirhe: {e}"

        print(
            f"  [fetch] {error}: {url}"
        )

        return {
            "success": False,
            "html": "",
            "final_url": url,
            "status_code": None,
            "error": error,
        }

    except requests.RequestException as e:
        error = (
            f"HTTP-pyyntö epäonnistui: {e}"
        )

        print(
            f"  [fetch] {error}: {url}"
        )

        return {
            "success": False,
            "html": "",
            "final_url": url,
            "status_code": None,
            "error": error,
        }

    except Exception as e:
        error = (
            f"Odottamaton virhe: {e}"
        )

        print(
            f"  [fetch] {error}: {url}"
        )

        return {
            "success": False,
            "html": "",
            "final_url": url,
            "status_code": None,
            "error": error,
        }

    finally:
        session.close()


def _clean_text(value: str) -> str:
    """
    Siistii ylimääräiset välilyönnit.
    """

    return " ".join(
        (value or "").split()
    )


def _extract_meta_description(
    soup: BeautifulSoup,
) -> str:
    """
    Hakee meta descriptionin.
    """

    tag = soup.find(
        "meta",
        attrs={
            "name": re.compile(
                r"^description$",
                re.IGNORECASE,
            )
        },
    )

    if not tag:
        return ""

    return _clean_text(
        tag.get("content", "")
    )


def _extract_headings(
    soup: BeautifulSoup,
) -> dict:
    """
    Kerää H1-H6-otsikot.
    """

    result = {}

    for level in range(1, 7):
        tag_name = f"h{level}"
        headings = []

        for tag in soup.find_all(
            tag_name
        ):
            text = _clean_text(
                tag.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                headings.append(
                    text[:500]
                )

        result[tag_name] = headings[:30]

    return result


def _extract_links(
    soup: BeautifulSoup,
) -> list[dict]:
    """
    Kerää linkit ja niiden näkyvät tekstit.
    """

    links = []

    for tag in soup.find_all(
        "a",
        href=True,
    ):
        href = _clean_text(
            tag.get("href", "")
        )

        text = _clean_text(
            tag.get_text(
                " ",
                strip=True,
            )
        )

        if not href:
            continue

        links.append(
            {
                "text": text[:200],
                "href": href[:500],
            }
        )

    return links[:150]


def _extract_buttons(
    soup: BeautifulSoup,
) -> list[str]:
    """
    Kerää button-elementit ja input-submitit.
    """

    buttons = []

    for tag in soup.find_all(
        ["button", "input"]
    ):
        if tag.name == "input":
            input_type = (
                tag.get(
                    "type",
                    "",
                )
                .lower()
            )

            if input_type not in (
                "button",
                "submit",
                "reset",
            ):
                continue

            text = (
                tag.get("value", "")
                or tag.get(
                    "aria-label",
                    "",
                )
            )

        else:
            text = (
                tag.get_text(
                    " ",
                    strip=True,
                )
                or tag.get(
                    "aria-label",
                    "",
                )
            )

        text = _clean_text(text)

        if text:
            buttons.append(
                text[:200]
            )

    return buttons[:100]


def _extract_forms(
    soup: BeautifulSoup,
) -> list[dict]:
    """
    Kerää lomakkeiden perustiedot.
    """

    forms = []

    for form in soup.find_all(
        "form"
    ):
        inputs = []

        for field in form.find_all(
            ["input", "textarea", "select"]
        ):
            inputs.append(
                {
                    "type": field.get(
                        "type",
                        field.name,
                    ),
                    "name": field.get(
                        "name",
                        "",
                    )[:200],
                    "placeholder": field.get(
                        "placeholder",
                        "",
                    )[:300],
                }
            )

        forms.append(
            {
                "action": form.get(
                    "action",
                    "",
                )[:500],
                "method": form.get(
                    "method",
                    "get",
                )[:20],
                "fields": inputs[:30],
            }
        )

    return forms[:30]


def _extract_images(
    soup: BeautifulSoup,
) -> list[dict]:
    """
    Kerää kuvien perustiedot.
    """

    images = []

    for img in soup.find_all(
        "img"
    ):
        src = (
            img.get("src")
            or img.get("data-src")
            or img.get("data-lazy-src")
            or ""
        )

        alt = img.get(
            "alt",
            "",
        )

        images.append(
            {
                "src": src[:500],
                "alt": _clean_text(
                    alt
                )[:300],
                "has_alt": bool(
                    _clean_text(alt)
                ),
            }
        )

    return images[:100]


def _extract_contact_signals(
    text: str,
    links: list[dict],
) -> dict:
    """
    Etsii karkean tason yhteystietosignaaleja.
    """

    lower_text = text.lower()

    email_found = bool(
        re.search(
            r"[\w.+-]+@[\w-]+\.[\w.-]+",
            text,
        )
    )

    phone_found = bool(
        re.search(
            r"(?:\+358|0)\s?\d[\d\s\-()]{5,}",
            text,
        )
    )

    address_keywords = [
        "osoite",
        "address",
        "katu",
        "street",
        "tie ",
        "tampere",
        "helsinki",
        "espoo",
        "turku",
        "oulu",
    ]

    address_signal = any(
        keyword in lower_text
        for keyword in address_keywords
    )

    booking_signal = False

    booking_keywords = [
        "ajanvaraus",
        "varaa aika",
        "varaa",
        "book",
        "booking",
        "appointment",
        "ajanvaraukseen",
    ]

    for link in links:
        combined = (
            f"{link.get('text', '')} "
            f"{link.get('href', '')}"
        ).lower()

        if any(
            keyword in combined
            for keyword in booking_keywords
        ):
            booking_signal = True
            break

    return {
        "email_found": email_found,
        "phone_found": phone_found,
        "address_signal": address_signal,
        "booking_signal": booking_signal,
    }


def _extract_cta_signals(
    links: list[dict],
    buttons: list[str],
) -> dict:
    """
    Etsii toimintakehotuksia.
    """

    cta_keywords = [
        "varaa",
        "ajanvaraus",
        "ota yhteyttä",
        "yhteydenotto",
        "contact",
        "book",
        "booking",
        "osta",
        "shop",
        "tilaa",
        "lue lisää",
        "read more",
        "get started",
        "call",
    ]

    cta_links = []
    cta_buttons = []

    for link in links:
        combined = (
            f"{link.get('text', '')} "
            f"{link.get('href', '')}"
        ).lower()

        if any(
            keyword in combined
            for keyword in cta_keywords
        ):
            text = link.get(
                "text",
                "",
            )

            if text:
                cta_links.append(text)

    for button in buttons:
        lower_button = button.lower()

        if any(
            keyword in lower_button
            for keyword in cta_keywords
        ):
            cta_buttons.append(button)

    return {
        "cta_links": cta_links[:20],
        "cta_buttons": cta_buttons[:20],
        "has_cta": bool(
            cta_links or cta_buttons
        ),
    }


def _is_internal_link(
    href: str,
    base_url: str,
) -> bool:
    """
    Selvittää onko linkki sisäinen.
    """

    if not href:
        return False

    href = href.strip()

    if href.startswith(
        (
            "#",
            "/",
            "./",
            "../",
        )
    ):
        return True

    parsed_href = urlparse(
        href
    )

    if not parsed_href.netloc:
        return True

    parsed_base = urlparse(
        base_url
    )

    if not parsed_base.netloc:
        return False

    return (
        parsed_href.netloc.lower()
        == parsed_base.netloc.lower()
    )


def _build_audit_signals(
    data: dict,
) -> dict:
    """
    Luo tekniset ongelmasignaalit.
    """

    issues = []
    positives = []

    title = data.get(
        "title",
        "",
    )

    meta_description = data.get(
        "meta_description",
        "",
    )

    visible_text_length = data.get(
        "visible_text_length",
        0,
    )

    h1_count = data.get(
        "h1_count",
        0,
    )

    link_count = data.get(
        "link_count",
        0,
    )

    button_count = data.get(
        "button_count",
        0,
    )

    image_count = data.get(
        "image_count",
        0,
    )

    images_without_alt_count = data.get(
        "images_without_alt_count",
        0,
    )

    contact = data.get(
        "contact_signals",
        {},
    )

    cta = data.get(
        "cta_signals",
        {},
    )

    if not data.get(
        "has_viewport_meta",
        False,
    ):
        issues.append(
            "Viewport-meta puuttuu."
        )
    else:
        positives.append(
            "Viewport-meta löytyy."
        )

    if not title:
        issues.append(
            "Sivulta puuttuu title."
        )
    elif len(title) < 20:
        issues.append(
            "Title on hyvin lyhyt."
        )
    else:
        positives.append(
            "Sivulla on title."
        )

    if not meta_description:
        issues.append(
            "Meta description puuttuu."
        )
    else:
        positives.append(
            "Meta description löytyy."
        )

    if visible_text_length < 150:
        issues.append(
            "Sivulla on hyvin vähän näkyvää tekstiä."
        )
    elif visible_text_length >= 500:
        positives.append(
            "Sivulla on riittävästi näkyvää sisältöä."
        )

    if h1_count == 0:
        issues.append(
            "Sivulta puuttuu H1-otsikko."
        )
    elif h1_count > 1:
        issues.append(
            f"Sivulla on useita H1-otsikoita ({h1_count})."
        )
    else:
        positives.append(
            "Sivulla on yksi H1-otsikko."
        )

    if link_count == 0:
        issues.append(
            "Sivulla ei ole linkkejä."
        )

    if button_count == 0:
        issues.append(
            "Sivulla ei ole HTML-painikkeita."
        )

    if image_count > 0:
        if images_without_alt_count == image_count:
            issues.append(
                "Kuvien alt-tekstit puuttuvat."
            )
        elif images_without_alt_count > 0:
            issues.append(
                "Osalta kuvista puuttuu alt-teksti."
            )
        else:
            positives.append(
                "Kuvien alt-tekstit ovat kunnossa."
            )

    if not contact.get(
        "email_found",
        False,
    ):
        issues.append(
            "Sivulta ei löytynyt sähköpostiosoitetta."
        )
    else:
        positives.append(
            "Sivulta löytyi sähköpostiosoite."
        )

    if not contact.get(
        "phone_found",
        False,
    ):
        issues.append(
            "Sivulta ei löytynyt puhelinnumeroa."
        )
    else:
        positives.append(
            "Sivulta löytyi puhelinnumero."
        )

    if not contact.get(
        "address_signal",
        False,
    ):
        issues.append(
            "Sivulta ei löytynyt selvää osoitesignaalia."
        )

    if cta.get(
        "has_cta",
        False,
    ):
        positives.append(
            "Sivulta löytyi CTA-elementtejä."
        )
    else:
        issues.append(
            "Selkeää CTA-elementtiä ei löytynyt."
        )

    if contact.get(
        "booking_signal",
        False,
    ):
        positives.append(
            "Sivulta löytyi ajanvaraukseen viittaava linkki."
        )

    problem_signals = len(
        issues
    )

    if problem_signals >= 7:
        priority = "high"
    elif problem_signals >= 4:
        priority = "medium"
    else:
        priority = "low"

    redesignable = (
        problem_signals >= 4
    )

    confidence = min(
        0.95,
        0.30 + (
            problem_signals * 0.08
        ),
    )

    return {
        "issues": issues,
        "positives": positives,
        "problem_signals": problem_signals,
        "priority": priority,
        "redesignable": redesignable,
        "confidence": round(
            confidence,
            2,
        ),
    }


def extract_text_and_meta(
    html: str,
    base_url: str = "",
) -> dict:
    """
    Kerää verkkosivusta auditointiin
    hyödyllistä tietoa ilman AI:ta.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "template",
            "svg",
        ]
    ):
        tag.decompose()

    title = ""

    if soup.title:
        title = _clean_text(
            soup.title.get_text(
                " ",
                strip=True,
            )
        )

    meta_description = (
        _extract_meta_description(
            soup
        )
    )

    viewport = soup.find(
        "meta",
        attrs={
            "name": re.compile(
                r"^viewport$",
                re.IGNORECASE,
            )
        },
    )

    has_viewport_meta = (
        viewport is not None
    )

    headings = _extract_headings(
        soup
    )

    links = _extract_links(
        soup
    )

    buttons = _extract_buttons(
        soup
    )

    forms = _extract_forms(
        soup
    )

    images = _extract_images(
        soup
    )

    text = soup.get_text(
        separator=" ",
        strip=True,
    )

    text = _clean_text(
        text
    )

    visible_text = text[:12000]

    contact_signals = (
        _extract_contact_signals(
            text,
            links,
        )
    )

    cta_signals = (
        _extract_cta_signals(
            links,
            buttons,
        )
    )

    internal_links = []
    external_links = []

    for link in links:
        href = link.get(
            "href",
            "",
        )

        if _is_internal_link(
            href,
            base_url,
        ):
            internal_links.append(
                link
            )
        else:
            external_links.append(
                link
            )

    images_without_alt = [
        image
        for image in images
        if not image.get(
            "has_alt",
            False,
        )
    ]

    h1_count = len(
        headings.get(
            "h1",
            [],
        )
    )

    data = {
        "success": True,
        "url": base_url,
        "final_url": base_url,
        "status_code": 200,
        "error": "",
        "title": title,
        "meta_description": meta_description,
        "has_viewport_meta": has_viewport_meta,
        "visible_text": visible_text,
        "visible_text_length": len(
            visible_text
        ),
        "raw_html_length": len(
            html
        ),
        "headings": headings,
        "h1_count": h1_count,
        "links": links,
        "link_count": len(
            links
        ),
        "internal_link_count": len(
            internal_links
        ),
        "external_link_count": len(
            external_links
        ),
        "buttons": buttons,
        "button_count": len(
            buttons
        ),
        "forms": forms,
        "form_count": len(
            forms
        ),
        "images": images,
        "image_count": len(
            images
        ),
        "images_without_alt_count": len(
            images_without_alt
        ),
        "contact_signals": contact_signals,
        "cta_signals": cta_signals,
    }

    signals = _build_audit_signals(
        data
    )

    data.update(
        signals
    )

    return data


def analyze_url(
    url: str,
) -> dict:
    """
    Hakee ja analysoi yhden URL:n.

    Tämä funktio palauttaa aina dict-olion.
    """

    normalized_url = normalize_url(
        url
    )

    if not normalized_url:
        return _empty_result(
            "",
            "Tyhjä URL.",
        )

    fetched = fetch_html(
        normalized_url
    )

    if not fetched:
        return _empty_result(
            normalized_url,
            "Tuntematon hakutulos.",
        )

    if not fetched.get(
        "success",
        False,
    ):
        error = fetched.get(
            "error",
            "Sivua ei voitu hakea.",
        )

        return _empty_result(
            normalized_url,
            error,
            fetched.get(
                "status_code"
            ),
        )

    html = fetched.get(
        "html",
        "",
    )

    if not html:
        return _empty_result(
            normalized_url,
            "HTML puuttuu.",
            fetched.get(
                "status_code"
            ),
        )

    final_url = fetched.get(
        "final_url",
        normalized_url,
    )

    try:
        data = extract_text_and_meta(
            html,
            base_url=final_url,
        )

        data["url"] = normalized_url
        data["final_url"] = final_url
        data["status_code"] = fetched.get(
            "status_code"
        )

        return data

    except Exception as e:
        print(
            f"  [fetch] HTML-analyysi "
            f"epäonnistui: "
            f"{normalized_url}: {e}"
        )

        return _empty_result(
            normalized_url,
            f"HTML-analyysivirhe: {e}",
            fetched.get(
                "status_code"
            ),
        )
