"""Offline unit tests plus an explicitly invoked live-DB smoke test."""

import unittest
from overlap_engine import score_pair, find_overlap_candidates


class TestOverlapScoring(unittest.TestCase):
    def setUp(self):
        self.case_a = {
            "institution_id": "INST-1", "group_id": "GROUP-1",
            "category": "Fees / Refund",
            "text": "The college has not refunded the fee.",
            "received_date": None,
        }

    def test_same_institution_receives_institution_evidence(self):
        result = score_pair(self.case_a, dict(self.case_a))
        self.assertTrue(result["same_institution"])
        self.assertIn("Same canonical institution", result["reasons"])

    def test_same_group_different_institution_is_group_evidence(self):
        case_b = {
            "institution_id": "INST-2", "group_id": "GROUP-1",
            "category": "Fees / Refund",
            "text": "A student has not received a fee refund.",
            "received_date": None,
        }
        result = score_pair(self.case_a, case_b)
        self.assertFalse(result["same_institution"])
        self.assertTrue(result["same_group"])
        self.assertNotIn("Same canonical institution", result["reasons"])

    def test_unrelated_cases_get_no_relationship_evidence(self):
        case_b = {
            "institution_id": "INST-9", "group_id": "GROUP-9",
            "category": "Other", "text": "A different issue entirely.",
            "received_date": None,
        }
        result = score_pair(self.case_a, case_b)
        self.assertFalse(result["same_institution"])
        self.assertFalse(result["same_group"])


def run_database_smoke_test():
    """Optional read-only database smoke test; run this file directly."""
    result = find_overlap_candidates(limit=10, minimum_score=50)
    assert result["returned_count"] <= 10
    assert all(item["review_required"] for item in result["items"])
    assert all(item["scope"] in ("institution", "group") for item in result["items"])
    print("Read-only candidate query: PASS")
    print("Candidate count:", result["candidate_count"])
    print("Returned:", result["returned_count"])


if __name__ == "__main__":
    import sys
    if "--live-db-smoke" in sys.argv:
        run_database_smoke_test()
    else:
        unittest.main(verbosity=2)
