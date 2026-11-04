"""Source-bound transactional feature parity: a working shop is not a header link.

No external calls, merchant credentials or fabricated carts. The store's real
catalog and product purchase paths must be researched before redesign can pass.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

SHOPS = re.compile(r"verkkokaupp|kauppa verkossa|online shop|webshop|\bshop\b|\bstore\b", re.I)
SHOP_ROUTE = re.compile(r"^(?:verkkokauppa|kauppa|shop|store)/index\.html$", re.I)
EURO = re.compile(r"\b\d{1,5}(?:[,.]\d{2})?\s*€")
KNOWN_PROVIDER = re.compile(r"(?:^|\.)(?:ekukka\.fi|myshopify\.com)$", re.I)
UNVERIFIED_CHECKOUT = re.compile(r"lisää ostoskoriin|siirry maksamaan|maksa nyt|pay now", re.I)


def _valid_url(url: str) -> bool:
    parsed = urlsplit(str(url or ""))
    return parsed.scheme == "https" and bool(parsed.hostname)


def _ecommerce_origin(research: dict) -> tuple[str, ...]:
    urls = set()
    facts = research.get("company_facts") or {}
    for key in ("external_shop_url", "shop_url", "webshop_url"):
        value = str(facts.get(key) or "")
        if _valid_url(value):
            urls.add(value.rstrip("/"))
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        root = str(page.get("url") or "")
        for link in page.get("links") or []:
            if not isinstance(link, dict):
                continue
            label = str(link.get("text") or link.get("label") or "")
            raw = str(link.get("href") or "")
            dest = urljoin(root, raw)
            if _valid_url(dest) and (
                SHOPS.search(label)
                or KNOWN_PROVIDER.search(urlsplit(dest).hostname or "")
            ):
                urls.add(dest.rstrip("/"))
    return tuple(sorted(urls))


def audit_commerce_parity(pages: dict[str, str], research: dict,
                          *, stage: str = "internal_demo") -> dict:
    """Fail when a source shop loses its browsable, sourced sale experience.

    A product card here opens its *original* working checkout; we do not claim
    a new on-site cart, eKukka integration, live inventory or payment approval.
    """
    sources = _ecommerce_origin(research or {})
    blocking, pending = [], []
    if not sources:
        return {"required": False, "blocking": blocking,
                "pending": pending, "source_shops": []}

    snapshot = (research.get("commerce_inventory") or {})
    products = snapshot.get("products") or []
    shop_url = str(snapshot.get("shop_url") or "")
    if not (_valid_url(shop_url)
            and any(urlsplit(shop_url).hostname == urlsplit(u).hostname for u in sources)
            and str(snapshot.get("observed_at") or "").strip()
            and isinstance(products, list)
            and len(products) >= 1):
        blocking.append("Source e-commerce existed, but no verified external product catalog "
                        "snapshot was captured. A generic shop link cannot pass.")
        return {"required": True, "blocking": blocking,
                "pending": pending, "source_shops": list(sources)}

    source_by_link = {}
    for product in products:
        if not isinstance(product, dict):
            continue
        href, title, price = (str(product.get(k) or "").strip()
                              for k in ("href", "name", "price"))
        if (_valid_url(href)
                and urlsplit(href).hostname == urlsplit(shop_url).hostname
                and title and EURO.search(price)):
            source_by_link[href] = product
    if not source_by_link:
        blocking.append("Commerce source products lack exact source-bound product URLs, "
                        "names or prices; do not invent catalog cards.")
    shop_routes = [route for route in pages if SHOP_ROUTE.fullmatch(route)]
    if not shop_routes:
        blocking.append("Original website has a functioning e-commerce catalog, but "
                        "redesign has no dedicated browsable store route. Header links are insufficient.")
        return {"required": True, "blocking": blocking,
                "pending": pending, "source_shops": list(sources)}

    for route in shop_routes:
        soup = BeautifulSoup(pages[route], "html.parser")
        main = soup.find("main")
        if not main:
            blocking.append(f"{route}: no storefront main content")
            continue
        main_text = main.get_text(" ", strip=True)
        cards = main.select("[data-source-product]")
        validated = set()
        for card in cards:
            href = str(card.get("data-source-product") or "")
            source = source_by_link.get(href)
            if source is None:
                blocking.append(f"{route}: product card does not match a documented real product: {href[:110]}")
                continue
            if (not card.find("img", src=True)
                or str(source["name"]).casefold() not in card.get_text(" ", strip=True).casefold()
                or str(source["price"]).strip() not in card.get_text(" ", strip=True)
                or not card.find("a", href=href)):
                blocking.append(f"{route}: source product lacks original photo, price, name "
                                f"or exact purchase link: {href[:110]}")
                continue
            validated.add(href)
        minimum = min(6, len(source_by_link))
        if len(validated) < minimum:
            blocking.append(f"{route}: {len(validated)} genuine purchasable product cards, "
                            f"require {minimum}; a link-only showcase is not a storefront.")
        expected = list(snapshot.get("categories") or [])
        if len(expected) >= 2:
            shown = sum(1 for name in expected if str(name).casefold() in main_text.casefold())
            if shown < 2:
                blocking.append(f"{route}: e-commerce category browsing/navigation missing.")
        if UNVERIFIED_CHECKOUT.search(" ".join(
                b.get_text(" ", strip=True) for b in main.select("button"))
             ) and not (research.get("commerce_release_verification") or {}).get(
                 "real_cart_integration_verified") is True:
            blocking.append(f"{route}: unverified native cart/payment controls falsely imply a working checkout.")

    verification = research.get("commerce_release_verification") or {}
    if not (verification.get("owner_approved") is True
            and verification.get("real_checkout_journey_tested") is True
            and verification.get("provider_connection_approved") is True):
        pending.append("Customer release: source e-commerce transaction journey, current "
                       "inventory, payment-provider agreement and checkout must be tested "
                       "end-to-end with owner/provider; a static catalog remains a demo.")
        if stage == "client_release":
            blocking.append("Client release missing owner/provider approval and real shopping checkout test.")
    return {"required": True, "blocking": blocking,
            "pending": pending, "source_shops": list(sources),
            "source_product_count": len(source_by_link)}
