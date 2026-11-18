"""Guard the entire reputation admission contract: search, source, UI, CRM."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT.parents[1]

class ReputationPipelineContractTests(unittest.TestCase):
    def test_review_source_gate_is_in_active_scheduler_and_server(self):
        workflow=(REPO/".github/workflows/kaurivo-national-prh.yml").read_text()
        script=(ROOT/"utils/kaurivo_reputation_research.py").read_text()
        edge=(ROOT/"docs/kaurivo/backend/prh_ingest_edge.ts").read_text()
        self.assertIn("utils.kaurivo_reputation_research",workflow)
        self.assertIn("--max-queries 8",workflow)
        self.assertIn("make_credit_reservation()",script)
        self.assertIn("re.status!==\"qualified\"",edge)
        self.assertIn("Number(re.review_count)<10",edge)
        self.assertIn("re.rating<4",edge)
        self.assertIn("reputation_evidence:reputationEvidence",edge)

    def test_owner_daily_list_is_explicitly_quality_gated(self):
        crm=(ROOT/"docs/kaurivo/assets/crm.js").read_text()
        html=(ROOT/"docs/kaurivo/admin/index.html").read_text()
        self.assertIn("function fourStarIndependentReputation(c)",crm)
        self.assertIn("fourStarIndependentReputation(x)",crm)
        self.assertIn("vähintään 10 arvostelua",crm)
        self.assertIn('value="all" selected',html)
        self.assertIn("Hyvämaineiset (vähintään 4/5)",html)

    def test_source_evidence_dedicated_field_and_no_paid_google(self):
        migration=(ROOT/"docs/kaurivo/backend/kaurivo_reputation_evidence_20261118.sql").read_text()
        script=(ROOT/"utils/kaurivo_reputation_research.py").read_text()
        self.assertIn("reputation_evidence jsonb",migration)
        self.assertIn("MIN_REVIEWS = 10",script)
        self.assertIn("MIN_RATING = 4.0",script)
        self.assertNotIn('"google.com",',script)
        self.assertIn("not config.tavily_free_plan_confirmed(scheduled=True)",script)

if __name__=="__main__":
    unittest.main()
