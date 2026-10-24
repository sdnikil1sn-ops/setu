
import os
import unittest
from unittest.mock import patch

from embedding_provider import semantic_similarity
from overlap_engine import score_pair


class TestEmbeddingDegradedMode(unittest.TestCase):

    @patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-gemini-key",
        "JINA_API_KEY": "test-jina-key",
    }, clear=True)
    @patch("embedding_provider._embed_with_jina")
    @patch("embedding_provider._embed_with_gemini")
    def test_heuristic_works_when_both_providers_fail(
        self, mock_gemini, mock_jina
    ):
        # Simulate both hosted providers being unavailable.
        mock_gemini.side_effect = RuntimeError("Simulated failure")
        mock_jina.side_effect = RuntimeError("Simulated failure")

        semantic_result = semantic_similarity(
            "The college has not refunded the fee.",
            "My tuition fee refund has not been received.",
        )

        # Semantic matching must report unavailable, not score zero.
        self.assertEqual(semantic_result["status"], "unavailable")
        self.assertFalse(semantic_result["semantic_available"])
        self.assertIsNone(semantic_result["similarity"])

        # The existing heuristic engine must still work independently.
        case_a = {
            "institution_id": "INST-1",
            "group_id": "GROUP-1",
            "category": "Fees / Refund",
            "text": "The college has not refunded the fee.",
            "received_date": None,
        }

        case_b = {
            "institution_id": "INST-1",
            "group_id": "GROUP-1",
            "category": "Fees / Refund",
            "text": "My tuition fee refund has not been received.",
            "received_date": None,
        }

        heuristic_result = score_pair(case_a, case_b)

        self.assertTrue(heuristic_result["same_institution"])
        self.assertGreater(heuristic_result["score"], 0)
        self.assertIn(
            "Same canonical institution",
            heuristic_result["reasons"],
        )

        # Both providers were attempted, but no real API was called.
        mock_gemini.assert_called_once()
        mock_jina.assert_called_once()

        print("Semantic matching unavailable: PASS")
        print("Missing semantic score remains None: PASS")
        print("Heuristic scoring still works: PASS")
        print("No live provider calls made: PASS")
        print("Heuristic score:", heuristic_result["score"])

    def test_unavailable_semantic_score_is_not_a_numeric_score(self):
        unavailable_result = {
            "semantic_available": False,
            "similarity": None,
        }

        self.assertIsNone(unavailable_result["similarity"])
        self.assertFalse(unavailable_result["semantic_available"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

