
from institution_resolution import get_connection
from overlap_engine import score_pair


def main():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM public.ground_truth_pairs
                ORDER BY pair_id
                """
            )
            ground_truth = cur.fetchall()

            results = []

            for pair in ground_truth:
                cur.execute(
                    """
                    SELECT *
                    FROM public.complaint_cases
                    WHERE case_id = %s OR case_ref = %s
                    LIMIT 1
                    """,
                    (pair["case_a"], pair["case_a"]),
                )
                case_a = cur.fetchone()

                cur.execute(
                    """
                    SELECT *
                    FROM public.complaint_cases
                    WHERE case_id = %s OR case_ref = %s
                    LIMIT 1
                    """,
                    (pair["case_b"], pair["case_b"]),
                )
                case_b = cur.fetchone()

                if case_a is None or case_b is None:
                    results.append({
                        "pair_id": pair["pair_id"],
                        "overlap_type": pair["overlap_type"],
                        "error": "Could not find both complaint records",
                    })
                    continue

                evidence = score_pair(
                    {
                        "institution_id": case_a["institution_id"],
                        "group_id": case_a["group_id"],
                        "category": case_a["category"],
                        "text": case_a["text"],
                        "received_date": case_a["received_date"],
                    },
                    {
                        "institution_id": case_b["institution_id"],
                        "group_id": case_b["group_id"],
                        "category": case_b["category"],
                        "text": case_b["text"],
                        "received_date": case_b["received_date"],
                    },
                )

                same_institution = (
                    case_a["institution_id"] is not None
                    and case_a["institution_id"] == case_b["institution_id"]
                )

                same_group = (
                    case_a["group_id"] is not None
                    and case_a["group_id"] == case_b["group_id"]
                )

                cross_bureau = (
                    case_a["source_system"] != case_b["source_system"]
                )

                restricted = (
                    bool(case_a["is_restricted"])
                    or bool(case_b["is_restricted"])
                )

                candidate_eligible = (
                    (same_institution or same_group)
                    and cross_bureau
                    and not restricted
                )

                results.append({
                    "pair_id": pair["pair_id"],
                    "overlap_type": pair["overlap_type"],
                    "expected_overlap": pair["is_true_overlap"],
                    "score": evidence["score"],
                    "text_similarity": evidence["text_similarity"],
                    "same_institution": same_institution,
                    "same_group": same_group,
                    "cross_bureau": cross_bureau,
                    "restricted": restricted,
                    "candidate_eligible": candidate_eligible,
                    "reasons": evidence["reasons"],
                })

    print("=== Ground-truth overlap evaluation ===")

    for result in results:
        print(
            f"\n{result['pair_id']} - "
            f"{result['overlap_type']}"
        )

        if "error" in result:
            print("ERROR:", result["error"])
            continue

        print("Expected overlap:", result["expected_overlap"])
        print("Score:", result["score"])
        print("Text similarity:", result["text_similarity"])
        print("Same institution:", result["same_institution"])
        print("Same group:", result["same_group"])
        print("Cross-bureau:", result["cross_bureau"])
        print("Restricted:", result["restricted"])
        print("Candidate eligible:", result["candidate_eligible"])
        print("Reasons:", ", ".join(result["reasons"]))

    valid = [r for r in results if "error" not in r]
    positives = [r for r in valid if r["expected_overlap"] is True]
    negatives = [r for r in valid if r["expected_overlap"] is False]

    print("\n=== Summary ===")
    print("Ground-truth pairs:", len(results))
    print("Pairs evaluated:", len(valid))
    print("Positive examples:", len(positives))
    print("Negative examples:", len(negatives))

    for threshold in (50, 75):
        detected = sum(r["score"] >= threshold for r in positives)
        false_positive = sum(r["score"] >= threshold for r in negatives)

        print(
            f"\nThreshold {threshold}:"
            f"\n  Positive examples scoring above threshold: "
            f"{detected}/{len(positives)}"
            f"\n  Negative examples scoring above threshold: "
            f"{false_positive}/{len(negatives)}"
        )

    eligible_positive = sum(
        r["candidate_eligible"] for r in positives
    )
    eligible_negative = sum(
        r["candidate_eligible"] for r in negatives
    )

    print(
        "\nEligible positive pairs:",
        f"{eligible_positive}/{len(positives)}",
    )
    print(
        "Eligible negative pairs:",
        f"{eligible_negative}/{len(negatives)}",
    )

    print(
        "\nInterpretation: eligibility means a pair can be considered "
        "by the candidate engine. It does not confirm an overlap."
    )
    print(
        "This is a small curated synthetic dataset, not a "
        "production performance benchmark."
    )


if __name__ == "__main__":
    main()
