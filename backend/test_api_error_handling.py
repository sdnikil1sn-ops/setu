
import unittest
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import main


client = TestClient(main.app)
SECRET_MARKER = "FAKE_SECRET_MARKER_INTERNAL_DETAIL"


class TestAPIErrorHandling(unittest.TestCase):

    def test_health_database_failure_is_safe_and_logged(self):
        with patch("main.get_connection", side_effect=RuntimeError(SECRET_MARKER)), \
             patch("main.logger") as mock_logger:
            response = client.get("/health")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Database connection failed")
        self.assertNotIn(SECRET_MARKER, response.text)
        mock_logger.exception.assert_called_once_with(
            "Database health check failed"
        )

    def test_summary_database_failure_is_safe_and_logged(self):
        with patch("auth.verify_supabase_jwt", return_value={"sub": "synthetic-admin"}), \
             patch(
                 "main.require_case_profile",
                 return_value={"user_id": "synthetic-admin", "role": "Admin"},
             ), \
             patch("main.get_connection", side_effect=RuntimeError(SECRET_MARKER)), \
             patch("main.logger") as mock_logger:
            response = client.get(
                "/api/v1/summary",
                headers={"Authorization": "Bearer synthetic-test-token"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Could not retrieve database summary",
        )
        self.assertNotIn(SECRET_MARKER, response.text)
        mock_logger.exception.assert_called_once_with(
            "Failed to retrieve database summary"
        )

    def test_case_database_failure_is_safe_and_logged(self):
        with patch("auth.verify_supabase_jwt", return_value={"sub": "synthetic-admin"}), \
             patch(
                 "main.require_case_profile",
                 return_value={"user_id": "synthetic-admin", "role": "Admin"},
             ), \
             patch("main.get_connection", side_effect=RuntimeError(SECRET_MARKER)), \
             patch("main.logger") as mock_logger:
            response = client.get(
                "/api/v1/cases/CASE-SYNTHETIC",
                headers={"Authorization": "Bearer synthetic-test-token"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Could not retrieve case")
        self.assertNotIn(SECRET_MARKER, response.text)
        mock_logger.exception.assert_called_once_with(
            "Failed to retrieve case"
        )

    def test_institution_resolution_failure_is_safe_and_logged(self):
        with patch("auth.verify_supabase_jwt", return_value={"sub": "synthetic-user"}), \
             patch(
                 "main.require_case_profile",
                 return_value={"user_id": "synthetic-user", "role": "Desk Officer"},
             ), \
             patch(
                 "main.resolve_institution",
                 side_effect=RuntimeError(SECRET_MARKER),
             ), \
             patch("main.logger") as mock_logger:
            response = client.post(
                "/api/v1/institutions/resolve",
                headers={"Authorization": "Bearer synthetic-test-token"},
                json={"raw_name": "Synthetic College"},
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json()["detail"],
            "Institution resolution could not be completed",
        )
        self.assertNotIn(SECRET_MARKER, response.text)
        mock_logger.exception.assert_called_once_with(
            "Institution resolution failed"
        )
    
    def test_profile_verification_failure_is_safe_and_logged(self):
        with patch(
            "main.get_connection",
            side_effect=RuntimeError(SECRET_MARKER),
        ), patch("main.logger") as mock_logger:
            with self.assertRaises(HTTPException) as context:
                main.require_case_profile("synthetic-user")

        self.assertEqual(context.exception.status_code, 503)
        self.assertEqual(
            context.exception.detail,
            "Could not verify user authorization",
        )
        self.assertNotIn(
            SECRET_MARKER,
            context.exception.detail,
        )
        mock_logger.exception.assert_called_once_with(
            "Failed to verify user authorization profile"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
