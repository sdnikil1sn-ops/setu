import unittest
from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parent.parent
    / "supabase" / "migrations" / "0005_rls_policies.sql"
)


class TestRlsMigrationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sql = MIGRATION.read_text(encoding="utf-8").lower()

    def test_policies_are_scoped_to_setu_api(self):
        self.assertIn("for select to setu_api", self.sql)
        self.assertNotIn("for all to public", self.sql)

    def test_case_policy_excludes_restricted_cases(self):
        self.assertIn("c.is_restricted is false", self.sql)
        self.assertIn("public.setu_can_read_case(case_id)", self.sql)

    def test_profile_mapping_uses_auth_user_id(self):
        self.assertIn("p.auth_user_id = public.setu_current_auth_user_id()", self.sql)
        self.assertIn("p.is_synthetic is false", self.sql)
        self.assertIn("p.demo_only is false", self.sql)

    def test_demo_policy_is_limited_to_institutions_table(self):
        self.assertIn("create policy setu_institutions_select on public.institutions", self.sql)
        self.assertIn("public.setu_is_demo_request()", self.sql)
        # The demo context is not an authorization branch in the case policy.
        case_policy = self.sql.split(
            "create policy setu_cases_select_scoped", 1
        )[1].split(";", 1)[0]
        self.assertNotIn("setu_is_demo_request", case_policy)

    def test_no_write_policies_are_created(self):
        self.assertNotIn("for insert to setu_api", self.sql)
        self.assertNotIn("for update to setu_api", self.sql)
        self.assertNotIn("for delete to setu_api", self.sql)


if __name__ == "__main__":
    unittest.main()
