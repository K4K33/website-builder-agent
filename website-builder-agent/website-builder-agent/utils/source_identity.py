"""Source-grounded business identity and testimonial fidelity, without AI credits.

An original logo, customer quote or star score is evidence, not decoration.
Unknown CSS/JS review widgets are *not* permission to invent ratings. The
output review gate operates on the complete generated multi-page site.
"""
from __future__ import annotations

import re
import unicodedata
from urllib.parse import urljoin
from bs4 import BeautifulSoup


REVIEW_SELECTOR = (
    '[itemtype*="schema.org/Review"],[itemprop="review"],[data-review],'
    '[class~="review"],[class~="review-card"],[class~="testimonial"],'
    '[class~="testimonial-card"],[class~="arvostelu"],[class~="asiakaspalaute"]'
)
QUOTE_SELECTOR = (
    '[itemprop="reviewBody"],[class*="review-text"],'
    '[class*="testimonial-text"],[class*="quote"],blockquote,q'
)
STAR_GLYPHS = "★⭐"
RATING_LABEL = re.compile(
    r"(?<!\d)([1-5])\s*(?:/\s*5|(?:out of|of)\s*5|tähteä|tähden|stars?)",
    re.IGNORECASE,
)


def plain(value: object) -> str:
    return " ".join(unicodedata.normalize("NFKC", str(value or "")).casefold().split())


def _stars(node) -> int | None:
    """Read only an EXPLICIT rating value, never infer it from a positive quote."""
    for tag in [node, *node.find_all(True)]:
        prop = str(tag.get("itemprop") or "").lower()
        if prop == "ratingvalue":
            raw = str(tag.get("content") or tag.get_text(" ", strip=True)).strip()
            if raw in {"1", "2", "3", "4", "5"}:
                return int(raw)
        for key in ("aria-label", "title", "data-rating", "data-stars"):
            raw = str(tag.get(key) or "").strip()
            if key in {"data-rating", "data-stars"} and raw in {"1", "2", "3", "4", "5"}:
                return int(raw)
            match = RATING_LABEL.search(raw)
            if match:
                return int(match.group(1))
        if tag.name in ("span", "div", "strong", "i", "b") and any(
            term in " ".join(tag.get("class") or []).lower()
            for term in ("star", "rating", "tähti")
        ):
            raw = "".join(tag.stripped_strings)
            count = sum(raw.count(glyph) for glyph in STAR_GLYPHS)
            if 1 <= count <= 5:
                return count
    return None


def extract_source_identity(html: str, source_url: str = "") -> dict:
    soup = BeautifulSoup(html, "html.parser")
    color = soup.find("meta", attrs={"name": re.compile("^theme-color$", re.I)})
    theme_color = str(color.get("content") or "").strip()[:40] if color else ""
    logo_candidates = []
    original_favicons = []
    for link in soup.select('link[rel~="icon"],link[rel~="apple-touch-icon"]'):
        href = str(link.get("href") or "").strip()
        if href:
            absolute = urljoin(source_url, href) if source_url else href
            if absolute not in original_favicons:
                original_favicons.append(absolute[:500])
    for img in soup.select('header img,[role="banner"] img,[class*="site-header"] img'):
        raw = str(img.get("src") or img.get("data-src") or "").strip()
        if raw:
            url = urljoin(source_url, raw) if source_url else raw
            if url not in logo_candidates:
                logo_candidates.append(url[:500])

    # Preserve real original work/staff photography as source candidates.
    # Their presence does not imply the agency has permission to republish.
    content_photos = []
    main = soup.find("main") or soup
    for img in main.find_all("img"):
        raw = str(img.get("src") or img.get("data-src") or "").strip()
        if not raw:
            continue
        url = urljoin(source_url, raw) if source_url else raw
        if url in logo_candidates or any(p["src"] == url for p in content_photos):
            continue
        alt = " ".join(str(img.get("alt") or "").split())[:200]
        content_photos.append({"src": url[:500], "alt": alt})

    candidates = soup.select(REVIEW_SELECTOR)
    # Some themes render individual testimonials as blockquotes without classes.
    for block in soup.select("blockquote"):
        if not block.find_parent(REVIEW_SELECTOR) and block not in candidates:
            candidates.append(block)
    reviews, seen = [], set()
    for node in candidates[:45]:
        quote_tag = node.select_one(QUOTE_SELECTOR)
        if quote_tag is None:
            quote_tag = node.find("p")
        if quote_tag is None and node.name == "blockquote":
            quote_tag = node
        if quote_tag is None:
            continue
        quote = " ".join(quote_tag.get_text(" ", strip=True).split())
        if not 12 <= len(quote) <= 1000 or plain(quote) in seen:
            continue
        seen.add(plain(quote))
        author_tag = node.select_one('[itemprop="author"],[class*="author"],cite')
        author = (" ".join(author_tag.get_text(" ", strip=True).split())[:120]
                  if author_tag else "")
        reviews.append({"quote": quote, "stars": _stars(node),
                        "author": author, "source_url": source_url})
        if len(reviews) >= 24:
            break

    # A detected third-party widget must be reviewed if it renders testimonials
    # dynamically: a static HTML snapshot cannot certify that they are absent.
    dynamic_review_widget = bool(soup.select(
        'iframe[src*="review"],iframe[src*="trustpilot"],'
        'iframe[src*="google.com/maps"],[class*="review-widget"],'
        '[data-widget*="review"]'
    ))
    return {
        "theme_color": theme_color,
        "original_logo_candidates": logo_candidates[:12],
        "original_favicon_candidates": original_favicons[:12],
        "original_content_photos": content_photos[:70],
        "reviews": reviews,
        "dynamic_review_widget": dynamic_review_widget,
        "source_url": source_url,
        "note": "Observed source HTML only; not proof of rights or complete JS-loaded reviews.",
    }



