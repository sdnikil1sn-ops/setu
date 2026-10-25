"""Offline fuzzy-name unit test and optional live DB smoke test."""

import unittest
from rapidfuzz import fuzz
from institution_resolution import find_fuzzy_candidates, normalize_name


class TestFuzzyNameSimilarity(unittest.TestCase):
    def test_small_typo_has_high_similarity(self):
        score = fuzz.ratio(
            normalize_name("ABC Engineering College"),
            normalize_name("ABC Enginering College"),
        )
        self.assertGreaterEqual(score, 90)


def run_database_smoke_test():
    result = find_fuzzy_candidates("ABC Enginering College")
    assert result["resolution_method"] == "fuzzy_name"
    assert result["resolution_status"] in ("needs_review", "unresolved")
    print("Fuzzy matching database smoke test: PASS")
    print("Resolution status:", result["resolution_status"])


if __name__ == "__main__":
    import sys
    if "--live-db-smoke" in sys.argv:
        run_database_smoke_test()
    else:
        unittest.main(verbosity=2)
