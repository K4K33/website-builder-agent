"""Regression: don't let valid HTML hide unsuitable route layout across brands.

These scenarios have zero network or AI/API calls. We do not claim that a
passing structural test is a good design or that original photos are licensed.
"""
from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest
from utils.route_experience_contract import (
    audit_route_experience, derive_route_experience_contract,
)


def research(photo_count=5):
    photos = [{"src":f"https://work.example/p{i}.jpg", "role":"gallery_photo"}
              for i in range(photo_count)]
    routes = [
        ("index.html","Welcome clients","Learn what the business provides"),
        ("catalog/index.html","Product catalogue","Browse original genuine products"),
        ("rental/index.html","Rent special clothes","View available outfit options"),
        ("contact/index.html","Get directions","Find our location and contact telephone"),
        ("services/index.html","Service enquiries","Understand how services work"),
    ]
    return {
        "company_facts":{"name":"Example Workshop","address":"Factory Street 2",
                         "phone":"+35840000123"},
        "source_inventory":{"pages":[{
            "url":"https://work.example/","source_identity":{
                "original_content_photos": photos,
                "original_logo_candidates":[],
            },
        }]},
        "site_architecture":{"pages":[
            {"path":path,"purpose":purpose,"user_task":task,
             "section_ids":["hero"]} for path,purpose,task in routes
        ]},
    }


def page(title, body="", *, image="", cta=""):
    img=f'<img src="{image}" alt="Real documented image">' if image else ""
    return (f"<!doctype html><html><body><header>Official logo</header>"
            f"<main><section id='hero'><h1>{title}</h1>{img}{body}</section>"
            f"<section><h2>{cta or title} specific details</h2></section>"
            f"</main></body></html>")


def good_pages():
    return {
        "index.html":page("Welcome",image="https://work.example/p0.jpg"),
        "catalog/index.html":page("See the goods",image="https://work.example/p1.jpg"),
        "rental/index.html":page("Dress rental",image="https://work.example/p2.jpg"),
        "contact/index.html":page("Visit us",body='<address>Factory Street 2</address>'),
        "services/index.html":page("Our services",body="<p>Real workshop service</p>"),
    }


