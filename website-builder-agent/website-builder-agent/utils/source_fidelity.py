"""Reusable source-to-redesign preservation and task-continuity gate.

No company names, AI calls, or fixed HTML templates. Evidence is grounded in
a bounded source crawl and checked against actual generated pages. This gate
does not pretend that text similarity certifies faithful semantic rewriting:
unclear scope remains pending for independent/client review.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256


TASK_WORDS = (
    "tuot", "product", "myyn", "myyt", "shop", "kauppa", "hinn",
    "price", "palvel", "service", "kohte", "referen", "portfolio",
    "menu", "lounas", "ruokalist", "kurss", "course", "gallery",
    "galler", "verhoilu", "huollot", "korjaus", "tarjous",
)
# Purely administrative/external checkout systems may legitimately remain
# outside a redesigned website. Internal source pages may not by default.
EXTERNAL_PROCESS_WORDS = ("checkout", "payment", "maksu", "booking", "ajanvaraus")
def _s(value: object) -> str:
    return " ".join(str(value or "").casefold().split())

def _url(value: str, base: str = "") -> str:
    raw = urljoin(base, str(value or "").strip())
    parsed = urlsplit(raw)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return ""
    host = parsed.hostname.lower().removeprefix("www.")
    path = parsed.path.rstrip("/") or "/"
    return host + path + (("?" + parsed.query) if parsed.query else "")

def _page_key(value: str) -> str:
    return str(value or "").split("#", 1)[0].lstrip("./").strip("/") or "index.html"

def _headings(page: dict) -> list[str]:
    d = page.get("headings") or {}
    result = []
    for k in ("h2", "h3"):
        for value in d.get(k) or []:
            label = " ".join(str(value).split()).strip()
            if 3 <= len(label) <= 160 and label not in result:
                result.append(label)
    return result[:32]

def source_manifest(research: dict) -> dict:
    """Produce a mandatory content and partner checklist from every source page."""
    inventory = research.get("source_inventory") or {}
    pages = [p for p in inventory.get("pages") or [] if isinstance(p, dict) and p.get("url")]
    assets, known = [], set()
    footer_links, known_links = [], set()
    for page in pages:
        for placement, key in (("brand", "header_assets"), ("affiliation", "footer_assets")):
            for a in page.get(key) or []:
                if not isinstance(a, dict) or not a.get("src"):
                    continue
                source = _url(a["src"],page["url"])
                href = _url(a.get("href") or "",page["url"]) if a.get("href") else ""
                item_key=(placement,source,href)
                if source and item_key not in known:
                    known.add(item_key)
                    assets.append({
                        "placement":placement, "original_src":source,
                        "original_href":href, "alt":str(a.get("alt") or "")[:180],
                        "role":"unverified" if placement=="affiliation" else "brand_candidate",
                        "source_url":page["url"],
                    })
        # Preserve external text/link affiliations and social links as well
        # as graphic marks; old brands can be text-only links.
        for link in page.get("footer_links") or []:
            if not isinstance(link,dict) or not link.get("href"):
                continue
            href=_url(link["href"],page["url"])
            host=urlsplit(page["url"]).hostname or ""
            if (not href or href.split("/",1)[0]==host.lower().removeprefix("www.")
                or href in known_links):
                continue
            known_links.add(href)
            footer_links.append({"href":href,"text":str(link.get("text") or "")[:150],
                                 "source_url":page["url"],"role":"unverified"})
    return {
        "source_sha256": source_inventory_sha256(inventory),
        "pages":[{"source_url":p["url"],"title":str(p.get("title") or "")[:180],
                  "headings":_headings(p),
                  "source_text_excerpt":str(p.get("text") or "")[:750],
                  "link_count":len(p.get("links") or []),
                  "asset_count":len(p.get("images") or []),
                  "source_text_truncated":len(str(p.get("text") or ""))>=6400}
                 for p in pages],
        "assets":assets,
        "footer_links":footer_links,
        "source_page_count":len(pages),
        "note":"Source-grounded coverage checklist; not proof of equivalence, rights or visual quality.",
    }

def _is_exact_human_approval(approval: object, *, source_sha: str,
                             build_sha: str = "") -> bool:
    return bool(
        isinstance(approval, dict)
        and approval.get("approved") is True
        and approval.get("reviewer_kind") == "human"
        and str(approval.get("reviewer") or "").strip()
        and str(approval.get("checked_at") or "").strip()
        and approval.get("source_sha256") == source_sha
        and (not build_sha or approval.get("build_sha256") == build_sha)
    )

def validate_source_plan(research: dict, *, source_url: str = "") -> dict:
    """Fail BEFORE a Builder API request if source pages/topics have no map.

    This is intentionally a completeness check, not a fake semantic judgment.
    """
    manifest=source_manifest(research)
    if not manifest["pages"]:
        if source_url and research.get("research_mode")!="verified_no_website":
            raise RuntimeError("Missing original-site inventory before Builder.")
        return {"pages":0,"topics":0}
    plan=research.get("source_content_map") or {}
    entries={str(item.get("source_url") or ""):item for item in plan.get("pages") or []
             if isinstance(item,dict)}
    problems=[]
    topics=0
    for page in manifest["pages"]:
        record=entries.get(page["source_url"])
        if not record or record.get("status") not in ("retain","merge"):
            problems.append(page["source_url"]+": source page not mapped for preservation")
            continue
        dest=str(record.get("target") or "")
        if not dest or dest.startswith(("http:","https:")):
            problems.append(page["source_url"]+": missing local destination")
        mapped={_s(x.get("source_heading")) for x in record.get("sections") or []
                if isinstance(x,dict) and x.get("target")}
        for heading in page["headings"]:
            topics+=1
            if _s(heading) not in mapped:
                problems.append(page["source_url"]+": unmapped source section "+heading)
    if problems:
        raise RuntimeError("Original-site preservation plan incomplete before paid Builder: "+
                           "; ".join(problems[:12]))
    return {"pages":len(manifest["pages"]),"topics":topics,
            "source_sha256":manifest["source_sha256"]}


def audit_source_fidelity(
    html: str, research: dict, *, source_url: str = "",
    rendered_pages: dict[str,str] | None = None,
    require_human_review: bool = True,
) -> dict:
    """Inspect preserved source pages, sections, brand/affiliation images and task links.

    A website-less verified profile has no fabricated old-site inventory.
    Each asset is checked for BOTH image and original destination on the
    rendered site (or source-exact replacement mapping). Omission requires
    explicit source-specific owner approval, not a blanket AI decision.
    """
    manifest=source_manifest(research)
    original_pages=manifest["pages"]
    if not original_pages and not source_url:
        return {"pass":True,"missing":[],"pending":[],"manifest":manifest,
                "checked":0,"old_site_handoffs":[]}
    missing,pending=[],[]
    if not original_pages:
        pending.append("Original business website has no source inventory; cannot certify redesign.")
        return {"pass":False,"missing":missing,"pending":pending,
                "manifest":manifest,"checked":0,"old_site_handoffs":[]}

    pages={"index.html":html}
    if isinstance(rendered_pages,dict):
        pages.update({_page_key(k):str(v) for k,v in rendered_pages.items() if isinstance(v,str)})
    soup_pages={p:BeautifulSoup(raw,"html.parser") for p,raw in pages.items()}
    source_sha=manifest["source_sha256"]
    digest=sha256("".join(k+"\n"+pages[k] for k in sorted(pages)).encode("utf-8")).hexdigest()
    content_plan=research.get("source_content_map") or {}
    plan_pages=content_plan.get("pages") or []
    by_source={str(p.get("source_url") or ""):p for p in plan_pages if isinstance(p,dict)}
    checked=0
    for original in original_pages:
        src_url=original["source_url"]
        mapping=by_source.get(src_url)
        checked+=1
        if not mapping:
            missing.append({"kind":"source_page","source":src_url,
                            "issue":"Original page missing from new-site content migration map"})
            continue
        destination=str(mapping.get("target") or "").strip()
        status=str(mapping.get("status") or "")
        if status=="remove":
            waiver=mapping.get("removal_approval")
            if not (isinstance(waiver,dict) and waiver.get("reviewer_kind")=="client"
                    and waiver.get("source_sha256")==source_sha
                    and str(waiver.get("reason") or "").strip()
                    and str(waiver.get("reviewer") or "").strip()):
                missing.append({"kind":"unauthorized_page_removal","source":src_url,
                                "issue":"Removing an original page requires source-bound customer approval"})
            continue
        if status not in ("retain","merge"):
            missing.append({"kind":"unclassified_page","source":src_url,
                            "issue":"Page must be retained, merged, or explicitly owner-approved for removal"})
        target=_page_key(destination)
        if not destination or target not in soup_pages:
            missing.append({"kind":"unavailable_new_page","source":src_url,
                            "target":destination,"issue":"Mapped content does not exist in rendered build"})
            continue
        soup=soup_pages[target]
        if "#" in destination and not soup.find(id=destination.split("#",1)[1]):
            missing.append({"kind":"unavailable_new_section","source":src_url,
                            "target":destination})
        # Every observed meaningful heading must be explicitly represented in
        # the mapping, with a real target anchor. Similar words ≠ semantic proof.
        topics=mapping.get("sections") or []
        by_heading={_s(t.get("source_heading")):t for t in topics if isinstance(t,dict)}
        for heading in original["headings"]:
            t=by_heading.get(_s(heading))
            checked+=1
            if not t:
                missing.append({"kind":"omitted_source_topic","source":src_url,
                                "heading":heading})
                continue
            dest=str(t.get("target") or destination)
            page_key=_page_key(dest)
            if page_key not in soup_pages or ("#" in dest and
                    not soup_pages.get(page_key).find(id=dest.split("#",1)[1])):
                missing.append({"kind":"unverifiable_topic_destination",
                                "source":src_url,"heading":heading,"target":dest})
        if original["source_text_truncated"]:
            pending.append(f"Original page text was truncated during source capture: {src_url}")

    # A large site reduced to a tiny brochure is NOT content preservation.
    # Word-count cannot certify meaning and source navigation can inflate it,
    # so use only a conservative severe-shrinkage guard plus human evidence.
    originals=[p for p in (research.get("source_inventory") or {}).get("pages") or []
               if isinstance(p,dict)]
    original_words=sum(len(str(p.get("text") or "").split()) for p in originals)
    new_words=sum(len(soup.get_text(" ",strip=True).split()) for soup in soup_pages.values())
    if original_words>=650 and new_words<0.38*original_words:
        signoff=research.get("approved_content_condensation") or {}
        accepted=bool(isinstance(signoff,dict)
                      and signoff.get("reviewer_kind")=="client"
                      and str(signoff.get("reviewer") or "").strip()
                      and str(signoff.get("reason") or "").strip()
                      and signoff.get("source_sha256")==source_sha
                      and signoff.get("build_sha256")==digest)
        if not accepted:
            missing.append({
                "kind":"suspicious_content_collapse",
                "old_word_count":original_words,
                "new_word_count":new_words,
                "issue":"Large reduction in useful text must be independently checked and specifically client-approved; not proof of automatic failure."
            })

    # The image and its link must remain together. A separately printed name
    # cannot silently stand in for the old partner/brand mark.
    mapping_entries=research.get("approved_asset_replacements") or []
    aliases={}
    for entry in mapping_entries:
        if not isinstance(entry,dict):
            continue
        src=_url(entry.get("original_src") or "",entry.get("source_url") or "")
        if src and entry.get("source_sha256")==source_sha:
            aliases[src]=entry

    removals=research.get("approved_asset_removals") or []
    for asset in manifest["assets"]:
        checked+=1
        src=asset["original_src"]
        excluded=any(
            isinstance(item,dict) and _url(item.get("original_src") or "",item.get("source_url") or "")==src
            and item.get("source_sha256")==source_sha
            and item.get("reviewer_kind")=="client"
            and str(item.get("reviewer") or "").strip()
            and str(item.get("reason") or "").strip()
            for item in removals
        )
        if excluded:
            continue
        mapped=aliases.get(src) or {}
        target_image=str(mapped.get("replacement_src") or "")
        original_dest=asset["original_href"]
        corrected_dest=_url(mapped.get("updated_href") or "") if mapped.get("updated_href") else ""
        found=False
        for _,soup in soup_pages.items():
            for img in soup.find_all("img",src=True):
                link=img.find_parent("a",href=True)
                image_raw=str(img["src"])
                if img["src"] == src or _url(img["src"],asset["source_url"]) == src or (target_image and image_raw==target_image):
                    # A mark originally linked out must retain the equivalent
                    # exact link (unless source-verified updated mapping).
                    if not original_dest or (link and _url(link.get("href","")) in
                                             {original_dest,corrected_dest}):
                        found=True
                        break
            if found:break
        if not found:
            missing.append({"kind":"missing_original_"+asset["placement"]+"_image",
                            "source":asset["source_url"],"original_src":src,
                            "original_href":original_dest,
                            "issue":"Original mark and linked destination must survive or have owner-approved removal"})
        if asset["placement"]=="affiliation":
            # The frame alone proves only that a graphic was on the old site.
            # Verified role and lawful reuse require a source-specific client
            # record, not a generic approval boolean.
            reviewed=any(
                isinstance(item,dict)
                and _url(item.get("original_src") or "",item.get("source_url") or "")==src
                and item.get("source_sha256")==source_sha
                and item.get("reviewer_kind")=="client"
                and str(item.get("reviewer") or "").strip()
                and str(item.get("relationship_role") or "").strip()
                and item.get("reuse_authorized") is True
                for item in research.get("affiliation_reviews") or []
            )
            if not reviewed:
                pending.append("Affiliation role and logo reproduction permission need confirmation: "+src)

    rendered_href_urls={
        _url(a.get("href") or "")
        for soup in soup_pages.values()
        for a in soup.find_all("a",href=True)
    }
    for link in manifest["footer_links"]:
        checked+=1
        href=link["href"]
        if href in rendered_href_urls:
            continue
        excepted=any(
            isinstance(row,dict)
            and row.get("kind")=="footer_link"
            and _url(row.get("original_href") or "")==href
            and row.get("source_sha256")==source_sha
            and row.get("reviewer_kind")=="client"
            and str(row.get("reason") or "").strip()
            and str(row.get("reviewer") or "").strip()
            for row in research.get("approved_asset_removals") or []
        )
        if not excepted:
            missing.append({"kind":"missing_original_footer_link",
                            "source":link["source_url"],"href":href,
                            "issue":"Original linked partner/social mark must remain or have owner-approved removal"})

    original_host=urlsplit(source_url or original_pages[0]["source_url"]).hostname or ""
    original_host=original_host.lower().removeprefix("www.")
    handoffs=[]
    for path,soup in soup_pages.items():
        for a in soup.find_all("a",href=True):
            raw=str(a.get("href") or "").strip()
            parsed=urlsplit(raw)
            if (parsed.hostname or "").lower().removeprefix("www.")!=original_host:
                continue
            hint=_s(a.get_text(" ",strip=True)+" "+parsed.path)
            if not any(word in hint for word in TASK_WORDS):
                continue
            if any(word in hint for word in EXTERNAL_PROCESS_WORDS):
                continue
            integration=any(
                isinstance(item,dict) and _url(item.get("url") or "")==_url(raw)
                and item.get("source_sha256")==source_sha
                and str(item.get("reason") or "").strip()
                and item.get("reviewer_kind")=="human"
                for item in research.get("approved_external_integrations") or []
            )
            if not integration:
                handoffs.append({"page":path,"text":a.get_text(" ",strip=True)[:100],
                                 "old_site_url":raw})
    if handoffs:
        missing.extend({"kind":"old_site_primary_task_handoff",**h} for h in handoffs)

    if require_human_review and not _is_exact_human_approval(
        research.get("source_fidelity_review"),source_sha=source_sha,build_sha=digest
    ):
        pending.append("Exact source-and-build-bound human review of page coverage and preserved content required.")
    return {"pass":not missing and not pending,
            "missing":missing,"pending":list(dict.fromkeys(pending)),
            "manifest":manifest,"checked":checked,"old_site_handoffs":handoffs,
            "source_sha256":source_sha,"build_sha256":digest,
            "note":"Coverage and DOM checks are evidence, not semantic fidelity or licensing proof."}
