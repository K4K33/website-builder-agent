"""Blind-sector, zero-network gates: creativity, real routes and AI pattern risk."""
from __future__ import annotations
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.creative_directions import validate_creative_directions
from utils.site_architecture import (
    validate_site_architecture,parse_generated_site,validate_site_navigation
)
from utils.visual_originality import audit_design_originality
from utils.site_build_pipeline import build_pages_from_response
from agents.qa import ai_style_review_passes


def creative():
    directions=[]
    for i,data in enumerate([
      ("Photo-led service review with calm authentic workshop portrait",
       "Individual product detail routes and easy quote comparison",
       "Horizontal clear navigation with product categories",
       "Full-size original process photography with detailed captions"),
      ("Typographic editorial orientation with information-first hero",
       "Question-led sections and searchable service categories",
       "Contextual short index anchored to visitor decisions",
       "Sparse project-detail documentation images with annotations"),
      ("Dense visual proof board with projects in the first viewport",
       "Portfolio-first case-study sequence and linked details",
       "Grid-based filter and direct reference navigation",
       "Paired original evidence shots with descriptive task labels")
    ],1):
        first,ia,nav,images=data
        directions.append({
          "id":f"concept_{i}","concept":"Company-specific business approach "+str(i),
          "business_reason":"Customer needs to identify credible services, products and answers in a practical way",
          "source_anchor":"Verified original business research and real archived customer work",
          "first_view":first,"information_architecture":ia,
          "navigation":nav,"image_strategy":images,
          "typography":"Distinctive readable company identity using client-approved fonts",
          "brand_continuity":"Preserve the original logo and company-approved colours",
          "non_goals":"Avoid decorative circles and generic luxury landing page patterns",
          "mobile_behavior":"Small screens prioritize visitor tasks and credible media without broken layouts"
        })
    return {"creative_directions":directions,
            "creative_selection":{"selected_id":"concept_2",
                "business_reason":"This customer's dense service information is better read through question-led hierarchy than imagery-only editorial alternatives",
                "rejected_ids":["concept_1","concept_3"]}}


def page(title,section,nav, copy="Real verified service"):
    return ('<!doctype html><html lang="fi"><head><title>'+title+'</title>'
      '<meta name="viewport" content="width=device-width,initial-scale=1">'
      '<meta name="description" content="Original workshop service facts"></head>'
      '<body><header><nav>'+nav+'</nav></header><main><section id="'+section+'">'
      '<h1>'+title+'</h1><p>'+copy+'</p></section></main><footer>Service studio</footer>'
      '</body></html>')