class PurposeFirstRouteTests(TestCase):
    def test_contract_preflight_tells_generator_each_page_specific_job(self):
        contract=derive_route_experience_contract(research())
        roles={x["route"]:x["role"] for x in contract["routes"]}
        self.assertEqual(roles["catalog/index.html"],"collection")
        self.assertEqual(roles["rental/index.html"],"rental")
        self.assertEqual(roles["contact/index.html"],"contact")
        self.assertTrue(contract["photo_rich_source"])
        self.assertEqual(len(set(roles.values())),5)

    def test_real_source_photo_hints_are_distinct_and_role_based(self):
        data=research()
        photos=data["source_inventory"]["pages"][0]["source_identity"]["original_content_photos"]
        labels=("Vintage juhlamekko","Myymälän sisätilat","Työnäyte tuotteesta",
                "Henkilökuva","Korjaus työpajalla")
        for item,label in zip(photos,labels):
            item["alt"]=label
        contract=derive_route_experience_contract(data)
        hints={item["route"]:item["source_photo_hint"]
               for item in contract["routes"]}
        self.assertIn("juhlamekko",hints["rental/index.html"]["alt"])
        self.assertIn("sisätilat",hints["contact/index.html"]["alt"])
        self.assertIn("Työnäyte",hints["catalog/index.html"]["alt"])
        selected=[hint["src"] for hint in hints.values() if hint]
        self.assertEqual(len(selected),len(set(selected)))
        self.assertTrue(all(hint["licensed_for_public_use"] is False
                            for hint in hints.values() if hint))

    def test_repeated_identical_visitor_tasks_are_stopped_before_generation(self):
        from utils.site_architecture import validate_site_architecture
        data=research()
        data["site_architecture"]["pages"][2]["user_task"]=(
            data["site_architecture"]["pages"][1]["user_task"])
        with self.assertRaisesRegex(RuntimeError,
                                    "repeat the same visitor task"):
            validate_site_architecture(data)

    def test_legitimate_varied_route_first_sections_pass(self):
        r=audit_route_experience(good_pages(),research())
        self.assertEqual(r["blocking"],[],r)

    def test_catalogue_is_not_allowed_to_hide_products_under_giant_text_intro(self):
        pages=good_pages()
        pages["catalog/index.html"]=page("Our enchanting catalogue")
        problems=audit_route_experience(pages,research())["blocking"]
        self.assertIn("task_first_view_has_no_product_evidence",
                      {x["kind"] for x in problems})
        self.assertTrue(any(x.get("route")=="catalog/index.html" for x in problems))

    def test_large_logo_or_svg_icon_does_not_count_as_catalogue_product(self):
        pages=good_pages()
        pages["catalog/index.html"]=page(
            "Nice logo",image="https://work.example/brand-logo.svg")
        issues=audit_route_experience(pages,research())["blocking"]
        self.assertIn("task_first_view_has_no_product_evidence",
                      {x["kind"] for x in issues})

    def test_rental_page_requires_real_product_in_opening(self):
        pages=good_pages()
        pages["rental/index.html"]=page("Rent beautiful things",
                                        body="<p>Scroll down to see all dresses.</p>")
        issues=audit_route_experience(pages,research())["blocking"]
        self.assertIn("task_first_view_has_no_product_evidence",{x["kind"] for x in issues})

    def test_contact_page_cannot_delay_its_real_address_and_phone(self):
        pages=good_pages()
        pages["contact/index.html"]=page(
            "Find our beautiful showroom",
            body='<a href="services/index.html">Discover our services</a>')
        issues=audit_route_experience(pages,research())["blocking"]
        self.assertIn("contact_page_hides_verified_visit_details",
                      {x["kind"] for x in issues})

    def test_one_photo_three_routes_and_identical_cta_rejected(self):
        pages=good_pages()
        picture="https://work.example/p0.jpg"
        pages["catalog/index.html"]=page("Goods",image=picture,cta="Come see our lovely showroom")
        pages["rental/index.html"]=page("Clothes",image=picture,cta="Come see our lovely showroom")
        pages["index.html"]=page("Welcome",image=picture,cta="Come see our lovely showroom")
        result=audit_route_experience(pages,research())
        self.assertIn("recycled_business_photography",
                      {x["kind"] for x in result["blocking"]})
        self.assertIn("repeated_full_width_call_to_action_copy",
                      {x["kind"] for x in result["blocking"]})

    def test_sponsor_logos_and_icons_do_not_trigger_photo_rich_retail_rules(self):
        from utils.route_experience_contract import source_photo_count
        data=research(photo_count=0)
        data["source_inventory"]["pages"][0]["source_identity"]["original_content_photos"]=[
            {"src":"https://work.example/partner-logo.png",
             "alt":"Yhteistyökumppanin logo","role":"unclassified"},
            {"src":"https://work.example/brand-icon.svg",
             "alt":"Sivuston icon","role":"unclassified"},
            {"src":"https://work.example/logo2.jpg",
             "alt":"Sponsor logo","role":"unclassified"},
            {"src":"https://work.example/staff.jpg",
             "alt":"Real staff group photograph","role":"unclassified"},
        ]
        self.assertEqual(source_photo_count(data),1)
        self.assertFalse(derive_route_experience_contract(data)["photo_rich_source"])

    def test_image_poor_source_not_forced_to_invent_brand_photos(self):
        pages={p:page(p) for p in ("index.html","catalog/index.html",
                                   "rental/index.html","services/index.html")}
        result=audit_route_experience(pages,research(photo_count=0))
        self.assertFalse(result["blocking"],result)

    def test_exception_needs_genuine_exact_build_independent_evidence(self):
        pages=good_pages()
        pages["rental/index.html"]=page("No photo for this outfit")
        # Keep only TWO text-only first sections, so this test isolates
        # the source+build-specific exception rather than a second
        # independent cross-route monotony violation.
        pages["services/index.html"]=page(
            "Our services", image="https://work.example/p3.jpg")
        data=research()
        issue="product_media_missing_first_section:rental/index.html"
        data["route_composition_exceptions"]=[{
            "issue":issue,
            "source_sha256":source_inventory_sha256(data["source_inventory"]),
            "build_sha256":site_digest(pages),
            "approved":True,
            "reviewer_kind":"independent_human",
            "reviewer_id":"External visual reviewer",
            "screenshot_evidence":"review-2026-11-04/pair-390.png",
            "justification":"Business owner has withheld publishing permissions for this specific rental garment.",
        }]
        self.assertFalse(audit_route_experience(pages,data)["blocking"])
        pages["rental/index.html"]+=" "
        self.assertTrue(audit_route_experience(pages,data)["blocking"],
                        "An unrelated build cannot recycle exact-build approval")

    def test_existing_real_penny_lane_v1_cannot_pass_new_rules(self):
        root=Path(__file__).resolve().parents[1]
        demo=root/"docs"/"kaurivo"/"demos"/"penny-lane-vintage-v1"
        provenance=root/"data"/"demo_provenance"/"penny-lane-vintage-v1.json"
        if not demo.exists() or not provenance.exists():
            self.skipTest("Historic demo fixture not present")
        data=json.loads(provenance.read_text(encoding="utf-8"))
        pages={str(p.relative_to(demo)):p.read_text(encoding="utf-8")
               for p in demo.rglob("index.html")}
        data["site_architecture"]={"pages":[
            {"path":p,"purpose":"","user_task":""} for p in pages
        ]}
        result=audit_route_experience(pages,data)
        kinds={x["kind"] for x in result["blocking"]}
        self.assertIn("task_first_view_has_no_product_evidence",kinds)
        self.assertIn("recycled_business_photography",kinds)
        self.assertIn("repeated_text_only_subpage_openings",kinds)

    def test_generator_must_fail_before_writing_repeated_template(self):
        from utils.site_build_pipeline import build_pages_from_response
        pages=good_pages()
        pages["catalog/index.html"]=page("Wonderful things to find")
        company={"url":"https://work.example","research":research(),
                 "name":"Example Workshop"}
        fake={
            "automated_pass":True,
        }
        from contextlib import ExitStack
        with TemporaryDirectory() as directory, ExitStack() as patches:
            for mocked in (
                patch("utils.site_build_pipeline.validate_creative_directions"),
                patch("utils.site_build_pipeline.validate_site_navigation",
                      return_value={"pass":True,"issues":[]}),
                patch("agents.builder._validate_generated_content"),
                patch("agents.builder._validate_plan_sections"),
                patch("agents.qa._automated_checks",return_value=fake),
                patch("utils.site_build_pipeline.audit_visual_media",
                      return_value={"static_pass":True,"blockers":[]}),
                patch("utils.site_build_pipeline.validate_locked_copy"),
                patch("utils.site_build_pipeline.audit_content_parity",
                      return_value={"missing":[],"review_required":[]}),
                patch("utils.site_build_pipeline.audit_source_fidelity",
                      return_value={"missing":[]}),
                patch("utils.site_build_pipeline.audit_universal_standards",
                      return_value={"automated_pass":True}),
                patch("utils.site_build_pipeline.client_design_brief",
                      return_value={}),
            ):
                patches.enter_context(mocked)
            with self.assertRaisesRegex(RuntimeError,
                                        "Route-specific composition rejected"):
                build_pages_from_response(
                    json.dumps({"pages":pages}),slug="example-workshop",
                    company=company,output_root=directory)
            self.assertFalse((Path(directory)/"example-workshop").exists(),
                             "No failed generic design may touch output HTML")


if __name__=="__main__":
    import unittest
    unittest.main()
