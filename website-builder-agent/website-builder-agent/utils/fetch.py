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
"""

import re

import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; WebsiteBuilderAgent/1.0; "
        "+https://github.com/K4K33/website-builder-agent)"
    )
}


def normalize_url(url: str) -> str:
    """
    Varmistaa, että URL sisältää http/https-protokollan.
    """

    url = (url or "").strip()

    if not url:
        return ""

    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "https://" + url

    return url


def fetch_html(
    url: str,
    timeout: int = 15,
) -> str | None:
    """
    Hakee verkkosivun HTML:n.
    """

    url = normalize_url(url)

    if not url:
        return None

    try:
        response = requests.get(
            url,
            headers=HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )

        response.raise_for_status()

        return response.text

    except requests.RequestException as e:
        print(
            f"  [fetch] Sivun haku epäonnistui "
            f"({url}): {e}"
        )

        return None


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

        for tag in soup.find_all(tag_name):
            text = _clean_text(
                tag.get_text(
                    " ",
                    strip=True,
                )
            )

            if text:
                headings.append(text)

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
            ):
                continue

            text = (
                tag.get("value", "")
                or tag.get("aria-label", "")
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
            buttons.append(text[:200])

    return buttons[:100]


def _extract_forms(
    soup: BeautifulSoup,
) -> list[dict]:
    """
    Kerää lomakkeiden perustiedot.
    """

    forms = []

    for form in soup.find_all("form"):

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
                    ),
                    "placeholder": field.get(
                        "placeholder",
                        "",
                    ),
                }
            )

        forms.append(
            {
                "action": form.get(
                    "action",
                    "",
                ),
                "method": form.get(
                    "method",
                    "get",
                ),
                "fields": inputs[:30],
            }
        )

    return forms[:30]


def _extract_images(
    soup: BeautifulSoup,
) -> list[dict]:
    """
    Kerää kuvien perustiedot.

    Erityisesti tarkistetaan alt-tekstit,
    koska niiden puuttuminen on hyödyllinen
    saavutettavuussignaali.
    """

    images = []

    for img in soup.find_all("img"):

        src = (
            img.get("src")
            or img.get("data-src")
            or ""
        )

        alt = img.get(
            "alt",
            "",
        )

        images.append(
            {
                "src": src[:500],
                "alt": _clean_text(alt)[:300],
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
            r"(\+358|0)\s?\d[\d\s\-]{5,}",
            text,
        )
    )

    address_keywords = [
        "osoite",
        "address",
        "katu",
        "street",
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
            cta_links.append(
                link.get("text", "")
            )

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


def extract_text_and_meta(
    html: str,
    base_url: str = "",
) -> dict:
    """
    Kerää verkkosivusta mahdollisimman paljon
    auditointiin hyödyllistä tietoa ilman AI:ta.
    """

    soup = BeautifulSoup(
        html,
        "html.parser",
    )

    # Poistetaan elementit, joiden sisältö ei ole
    # käyttäjälle normaalia näkyvää sivutekstiä.
    for tag in soup(
        [
            "script",
            "style",
            "noscript",
            "template",
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

    # Teksti kerätään uudelleen.
    # Tässä vaiheessa script/style-elementit on poistettu.
    text = soup.get_text(
        separator=" ",
        strip=True,
    )

    text = _clean_text(text)

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

        if (
            href.startswith("/")
            or href.startswith("#")
            or base_url in href
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

    return {
        "url": base_url,
        "title": title,
        "meta_description": meta_description,
        "has_viewport_meta": has_viewport_meta,
        "visible_text": visible_text,
        "visible_text_length": len(
            visible_text
        ),
        "raw_html_length": len(html),
        "headings": headings,
        "h1_count": h1_count,
        "links": links,
        "link_count": len(links),
        "internal_link_count": len(
            internal_links
        ),
        "external_link_count": len(
            external_links
        ),
        "buttons": buttons,
        "button_count": len(buttons),
        "forms": forms,
        "form_count": len(forms),
        "images": images,
        "image_count": len(images),
        "images_without_alt_count": len(
            images_without_alt
        ),
        "contact_signals": contact_signals,
        "cta_signals": cta_signals,
    }


def analyze_url(
    url: str,
) -> dict | None:
    """
    Hakee ja analysoi yhden URL:n.
    """

    normalized_url = normalize_url(
        url
    )

    if not normalized_url:
        return None

    html = fetch_html(
        normalized_url
    )

    if html is None:
        return None

    data = extract_text_and_meta(
        html,
        base_url=normalized_url,
    )

    return data
