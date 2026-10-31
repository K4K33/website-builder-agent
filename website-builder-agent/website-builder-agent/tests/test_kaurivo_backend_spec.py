"""Static, no-credit security checks for prepared (not deployed) Kaurivo storage."""
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"backend"

class KaurivoFeedbackBackendSpec(unittest.TestCase):
    def test_private_storage_guards(self):
        sql=(BASE/"schema.sql").read_text(encoding="utf-8")
        self.assertIn("enable row level security",sql)
        self.assertGreaterEqual(sql.count("enable row level security"),2)
        self.assertIn("revoke all on public.kaurivo_feedback_submissions",sql)
        self.assertIn("revoke all on public.kaurivo_feedback_invitations",sql)
        self.assertIn("revoke all on function public.kaurivo_submit_invited_feedback",sql)
        self.assertIn("to service_role;",sql)
        self.assertIn("for update;",sql.lower())
        self.assertIn("security invoker",sql.lower())
        self.assertNotRegex(sql.lower(), r"(?m)^\s*security\s+definer\b")
        self.assertIn("submitted_email text not null",sql)
        self.assertIn("used_at is null",sql)
        self.assertIn("expires_at > now()",sql)
        self.assertIn("source_verified boolean not null default false",sql)
        self.assertIn("public_approval_record text",sql)

    def test_edge_invitation_security(self):
        code=(BASE/"edge_function.ts").read_text(encoding="utf-8")
        self.assertIn("crypto.subtle.digest",code)
        self.assertIn("trustedOrigin = ",code)
        self.assertIn("SUPABASE_SERVICE_ROLE_KEY",code)
        self.assertIn("kaurivo_submit_invited_feedback_v2",code)
        self.assertIn('origin !== trustedOrigin',code)
        self.assertIn('return answer(400, { success: false, error: "invalid_or_used" })',code)
        self.assertNotIn("console.log",code)
        instructions=(BASE/"README.md").read_text(encoding="utf-8")
        self.assertIn("INSTALLED",instructions)
        self.assertIn("OAVIR",instructions)

if __name__=="__main__":
    unittest.main()
