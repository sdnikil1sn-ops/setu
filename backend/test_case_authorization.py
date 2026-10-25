
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException

from main import require_case_profile


class TestCaseAuthorization(unittest.TestCase):

    def setUp(self):
        self.connection_patch = patch("main.get_connection")
        self.mock_connection_factory = self.connection_patch.start()
        self.addCleanup(self.connection_patch.stop)

        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value

        self.mock_connection_factory.return_value.__enter__.return_value = (
            connection
        )
        self.cursor = cursor

    def profile(self, **overrides):
        result = {
            "user_id": "test-user",
            "role": "Admin",
            "bureau_id": None,
            "region_id": None,
            "demo_only": False,
            "is_synthetic": False,
        }
        result.update(overrides)
        return result

    def test_missing_profile_is_denied(self):
        self.cursor.fetchone.return_value = None

        with self.assertRaises(HTTPException) as context:
            require_case_profile("unlinked-user")

        self.assertEqual(context.exception.status_code, 403)

    def test_demo_profile_is_denied(self):
        self.cursor.fetchone.return_value = self.profile(
            demo_only=True
        )

        with self.assertRaises(HTTPException) as context:
            require_case_profile("test-user")

        self.assertEqual(context.exception.status_code, 403)

    def test_synthetic_profile_is_denied(self):
        self.cursor.fetchone.return_value = self.profile(
            is_synthetic=True
        )

        with self.assertRaises(HTTPException) as context:
            require_case_profile("test-user")

        self.assertEqual(context.exception.status_code, 403)

    def test_unsupported_role_is_denied(self):
        self.cursor.fetchone.return_value = self.profile(
            role="Unknown Role"
        )

        with self.assertRaises(HTTPException) as context:
            require_case_profile("test-user")

        self.assertEqual(context.exception.status_code, 403)

    def test_bureau_head_without_bureau_is_denied(self):
        self.cursor.fetchone.return_value = self.profile(
            role="Bureau Head",
            bureau_id=None,
        )

        with self.assertRaises(HTTPException) as context:
            require_case_profile("test-user")

        self.assertEqual(context.exception.status_code, 403)

    def test_regional_officer_without_region_is_denied(self):
        self.cursor.fetchone.return_value = self.profile(
            role="Regional Officer",
            region_id=None,
        )

        with self.assertRaises(HTTPException) as context:
            require_case_profile("test-user")

        self.assertEqual(context.exception.status_code, 403)

    def test_database_error_fails_closed(self):
        self.mock_connection_factory.side_effect = Exception(
            "Simulated database failure"
        )

        with self.assertRaises(HTTPException) as context:
            require_case_profile("test-user")

        self.assertEqual(context.exception.status_code, 503)

    def test_approved_profile_is_returned(self):
        approved_profile = self.profile()
        self.cursor.fetchone.return_value = approved_profile

        result = require_case_profile("test-user")

        self.assertEqual(result, approved_profile)


if __name__ == "__main__":
    unittest.main(verbosity=2)
