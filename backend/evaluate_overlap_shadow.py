
"""SETU Phase 4.6: read-only shadow evaluation.

Default mode does not call embedding providers.
Pass --enable-semantic to explicitly permit external embedding calls
for non-restricted pairs only.
"""

import argparse
import math
import statistics

from institution_resolution import get_connection
from overlap_engine import score_pair
from embedding_provider import semantic_similarity


def cosine_safe_text(value):
    """Return a usable text string without exposing database values."""
    if value is None:
        return ""
    return str(value).strip()


def make_case(case):
    return {
        "institution_id": case["institution_id"],
        "group_id": case["group_id"],
        "category": case["category"],
        "text": case["text"],
        "received_date": case["received_date"],
    }


def main():
    parser = argparse.ArgumentParser(
        description="Read-only SETU overlap shadow evaluation."
    )
    parser.add_argument(
        "--enable-semantic",
        action="store_true",
        help=(
            "Allow embedding API calls for non-restricted pairs. "
            "May consume API quota and sends text to a configured provider."
        ),
    )
    args = parser.parse_args()

    results = []

    # Read-only SELECT queries only.
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM public.ground_truth_pairs
                ORDER BY pair_id
                """
            )
            pairs = cur.fetchall()

            for pair in pairs:
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

                row = {
                    "pair_id": pair["pair_id"],
                    "overlap_type": pair["overlap_type"],
                    "expected_overlap": pair["is_true_overlap"],
                    "heuristic_score": None,
                    "semantic_similarity": None,
                    "semantic_status": "not_requested",
                    "provider": None,
                    "restricted": False,
                    "error": None,
                }

                if case_a is None or case_b is None:
                    row["error"] = "Complaint record not found"
                    results.append(row)
                    continue

                restricted = (
                    bool(case_a["is_restricted"])
                    or bool(case_b["is_restricted"])
                )
                row["restricted"] = restricted

                heuristic = score_pair(
                    make_case(case_a),
                    make_case(case_b),
                )
                row["heuristic_score"] = heuristic["score"]

                # Restricted text is never sent to an embedding provider.
                if restricted:
                    row["semantic_status"] = "skipped_restricted"

                elif not args.enable_semantic:
                    row["semantic_status"] = "not_requested"

                else:
                    text_a = cosine_safe_text(case_a["text"])
                    text_b = cosine_safe_text(case_b["text"])

                    if not text_a or not text_b:
                        row["semantic_status"] = "skipped_empty_text"
                    else:
                        semantic = semantic_similarity(text_a, text_b)
                        row["semantic_status"] = semantic["status"]
                        row["semantic_similarity"] = semantic["similarity"]
                        row["provider"] = semantic["provider"]

                results.append(row)

    valid = [r for r in results if r["error"] is None]
    scored = [
        r for r in valid
        if r["semantic_similarity"] is not None
    ]
    positives = [r for r in scored if r["expected_overlap"] is True]
    negatives = [r for r in scored if r["expected_overlap"] is False]

    print("=== SETU Phase 4.6: Shadow Evaluation ===")
    print("Mode:", "semantic enabled" if args.enable_semantic else "dry run")
    print("Database changes: none")
    print("Ground-truth pairs:", len(results))
    print("Pairs evaluated by heuristic:", len(valid))
    print("Restricted pairs skipped for semantics:",
          sum(r["restricted"] for r in valid))
    print("Pairs with semantic scores:", len(scored))

    print("\n=== Pair-level results ===")
    for row in results:
        print(
            f"\n{row['pair_id']} | {row['overlap_type']}"
        )
        if row["error"]:
            print("Error:", row["error"])
            continue

        print("Expected overlap:", row["expected_overlap"])
        print("Heuristic score:", row["heuristic_score"])
        print("Semantic status:", row["semantic_status"])
        print("Semantic similarity:", row["semantic_similarity"])
        print("Provider:", row["provider"])

    
    print("\n=== Threshold comparison ===")

    def report_metrics(name, predictions, labels):
        tp = sum(p and y for p, y in zip(predictions, labels))
        fp = sum(p and not y for p, y in zip(predictions, labels))
        fn = sum(not p and y for p, y in zip(predictions, labels))
        tn = sum(not p and not y for p, y in zip(predictions, labels))

        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (
            2 * precision * recall / (precision + recall)
            if precision + recall else 0.0
        )

        print(f"\n{name}")
        print(f"  TP={tp}, FP={fp}, FN={fn}, TN={tn}")
        print(f"  Precision: {precision:.3f}")
        print(f"  Recall:    {recall:.3f}")
        print(f"  F1:        {f1:.3f}")

    if scored:
        labels = [r["expected_overlap"] is True for r in scored]

        for threshold in (0.85, 0.90, 0.95, 0.99):
            predictions = [
                r["semantic_similarity"] >= threshold
                for r in scored
            ]
            report_metrics(
                f"Semantic threshold >= {threshold:.2f}",
                predictions,
                labels,
            )

        for threshold in (50, 75):
            predictions = [
                r["heuristic_score"] >= threshold
                for r in scored
            ]
            report_metrics(
                f"Heuristic threshold >= {threshold}",
                predictions,
                labels,
            )
    else:
        print("No semantic scores available; threshold comparison skipped.")

    
    print("\n=== Experimental hybrid comparison ===")

    # Compare only pairs with both heuristic and semantic scores.
    # This is offline evaluation; production rankings are unchanged.
    if scored:
        labels = [r["expected_overlap"] is True for r in scored]

        for heuristic_weight in (0.8, 0.6, 0.4):
            semantic_weight = 1.0 - heuristic_weight

            hybrid_scores = [
                heuristic_weight * (r["heuristic_score"] / 100.0)
                + semantic_weight * r["semantic_similarity"]
                for r in scored
            ]

            print(
                f"\nWeights: heuristic={heuristic_weight:.0%}, "
                f"semantic={semantic_weight:.0%}"
            )

            # Explore thresholds; do not treat them as production values.
            for threshold in (0.65, 0.70, 0.75, 0.80, 0.85):
                predictions = [
                    score >= threshold for score in hybrid_scores
                ]

                tp = sum(p and y for p, y in zip(predictions, labels))
                fp = sum(p and not y for p, y in zip(predictions, labels))
                fn = sum(not p and y for p, y in zip(predictions, labels))
                tn = sum(not p and not y for p, y in zip(predictions, labels))

                precision = tp / (tp + fp) if tp + fp else 0.0
                recall = tp / (tp + fn) if tp + fn else 0.0
                f1 = (
                    2 * precision * recall / (precision + recall)
                    if precision + recall else 0.0
                )

                print(
                    f"  threshold={threshold:.2f} | "
                    f"TP={tp} FP={fp} FN={fn} TN={tn} | "
                    f"P={precision:.3f} R={recall:.3f} F1={f1:.3f}"
                )
    else:
        print("No semantic scores available; hybrid comparison skipped.")

    print("\n=== Interpretation ===")
    print(
        "Metrics describe only this small curated dataset. "
        "Thresholds are exploratory, not production recommendations."
    )
    print(
        "Semantic similarity is not proof of an overlap. "
        "Keep human review and the existing production ranking unchanged."
    )


if __name__ == "__main__":
    main()