def validate_brand_preservation_plan(research: dict) -> dict:
    """Require an evidence-linked brand plan before spending Builder credits.

    The source is authoritative; a new visual style is allowed, but ignoring
    original colors/logos is not. Human media rights approval is separate.
    Offline test fixtures without observable source identity remain unchanged.
    """
    observed = []
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        identity = page.get("source_identity") or {}
        if not isinstance(identity, dict):
            continue
        if (identity.get("theme_color") or identity.get("original_logo_candidates")
                or identity.get("original_content_photos")):
            observed.append((str(page.get("url") or ""), identity))
    if not observed:
        return {"required": False, "source_pages": 0}
    plan = research.get("brand_preservation_plan")
    if not isinstance(plan, dict):
        raise RuntimeError("Missing evidence-linked original brand preservation plan.")
    required = ("logo_treatment", "color_treatment",
                "typography_treatment", "photography_treatment")
    missing = [key for key in required
               if len(str(plan.get(key) or "").strip()) < 24]
    if missing:
        raise RuntimeError("Original brand plan incomplete: " + ", ".join(missing))
    urls = set(str(x) for x in plan.get("source_urls") or [])
    if not all(url and url in urls for url, _ in observed):
        raise RuntimeError("Original brand plan does not cite every brand-evidence source page.")
    originals = {
        logo for _, identity in observed
        for logo in identity.get("original_logo_candidates") or []
        if isinstance(logo, str) and logo.strip()
    }
    cited = set(str(x) for x in plan.get("original_logo_candidates") or [])
    if not originals.issubset(cited):
        raise RuntimeError("Original brand plan omitted one or more sourced logo assets.")
    colors = {str(identity.get("theme_color"))
              for _, identity in observed if identity.get("theme_color")}
    if not colors.issubset(set(map(str, plan.get("original_theme_colors") or []))):
        raise RuntimeError("Original brand plan omitted a source theme color.")
    return {"required": True, "source_pages": len(observed),
            "observed_logos": len(originals), "observed_colors": sorted(colors)}



