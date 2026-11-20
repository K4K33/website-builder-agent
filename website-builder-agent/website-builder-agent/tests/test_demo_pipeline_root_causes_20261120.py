"""Regression tests for root causes found in the 20.11.2026 queue audit.

Supabase showed 33 demo jobs and none reaching a preview. Two blockers here
are deterministic, not free-model capacity problems.
"""
import hashlib
import unittest

from utils.creative_directions import (
    CreativeBusinessReasonError,
    validate_creative_directions,
)
from utils import service_quality


def _direction(identifier, reason, axis_text):
    base = {
        "id": identifier,
        "concept": "Concept text long enough " + identifier,
        "business_reason": reason,
        "source_anchor": "Source anchor from page " + identifier,
        "typography": "Typography choice " + identifier,
        "brand_continuity": "Keeps original logo " + identifier,
        "non_goals": "No invented proof " + identifier,
        "mobile_behavior": "Phone-first navigation " + identifier,
    }
    for axis in ("first_view", "information_architecture", "navigation",
                 "image_strategy"):
        base[axis] = f"{axis_text} {axis} " * 3
    return base


class FinnishAudienceInflectionTests(unittest.TestCase):
    """Ostroferia job 950ec193 looped on 'Konseptin 2 perustelusta puuttuu
    asiakkaan tarve' because 'asiakkaan' did not contain the stem 'asiaka'."""

    def _plan(self, reason):
        return {"creative_directions": [
            _direction("a", "Yritys tarvitsee selkeän palvelupolun.",
                       "Full-bleed project photo with enquiry"),
            _direction("b", reason,
                       "Editorial split layout reference list grid"),
            _direction("c", "Kävijä löytää yhteystiedot heti.",
                       "Typographic statement map contact strip"),
        ]}

    def test_inflected_finnish_customer_is_accepted(self):
        for reason in (
            "Asiakkaan tarve on löytää hinnat nopeasti.",
            "Asiakkaat haluavat nähdä valmiit kohteet ennen yhteydenottoa.",
            "Näytetään asiakkaille aidot ennen ja jälkeen -kuvat.",
            "Asiakkaiden yleisin kysymys on toimitusaika.",
        ):
            with self.subTest(reason=reason):
                try:
                    validate_creative_directions(self._plan(reason))
                except CreativeBusinessReasonError:
                    self.fail("Natural Finnish audience wording was rejected")
                except RuntimeError:
                    pass  # Later, unrelated distinctness checks may apply.

    def test_reason_without_any_audience_is_still_rejected(self):
        with self.assertRaises(CreativeBusinessReasonError) as caught:
            validate_creative_directions(self._plan("Tumma tausta ja iso fontti näyttää hienolta."))
        self.assertEqual(caught.exception.index, 1)


class MasterPromptCheckpointBindingTests(unittest.TestCase):
    """Research checkpoints must not be wiped by text the models never see."""

    def test_hash_is_bound_to_active_runtime_contract(self):
        source = service_quality.MASTER_PROMPT_SOURCE
        active = source.split("<!-- ACTIVE_RUNTIME_CONTRACT_START -->", 1)[1]
        active = active.split("<!-- ACTIVE_RUNTIME_CONTRACT_END -->", 1)[0].strip()
        self.assertEqual(service_quality.MASTER_PROMPT_SHA256,
                         hashlib.sha256(active.encode("utf-8")).hexdigest())
        self.assertIn(active, service_quality.POLICY)

    def test_history_outside_active_block_does_not_change_hash(self):
        source = service_quality.MASTER_PROMPT_SOURCE
        edited = source + "\n\n## 21.11.2026 uusi historiamerkintä\n- Pelkkä muistiinpano.\n"
        active = edited.split("<!-- ACTIVE_RUNTIME_CONTRACT_START -->", 1)[1]
        active = active.split("<!-- ACTIVE_RUNTIME_CONTRACT_END -->", 1)[0].strip()
        self.assertEqual(hashlib.sha256(active.encode("utf-8")).hexdigest(),
                         service_quality.MASTER_PROMPT_SHA256)


class PrimaryOfferingInflectionTests(unittest.TestCase):
    """12 of 33 jobs stopped at 'primary offering unverified' with no reason."""

    PAGES = [{"url": "https://example.fi/palvelut",
              "text": "Teemme lukitustekniikan asennukset ja huollot "
                      "yrityksille ja taloyhtiöille koko pääkaupunkiseudulla."}]

    def test_inflected_label_with_verbatim_quote_passes(self):
        ok = service_quality.validate_primary_offering({
            "source_url": "https://example.fi/palvelut",
            "label": "Lukitustekniikka",
            "quote": "Teemme lukitustekniikan asennukset ja huollot",
        }, self.PAGES)
        self.assertEqual(ok["label"], "Lukitustekniikka")

    def test_paraphrased_quote_is_still_rejected_with_reason(self):
        with self.assertRaises(RuntimeError) as caught:
            service_quality.validate_primary_offering({
                "source_url": "https://example.fi/palvelut",
                "label": "Lukitustekniikka",
                "quote": "Tarjoamme laadukasta lukitustekniikkaa",
            }, self.PAGES)
        self.assertIn("Original-site primary offering unverified", str(caught.exception))
        self.assertIn("reason=quote_not_verbatim", str(caught.exception))

    def test_unrelated_label_is_rejected(self):
        self.assertEqual(service_quality.primary_offering_failure({
            "source_url": "https://example.fi/palvelut",
            "label": "Kattoremontit",
            "quote": "Teemme lukitustekniikan asennukset ja huollot",
        }, self.PAGES), "label_not_in_quote")

    def test_registry_source_is_rejected(self):
        self.assertEqual(service_quality.primary_offering_failure({
            "source_url": "https://www.ytj.fi/x", "label": "Lukitus",
            "quote": "Lukitus asennukset ja huollot",
        }, self.PAGES), "registry_source")

    def test_admin_diagnostic_shows_only_reason_code(self):
        import tempfile
        from scripts import run_kaurivo_demo_queue as queue
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as handle:
            handle.write("RuntimeError: Original-site primary offering unverified; "
                         "confirm a current product or service with a customer-facing "
                         "source. reason=quote_not_verbatim\n")
            message = queue.source_failure_diagnostic(handle)
        self.assertTrue(message.endswith("Syy: quote_not_verbatim"))


if __name__ == "__main__":
    unittest.main()
