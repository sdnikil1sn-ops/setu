
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient
from main import app


client = TestClient(app)


class TestSemanticCheckAPI(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    @patch("main.semantic_similarity")
    def test_endpoint_disabled_by_default(self, mock_similarity):
        response = client.post(
            "/api/v1/overlaps/semantic-check",
            json={
                "text_a": "Synthetic tuition refund complaint A",
                "text_b": "Synthetic tuition refund complaint B",
            },
        )

        self.assertEqual(response.status_code, 404)
        mock_similarity.assert_not_called()

    @patch.dict(
        os.environ,
        {"SETU_ENABLE_SEMANTIC_CHECK": "true"},
        clear=True,
    )
    @patch("main.semantic_similarity")
    def test_enabled_endpoint_returns_semantic_result(
        self, mock_similarity
    ):
        mock_similarity.return_value = {
            "status": "available",
            "semantic_available": True,
            "provider": "gemini",
            "model": "test-model",
            "similarity": 0.91,
            "dimensions": 768,
            "fallback_used": False,
            "failed_providers": [],
        }

        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "synthetic-test-user"},
        ), patch(
            "main.require_case_profile",
            return_value={"user_id": "synthetic-test-user", "role": "Admin"},
        ):
            response = client.post(
                "/api/v1/overlaps/semantic-check",
                headers={"Authorization": "Bearer synthetic-test-token"},
                json={
                    "text_a": "Synthetic tuition refund complaint A",
                    "text_b": "Synthetic tuition refund complaint B",
                },
            )

        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertTrue(data["semantic_available"])
        self.assertEqual(data["provider"], "gemini")
        self.assertAlmostEqual(data["similarity"], 0.91)
        self.assertTrue(data["review_required"])
        self.assertFalse(data["database_modified"])

        mock_similarity.assert_called_once_with(
            "Synthetic tuition refund complaint A",
            "Synthetic tuition refund complaint B",
        )

    @patch.dict(
        os.environ,
        {"SETU_ENABLE_SEMANTIC_CHECK": "true"},
        clear=True,
    )
    @patch("main.semantic_similarity")
    def test_unavailable_semantics_are_returned_safely(
        self, mock_similarity
    ):
        mock_similarity.return_value = {
            "status": "unavailable",
            "semantic_available": False,
            "provider": None,
            "model": None,
            "similarity": None,
            "dimensions": None,
            "fallback_used": False,
            "failed_providers": [
                {"provider": "gemini", "error_type": "RuntimeError"}
            ],
            "message": "Semantic matching is unavailable.",
        }

        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "synthetic-test-user"},
        ), patch(
            "main.require_case_profile",
            return_value={"user_id": "synthetic-test-user", "role": "Senior Management"},
        ):
            response = client.post(
                "/api/v1/overlaps/semantic-check",
                headers={"Authorization": "Bearer synthetic-test-token"},
                json={
                    "text_a": "Synthetic complaint A",
                    "text_b": "Synthetic complaint B",
                },
            )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["semantic_available"])
        self.assertIsNone(data["similarity"])
        self.assertTrue(data["review_required"])

    @patch.dict(
        os.environ,
        {"SETU_ENABLE_SEMANTIC_CHECK": "true"},
        clear=True,
    )
    @patch("main.semantic_similarity")
    def test_enabled_endpoint_denies_non_management_profile(self, mock_similarity):
        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "desk-user"},
        ), patch(
            "main.require_case_profile",
            return_value={"user_id": "desk-user", "role": "Desk Officer"},
        ):
            response = client.post(
                "/api/v1/overlaps/semantic-check",
                headers={"Authorization": "Bearer synthetic-test-token"},
                json={"text_a": "Synthetic A", "text_b": "Synthetic B"},
            )

        self.assertEqual(response.status_code, 403)
        mock_similarity.assert_not_called()

    @patch("main.find_overlap_candidates")
    def test_existing_candidates_endpoint_contract(self, mock_candidates):
        expected = {
            "candidate_count": 1,
            "returned_count": 1,
            "minimum_score": 50,
            "items": [
                {
                    "case_a": "CASE-A",
                    "case_b": "CASE-B",
                    "score": 73.7,
                    "scope": "institution",
                    "review_required": True,
                }
            ],
            "note": "Synthetic test response",
        }
        mock_candidates.return_value = expected

        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "approved-admin"},
        ), patch(
            "main.require_case_profile",
            return_value={"user_id": "approved-admin", "role": "Admin"},
        ):
            response = client.get(
                "/api/v1/overlaps/candidates",
                headers={"Authorization": "Bearer synthetic-test-token"},
                params={"limit": 1, "minimum_score": 50},
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), expected)
        mock_candidates.assert_called_once_with(
            limit=1,
            minimum_score=50.0,
        )

    @patch("main.find_overlap_candidates")
    def test_non_management_role_cannot_access_overlap_candidates(
        self, mock_candidates
    ):
        with patch(
            "auth.verify_supabase_jwt",
            return_value={"sub": "approved-desk-officer"},
        ), patch(
            "main.require_case_profile",
            return_value={
                "user_id": "approved-desk-officer",
                "role": "Desk Officer",
            },
        ):
            response = client.get(
                "/api/v1/overlaps/candidates",
                headers={"Authorization": "Bearer synthetic-test-token"},
            )

        self.assertEqual(response.status_code, 403)
        mock_candidates.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
