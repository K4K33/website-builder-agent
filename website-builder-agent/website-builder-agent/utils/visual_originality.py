"""Offline anti-template analysis using visible structure and editorial patterns.

No AI-detector claims: genre conventions, accessible navigation and a
left-text/right-photo hero alone are NOT grounds for rejecting a site.
Flag unusually repeated combinations across unrelated client companies,
and ground AI-copy concerns in specific excerpts, never an invented score.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
import re
from bs4 import BeautifulSoup

BAD_CLICHES=(
    r"vähemmän .{3,70} enemmän ",
    r"ei vain .{4,75} vaan ",
    r"enemmän kuin .{3,80}",
    r"not just .{4,80} but ",
    r"less .{3,70} more ",
)

def _structure(html: str) -> tuple:
    soup=BeautifulSoup(html,"html.parser")
    main=soup.find("main")
    if not main: return ()
    sections=main.find_all(["section","article"],recursive=False)
    if not sections:
        sections=main.find_all(["section","article"],limit=16)
    results=[]
    for sec in sections[:16]:
        direct=sec.find_all(recursive=False)
        image_count=len(sec.find_all(["img","picture","video"]))
        heads=[h.name for h in sec.find_all(["h1","h2","h3"],limit=4)]
        links=len(sec.find_all("a"))
        results.append((
            sec.name,
            "image" if image_count else "text",
            min(image_count,3),
            min(links,4),
            tuple(heads),
            tuple(t.name for t in direct[:4]),
        ))
    return tuple(results)

def _hero_type(html: str) -> str:
    soup=BeautifulSoup(html,"html.parser")
    main=soup.find("main")
    if not main: return "unknown"
    first=main.find(["section","article","div"],recursive=False)
    if first is None:return "none"
    blocks=first.find_all(recursive=False)
    parts=[]
    for el in blocks[:4]:
        img=el.find(["img","picture","video"]) is not None
        heading=el.find(["h1","h2","h3"]) is not None or el.name in ("h1","h2")
        parts.append("M" if img and not heading else "T" if heading else "X")
    return "".join(parts) or "single"

def _layout_similarity(first: str, second: str) -> float:
    from difflib import SequenceMatcher
    left,right=_structure(first),_structure(second)
    if min(len(left),len(right))<3:
        return 0.0
    return SequenceMatcher(None,left,right,autojunk=False).ratio()

def _cliche_evidence(html: str) -> list[str]:
    soup=BeautifulSoup(html,"html.parser")
    body=soup.find("main") or soup
    text=body.get_text(" ",strip=True)
    result=[]
    for p in BAD_CLICHES:
        for match in re.finditer(p,text,re.I):
            snippet=text[max(0,match.start()-25):match.end()+25]
            if snippet not in result:
                result.append(snippet[:150])
    return result[:8]

def _client_key(name: str) -> str:
    # One sample from each client, not Kotifixi v1..v15 inflation.
    return re.sub(r"-v\d+$","",name.casefold())

def _presentation_formula(html: str, css: str = "") -> dict:
    soup = BeautifulSoup(html, "html.parser")
    heading = soup.select_one("main h1")
    styles = " ".join(x.get_text() for x in soup.find_all("style")) + " " + css
    # A style hint requires actual CSS; serif-looking filenames are not proof.
    families = sorted(set(re.findall(r"font-family\s*:\s*([^;}]+)", styles, re.I)))
    return {"hero": _hero_type(html),
            "italic_heading": bool(heading and heading.find(["em", "i"])),
            "font_families": families[:12]}


def _linked_styles(html: str, folder: Path) -> str:
    pieces = []
    for link in BeautifulSoup(html, "html.parser").select('link[rel="stylesheet"][href]'):
        raw = str(link.get("href") or "")
        if raw.startswith(("/", "http:", "https:", "//")):
            continue
        file = (folder / raw.split("?", 1)[0]).resolve()
        if file.is_relative_to(folder.resolve()) and file.is_file() and file.stat().st_size < 500000:
            pieces.append(file.read_text(encoding="utf-8"))
    return "\n".join(pieces)


def audit_design_originality(
    html: str, *, site_slug: str,
    reference_demos: str | Path | None = None,
    additional_sites: dict[str,str] | None = None,
    stylesheet_text: str = "",
    additional_styles: dict[str,str] | None = None,
) -> dict:
    references=dict(additional_sites or {})
    styles=dict(additional_styles or {})
    if reference_demos:
        root=Path(reference_demos)
        if root.exists():
            current = root / site_slug / "index.html"
            if not stylesheet_text and current.is_file():
                stylesheet_text = _linked_styles(html, current.parent)
            grouped={}
            for p in sorted(root.glob("*/index.html")):
                group=_client_key(p.parent.name)
                if group==_client_key(site_slug) or p.parent.name==site_slug:
                    continue
                grouped[group]=p
            for group,p in list(grouped.items())[:60]:
                try:
                    other_html = p.read_text(encoding="utf-8")
                    references.setdefault(group, other_html)
                    styles.setdefault(group, _linked_styles(other_html, p.parent))
                except OSError:
                    pass
    reference_signatures=[]
    for name,other in list(references.items())[:24]:
        signature=_structure(other)
        if signature:
            reference_signatures.append({
                "site":name,"first_view_structure":_hero_type(other),
                "section_count":len(signature),
                "presentation_formula":_presentation_formula(other, styles.get(name, "")),
                "section_rhythm":[str(item[:4]) for item in signature[:6]],
                "formulaic_copy_examples":_cliche_evidence(other)[:2],
            })
    own_formula = _presentation_formula(html, stylesheet_text)
    formula_flags = []
    for name, other in references.items():
        if _client_key(name) == _client_key(site_slug):
            continue
        formula = _presentation_formula(other, styles.get(name, ""))
        if (own_formula["hero"] in ("TM", "MT")
            and own_formula["hero"] == formula["hero"]
            and own_formula["italic_heading"] and formula["italic_heading"]
            and own_formula["font_families"]
            and own_formula["font_families"] == formula["font_families"]):
            formula_flags.append({"kind":"repeated_presentation_formula", "other_site":name,
                                  "evidence":own_formula,
                                  "status":"requires_visual_comparison"})
    matches=[]
    for name,other in references.items():
        if name==site_slug: continue
        value=_layout_similarity(html,other)
        if value>=.68:
            matches.append({"other_site":name,"structural_similarity":round(value,3),
                            "hero_match":_hero_type(html)==_hero_type(other)})
    matches.sort(key=lambda x:x["structural_similarity"],reverse=True)
    close=[m for m in matches if m["structural_similarity"]>=.87 and m["hero_match"]]
    generic_copy=_cliche_evidence(html)
    problems=[]
    if close:
        problems.append(
            "Company website repeats the section composition and first-view approach of "
            "another customer; original art direction required. "
            + ", ".join(x["other_site"] for x in close[:3])
        )
    if len(generic_copy)>1:
        problems.append("Repeated generic contrast-pair sales copy; rewrite in natural company language.")
    warnings=[]
    if _hero_type(html)=="TM":
        warnings.append("Common text-left/media-right hero; justify this choice with business and content evidence.")
    if generic_copy:
        warnings.append("Review formulaic sales copy: "+"; ".join(generic_copy))
    if formula_flags:
        warnings.append("Repeated split hero, italic headline and CSS type choices across unrelated clients; inspect visual evidence.")
    return {"review_flags":formula_flags, "presentation_formula":own_formula,
            "pass":not problems,"blocking_problems":problems,
            "warnings":warnings,"similar_sites":matches[:8],
            "reference_signatures":reference_signatures[:16],
            "hero_composition":_hero_type(html),
            "generic_copy_examples":generic_copy,
            "note":"Heuristic duplication/copy check, NOT proof of human design or AI origin."}
