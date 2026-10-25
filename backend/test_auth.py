
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


class TestAuthentication(unittest.TestCase):

    @patch.dict(os.environ, {}, clear=True)
    def test_api_requires_authentication(self):
        response = client.get("/api/v1/cases")
        self.assertEqual(response.status_code, 401)

    @patch.dict(
        os.environ,
        {"SETU_API_TOKEN": "synthetic-demo-token"},
        clear=True,
    )
    @patch("main.fetch_page")
    def test_demo_token_allows_approved_read_only_route(
        self, mock_fetch_page
    ):
        mock_fetch_page.return_value = {
            "total": 0,
            "limit": 20,
            "offset": 0,
            "items": [],
        }

        response = client.get(
            "/api/v1/institutions",
            headers={"X-SETU-API-TOKEN": "synthetic-demo-token"},
        )

        self.assertEqual(response.status_code, 200)

    @patch.dict(
        os.environ,
        {"SETU_API_TOKEN": "synthetic-demo-token"},
        clear=True,
    )
    def test_demo_token_cannot_access_cases(self):
        response = client.get(
            "/api/v1/cases",
            headers={"X-SETU-API-TOKEN": "synthetic-demo-token"},
        )
        self.assertEqual(response.status_code, 403)

    @patch.dict(os.environ, {}, clear=True)
    @patch("auth.verify_supabase_jwt")
    @patch("main.require_case_profile")
    @patch("main.fetch_page")
    def test_validated_user_can_access_cases(
        self, mock_fetch_page, mock_require_profile, mock_verify
    ):
        mock_verify.return_value = {
            "sub": "approved-test-user",
            "aud": "authenticated",
        }

        mock_require_profile.return_value = {
            "user_id": "approved-test-user",
            "role": "Admin",
            "bureau_id": None,
            "region_id": None,
            "demo_only": False,
            "is_synthetic": False,
        }

        mock_fetch_page.return_value = {
            "total": 0,
            "limit": 20,
            "offset": 0,
            "items": [],
        }

        response = client.get(
            "/api/v1/cases",
            headers={
                "Authorization": "Bearer synthetic-test-token",
            },
        )

        self.assertEqual(response.status_code, 200)
        mock_verify.assert_called_once_with("synthetic-test-token")
        mock_require_profile.assert_called_once_with(
            "approved-test-user"
        )
        mock_fetch_page.assert_called_once()

    
    @patch.dict(
        os.environ,
        {"SETU_API_TOKEN": "synthetic-demo-token"},
        clear=True,
    )
    def test_demo_token_cannot_access_overlap_candidates(self):
        response = client.get(
            "/api/v1/overlaps/candidates",
            headers={"X-SETU-API-TOKEN": "synthetic-demo-token"},
        )
        self.assertEqual(response.status_code, 403)
    
    @patch.dict(
        os.environ,
        {"SETU_API_TOKEN": "synthetic-demo-token"},
        clear=True,
    )
    def test_demo_token_cannot_access_full_summary(self):
        response = client.get(
            "/api/v1/summary",
            headers={"X-SETU-API-TOKEN": "synthetic-demo-token"},
        )
        self.assertEqual(response.status_code, 403)
    
    @patch.dict(
        os.environ,
        {"SETU_API_TOKEN": "synthetic-demo-token"},
        clear=True,
    )
    @patch("main.fetch_page")
    def test_demo_institutions_excludes_internal_fields(
        self, mock_fetch_page
    ):
        mock_fetch_page.return_value = {
            "total": 1,
            "limit": 20,
            "offset": 0,
            "items": [
                {
                    "institution_id": "inst-001",
                    "permanent_id": "PERM-001",
                    "name": "Example College",
                    "address": "Example Road",
                    "state": "Tamil Nadu",
                    "district": "Chennai",
                    "normalized_name": "example college",
                    "region_id": "region-001",
                    "group_id": "group-001",
                    "campus_number": 1,
                    "is_synthetic": True,
                }
            ],
        }

        response = client.get(
            "/api/v1/institutions",
            headers={"X-SETU-API-TOKEN": "synthetic-demo-token"},
        )

        self.assertEqual(response.status_code, 200)
        item = response.json()["items"][0]

        expected_fields = {
            "institution_id",
            "permanent_id",
            "name",
            "address",
            "state",
            "district",
        }
        self.assertEqual(set(item.keys()), expected_fields)



if __name__ == "__main__":
    unittest.main(verbosity=2)
