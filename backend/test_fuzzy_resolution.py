
from institution_resolution import (
    find_fuzzy_candidates,
    normalize_name,
)

# First, test the similarity function independently of the database.
original = "ABC Engineering College"
misspelled = "ABC Enginering College"

score = find_similarity = None

from rapidfuzz import fuzz

score = fuzz.ratio(
    normalize_name(original),
    normalize_name(misspelled),
)

print("Original:", original)
print("Misspelled:", misspelled)
print("Similarity score:", round(score, 2))

assert score >= 90, "Expected a high similarity score."

# Then test candidate retrieval using the existing database.
result = find_fuzzy_candidates(misspelled)

print("Resolution status:", result["resolution_status"])
print("Reason:", result["reason"])
print("Candidates:")

for candidate in result["candidates"]:
    print(
        candidate["name"],
        "| score:", candidate["score"],
        "| matched on:", candidate["matched_on"],
    )

assert result["resolution_method"] == "fuzzy_name"
assert result["resolution_status"] in ("needs_review", "unresolved")

print("FUZZY MATCHING TEST PASSED")
