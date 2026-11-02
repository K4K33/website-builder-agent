"""No-credit guard tests. Existing V1 trio must fail originality."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.design_distinctness import (
    assert_unique_against_output, compare_site_designs,
)

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos"

class TestDifferentCompanies(unittest.TestCase):
    def test_rejected_v1_site_trio_is_detected(self):
        demos = [(ROOT / n / "index.html").read_text(encoding="utf-8")
                 for n in ("te-service-v1", "ravintola-rosanne-v1",
                           "rakennuspalvelu-rili-v1")]
        for a,b in ((0,1),(0,2),(1,2)):
            with self.subTest(pair=(a,b)):
                result = compare_site_designs(demos[a], demos[b])
                self.assertTrue(result["same_core_stylesheet"])
                self.assertTrue(result["too_similar"], result)

    def test_gate_blocks_duplicate_company_but_allows_own_revision(self):
        html = (ROOT / "te-service-v1" / "index.html").read_text(encoding="utf-8")
        with TemporaryDirectory() as directory:
            other = Path(directory) / "existing"
            other.mkdir()
            (other / "index.html").write_text(html, encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "Reused customer website template"):
                assert_unique_against_output(html, "new-company", directory)
            assert_unique_against_output(html, "existing", directory)

    def test_shared_basic_components_are_not_alone_an_error(self):
        a = "<main><section class='hero'><h1>A</h1></section></main>"
        b = "<main><section class='hero'><h1>B</h1></section></main>"
        self.assertFalse(compare_site_designs(a,b)["too_similar"])
