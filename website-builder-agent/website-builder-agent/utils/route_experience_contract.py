"""Source-grounded purpose-first page layouts, enforced BEFORE saving HTML.

The previous QA kept original images somewhere but allowed enormous empty
title bands, recycled pictures and duplicated CTAs on every route. Known
failures on photo-rich businesses now BLOCK output; image-poor businesses
are never told to invent media. This is not a numeric aesthetic grade.
"""
from __future__ import annotations
import re
from urllib.parse import urlsplit
from bs4 import BeautifulSoup
from utils.content_parity import source_inventory_sha256
from utils.cross_route_editorial_risks import audit_cross_route_editorial_risks
from utils.premium_quality_gate import site_digest

ROLE_PATTERNS = (
    ("rental", re.compile(r"vuokra|rental|hire|juhlapuku", re.I)),
    ("contact", re.compile(r"yhteys|yhteystied|myym[aä]l[aä]|contact|visit|käynti|k[aä]ynti|osoite|aukiolo|location|directions|toimipiste", re.I)),
    ("collection", re.compile(r"valikoima|tuotte|product|mallisto|catalog|galler|gallery|referens|portfolio|ty[oö]t|projektit|collection|stock", re.I)),
    ("people", re.compile(r"meist[aä]|about us|tiimi|team|henkil[oö]st|tekij[aä]t|employees|our people", re.I)),
    ("booking", re.compile(r"ajanvara|booking|varaa aika|appointment", re.I)),
    ("service", re.compile(r"palvelu|huolto|myyntitili|myy vaatte|consign|repair|service|korja|asenn|tilaa", re.I)),
)
EXPECTATIONS = {
    "rental": "Show an authentic example product and a truthful enquiry route early.",
    "collection": "Show genuine products/work in first content section.",
    "contact": "Present verified address/contact details in the first content section.",
    "people": "Lead with real staff or workshop identity if sourced.",
    "booking": "Show the real booking action early.",
    "service": "Explain the specific service and its actual next step.",
    "general": "Explain this route's visitor task, without a reused agency hero.",
}

def _is_actual_source_photo(candidate: dict) -> bool:
    """Keep sponsor marks and SVG icons out of the PHOTO-RICH threshold."""
    if candidate.get("role") in ("gallery_photo", "staff_portrait"):
        return True
    src=str(candidate.get("src") or "")
    marker=(str(candidate.get("alt") or "")+" "+
            src.rsplit("/",1)[-1]).casefold()
    if re.search(r"(?:logo|sponsor|partner|yhteisty[oö]|kumppani|"
                 r"icon|ikoni|favicon|badge|merkki)",marker):
        return False
    if urlsplit(src).path.casefold().endswith(".svg"):
        return False
    return True

def source_photo_count(research: dict) -> int:
    seen = set()
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if isinstance(page, dict):
            ident = page.get("source_identity") or {}
            for p in ident.get("original_content_photos") or []:
                if (isinstance(p, dict) and p.get("src")
                    and _is_actual_source_photo(p)):
                    seen.add(str(p["src"]).strip())
    return len(seen)

def _route_role(page: dict) -> str:
    if str(page.get("path") or "") == "index.html":
        return "general"
    for text in (str(page.get("path") or ""), str(page.get("purpose") or ""),
                 str(page.get("user_task") or "")):
        for role, pattern in ROLE_PATTERNS:
            if pattern.search(text):
                return role
    return "general"

PHOTO_ROLE_HINTS = {
    "rental": re.compile(r"mekko|puku|dress|gown|suit|juhla|vuokra|rental|formal",re.I),
    "collection": re.compile(r"tuote|product|work|ty[oö]|referens|galler|portfolio|shoes|keng|vintage|dress|mekko",re.I),
    "contact": re.compile(r"myym[aä]l[aä]|liiketila|julkisiv|storefront|interior|shop|store|building|sis[aä]til|toimipiste",re.I),
    "people": re.compile(r"henkil[oö]|yritt[aä]j|team|person|portrait|staff|employee|founder|tekij[aä]",re.I),
    "service": re.compile(r"huolto|process|service|workshop|ty[oö]tila|korja|installation|valmist",re.I),
}

def _observed_photo_candidates(research: dict) -> list[dict]:
    images, seen = [], set()
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(page,dict): continue
        url=str(page.get("url") or "")
        identity=page.get("source_identity") or {}
        for photo in identity.get("original_content_photos") or []:
            if (not isinstance(photo,dict) or not photo.get("src")
                or not _is_actual_source_photo(photo)):
                continue
            src=str(photo["src"]).strip()
            if src in seen: continue
            seen.add(src)
            images.append({"src":src, "alt":str(photo.get("alt") or "")[:130],
                           "role":str(photo.get("role") or ""),
                           "observed_on":url})
    return images

