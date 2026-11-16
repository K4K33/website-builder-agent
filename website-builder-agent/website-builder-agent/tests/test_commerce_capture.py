import unittest
from unittest.mock import patch

from utils.commerce_capture import _capture_shopify
from utils.commerce_catalogue import bind_commerce_architecture, attach_commerce_catalogue
from utils.commerce_parity import commerce_problems


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


if __name__ == "__main__": unittest.main()
