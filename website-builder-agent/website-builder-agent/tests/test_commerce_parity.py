"""Regression: storefront loss must fail before a new Kaurivo demo can ship."""
from unittest import TestCase
from utils.commerce_parity import audit_commerce_parity
from utils.universal_quality import audit_universal_standards

STORE = "https://castanum.ekukka.fi/"
ONE = STORE + "tuotteet/onnittelukukat/kukkakimput/113/floristin%20suosikki"
TWO = STORE + "tuotteet/onnittelukukat/kukkakimput/201/castanum%20kimppu"


def research():
    return {
        "company_facts": {"external_shop_url": STORE},
        "source_inventory": {"pages": [{
            "url": "https://www.castanum.fi/",
            "text": "Verkkokauppa, kukkakimput",
            "links": [{"href": STORE, "text": "Verkkokauppa"}],
        }]},
        "commerce_inventory": {
            "shop_url": STORE,
            "observed_at": "2026-11-04T10:52:44Z",
            "categories": ["Onnittelukukat", "Surukukat"],
            "products": [
                {"name": "Floristin suosikki", "price": "40,00 €", "href": ONE},
                {"name": "Castanum kimppu", "price": "30,00 €", "href": TWO},
            ],
        },
    }


def card(name, price, href):
    return (f'<article class="product-card" data-source-product="{href}">'
            f'<img src="https://castanum.ekukka.fi/pictures/original.jpg" alt="{name}">'
            f'<h2>{name}</h2><span>{price}</span>'
            f'<a href="{href}">Valitse tuote</a></article>')


def store():
    return ('<main><section><h1>Verkkokauppa</h1>'
            '<nav>Onnittelukukat | Surukukat</nav>'
            + card("Floristin suosikki", "40,00 €", ONE)
            + card("Castanum kimppu", "30,00 €", TWO)
            + '</section></main>')


class CommerceParityTests(TestCase):
    def test_no_original_store_does_not_require_an_unnatural_store(self):
        r={"source_inventory":{"pages":[{"url":"https://florist.example/","links":[]}]}}
        self.assertFalse(audit_commerce_parity({"index.html":"<main/>"},r)["required"])

    def test_header_external_shop_link_is_not_equivalent_to_a_store(self):
        pages={"index.html":'<a href="'+STORE+'">Verkkokauppa</a>'}
        result=audit_commerce_parity(pages,research())
        self.assertTrue(result["required"])
        self.assertTrue(any("no dedicated browsable store" in e for e in result["blocking"]))

    def test_original_shop_requires_research_of_real_products(self):
        r=research();r.pop("commerce_inventory")
        report=audit_commerce_parity({"index.html":"<main/>"},r)
        self.assertTrue(any("no verified external product catalog" in e
                            for e in report["blocking"]))

    def test_original_product_cards_must_have_exact_prices_and_purchase_links(self):
        fake=store().replace('40,00 €','399,00 €').replace(ONE,STORE)
        result=audit_commerce_parity({"verkkokauppa/index.html":fake},research())
        self.assertTrue(result["blocking"])

    def test_source_bound_catalog_passes_demo_but_checkout_approval_remains_pending(self):
        report=audit_commerce_parity({"verkkokauppa/index.html":store()},research())
        self.assertEqual(report["blocking"],[])
        self.assertTrue(report["pending"])

    def test_fake_native_cart_button_is_rejected(self):
        html=store().replace("</section>",'<button>Lisää ostoskoriin</button></section>')
        report=audit_commerce_parity({"verkkokauppa/index.html":html},research())
        self.assertTrue(any("unverified native cart" in err for err in report["blocking"]))

    def test_client_release_requires_owner_provider_checkout_proof(self):
        report=audit_commerce_parity({"verkkokauppa/index.html":store()},
                                     research(),stage="client_release")
        self.assertTrue(any("release missing" in err for err in report["blocking"]))

    def test_hand_coded_demo_source_audit_keeps_commerce_snapshot(self):
        # Regression for losing research.commerce_inventory in the CI adapter.
        from scripts.audit_changed_demo_previews import verified_source_evidence
        evidence=verified_source_evidence("castanum-toolon-kukkakauppa-v1")
        self.assertEqual(
            evidence["commerce_inventory"]["observed_total_products"], 87
        )
        self.assertGreaterEqual(len(evidence["commerce_inventory"]["products"]), 6)
        self.assertEqual(
            evidence["company_facts"]["external_shop_url"], STORE
        )

    def test_universal_audit_cannot_greenlight_shopless_castanum(self):
        page='<!doctype html><html lang="fi"><head><title>Castanum</title></head>' + (
            '<body><header><a href="'+STORE+'">Verkkokauppa</a></header>'
            '<main><section><h1>Castanum</h1><p>Kukkia Töölössä</p></section></main>'
            '</body></html>'
        )
        report=audit_universal_standards(page,research=research(),
                                        rendered_pages={"index.html":page},
                                        stage="internal_demo")
        self.assertIn("commerce_parity",report["blocking_problems"])


if __name__ == "__main__":
    import unittest
    unittest.main()