def _candidate_score(role: str, candidate: dict) -> int:
    if role=="general": return 0
    alt=str(candidate["alt"])+" "+str(candidate["src"]).split("/")[-1]
    score=0
    if role=="people" and candidate["role"]=="staff_portrait": score+=10
    if role=="collection" and candidate["role"]=="gallery_photo": score+=6
    if role=="contact" and candidate["role"] in ("shop_interior","exterior"): score+=8
    hint=PHOTO_ROLE_HINTS.get(role)
    if hint and hint.search(alt): score+=5
    return score

def _allocate_distinct_source_photo_hints(rows: list[dict],
                                          research: dict) -> None:
    """Provide each task a distinct, source-OBSERVED candidate where possible.

    Alt/file-name matching is a weak inventory hint, NOT proof of the subject,
    permission to use original media, or a mandatory exact filename.
    Unknown/unlabelled images remain available for human assignment.
    """
    candidates=_observed_photo_candidates(research)
    used=set()
    priority={"rental":0,"contact":1,"people":2,"collection":3,
              "service":4,"booking":5,"general":6}
    for row in sorted(rows,key=lambda row:(priority.get(row["role"],9),row["route"])):
        role=row["role"]
        ranked=sorted((( _candidate_score(role,p),p) for p in candidates
                       if p["src"] not in used),
                      key=lambda x:(-x[0],x[1]["src"]))
        if not ranked or ranked[0][0] <= 0:
            row["source_photo_hint"] = None
            continue
        score,photo=ranked[0]
        used.add(photo["src"])
        row["source_photo_hint"]={
            "src":photo["src"],"alt":photo["alt"],
            "observed_on":photo["observed_on"],
            "verified_visual_subject":False,
            "licensed_for_public_use":False,
            "note":"Source observed reference; verify subject and rights before use."
        }


def derive_route_experience_contract(research: dict) -> dict:
    """Deterministic pre-build contract tied to actual planned visitor jobs."""
    count = source_photo_count(research)
    inv = research.get("source_inventory") or {}
    plan = (research.get("site_architecture") or {}).get("pages") or []
    routes = []
    for row in plan:
        if not isinstance(row, dict): continue
        role = _route_role(row)
        routes.append({
            "route": str(row.get("path") or ""),
            "role": role,
            "visitor_task": str(row.get("user_task") or "")[:280],
            "purpose": str(row.get("purpose") or "")[:280],
            "first_section_requirement": EXPECTATIONS[role],
            "product_media_required": count >= 3 and role in ("collection", "rental"),
            "contact_details_required": role == "contact",
        })
    _allocate_distinct_source_photo_hints(routes, research)
    return {
        "protocol": "purpose-first-route-v1",
        "source_sha256": source_inventory_sha256(inv) if inv.get("pages") else "",
        "source_photo_count": count,
        "photo_rich_source": count >= 3,
        "routes": routes,
        "rule": "Each route serves its own real visitor task. Product/rental "
                "routes with original photographs MUST open with relevant "
                "authentic media; contact routes with verified details MUST "
                "present contact information promptly. Do not reuse a single "
                "original photo or identical CTA across three unrelated routes. "
                "Don't invent photos when rights are absent."
    }

def _signed_exception(research: dict, pages: dict[str, str],
                      source_hash: str, issue: str) -> bool:
    """Specific reviewed exception cannot be invented once for every site."""
    current = site_digest(pages)
    for rec in research.get("route_composition_exceptions") or []:
        if not isinstance(rec, dict): continue
        if (rec.get("issue") == issue and rec.get("approved") is True
            and rec.get("reviewer_kind") == "independent_human"
            and str(rec.get("reviewer_id") or "").strip()
            and str(rec.get("screenshot_evidence") or "").strip()
            and len(str(rec.get("justification") or "").strip()) >= 30
            and rec.get("source_sha256") == source_hash
            and rec.get("build_sha256") == current):
            return True
    return False

def _first_section(raw: str):
    main = BeautifulSoup(raw, "html.parser").find("main")
    return (main.find(["section", "article"], recursive=False)
            or main.find(["section", "article"]) or main) if main else None

def _meaningful_first_section_media(first) -> bool:
    """Brand marks, decorative SVG icons and dummy placeholder IMG are not goods."""
    if first.select_one("video,iframe[src]"):
        return True
    for image in first.select("img[src],img[data-src],picture img"):
        src = str(image.get("data-src") or image.get("src") or "")
        alt = str(image.get("alt") or "")
        marker = (alt + " " + src.rsplit("/", 1)[-1]).casefold()
        if re.search(r"logo|favicon|brand.?mark|placeholder|sponsor|partner|icon|ikoni|"
                     r"yhteisty[oö]kumppani|logo.svg", marker):
            continue
        if urlsplit(src).path.casefold().endswith(".svg"):
            continue
        if not src or src.startswith(("data:image/svg+xml", "javascript:", "blob:")):
            continue
        return True
    return False

