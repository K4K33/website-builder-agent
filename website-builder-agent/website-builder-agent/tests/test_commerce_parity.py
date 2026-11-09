"""Catalogue loss must block both Builder and hand-coded demo publication."""
import copy
import unittest
from utils.commerce_parity import commerce_problems
from utils.source_fidelity import validate_source_plan


def fixture():
    product = {"name": "Blue bouquet", "price_text": "30,00 €",
               "image": "https://shop.example/image.jpg", "url": "https://shop.example/product/1"}
    research = {"source_inventory": {"pages": [{"url": "https://florist.example/",
                "links": [{"text": "Verkkokauppa", "href": "https://shop.example/"}]}]},
                "commerce_inventory": [{"shop_url": "https://shop.example/", "captured_at": "2026-11-04",
                "complete": True, "observed_product_count": 1, "target": "kauppa/index.html", "products": [product]}]}
    research['commerce_plan'] = {'protocol': 'commerce-v1', 'mode': 'preserve_existing',
        'backend_url': 'https://shop.example/', 'catalogue_strategy': 'Retain native catalogue/checkout',
        'inspection': {'inspected_urls': ['https://shop.example/'], 'catalogue_url': 'https://shop.example/',
            'captured_at': '2026-11-08', 'catalogue_inspected': True,
            'observed_product_count': 1, 'reason': 'Synthetic catalogue snapshot'}}
    pages = {"index.html": '<a href="kauppa/" data-shop-entry>Kauppa</a>',
             "kauppa/index.html": '<form data-shop-controls></form><article data-product-source="https://shop.example/product/1"><a href="https://shop.example/product/1"><img src="https://shop.example/image.jpg">Blue bouquet 30,00 €</a></article>'}
    return research, pages


class CommerceParityTests(unittest.TestCase):
    def test_captured_catalogue_and_real_product_links_pass(self):
        r, p = fixture()
        self.assertEqual(commerce_problems(r, p), [])

    def test_external_shop_link_alone_blocks_before_builder(self):
        r, p = fixture(); r.pop("commerce_inventory")
        with self.assertRaisesRegex(RuntimeError, "shop catalogue"):
            validate_source_plan(r)

    def test_omitted_product_blocks_even_with_shop_button(self):
        r, p = fixture(); p["kauppa/index.html"] = '<a href="https://shop.example/">Shop</a>'
        self.assertIn("missing_shop_product", [x["kind"] for x in commerce_problems(r, p)])

    def test_wrong_price_image_name_or_product_link_blocks(self):
        for before, after in [("30,00 €", "20,00 €"), ("Blue bouquet", "Fake flowers"),
                              ('src="https://shop.example/image.jpg"', 'src="invented.jpg"'),
                              ('href="https://shop.example/product/1"', 'href="https://shop.example/"')]:
            r, p = fixture(); p["kauppa/index.html"] = p["kauppa/index.html"].replace(before, after)
            self.assertIn("missing_shop_product", [x["kind"] for x in commerce_problems(r, p)])

    def test_partial_and_duplicate_inventory_blocks(self):
        r, p = fixture(); r["commerce_inventory"][0]["observed_product_count"] = 2
        self.assertEqual(commerce_problems(r)[0]["kind"], "incomplete_shop_catalogue")
        r["commerce_inventory"][0]["products"] *= 2
        self.assertEqual(commerce_problems(r)[0]["kind"], "incomplete_shop_catalogue")

    def test_external_entry_cannot_pose_as_local_catalogue(self):
        r, p = fixture(); p["index.html"] = '<a data-shop-entry href="https://shop.example/">Shop</a>'
        self.assertIn("missing_local_shop_entry", [x["kind"] for x in commerce_problems(r, p)])

    def test_secondary_shop_is_not_silently_ignored(self):
        r, p = fixture()
        r["source_inventory"]["pages"][0]["links"].append({"text": "Webbutik", "href": "https://second.example/"})
        r['commerce_plan']['inspection']['inspected_urls'].append('https://second.example/')
        self.assertIn("shop_not_inspected", [x["kind"] for x in commerce_problems(r, p)])

    def test_non_shop_sites_have_no_catalogue_requirement(self):
        self.assertEqual(commerce_problems({"source_inventory": {"pages": []}}, {}), [])

    def test_native_catalogue_requires_real_product_mapping_without_fake_static_cards(self):
        r, _ = fixture()
        r['commerce_plan']['mode'] = 'woocommerce_native'
        native_html = {'kauppa/index.html': '<main class="woocommerce">Native product archive</main>'}
        self.assertIn('native_product_mapping_missing', [x['kind'] for x in commerce_problems(r, native_html)])
        r['commerce_inventory'][0]['products'][0]['backend_product_id'] = 42
        # Preflight only. Native runtime catalogue/payment tests remain mandatory.
        self.assertEqual(commerce_problems(r, native_html), [])
        r['commerce_inventory'][0]['complete'] = False
        self.assertIn('shop_not_inspected', [x['kind'] for x in commerce_problems(r, native_html)])
