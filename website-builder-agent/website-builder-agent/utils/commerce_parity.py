"""Offline checks for original shops, including separately hosted catalogues.

A shop link is discovery evidence, never evidence that its catalogue survived.
Checkout remains on the merchant's existing platform unless actually integrated.
"""
from urllib.parse import urljoin, urlsplit
import re
from bs4 import BeautifulSoup


def shop_urls(research):
    urls = set()
    for page in (research.get("source_inventory") or {}).get("pages", []):
        for link in page.get("links", []):
            label = str(link.get("text") or "").casefold()
            href = urljoin(page.get("url", ""), str(link.get("href") or ""))
            if re.search(r"verkkokau|webshop|webbutik|online\s*shop|\bshop\b|\bstore\b", label):
                if urlsplit(href).scheme in ("https", "http"):
                    urls.add(href.rstrip("/"))
    explicit = (research.get("company_facts") or {}).get("external_shop_url")
    if explicit:
        urls.add(str(explicit).rstrip("/"))
    return sorted(urls)


def commerce_problems(research, pages=None):
    """Return blockers before generation, and inspect actual cards after it.

    Each captured shop has its own source, products, local target and timestamp.
    Product records require exact source URLs, names and observed prices. Cards
    use data-product-source, visible name/price/image and the real product link.
    This does not certify live stock, checkout completion or visual quality.
    """
    issues = []
    captures = research.get("commerce_inventory") or []
    for shop in shop_urls(research):
        capture = next((c for c in captures if str(c.get("shop_url", "")).rstrip("/") == shop), None)
        if not capture or not capture.get("captured_at") or capture.get("complete") is not True:
            issues.append({"kind": "shop_not_inspected", "source": shop})
            continue
        products = capture.get("products") or []
        expected = capture.get("observed_product_count")
        target = str(capture.get("target") or "")
        urls = [str(p.get("url") or "") for p in products]
        if (not products or type(expected) is not int or expected != len(products)
                or len(set(urls)) != len(urls) or not target
                or target.startswith(("/", "http:", "https:")) or ".." in target.split("/")):
            issues.append({"kind": "incomplete_shop_catalogue", "source": shop})
            continue
        for product in products:
            parsed = urlsplit(product.get("url") or "")
            price = product.get("price_text")
            if (parsed.scheme != "https" or parsed.netloc != urlsplit(shop).netloc
                    or not product.get("name") or not price or not product.get("image")):
                issues.append({"kind": "unverified_shop_product", "source": shop})
        if pages is None:
            continue
        soup = BeautifulSoup(pages.get(target, ""), "html.parser")
        for product in products:
            card = soup.find(attrs={"data-product-source": product["url"]})
            text = card.get_text(" ", strip=True) if card else ""
            if (not card or product["name"] not in text or product["price_text"] not in text
                    or not card.find("img", src=product["image"])
                    or not ((card.name == "a" and card.get("href") == product["url"])
                            or card.find("a", href=product["url"]))):
                issues.append({"kind": "missing_shop_product", "source": product["url"]})
        if not soup.select('[data-shop-controls]'):
            issues.append({"kind": "missing_shop_controls", "source": shop})
        if not any(
            urljoin("https://preview.invalid/" + path, a.get("href", ""))
            == "https://preview.invalid/" + target.removesuffix("index.html")
            or urljoin("https://preview.invalid/" + path, a.get("href", ""))
            == "https://preview.invalid/" + target
            for path, raw in pages.items()
            for a in BeautifulSoup(raw, "html.parser").select('a[data-shop-entry][href]')
        ):
            issues.append({"kind": "missing_local_shop_entry", "source": shop})
    return issues