def _known_contact_markers(research: dict) -> list[str]:
    """Grounded tokens from verified facts OR the captured original website.

    External/hand-written demos do not always carry company_facts: their
    source_inventory still contains real contact details. A made-up tel link
    must not count as proof of the original address or email.
    """
    markers = []
    facts = research.get("company_facts") or {}
    for key in ("address", "phone", "email"):
        value = str(facts.get(key) or "").strip()
        if value:
            markers.append(value.casefold())
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        text = str(page.get("text") or "")
        markers.extend(m.casefold() for m in re.findall(
            r"\b[\wåäöÅÄÖ-]*(?:katu|tie|kuja|polku|vägen|gatan)\s+\d+[a-z]?\b",
            text, flags=re.I))
        markers.extend(m.casefold() for m in re.findall(
            r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", text, flags=re.I))
        for field in ("links", "footer_links"):
            for link in page.get(field) or []:
                if not isinstance(link, dict):
                    continue
                href = str(link.get("href") or "")
                if href.lower().startswith(("mailto:", "tel:")):
                    markers.append(href.split(":", 1)[1].strip().casefold())
    return sorted({m for m in markers if len(m) >= 5})


def _source_has_contact_facts(research: dict) -> bool:
    if _known_contact_markers(research):
        return True
    facts = research.get("company_facts") or {}
    if facts.get("opening_hours"):
        return True
    # Exact hours may be presented in prose, not structured research.
    source_text = " ".join(str(page.get("text") or "")
                           for page in (research.get("source_inventory") or {}).get("pages") or []
                           if isinstance(page, dict))
    return bool(re.search(r"\b(?:aukioloaj\w*|avoinna|opening hours|opening times)\b",
                          source_text, flags=re.I))


def _contact_evidence(first, research: dict) -> bool:
    visible = first.get_text(" ", strip=True).casefold()
    hrefs = " ".join(str(a.get("href") or "") for a in first.select("a[href]")).casefold()
    observed = visible + " " + hrefs
    known = _known_contact_markers(research)
    if known:
        # Source-grounded identity matters: any arbitrary phone/address can
        # be present in the markup but still belong to the wrong business.
        return any(marker in observed for marker in known)
    if first.select_one('address,a[href^="tel:"],a[href^="mailto:"]'):
        return True
    directions = first.select_one('a[href*="google.com/maps"],'
                                  'a[href*="maps.apple.com"],'
                                  'a[href*="openstreetmap.org"]')
    return bool(directions and len(visible) >= 20)

def audit_route_experience(pages: dict[str, str], research: dict) -> dict:
    contract = derive_route_experience_contract(research)
    blocking, pending = [], []
    if not pages or len(pages) < 2:
        return {"blocking": blocking, "pending": pending, "contract": contract}
    for row in contract["routes"]:
        route = row["route"]
        if route not in pages: continue  # Source architecture checks this.
        first = _first_section(pages[route])
        if first is None:
            if row["product_media_required"] or (
                    row["contact_details_required"] and _source_has_contact_facts(research)):
                blocking.append({"kind":"missing_task_first_section",
                                 "route":route,
                                 "detail":"No real first main content section for this visitor task."})
            continue
        if row["product_media_required"] and not _meaningful_first_section_media(first):
            issue = "product_media_missing_first_section:" + route
            if not _signed_exception(research,pages,contract["source_sha256"],issue):
                blocking.append({
                    "kind":"task_first_view_has_no_product_evidence",
                    "issue":issue, "route":route,
                    "detail":"Original photos exist but product/rental page starts "
                             "without merchandise evidence. A huge title and a "
                             "photo several sections later are not equivalent.",
                })
        if row["contact_details_required"]:
            if _source_has_contact_facts(research) and not _contact_evidence(first, research):
                issue = "real_contact_missing_first_section:" + route
                if not _signed_exception(research,pages,contract["source_sha256"],issue):
                    blocking.append({
                        "kind":"contact_page_hides_verified_visit_details",
                        "issue":issue, "route":route,
                        "detail":"Verified visitor information exists but is absent "
                                 "from the contact page's opening section.",
                    })
    editorial = audit_cross_route_editorial_risks(pages,research)
    hard = {"recycled_business_photography",
            "repeated_text_only_subpage_openings",
            "repeated_full_width_call_to_action_copy"}
    for risk in editorial["pending"]:
        kind = str(risk.get("category") or "")
        issue = "cross_route:" + kind
        # Identical conversion banners across unrelated pages are agency
        # template repetition even for a business with NO original images.
        # Product-photo and text-only penalties remain conditional on real
        # source photography so that no-site leads needn't fabricate images.
        should_block = (
            kind=="repeated_full_width_call_to_action_copy" and len(pages)>=3
            or kind in hard and contract["photo_rich_source"] and len(pages)>=3
        )
        if (should_block
            and not _signed_exception(research,pages,contract["source_sha256"],issue)):
            blocking.append({"kind":kind, "issue":issue,
                             "detail":risk.get("issue"),
                             "examples":risk.get("examples",risk.get("routes",[]))})
        else:
            pending.append(risk)
    return {
        "blocking":blocking, "pending":pending,"contract":contract,
        "editorial_observations":editorial.get("observations",{}),
        "note":"Deterministic task-specific evidence gate, not an aesthetic "
               "score. Actual browser folds, client media rights, and independent "
               "visual review still required.",
    }
