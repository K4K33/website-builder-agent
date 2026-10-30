"""No-credit tests for client demo wishes and post-handover feedback.

No Gmail, third-party form submission, AI calls or secrets.
"""
from pathlib import Path
import unittest

from utils.customer_feedback import (
    DEMO_REVIEW_URL, SENDER, demo_review_invitation,
    draft_completed_project_feedback, triage_feedback,
)

SITE = Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
ROOT = Path(__file__).resolve().parents[1]


class CustomerFeedbackTests(unittest.TestCase):
    def test_demo_intake_is_private_and_transparent(self):
        html = (SITE / "demo-review" / "index.html").read_text(encoding="utf-8")
        privacy = (SITE / "privacy" / "index.html").read_text(encoding="utf-8")
        self.assertIn('name="must_haves"', html)
        self.assertIn('name="other_wishes"', html)
        self.assertIn('name="company"', html)
        self.assertIn('name="email"', html)
        self.assertIn('method="POST"', html)
        self.assertIn('action="https://formsubmit.co/hello.kaurivo@gmail.com"', html)
        self.assertIn('href="../privacy/"', html)
        self.assertIn('name="privacy_ack"', html)
        self.assertIn("reply directly", html)
        self.assertIn("before delivery is active", html)
        self.assertIn("Demo review and final-site wishes", privacy)
        self.assertIn("noindex", html)

    def test_review_invite_requires_confirmed_activation(self):
        url = "https://example.org/demo/"
        draft = demo_review_invitation(url)
        self.assertIn(url, draft)
        self.assertNotIn(DEMO_REVIEW_URL, draft)
        self.assertIn("vastaamalla suoraan", draft)
        confirmed = demo_review_invitation(url, intake_activated=True)
        self.assertIn(DEMO_REVIEW_URL, confirmed)
        self.assertIn("vastata tähän sähköpostiin", confirmed)
        for bad_url in ("file:///tmp/demo", "javascript:alert(1)", "//example.org/demo",
                        "http://example.org", "https://me:password@example.org"):
            with self.subTest(url=bad_url):
                with self.assertRaises(ValueError):
                    demo_review_invitation(bad_url, intake_activated=True)

    def test_post_project_request_is_draft_and_requires_real_client(self):
        with self.assertRaises(ValueError):
            draft_completed_project_feedback(recipient_email="person@example.org",
                                             company_name="Example Oy", project_completed=False,
                                             relationship_verified=True)
        with self.assertRaises(ValueError):
            draft_completed_project_feedback(recipient_email="person@example.org",
                                             company_name="Example Oy", project_completed=True,
                                             relationship_verified=False)
        draft = draft_completed_project_feedback(
            recipient_email="person@example.org", company_name="Example Oy",
            contact_first_name="Anna", project_completed=True, relationship_verified=True
        )
        self.assertEqual(draft["from"], SENDER)
        self.assertFalse(draft["send_approved"])
        self.assertFalse(draft["send_performed"])
        self.assertFalse(draft["public_testimonial_permission"])
        self.assertIn("Hei Anna,", draft["body"])
        self.assertIn("suoraan tähän sähköpostiin", draft["body"])
        self.assertIn("kriittinen palaute", draft["body"])

    def test_negative_feedback_is_not_dismissed(self):
        result = triage_feedback("Lomake ei toimi puhelimella, emme voi lähettää yhtään viestiä",
                                 relationship_verified=False, project_verified=False)
        self.assertEqual(result["source_status"], "unverified_source")
        self.assertEqual(result["priority"], "urgent_review")
        self.assertTrue(result["human_review_required"])
        self.assertFalse(result["publish_permitted"])
        self.assertFalse(result["auto_revise_or_send"])
        known = triage_feedback("I would like the homepage background to be warm green instead",
                               relationship_verified=True, project_verified=True)
        self.assertEqual(known["source_status"], "verified_client_project")
        self.assertEqual(known["priority"], "normal_review")
        self.assertIn("content_and_brand", known["categories"])
        vague = triage_feedback("Ei hyvä", relationship_verified=True, project_verified=True)
        self.assertEqual(vague["priority"], "clarify")
        with self.assertRaises(ValueError):
            triage_feedback("   ")

    def test_internal_process_does_not_publish_or_send(self):
        docs = (ROOT / "docs" / "CUSTOMER_FEEDBACK.md").read_text()
        self.assertIn("Gmail", docs)
        self.assertIn("weekly internal review", docs)
        self.assertIn("not automatically a public testimonial", docs.lower())
        code = (ROOT / "utils" / "customer_feedback.py").read_text()
        self.assertNotIn("smtplib", code)
        self.assertNotIn("requests.post(", code)


if __name__ == "__main__":
    unittest.main()
