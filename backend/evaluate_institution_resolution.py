
from institution_resolution import get_connection, resolve_institution


SAMPLE_SIZE = 25


def main():
    # Read a small, deterministic sample of ground-truth test cases.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    test_id,
                    raw_name,
                    raw_permanent_id,
                    expected_institution_id,
                    expected_resolution_method,
                    expected_status,
                    scenario
                FROM public.institution_resolution_ground_truth
                ORDER BY test_id
                LIMIT %s
                """,
                (SAMPLE_SIZE,),
            )
            test_cases = cur.fetchall()

    if not test_cases:
        print("No ground-truth test cases found.")
        return

    status_correct = 0
    identity_correct = 0
    method_correct = 0
    identity_evaluable = 0
    method_evaluable = 0

    print(f"Evaluating {len(test_cases)} ground-truth cases...\n")

    for test_case in test_cases:
        result = resolve_institution(
            raw_permanent_id=test_case["raw_permanent_id"],
            raw_name=test_case["raw_name"],
        )

        expected_status = test_case["expected_status"]
        actual_status = result["resolution_status"]

        expected_method = test_case["expected_resolution_method"]
        actual_method = result["resolution_method"]

        expected_id = test_case["expected_institution_id"]
        institution = result.get("institution")
        actual_id = institution["institution_id"] if institution else None

        if expected_status is not None:
            status_correct += (
                str(expected_status).casefold()
                == str(actual_status).casefold()
            )

        if expected_id is not None:
            identity_evaluable += 1
            identity_correct += actual_id == expected_id

        if expected_method is not None:
            method_evaluable += 1
            method_correct += (
                str(expected_method).casefold()
                == str(actual_method).casefold()
            )

        print(
            f"Test: {test_case['test_id']} | "
            f"Scenario: {test_case['scenario']} | "
            f"Expected: {expected_status} | "
            f"Actual: {actual_status} | "
            f"Expected institution: {expected_id} | "
            f"Matched institution: {actual_id} | "
            f"Method: {actual_method}"
        )

    print("\n--- Evaluation Summary ---")
    print("Cases evaluated:", len(test_cases))
    print("Status matches:", status_correct, "/", len(test_cases))

    if identity_evaluable:
        print(
            "Institution identity accuracy:",
            f"{identity_correct / identity_evaluable:.1%}",
            f"({identity_correct}/{identity_evaluable})",
        )
    else:
        print("Institution identity accuracy: not measurable")

    if method_evaluable:
        print(
            "Resolution method agreement:",
            f"{method_correct / method_evaluable:.1%}",
            f"({method_correct}/{method_evaluable})",
        )
    else:
        print("Resolution method agreement: not measurable")

    print(
        "\nNote: This is a small initial sample, "
        "not a final performance benchmark."
    )


if __name__ == "__main__":
    main()
