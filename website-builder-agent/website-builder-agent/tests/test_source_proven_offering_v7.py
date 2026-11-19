"""Guard the first-party-only V7 primary-service recovery from cheap-model quotes.

Source-grounded recovery is allowed; fictional product/brand, registry scope,
privacy text, empty navigation headings and paraphrased quotes never are.
"""
from __future__ import annotations

from unittest import TestCase
from utils.service_quality import (
    source_proven_primary_offering, reconcile_primary_offering_with_source,
)

URL="https://operator.example/"
SOURCE={
  "url":URL,
  "title":"Example operator – services",
  "text":(
     "Company – logistics in Ostrobothnia. Services. "
     "Elintarvikekuljetukset. Pakaste- ja kylmäkuljetukset katkeamattomalla "
     "kylmäketjulla. Lämpötilaseuranta ja täysi jäljitettävyys. "
     "Runko- ja jakelukuljetukset. Joustavat kappaletavara- ja "
     "jakelukuljetukset päivittäistavarakaupalle ja tukuille. "
     "Ota yhteyttä ja pyydä kuljetustarjous omilla tiedoillasi."
  ),
  "headings":{"h2":["Palvelut"],"h3":["Elintarvikekuljetukset","Runko- ja jakelukuljetukset"]},
}

class VerbatimSourceOfferingFallback(TestCase):
    def test_extract_service_from_actual_crawled_heading_without_model_quote(self):
        result=source_proven_primary_offering([SOURCE], ["Elintarvikekuljetukset"])
        self.assertEqual(result["source_url"],URL)
        self.assertEqual(result["label"],"Elintarvikekuljetukset")
        self.assertIn("Pakaste- ja kylmäkuljetukset",result["quote"])
        self.assertIn(result["quote"],SOURCE["text"])

    def test_fallback_without_model_response_uses_only_real_service_heading(self):
        result=source_proven_primary_offering([SOURCE], [])
        self.assertEqual(result["source_url"],URL)
        self.assertEqual(result["label"],"Elintarvikekuljetukset")
        self.assertNotEqual(result["label"],"Palvelut")

    def test_unverified_hallucinated_model_quote_may_recover_only_real_source(self):
        fake={"source_url":URL,"label":"Elintarvikekuljetukset",
              "quote":"Kuljetamme kaikilla reiteillä tunnissa ilmaiseksi."}
        with self.assertRaises(RuntimeError):
            reconcile_primary_offering_with_source(fake,[SOURCE])
        evidence=source_proven_primary_offering([SOURCE], [fake["label"]])
        self.assertNotIn("tunnissa",evidence["quote"])
        self.assertIn("kylmäketjulla",evidence["quote"])

    def test_unverified_services_and_fabricated_headings_stay_blocked(self):
        page={"url":URL,"text":("Ota yhteyttä. Tämä sivusto esittelee "
              "yrityksen historiaa ja yhteystietoja, mutta asiakkaiden "
              "ostettavia palveluita ei kerrota tällä sivulla lainkaan. "
              "Etusivu ja uutiset kertovat vain arjesta, ihmisistä ja tapahtumista."),
              "headings":{"h2":["Palvelut"],"h3":["Elintarvikekuljetukset"]}}
        with self.assertRaises(RuntimeError):
            source_proven_primary_offering([page],["Elintarvikekuljetukset"])

    def test_registry_and_privacy_pages_cannot_be_copied_as_service_proof(self):
        for url in (
            "https://ytj.fi/example",
            "https://operator.example/tietosuoja/",
            "https://operator.example/privacy/",
            "http://operator.example/",
        ):
            with self.subTest(url=url):
                page={**SOURCE,"url":url}
                with self.assertRaises(RuntimeError):
                    source_proven_primary_offering([page],["Elintarvikekuljetukset"])

    def test_service_candidate_must_appear_in_exact_observed_source_text(self):
        page={"url":URL,"text":("Rautakaupan palautusohjeet ja yhteystiedot. "
             "Tämä osio kertoo aukioloajoista ja henkilökunnan työvuoroista. "
             "Varmistamme, että uutiset pysyvät kaikkien nähtävillä. "
             "Asiakkaita palvellaan normaalien aukioloaikojen mukaan."),
             "headings":{"h2":["Yhteystiedot","Ajankohtaista"]}}
        with self.assertRaises(RuntimeError):
            source_proven_primary_offering([page],["Elintarvikekuljetukset"])