def audit_source_reviews(rendered_pages: dict[str, str], research: dict) -> dict:
    """Require original observed review text and its true star score to survive.

    Scores must be visually associated with the exact originating quote. Do not
    accept a global '★★★★★' elsewhere as a substitute for each review.
    """
    originals = [
        row for page in (research.get("source_inventory") or {}).get("pages") or []
        if isinstance(page, dict)
        for row in (page.get("source_identity") or {}).get("reviews") or []
        if isinstance(row, dict) and str(row.get("quote") or "").strip()
    ]
    missing = []
    pending = []
    all_soups = {
        path: BeautifulSoup(html, "html.parser")
        for path, html in rendered_pages.items()
    }
    for row in originals:
        quote = plain(row["quote"])
        # Search a text-bearing subelement so we can look for local stars.
        matching = []
        for path, soup in all_soups.items():
            for node in soup.find_all(["blockquote", "q", "p", "div", "span", "li"]):
                if plain(node.get_text(" ", strip=True)) == quote:
                    matching.append((path, node))
                    break
        if not matching:
            missing.append({
                "kind": "lost_source_testimonial",
                "source_url": row.get("source_url", ""),
                "quote": row["quote"][:150],
            })
            continue
        stars = row.get("stars")
        if type(stars) is int and 1 <= stars <= 5:
            matched = False
            for _, node in matching:
                # Permits explicit accessible labels OR literal star characters
                # within the review's own compact card, not an unrelated banner.
                parent = node
                for _ in range(3):
                    if parent is None:
                        break
                    if _stars(parent) == stars:
                        matched = True
                        break
                    parent = parent.parent if parent.name not in ("body", "html") else None
            if not matched:
                missing.append({
                    "kind": "lost_verified_review_stars",
                    "source_url": row.get("source_url", ""),
                    "quote": row["quote"][:150],
                    "expected_stars": stars,
                })
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if isinstance(page, dict) and (
            (page.get("source_identity") or {}).get("dynamic_review_widget")
        ):
            pending.append(
                "Dynamic original review widget requires visual/source verification: "
                + str(page.get("url") or "")
            )
    return {
        "pass": not missing and not pending,
        "original_review_count": len(originals),
        "missing": missing,
        "pending": pending,
        "note": "Only observed original reviews and explicit ratings; no fabricated stars.",
    }


def extract_price_faq_evidence(html: str) -> dict:
    """Inventory explicit source price table rows and FAQ disclosure questions."""
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.find_all("tr"):
        cells = [" ".join(tag.get_text(" ", strip=True).split())
                 for tag in tr.find_all(["td", "th"], recursive=False)]
        if not 2 <= len(cells) <= 8 or len(cells[0]) < 3:
            continue
        price = next((cell for cell in reversed(cells[1:])
                      if any(char.isdigit() for char in cell)
                      and ("€" in cell or " eur" in cell.lower())), "")
        if price:
            row = {"label": cells[0][:320], "price": price[:100]}
            if row not in rows:
                rows.append(row)
    questions = []
    for details in soup.find_all("details"):
        summary = details.find("summary")
        if summary:
            value = " ".join(summary.get_text(" ", strip=True).split())[:300]
            if len(value) >= 7 and value not in questions:
                questions.append(value)
    return {"price_rows": rows[:120], "faq_questions": questions[:80]}


def audit_price_faq_preservation(rendered_pages: dict[str, str], research: dict) -> dict:
    """Compare high-value facts in each source table row, not unrelated tokens."""
    source = (research.get("source_inventory") or {}).get("pages") or []
    rows, questions = [], []
    for page in source:
        if isinstance(page, dict):
            evidence = page.get("price_faq_evidence") or {}
            rows.extend((page.get("url", ""), row) for row in evidence.get("price_rows") or []
                        if isinstance(row, dict))
            questions.extend((page.get("url", ""), question)
                             for question in evidence.get("faq_questions") or [])
    soup = BeautifulSoup("<html><body>" + "\n".join(rendered_pages.values()) +
                         "</body></html>", "html.parser")
    units = []
    for node in soup.select("tr,li,article,details,[class*='pricing'],[class*='price-row']"):
        value = plain(node.get_text(" ", strip=True))
        if 1 <= len(value) <= 700:
            units.append(value)
    visible = plain(soup.get_text(" ", strip=True))
    missing = []
    for url, row in rows:
        label, price = plain(row.get("label")), plain(row.get("price"))
        if label and price and not any(label in unit and price in unit for unit in units):
            missing.append({"kind": "lost_source_price_row", "source_url": url,
                            "label": row.get("label"), "price": row.get("price")})
    for url, question in questions:
        if plain(question) not in visible:
            missing.append({"kind": "lost_source_faq_question", "source_url": url,
                            "question": question})
    return {"pass": not missing, "missing": missing,
            "price_rows_checked": len(rows), "faq_questions_checked": len(questions)}
