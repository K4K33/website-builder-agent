"""Local-only tests for anonymous feedback digests."""
from datetime import datetime, timezone
import unittest
from utils.process_kaurivo_feedback import recent_archive_digest

class FeedbackDigestTests(unittest.TestCase):
    def test_invalid_and_duplicate_records(self):
        now=datetime(2026,10,31,12,0,tzinfo=timezone.utc)
        event={"submitted_at":{"date":"2026-10-31 10:00:00"},
               "form_data":{"feedback_stage":"post_sale_experience","rating":"2",
                            "message":"Lomake ei toimi puhelimella", "company":"EXAMPLE_PRIVATE"}}
        data={"submissions":[event,event,{"submitted_at":{"date":"2026-10-31 11:00:00"},
               "form_data":{"feedback_stage":"post_sale_experience","rating":"5",
                            "message":"Yhteydenpito oli erinomaista"}}]}
        result=recent_archive_digest(data,now=now)
        self.assertEqual(result["feedback_received_unverified"],2)
        self.assertEqual(result["ratings"]["2"],1)
        self.assertEqual(result["ratings"]["5"],1)
        self.assertGreaterEqual(result["requires_urgent_human_review"],1)
        self.assertEqual(result["automatic_fixes_applied"],0)
        self.assertNotIn("EXAMPLE_PRIVATE",str(result))

    def test_bad_input_is_not_misreported(self):
        with self.assertRaises(ValueError):
            recent_archive_digest({"wrong":"data"})
        with self.assertRaises(ValueError):
            recent_archive_digest({"submissions":[]},now=datetime(2026,10,31))
        self.assertEqual(recent_archive_digest({"submissions":[]})["feedback_received_unverified"],0)

if __name__=="__main__":
    unittest.main()
