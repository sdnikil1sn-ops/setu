import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestSensitiveEndpointAuthorization(unittest.TestCase):

    def test_summary_requires_approved_profile_and_management_role(self):
        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "desk-user"},
        ), patch(
            "main.require_case_profile",
            return_value={"user_id": "desk-user", "role": "Desk Officer"},
        ), patch("main.get_connection") as mock_connection:
            response = client.get(
                "/api/v1/summary",
                headers={"Authorization": "Bearer synthetic-test-token"},
            )

        self.assertEqual(response.status_code, 403)
        mock_connection.assert_not_called()

    def test_summary_allows_management_profile(self):
        from unittest.mock import MagicMock

        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = {"total": 0}
        connection.__enter__.return_value = connection

        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "approved-admin"},
        ), patch(
            "main.require_case_profile",
            return_value={"user_id": "approved-admin", "role": "Admin"},
        ), patch("main.get_connection", return_value=connection):
            response = client.get(
                "/api/v1/summary",
                headers={"Authorization": "Bearer synthetic-test-token"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("actual_counts", response.json())

    @patch("main.resolve_institution")
    def test_institution_resolution_candidates_are_allowlisted(self, mock_resolve):
        mock_resolve.return_value = {
            "resolution_status": "needs_review",
            "resolution_method": "fuzzy_name",
            "resolution_confidence": 0.0,
            "reason": "Synthetic test",
            "institution": None,
            "candidates": [{
                "institution_id": "inst-1",
                "name": "Example College",
                "permanent_id": "P-1",
                "score": 91.0,
                "matched_on": "institution_name",
                "internal_notes": "must not be returned",
                "region_id": "internal-region",
            }],
        }

        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "approved-user"},
        ), patch(
            "main.require_case_profile",
            return_value={"user_id": "approved-user", "role": "Desk Officer"},
        ):
            response = client.post(
                "/api/v1/institutions/resolve",
                headers={"Authorization": "Bearer synthetic-test-token"},
                json={"raw_name": "Example College"},
            )

        self.assertEqual(response.status_code, 200)
        candidate = response.json()["candidates"][0]
        self.assertEqual(
            set(candidate),
            {"institution_id", "name", "permanent_id", "score", "matched_on"},
        )
        self.assertNotIn("internal_notes", candidate)
        self.assertNotIn("region_id", candidate)

    @patch("main.resolve_institution")
    def test_institution_resolution_requires_approved_profile(
        self, mock_resolve
    ):
        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "unapproved-user"},
        ), patch(
            "main.require_case_profile",
            side_effect=HTTPException(
                status_code=403,
                detail="No approved SETU profile is linked to this account",
            ),
        ):
            response = client.post(
                "/api/v1/institutions/resolve",
                headers={"Authorization": "Bearer synthetic-test-token"},
                json={"raw_name": "Synthetic College"},
            )

        self.assertEqual(response.status_code, 403)
        mock_resolve.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
