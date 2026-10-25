
import unittest
from unittest.mock import patch

from starlette.requests import Request

import main


class TestCaseScope(unittest.TestCase):

    def setUp(self):
        self.profile_patch = patch("main.require_case_profile")
        self.fetch_patch = patch("main.fetch_page")

        self.mock_profile = self.profile_patch.start()
        self.mock_fetch = self.fetch_patch.start()

        self.addCleanup(self.profile_patch.stop)
        self.addCleanup(self.fetch_patch.stop)

        self.mock_fetch.return_value = {
            "total": 0,
            "limit": 20,
            "offset": 0,
            "items": [],
        }

    def make_request(self):
        return Request({
            "type": "http",
            "method": "GET",
            "path": "/api/v1/cases",
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

    
    def run_list(self, **filters):
        main.get_cases(
            request=self.make_request(),
            **filters,
        )
        args = self.mock_fetch.call_args.args
        conditions = [
            condition.as_string(None)
            for condition in args[1]
        ]
        values = args[2]
        return conditions, values


    def test_regional_officer_is_limited_to_region(self):
        self.set_profile(
            "Regional Officer",
            region_id="REG-1",
        )

        conditions, values = self.run_list()

        self.assertTrue(
    any("region_id = %s" in condition for condition in conditions)
)
        self.assertIn("is_restricted IS FALSE", conditions)
        self.assertIn("REG-1", values)

    def test_bureau_head_is_limited_to_bureau(self):
        self.set_profile(
            "Bureau Head",
            bureau_id="BUR-1",
        )

        conditions, values = self.run_list()

        self.assertIn("current_bureau_id = %s", conditions)
        self.assertIn("is_restricted IS FALSE", conditions)
        self.assertEqual(values, ["BUR-1"])

    def test_desk_officer_is_limited_to_assigned_cases(self):
        self.set_profile(
            "Desk Officer",
            user_id="desk-user-1",
        )

        conditions, values = self.run_list()

        self.assertIn("assigned_user_id = %s", conditions)
        self.assertIn("is_restricted IS FALSE", conditions)
        self.assertIn("desk-user-1", values)

    def test_requested_bureau_cannot_expand_bureau_head_scope(self):
        self.set_profile(
            "Bureau Head",
            bureau_id="BUR-1",
        )

        conditions, values = self.run_list(bureau_id="BUR-2")

        self.assertEqual(
            conditions.count("current_bureau_id = %s"),
            2,
        )
        self.assertEqual(values, ["BUR-1", "BUR-2"])

    def test_restricted_cases_are_always_excluded(self):
        self.set_profile("Admin")

        conditions, _ = self.run_list()

        self.assertIn("is_restricted IS FALSE", conditions)


if __name__ == "__main__":
    unittest.main(verbosity=2)
