"""Deterministic tests for the Kaurivo owner-approved AI workforce pilot."""
import os
import unittest
from unittest.mock import patch
from scripts import kaurivo_ai_team as team


def issue(body="Role: designer\n\nTask: Plan a Kaurivo homepage", labels=None,
          author="K4K33", number=7):
    return {"number": number, "body": body, "user": {"login": author},
            "labels": [{"name": name} for name in (labels or [team.READY])]}


class AITeamTests(unittest.TestCase):
    def test_only_owner_approved_supported_roles(self):
        self.assertEqual(team.task_role(issue()), "designer")
        self.assertEqual(team.task_role(issue(body="Role: social_strategist\nTask: hello")),
                         "social_strategist")
        self.assertIsNone(team.task_role(issue(author="visitor")))
        self.assertIsNone(team.task_role(issue(labels=[])))
        self.assertIsNone(team.task_role(issue(body="Role: admin\nTask: hello")))
        self.assertIsNone(team.task_role({**issue(), "pull_request": {}}))
        self.assertIsNone(team.task_role(issue(labels=[team.RUNNING, team.READY])))

    def test_paid_model_rejected_before_http(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "pretend-token",
                                      "KAURIVO_TEAM_MODEL_FREE": "openai/gpt-6.2"}, clear=False):
            with patch.object(team, "urlopen") as network:
                with self.assertRaisesRegex(RuntimeError, "missing_exact_free_model"):
                    team.make_draft("designer", issue())
                network.assert_not_called()

    def test_missing_key_rejected_before_http(self):
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
            with patch.object(team, "urlopen") as network:
                with self.assertRaisesRegex(RuntimeError, "missing_free_ai_key"):
                    team.make_draft("designer", issue())
                network.assert_not_called()

    def test_no_unapproved_work_uses_no_ai(self):
        with patch.object(team, "ensure_labels"), \
             patch.object(team, "get_builder_status", return_value="Builder status not verified"), \
             patch.object(team, "api", return_value=[]), \
             patch.object(team, "make_draft") as infer:
            team.run_once()
            infer.assert_not_called()

    def test_claim_before_one_call_and_review_after(self):
        task = issue()
        order = []
        def state(_issue, old, new):
            order.append(new)
        with patch.object(team, "ensure_labels"), \
             patch.object(team, "get_builder_status", return_value="ok"), \
             patch.object(team, "api", return_value=[task]), \
             patch.object(team, "update_label", side_effect=state), \
             patch.object(team, "comment"), \
             patch.object(team, "make_draft", return_value="draft") as infer:
            team.run_once()
        self.assertEqual(order, [team.RUNNING, team.REVIEW])
        infer.assert_called_once()

    def test_free_model_failure_is_blocked_without_retry(self):
        task = issue()
        transitions = []
        with patch.object(team, "ensure_labels"), \
             patch.object(team, "get_builder_status", return_value="ok"), \
             patch.object(team, "api", return_value=[task]), \
             patch.object(team, "update_label", side_effect=lambda i,a,b:transitions.append(b)), \
             patch.object(team, "comment"), \
             patch.object(team, "make_draft", side_effect=RuntimeError("missing_free_ai_key")) as infer:
            team.run_once()
        self.assertEqual(transitions, [team.RUNNING, team.BLOCKED])
        infer.assert_called_once()


if __name__ == "__main__":
    unittest.main()
