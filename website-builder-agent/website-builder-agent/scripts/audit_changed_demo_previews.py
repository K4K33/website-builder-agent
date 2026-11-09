"""Check every changed static demo through real universal QA before merge.

This catches hand-committed demos that skip Builder's preflight; passing
objective checks is NOT an independent premium quality score.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
# Executed as python scripts/..., so explicitly make the project package root importable.
sys.path.insert(0, str(ROOT))
from utils.universal_quality import audit_universal_standards
from utils.visual_originality import audit_design_originality
from utils.route_experience_contract import audit_route_experience
from utils.commerce_parity import commerce_problems
from utils.visual_direction import audit_visual_motion
from utils.brand_signature_plan import derive_brand_signature_plan
from utils.demo_origin_gate import verify_demo_concept_evidence
from bs4 import BeautifulSoup
DEMOS=ROOT/"docs"/"kaurivo"/"demos"
PREFIX="website-builder-agent/website-builder-agent/docs/kaurivo/demos/"

def changed_slugs(base,head):
    changed=subprocess.check_output(["git","diff","--name-only",base,head],cwd=ROOT,text=True).splitlines()
    return sorted({p[len(PREFIX):].split("/",1)[0] for p in changed
                   if p.startswith(PREFIX) and "/" in p[len(PREFIX):]
                   and not p[len(PREFIX):].startswith("_shared/")})

def verified_source_evidence(slug):
    """A static demo may not pass without ORIGINAL researched source evidence.

    This applies to every newly changed demo, including hand-coded/Codex
    output. A few unverified footer logos are not a source inventory.
    """
    import json
    from urllib.parse import urlsplit
    from utils.content_parity import source_inventory_sha256

    safe = slug.replace("-", "").replace("_", "")
    if not safe.isalnum() or not slug:
        raise ValueError("Invalid demo slug")
    manifest = ROOT / "data" / "demo_provenance" / (slug + ".json")
    if not manifest.is_file():
        raise ValueError(
            "Missing source-bound demo provenance. Run Research and commit a "
            "schema_version=2 original media/identity inventory before adding a demo.")
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schema_version") != 2 or data.get("stage") != "internal_demo":
        raise ValueError(
            "Legacy partial provenance is not acceptable for changed demos. "
            "A source-origin and browser media inventory are mandatory.")

    if data.get("research_mode") == "verified_no_website":
        independent = data.get("verified_no_website_company") or {}
        if (not str(independent.get("source_url") or "").startswith("https://")
            or not str(independent.get("checked_at") or "").strip()
            or not str(independent.get("business_name") or "").strip()):
            raise ValueError("No-website prospect must have verified real-business evidence.")
        return {"research_mode":"verified_no_website",
                "company_facts":{"name":independent["business_name"]}}

    inventory = data.get("source_inventory") or {}
    pages = inventory.get("pages") or []
    source_url = str(data.get("source_url") or "")
    source_host = (urlsplit(source_url).hostname or "").removeprefix("www.")
    if not source_url.startswith("https://") or not source_host or not pages:
        raise ValueError("Complete HTTPS original-site inventory required.")
    if len(pages) > 80:
        raise ValueError("Unbounded manifest exceeds source capture limit.")
    for page in pages:
        if not isinstance(page, dict):
            raise ValueError("Each original route requires a source observation.")
        observed_url = str(page.get("url") or "")
        host = (urlsplit(observed_url).hostname or "").removeprefix("www.")
        ident = page.get("source_identity")
        if (host != source_host or not observed_url.startswith("https://")
            or not isinstance(ident, dict)
            or "original_logo_candidates" not in ident
            or "original_content_photos" not in ident
            or not isinstance(ident.get("source_experience"), dict)):
            raise ValueError(
                "Original page is missing captured logo, photo-role or media signals: "
                + observed_url[:120])
    profile = data.get("original_experience_profile") or {}
    if (profile.get("source_sha256") != source_inventory_sha256(inventory)
        or profile.get("capture_method") not in ("browser", "human_browser_review")
        or profile.get("complete") is not True
        or not str(profile.get("checked_at") or "").strip()):
        raise ValueError("Source browser profile missing/incomplete/stale; cannot treat "
                         "unobserved original video, colors or textures as absent.")

    paired = data.get("source_comparison_evidence") or {}
    if (not str(paired.get("source_desktop") or "").strip()
        or not str(paired.get("source_mobile") or "").strip()
        or not str(paired.get("redesign_desktop") or "").strip()
        or not str(paired.get("redesign_mobile") or "").strip()):
        raise ValueError("Missing paired original/new desktop/mobile screenshot references. "
                         "These are only references; independent visual signoff remains pending.")

    return {
        "source_inventory": inventory,
        "original_experience_profile": profile,
        "source_comparison_evidence": paired,
        "commerce_inventory": data.get("commerce_inventory", []),
        "company_facts": data.get("company_facts", {}),
        **{key: data.get(key) for key in ("business_task_plan", "media_purpose_plan",
                                         "company_voice_brief", "service_quality_reviews",
                                         "fact_sources", "service_quality_protocol",
                                         "review_evidence_protocol", "visual_concepts_protocol",
                                         "creative_selection")},
    }

def main():
    base,head=os.environ.get("BASE_SHA",""),os.environ.get("HEAD_SHA","")
    if not base or not head:
        print("BLOCK: missing commit range for universal demo audit")
        return 2
    failed=False
    for slug in changed_slugs(base,head):
        folder=DEMOS/slug
        if not folder.is_dir():
            continue
        pages={str(p.relative_to(folder)):p.read_text(encoding="utf-8")
               for p in folder.rglob("index.html")}
        if "index.html" not in pages:
            print("BLOCK",slug,"missing index.html")
            failed=True
            continue
        css = "\n".join(f.read_text(encoding="utf-8") for f in folder.rglob("*.css"))
        js = "\n".join(f.read_text(encoding="utf-8") for f in folder.rglob("*.js"))
        remote_assets = any(
            str(tag.get("href") or tag.get("src") or "").startswith(("http:", "https:", "//"))
            for html in pages.values()
            for tag in BeautifulSoup(html, "html.parser").select(
                'link[rel~="stylesheet"][href],script[src]')
        )
        # Inspect the real committed style/JS assets. Remote dependencies make
        # completeness unprovable, so report them as pending, not safe.
        motion = audit_visual_motion(
            pages, css_text=css, js_text=js, assets_complete=not remote_assets)
        for problem in motion["blocking"]:
            print("BLOCK", slug, "inaccessible_visual_motion", problem)
            failed=True
        if motion["pending"]:
            print("VISUAL_REVIEW_PENDING", slug, "; ".join(motion["pending"][:3]))
        try:
            evidence=verified_source_evidence(slug)
            import json
            manifest=json.loads((ROOT / "data" / "demo_provenance" / (slug + ".json")).read_text(encoding="utf-8"))
            concepts=verify_demo_concept_evidence(slug, folder, manifest)
            print("RENDERED_CONCEPT_GATE_PASS", slug, concepts["screenshots"], "original rendered screenshots")
            # Source-approved and hand-authored demos share the same premium
            # anti-filler, original-form and original-signature rules. No
            # bypass by omitting a model-generated research protocol field.
            evidence["premium_visual_protocol"] = "v2"
            evidence["brand_signature_plan"] = derive_brand_signature_plan(evidence)
            for issue in commerce_problems(evidence, pages):
                print("BLOCK", slug, issue["kind"], issue["source"])
                failed=True
            # Hand-coded / external-agent demos used to bypass the entire
            # research-to-route Builder plan. Derive the visitor job from real
            # page paths, then enforce the SAME pre-write composition policy.
            evidence["site_architecture"]={"pages":[
                {"path":route,"purpose":"","user_task":""}
                for route in pages
            ]}
            composition=audit_route_experience(pages,evidence)
            if composition["blocking"]:
                failed=True
                for item in composition["blocking"][:12]:
                    print("BLOCK",slug,"route_composition",
                          str(item.get("kind")),"@",str(item.get("route") or item.get("issue")))
            result=audit_universal_standards(
                pages["index.html"], research=evidence,
                rendered_pages=pages, stage="internal_demo")
        except (ValueError, KeyError, TypeError, RuntimeError, OSError) as exc:
            print("BLOCK",slug,"source_evidence",str(exc))
            failed=True
            continue
        originality=audit_design_originality(
            pages["index.html"], site_slug=slug, reference_demos=DEMOS)
        if originality["blocking_problems"]:
            failed=True
            for issue in originality["blocking_problems"]:
                print("BLOCK",slug,"reused_template_or_copy",issue[:550])
        problems=result.get("blocking_problems") or {}
        if problems:
            failed=True
            for category,messages in sorted(problems.items()):
                print("BLOCK",slug,category,"; ".join(messages[:3])[:550])
        else:
            print("OBJECTIVE PASS",slug,len(pages),"routes; real visual/media and source review still required")
    return 1 if failed else 0

if __name__=="__main__":
    sys.exit(main())
