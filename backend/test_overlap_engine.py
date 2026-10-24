
from overlap_engine import score_pair, find_overlap_candidates


# Test 1: Same institution should receive institution evidence.
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
    "text": "The college has not refunded the fee.",
    "received_date": None,
}

result = score_pair(case_a, case_b)

assert result["same_institution"] is True
assert "Same canonical institution" in result["reasons"]


# Test 2: Different campuses in the same group must not
# receive the same-institution explanation.
case_c = {
    "institution_id": "INST-2",
    "group_id": "GROUP-1",
    "category": "Fees / Refund",
    "text": "A student has not received a fee refund.",
    "received_date": None,
}

result = score_pair(case_a, case_c)

assert result["same_institution"] is False
assert result["same_group"] is True
assert "Same canonical institution" not in result["reasons"]
assert any("institution group" in reason for reason in result["reasons"])


# Test 3: Unrelated institution and group must not get
# either relationship's points.
case_d = {
    "institution_id": "INST-9",
    "group_id": "GROUP-9",
    "category": "Other",
    "text": "A different issue entirely.",
    "received_date": None,
}

result = score_pair(case_a, case_d)

assert result["same_institution"] is False
assert result["same_group"] is False
assert "Same canonical institution" not in result["reasons"]


# Test 4: Run a read-only candidate query.
result = find_overlap_candidates(limit=10, minimum_score=50)

assert result["returned_count"] <= 10
assert all(item["review_required"] for item in result["items"])
assert all(item["scope"] in ("institution", "group") for item in result["items"])

print("Same-institution scoring: PASS")
print("Group-level scoring: PASS")
print("Unrelated-pair scoring: PASS")
print("Read-only candidate query: PASS")
print("Candidate count:", result["candidate_count"])
print("Returned:", result["returned_count"])

for item in result["items"][:5]:
    print(
        item["case_a"],
        "<->",
        item["case_b"],
        "| scope:", item["scope"],
        "| score:", item["score"],
        "| reasons:", ", ".join(item["reasons"]),
    )

print("OVERLAP ENGINE TEST PASSED")
