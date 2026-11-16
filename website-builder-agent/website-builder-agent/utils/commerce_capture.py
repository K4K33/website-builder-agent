"""Capture complete public Shopify catalogues without AI or paid services."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import ipaddress
from urllib.parse import urlsplit

import requests

from utils.commerce_parity import shop_urls


def _public_https(url: str) -> bool:
    parsed = urlsplit(str(url or ""))
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return False
    try:
        return not ipaddress.ip_address(parsed.hostname).is_private
    except ValueError:
        return parsed.hostname not in {"localhost"}


def _host_key(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def _price_text(variants: list[dict]) -> str:
    values = []
    for variant in variants:
        try:
            values.append(Decimal(str(variant.get("price"))))
        except (InvalidOperation, TypeError, ValueError):
            continue
    if not values:
        return ""
    low, high = min(values), max(values)
    amount = f"{low:.2f}".replace(".", ",") + " €"
    return ("alk. " + amount) if high != low else amount


def _capture_shopify(shop_url: str, *, timeout: int = 20,
                     max_pages: int = 40) -> dict | None:
    if not _public_https(shop_url):
        return None
    origin = urlsplit(shop_url)
    endpoint = f"{origin.scheme}://{origin.netloc}/products.json"
    session = requests.Session()
    session.headers.update({
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0 KaurivoCatalogueAudit/1.0",
    })
    products: list[dict] = []
    seen: set[str] = set()
    final_origin = endpoint
    complete = False
    for page in range(1, max_pages + 1):
        reply = session.get(endpoint, params={"limit": 250, "page": page,
                            "country": "FI", "currency": "EUR"},
                            timeout=timeout, allow_redirects=True)
        if reply.status_code != 200 or not _public_https(reply.url):
            return None
        if _host_key(reply.url) != _host_key(shop_url):
            return None
        try:
            rows = reply.json().get("products")
        except (ValueError, AttributeError):
            return None
        if not isinstance(rows, list):
            return None
        final_origin = reply.url
        for item in rows:
            if not isinstance(item, dict):
                return None
            handle = str(item.get("handle") or "").strip()
            title = " ".join(str(item.get("title") or "").split()).strip()
            price = _price_text(item.get("variants") or [])
            if not handle or not title or not price:
                return None
            host = urlsplit(reply.url)
            product_url = f"{host.scheme}://{host.netloc}/products/{handle}"
            if product_url in seen:
                continue
            seen.add(product_url)
            images = item.get("images") or []
            image = str(images[0].get("src") or "") if images and isinstance(images[0], dict) else ""
            if image and not _public_https(image):
                image = ""
            products.append({
                "url": product_url, "name": title, "price_text": price,
                "image": image, "image_status": "source_only" if image else "not_provided",
            })
        if len(rows) < 250:
            complete = True
            break
    if not complete or not products:
        return None
    return {
        "shop_url": shop_url.rstrip("/"),
        "catalogue_source": final_origin.split("?", 1)[0],
        "platform": "shopify_public_catalogue",
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "complete": True,
        "currency": "EUR",
        "render_mode": "local_paginated_catalogue",
        "observed_product_count": len(products),
        "target": "verkkokauppa.html",
        "products": products,
    }


def capture_shop_catalogues(research: dict) -> list[dict]:
    """Capture every discovered shop; unsupported shops remain fail-closed."""
    captures = []
    for shop in shop_urls(research):
        captured = _capture_shopify(shop)
        if captured is not None:
            captures.append(captured)
    return captures