class CreativeMultipageTests(unittest.TestCase):
    def test_three_substantive_directions_required(self):
        research=creative()
        self.assertEqual(validate_creative_directions(research)["selected"]["id"],"concept_2")
        research["creative_directions"][2]["first_view"]=research["creative_directions"][0]["first_view"]
        research["creative_directions"][2]["information_architecture"]=research["creative_directions"][0]["information_architecture"]
        research["creative_directions"][2]["navigation"]=research["creative_directions"][0]["navigation"]
        with self.assertRaisesRegex(RuntimeError,"differ mostly"):
            validate_creative_directions(research)

    def test_real_multipage_required_when_original_is_content_rich(self):
        research={
          "source_inventory":{"pages":[
            {"url":"https://studio.example.fi/","text":"Full company facts"},
            {"url":"https://studio.example.fi/services","text":"Service list"},
            {"url":"https://studio.example.fi/products","text":"Product selection"}]},
          "source_content_map":{"pages":[
            {"source_url":"https://studio.example.fi/","target":"index.html#hero","sections":[]},
            {"source_url":"https://studio.example.fi/services","target":"palvelut/index.html#services","sections":[]},
            {"source_url":"https://studio.example.fi/products","target":"palvelut/index.html#services","sections":[]}]},
          "site_architecture":{"pages":[
            {"path":"index.html","purpose":"Explain the service to customers","user_task":"Find verified company details","section_ids":["hero"]},
            {"path":"palvelut/index.html","purpose":"Browse actual products and services","user_task":"Compare repair and sales options","section_ids":["services"]}]}}
        self.assertEqual(validate_site_architecture(research)["minimum_page_count"],2)
        research["site_architecture"]["pages"].pop()
        with self.assertRaisesRegex(RuntimeError,"brochure"):
            validate_site_architecture(research)

    def test_bundle_rejects_traversal_and_missing_routes(self):
        architecture={"page_paths":["index.html","palvelut/index.html"]}
        with self.assertRaisesRegex(RuntimeError,"single index|multi-page"):
            parse_generated_site(page("A","hero","Home"),architecture)
        with self.assertRaisesRegex(RuntimeError,"exactly"):
            parse_generated_site(json.dumps({"pages":{"index.html":page("A","hero","Home")}}),architecture)
        with self.assertRaisesRegex(RuntimeError,"Invalid|unsafe|Route"):
            parse_generated_site(json.dumps({"pages":{"index.html":page("A","hero","Home"),
                              "../private.html":page("B","services","Home")}}),architecture)

    def test_only_genuine_connected_routes_pass(self):
        architecture={"page_paths":["index.html","palvelut/index.html"],
                       "pages":[{"path":"index.html","section_ids":["hero"]},
                                {"path":"palvelut/index.html","section_ids":["services"]}]}
        pages={
          "index.html":page("Workshop","hero",'<a href="palvelut/index.html">Services</a>'),
          "palvelut/index.html":page("All services","services",'<a href="../index.html">Home</a>'),
        }
        self.assertTrue(validate_site_navigation(pages,architecture)["pass"])
        pages["index.html"]=pages["index.html"].replace('palvelut/index.html','missing.html')
        self.assertFalse(validate_site_navigation(pages,architecture)["pass"])

    def test_originality_catches_repeated_layout_and_generic_contrasts(self):
        sections=lambda x: '<main>'+''.join(
          '<section><div><h2>Studio '+x+'</h2></div><figure><img src="data:image/png;base64,AA" alt="Item"></figure></section>'
          for _ in range(5))+'</main>'
        first=sections("A")
        second=sections("B")
        result=audit_design_originality(first,site_slug="new",
              additional_sites={"existing-client":second})
        self.assertFalse(result["pass"])
        self.assertTrue(result["similar_sites"])
        copy=audit_design_originality(
          '<main><p>Vähemmän säätöä enemmän aikaa. Ei vain huoltoa vaan ratkaisu.</p></main>',
          site_slug="copy")
        self.assertFalse(copy["pass"])

    def test_ai_pattern_qa_score_requires_evidence_not_model_self_praise(self):
        base={"ai_style_review":{"risk_score":1.5,
             "evidence":["Actual original logo and brand colours preserved",
                         "Reference projects featured before generic marketing text"],
             "company_authenticity":"Business-specific products and authentic company language are visible.",
             "prior_patterns_compared":["Previously built garage","Prior florist concept"],
             "unresolved":[]}}
        self.assertTrue(ai_style_review_passes(base))
        self.assertTrue(ai_style_review_passes(base,available_patterns=[
            {"site":"Previously built garage"},{"site":"Prior florist concept"}]))
        self.assertFalse(ai_style_review_passes(base,available_patterns=[
            {"site":"unrelated A"},{"site":"unrelated B"}]))
        base["ai_style_review"]["risk_score"]=4
        self.assertFalse(ai_style_review_passes(base))
        base["ai_style_review"]["risk_score"]=1
        base["ai_style_review"]["prior_patterns_compared"]=[]
        self.assertFalse(ai_style_review_passes(base))

    def test_real_multi_page_build_writes_all_routes_without_paid_api(self):
        research=creative()
        research.update({
            "research_mode":"verified_no_website",
            "source_inventory":{"pages":[]},
            "company_facts":{"name":"Independent Test Studio",
                             "industry":"Home services",
                             "services":["Verified restoration"]},
            "site_architecture":{"pages":[
              {"path":"index.html","purpose":"Show business to new clients","user_task":"Identify actual verified service","section_ids":["hero"]},
              {"path":"palvelut/index.html","purpose":"Describe each real service offering","user_task":"Understand the restoration process","section_ids":["services"]}]},
            "source_content_map":{"pages":[]}
        })
        company={"name":"Independent Test Studio","research":research}
        pages={
          "index.html":page("Original Studio","hero",'<a href="palvelut/index.html">Services</a>'),
          "palvelut/index.html":page("Restoration services","services",
                                     '<a href="../index.html">Home</a>'),
        }
        with TemporaryDirectory() as folder:
            from agents import builder
            with patch.object(builder,"_validate_plan_sections",return_value=None):
                result=build_pages_from_response(json.dumps({"pages":pages}),slug="brand-new",
                                                  company=company,output_root=folder)
            self.assertEqual(set(result["page_paths"]),set(pages))
            self.assertTrue((Path(folder)/"brand-new"/"palvelut"/"index.html").is_file())
            with self.assertRaisesRegex(RuntimeError,"route|pages|navigation"):
                with patch.object(builder,"_validate_plan_sections",return_value=None):
                    build_pages_from_response(
                        json.dumps({"pages":{"index.html":pages["index.html"]}}),
                        slug="bad-client",company=company,output_root=folder)
            self.assertFalse((Path(folder)/"bad-client"/"index.html").exists())

if __name__=="__main__":
    unittest.main()
