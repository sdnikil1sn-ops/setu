
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from starlette.requests import Request

import main


class TestSingleCaseScope(unittest.TestCase):

    def setUp(self):
        self.profile_patch = patch("main.require_case_profile")
        self.connection_patch = patch("main.get_connection")

        self.mock_profile = self.profile_patch.start()
        self.mock_connection = self.connection_patch.start()

        self.addCleanup(self.profile_patch.stop)
        self.addCleanup(self.connection_patch.stop)

        self.connection = MagicMock()
        self.cursor = (
            self.connection.cursor.return_value.__enter__.return_value
        )
        self.mock_connection.return_value.__enter__.return_value = (
            self.connection
        )

    def make_request(self):
        return Request({
            "type": "http",
            "method": "GET",
            "path": "/api/v1/cases/CASE-1",
            "headers": [],
            "state": {"user_id": "test-user"},
        })

    def set_profile(self, role, **overrides):
        profile = {
            "user_id": "test-user",
            "role": role,
            "bureau_id": None,
            "region_id": None,
            "demo_only": False,
            "is_synthetic": False,
        }
        profile.update(overrides)
        self.mock_profile.return_value = profile

    def run_case(self):
        return main.get_case(
            case_id="CASE-1",
            request=self.make_request(),
        )

    def test_regional_officer_query_is_scoped(self):
        self.set_profile("Regional Officer", region_id="REG-1")
        self.cursor.fetchone.return_value = {"case_id": "CASE-1"}

        self.run_case()

        query = self.cursor.execute.call_args.args[0].as_string(None)
        params = self.cursor.execute.call_args.args[1]

        self.assertIn("region_id = %s", query)
        self.assertIn("is_restricted IS FALSE", query)
        self.assertIn("REG-1", params)

    def test_bureau_head_query_is_scoped(self):
        self.set_profile("Bureau Head", bureau_id="BUR-1")
        self.cursor.fetchone.return_value = {"case_id": "CASE-1"}

        self.run_case()

        query = self.cursor.execute.call_args.args[0].as_string(None)
        params = self.cursor.execute.call_args.args[1]

        self.assertIn("current_bureau_id = %s", query)
        self.assertIn("BUR-1", params)

    def test_desk_officer_query_is_scoped(self):
        self.set_profile("Desk Officer", user_id="desk-user-1")
        self.cursor.fetchone.return_value = {"case_id": "CASE-1"}

        self.run_case()

        query = self.cursor.execute.call_args.args[0].as_string(None)
        params = self.cursor.execute.call_args.args[1]

        self.assertIn("assigned_user_id = %s", query)
        self.assertIn("desk-user-1", params)

    def test_restricted_cases_are_excluded(self):
        self.set_profile("Admin")
        self.cursor.fetchone.return_value = None

        with self.assertRaises(HTTPException) as context:
            self.run_case()

        self.assertEqual(context.exception.status_code, 404)

        query = self.cursor.execute.call_args.args[0].as_string(None)
        self.assertIn("is_restricted IS FALSE", query)

    def test_case_outside_scope_appears_not_found(self):
        self.set_profile("Regional Officer", region_id="REG-1")
        self.cursor.fetchone.return_value = None

        with self.assertRaises(HTTPException) as context:
            self.run_case()

        self.assertEqual(context.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
