
import os
import unittest
from unittest.mock import patch

from embedding_provider import semantic_similarity


TEXT_A = "The college has not refunded my tuition fee."
TEXT_B = "My admission was cancelled, but the fee was not returned."

VECTOR_A = [1.0, 0.0, 0.0]
VECTOR_B = [0.8, 0.6, 0.0]


class TestEmbeddingFallback(unittest.TestCase):

    @patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-gemini-key",
        "GEMINI_EMBEDDING_MODEL": "test-gemini-model",
    }, clear=True)
    @patch("embedding_provider._embed_with_gemini")
    def test_gemini_success(self, mock_gemini):
        mock_gemini.return_value = [VECTOR_A, VECTOR_B]

        result = semantic_similarity(TEXT_A, TEXT_B)

        self.assertEqual(result["status"], "available")
        self.assertTrue(result["semantic_available"])
        self.assertEqual(result["provider"], "gemini")
        self.assertAlmostEqual(result["similarity"], 0.8)
        self.assertFalse(result["fallback_used"])
        self.assertEqual(result["failed_providers"], [])

        mock_gemini.assert_called_once()

    @patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-gemini-key",
        "GEMINI_EMBEDDING_MODEL": "test-gemini-model",
        "JINA_API_KEY": "test-jina-key",
        "JINA_EMBEDDING_MODEL": "test-jina-model",
    }, clear=True)
    @patch("embedding_provider._embed_with_jina")
    @patch("embedding_provider._embed_with_gemini")
    def test_jina_fallback(self, mock_gemini, mock_jina):
        mock_gemini.side_effect = RuntimeError("Simulated Gemini failure")
        mock_jina.return_value = [VECTOR_A, VECTOR_B]

        result = semantic_similarity(TEXT_A, TEXT_B)

        self.assertEqual(result["status"], "available")
        self.assertTrue(result["semantic_available"])
        self.assertEqual(result["provider"], "jina")
        self.assertTrue(result["fallback_used"])
        self.assertAlmostEqual(result["similarity"], 0.8)
        self.assertEqual(
            result["failed_providers"][0]["provider"], "gemini"
        )

        mock_gemini.assert_called_once()
        mock_jina.assert_called_once()

    @patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-gemini-key",
        "JINA_API_KEY": "test-jina-key",
    }, clear=True)
    @patch("embedding_provider._embed_with_jina")
    @patch("embedding_provider._embed_with_gemini")
    def test_both_providers_fail(self, mock_gemini, mock_jina):
        mock_gemini.side_effect = RuntimeError("Simulated failure")
        mock_jina.side_effect = RuntimeError("Simulated failure")

        result = semantic_similarity(TEXT_A, TEXT_B)

        self.assertEqual(result["status"], "unavailable")
        self.assertFalse(result["semantic_available"])
        self.assertIsNone(result["similarity"])
        self.assertIsNone(result["provider"])
        self.assertEqual(len(result["failed_providers"]), 2)

        mock_gemini.assert_called_once()
        mock_jina.assert_called_once()

    @patch.dict(os.environ, {
        "GEMINI_API_KEY": "test-gemini-key",
    }, clear=True)
    @patch("embedding_provider._embed_with_gemini")
    def test_no_backup_configured(self, mock_gemini):
        mock_gemini.side_effect = RuntimeError("Simulated failure")

        result = semantic_similarity(TEXT_A, TEXT_B)

        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["similarity"])
        self.assertEqual(len(result["failed_providers"]), 1)
        self.assertEqual(
            result["failed_providers"][0]["provider"], "gemini"
        )
        mock_gemini.assert_called_once()

    def test_empty_text_rejected(self):
        with self.assertRaises(ValueError):
            semantic_similarity("", TEXT_B)

    def test_different_vector_dimensions_rejected(self):
        from embedding_provider import cosine_similarity

        with self.assertRaises(ValueError):
            cosine_similarity([1.0, 0.0], [1.0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
