import io
from pathlib import Path

import pytest

from utils.pre_build_brief import (
    PROTOCOL, derive_pre_build_brief, ensure_pre_build_brief, validate_pre_build_brief,
)

ROOT = Path(__file__).resolve().parents[1]


def research(images=(), links=(), refs=2, journeys=True, contact=True, name="Esimerkki Oy"):
    return {
        "company_facts": {"name": name, "services": ["Rivitalot"],
                          "contact": {"phone": "010 123 4567" if contact else "",
                                      "email": "", "address": ""}},
        "primary_offering_evidence": {"quote": "Rakennamme rivitaloja puusta."},
        "source_inventory": {"pages": [{
            "url": "https://example.fi/",
            "images": [{"src": s, "alt": ""} for s in images],
            "links": [{"href": h, "text": ""} for h in links],
        }]},
        "creative_directions": [{"id": "a", "concept": "Rauhallinen puu",
                                 "first_view": "Elementti nousee paikalleen",
                                 "business_reason": "Asiakas näkee rakentamistavan",
                                 "typography": "Kapea groteski"}],
        "creative_selection": {"selected_id": "a"},
        "reference_comparison": [{"url": f"https://ref{i}.fi/"} for i in range(refs)],
        "primary_user_journeys": ([{"kind": "phone", "destination": "tel:+3581012345",
                                    "label": "Soita", "source_url": "https://example.fi/"}]
                                  if journeys else []),
    }


def test_all_six_questions_answered():
    brief = derive_pre_build_brief(research(images=["/a.jpg", "/b.jpg", "/c.jpg"]))
    assert brief["protocol"] == PROTOCOL and brief["gaps"] == []
    for key in ("q1_signature_moment", "q2_assets", "q3_brand_feel",
                "q4_primary_action", "q5_performance", "q6_verified_facts"):
        assert brief[key]
    assert brief["q1_signature_moment"]["moment"] == "Elementti nousee paikalleen"
    assert brief["q4_primary_action"]["href"] == "tel:+3581012345"
    assert brief["q6_verified_facts"]["primary_offering_quote"]
    assert brief["q2_assets"]["generation_allowed"] is False


@pytest.mark.parametrize("images,links,technique", [
    ((), (), "typographic_statement"),
    (("/hero.jpg",), (), "cinematic_photo_scroll"),
    (("/1.jpg", "/2.webp", "/3.png"), (), "photo_sequence_scrub"),
    (("/1.jpg",), ("/esittely.mp4",), "video_scrub"),
    (("/1.jpg",), ("/tuote.glb",), "product_3d"),
    (("/logo.png", "/icon-phone.png", "/facebook.jpg"), (), "typographic_statement"),
])
def test_technique_follows_real_material(images, links, technique):
    brief = derive_pre_build_brief(research(images=images, links=links))
    assert brief["q1_signature_moment"]["technique"] == technique


def test_procedural_3d_is_forbidden_in_every_brief():
    brief = derive_pre_build_brief(research())
    assert any("procedural" in rule for rule in brief["q1_signature_moment"]["forbidden"])


def test_staged_media_decides_usable_technique():
    data = research(images=["/1.jpg", "/2.jpg", "/3.jpg"])
    assert derive_pre_build_brief(data, staged_media=[])["q1_signature_moment"]["technique"] \
        == "typographic_statement"
    staged = [{"src": "assets/a.jpg"}]
    assert derive_pre_build_brief(data, staged_media=staged)["q1_signature_moment"]["technique"] \
        == "cinematic_photo_scroll"


@pytest.mark.parametrize("kwargs,gap", [
    ({"refs": 1}, "q3_brand_feel"),
    ({"journeys": False, "contact": False}, "q4_primary_action"),
    ({"name": ""}, "q6_verified_facts"),
])
def test_gaps_block_before_any_page_is_authored(kwargs, gap):
    data = research(**kwargs)
    with pytest.raises(RuntimeError, match="PRE_BUILD_BRIEF_INCOMPLETE: .*" + gap):
        ensure_pre_build_brief(data)
    assert gap in data["pre_build_brief"]["gaps"]


def test_phone_from_facts_when_no_journey():
    brief = derive_pre_build_brief(research(journeys=False))
    assert brief["q4_primary_action"]["href"] == "tel:0101234567"


def test_missing_brief_is_rejected():
    with pytest.raises(RuntimeError, match="missing"):
        validate_pre_build_brief({})


def test_pipeline_wiring():
    research_src = (ROOT / "agents/research.py").read_text(encoding="utf-8")
    assert research_src.count('research_data["pre_build_brief"] = derive_pre_build_brief') == 2
    concept_src = (ROOT / "utils/concept_workflow.py").read_text(encoding="utf-8")
    assert "ensure_pre_build_brief(research, media)" in concept_src
    builder_src = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
    assert builder_src.count("ensure_pre_build_brief(research, media_manifest)") == 2


def test_queue_classifies_and_explains_gap():
    from scripts.run_kaurivo_demo_queue import classify_stage_failure
    log = io.StringIO("Traceback\nRuntimeError: PRE_BUILD_BRIEF_INCOMPLETE: q4_primary_action\n")
    assert classify_stage_failure(log, "concepting") == "pre_build_brief_incomplete"
