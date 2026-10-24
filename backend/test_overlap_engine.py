
from overlap_engine import (
    find_overlap_candidates,
    score_pair,
)


# Test the scoring logic without accessing the database.
case_a = {
    "category": "Fees / Refund",
    "text": "Student reports that the college has not refunded the fee.",
    "received_date": None,
}

case_b = {
    "category": "Fees / Refund",
    "text": "College fee refund has not been provided to the student.",
    "received_date": None,
}

result = score_pair(case_a, case_b)

print("=== Scoring unit test ===")
print("Score:", result["score"])
print("Text similarity:", result["text_similarity"])
print("Reasons:", result["reasons"])

assert result["score"] >= 50
assert "Same complaint category" in result["reasons"]


# Read-only integration test against the existing database.
print("\n=== Database candidate test ===")

result = find_overlap_candidates(
    limit=10,
    minimum_score=50,
)

print("Candidates found:", result["candidate_count"])
print("Candidates returned:", result["returned_count"])

for candidate in result["items"]:
    print(
        candidate["case_a"],
        "<->",
        candidate["case_b"],
        "| score:",
        candidate["score"],
        "| reasons:",
        ", ".join(candidate["reasons"]),
    )

assert len(result["items"]) <= 10

print("\nOVERLAP ENGINE TEST PASSED")
