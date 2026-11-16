import unittest
from unittest.mock import patch

from utils.commerce_capture import _capture_shopify
from utils.commerce_catalogue import bind_commerce_architecture, attach_commerce_catalogue
from utils.commerce_parity import commerce_problems
from utils.site_architecture import bind_source_routes, validate_site_architecture


class Reply:
    status_code = 200
    url = "https://shop.example/products.json?limit=250&page=1"
    def __init__(self, products): self._products = products
    def json(self): return {"products": self._products}


class CommerceCaptureTests(unittest.TestCase):
    @patch("utils.commerce_capture.requests.Session.get")
    def test_shopify_catalogue_is_complete_and_materialized(self, get):
        get.return_value = Reply([{
            "handle": "kitara", "title": "Aito kitara",
            "variants": [{"price": "99.90"}], "images": []
        }])
        capture = _capture_shopify("https://shop.example")
        self.assertTrue(capture["complete"])
        research = {"commerce_inventory": [capture], "site_architecture": {"pages": [
            {"path": "index.html", "purpose": "Etusivun yritysesittely asiakkaalle",
             "user_task": "Asiakas löytää yrityksen tärkeimmät palvelut", "section_ids": ["hero"]}
        ]}}
        bind_commerce_architecture(research)
        target = capture["target"]
        pages = {"index.html": '<!doctype html><html><body><main><h1>Etusivu</h1><a href="verkkokauppa.html">Kauppa</a><section id="hero"></section></main></body></html>',
                 target: '<!doctype html><html><body><main><h1>Kauppa</h1></main></body></html>'}
        pages, artifacts = attach_commerce_catalogue(pages, research)
        self.assertEqual(commerce_problems({**research, "source_inventory": {"pages": [],}}, pages), [])
        self.assertIn("Aito kitara", next(iter(artifacts.values())))

    def test_architecture_reuses_existing_shop_route(self):
        r = {"commerce_inventory": [{"products": [], "target": "old"}], "site_architecture": {"pages": [
            {"path": "index.html", "section_ids": ["hero"]},
            {"path": "shop.html", "section_ids": ["intro"]},
        ]}}
        bind_commerce_architecture(r)
        self.assertEqual(r["commerce_inventory"][0]["target"], "shop.html")
        self.assertIn("kauppa-valikoima", r["site_architecture"]["pages"][1]["section_ids"])

    def test_source_map_destinations_become_real_routes_and_sections(self):
        r = {"source_inventory": {"pages": [{"url": "https://example.fi/palvelut", "text": "sana " * 700}]},
             "source_content_map": {"pages": [{"source_url": "https://example.fi/palvelut",
                 "status": "retain", "target": "palvelut.html#palvelut",
                 "sections": [{"source_heading": "Huolto", "target": "palvelut.html#huolto"}]}]},
             "site_architecture": {"pages": [{"path": "index.html",
                 "purpose": "Yrityksen etusivu ja tärkeimmät tiedot",
                 "user_task": "Asiakas löytää yrityksen pääpalvelut etusivulta",
                 "section_ids": ["hero"]}]}}
        bind_source_routes(r)
        result = validate_site_architecture(r)
        self.assertEqual(result["page_paths"], ["index.html", "palvelut.html"])
        self.assertEqual(r["site_architecture"]["pages"][1]["section_ids"], ["huolto", "palvelut"])

    def test_source_map_repair_is_deterministic_without_ai(self):
        from agents.research import _repair_source_map
        r = {"source_inventory": {"pages": [{
                "url": "https://example.fi/huolto", "title": "Huolto",
                "headings": {"h2": ["Kitarahuolto"], "h3": ["Hinnasto"]},
                "text": "Kitarahuolto Hinnasto", "links": [], "images": []}]},
             "source_content_map": {"pages": []},
             "site_architecture": {"pages": [{"path": "index.html",
                 "purpose": "Yrityksen etusivu ja tärkeimmät tiedot",
                 "user_task": "Asiakas löytää yrityksen tärkeimmät palvelut",
                 "section_ids": ["hero"]}, {"path": "huolto.html",
                 "purpose": "Soitinten huollon palvelut ja hinnat",
                 "user_task": "Asiakas tutkii huoltopalvelut ja hinnaston",
                 "section_ids": ["huolto"]}]}}
        _repair_source_map(r, "https://example.fi")
        row = r["source_content_map"]["pages"][0]
        self.assertEqual(row["target"], "huolto.html")
        self.assertEqual([x["source_heading"] for x in row["sections"]],
                         ["Kitarahuolto", "Hinnasto"])
        self.assertTrue(all(x["target"].startswith("huolto.html#source-")
                            for x in row["sections"]))


if __name__ == "__main__": unittest.main()
