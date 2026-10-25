
"""Evaluate SETU's expanded local synthetic benchmark.

Default mode uses only the existing text heuristic.
--enable-semantic explicitly permits embedding API calls.
No database access or writes occur.
"""

import argparse
import csv
from pathlib import Path

from overlap_engine import score_pair
from embedding_provider import semantic_similarity


CSV_PATH = Path(__file__).resolve().parent / "ground_truth_expansion.csv"


def load_pairs():
    with CSV_PATH.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        rows = list(csv.DictReader(file))

    required = {
        "pair_id",
        "is_true_overlap",
        "pair_type",
        "text_a",
        "text_b",
        "is_synthetic",
    }

    if not rows:
        raise ValueError("The benchmark CSV is empty.")

    missing = required - set(rows[0].keys())
    if missing:
        raise ValueError(f"Missing required CSV columns: {sorted(missing)}")

    for row in rows:
        if row["is_synthetic"].strip().lower() != "true":
            raise ValueError(
                f"{row['pair_id']} is not marked synthetic."
            )

        row["expected_overlap"] = (
            row["is_true_overlap"].strip().lower() == "true"
        )

        if not row["text_a"].strip() or not row["text_b"].strip():
            raise ValueError(f"{row['pair_id']} has empty complaint text.")

    return rows


def heuristic_text_score(text_a, text_b):
    """Return only text similarity, excluding metadata-based scoring."""
    result = score_pair(
        {
            "institution_id": None,
            "group_id": None,
            "category": None,
            "text": text_a,
            "received_date": None,
        },
        {
            "institution_id": None,
            "group_id": None,
            "category": None,
            "text": text_b,
            "received_date": None,
        },
    )

    return float(result.get("text_similarity", 0.0))


def metrics(rows, prediction_key):
    tp = sum(
        bool(row[prediction_key]) and row["expected_overlap"]
        for row in rows
    )
    fp = sum(
        bool(row[prediction_key]) and not row["expected_overlap"]
        for row in rows
    )
    fn = sum(
        not bool(row[prediction_key]) and row["expected_overlap"]
        for row in rows
    )
    tn = sum(
        not bool(row[prediction_key]) and not row["expected_overlap"]
        for row in rows
    )

    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (
        2 * precision * recall / (precision + recall)
        if precision + recall else 0.0
    )

    return tp, fp, fn, tn, precision, recall, f1


def report_threshold(rows, score_key, threshold, prediction_key):
    for row in rows:
        row[prediction_key] = (
            row[score_key] is not None
            and row[score_key] >= threshold
        )

    tp, fp, fn, tn, precision, recall, f1 = metrics(
        rows, prediction_key
    )

    print(
        f"  threshold={threshold:.3f} | "
        f"TP={tp} FP={fp} FN={fn} TN={tn} | "
        f"P={precision:.3f} R={recall:.3f} F1={f1:.3f}"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--enable-semantic",
        action="store_true",
        help="Allow hosted embedding calls for synthetic CSV texts.",
    )
    args = parser.parse_args()

    pairs = load_pairs()
    results = []

    for pair in pairs:
        heuristic = heuristic_text_score(
            pair["text_a"], pair["text_b"]
        )

        row = {
            "pair_id": pair["pair_id"],
            "pair_type": pair["pair_type"],
            "expected_overlap": pair["expected_overlap"],
            "heuristic_score": heuristic,
            "semantic_similarity": None,
            "semantic_status": "not_requested",
            "provider": None,
        }

        if args.enable_semantic:
            semantic = semantic_similarity(
                pair["text_a"],
                pair["text_b"],
            )
            row["semantic_similarity"] = semantic["similarity"]
            row["semantic_status"] = semantic["status"]
            row["provider"] = semantic["provider"]

        results.append(row)

    print("=== SETU Expanded Synthetic Benchmark ===")
    print("Pairs:", len(results))
    print(
        "Positive:",
        sum(row["expected_overlap"] for row in results),
    )
    print(
        "Negative:",
        sum(not row["expected_overlap"] for row in results),
    )
    print(
        "Mode:",
        "semantic enabled" if args.enable_semantic else "heuristic only",
    )
    print("Database access: none")
    print("Database changes: none")

    print("\n=== Pair-level results ===")
    for row in results:
        print(
            f"{row['pair_id']} | {row['pair_type']} | "
            f"expected={row['expected_overlap']} | "
            f"heuristic={row['heuristic_score']:.2f} | "
            f"semantic={row['semantic_similarity']} | "
            f"status={row['semantic_status']}"
        )

    print("\n=== Heuristic text-score thresholds ===")
    for threshold in (50.0, 60.0, 70.0, 80.0):
        report_threshold(
            results,
            "heuristic_score",
            threshold,
            "_heuristic_prediction",
        )

    semantic_rows = [
        row for row in results
        if row["semantic_similarity"] is not None
    ]

    print("\n=== Semantic thresholds ===")
    print("Pairs with semantic scores:", len(semantic_rows))

    if semantic_rows:
        for threshold in (0.80, 0.85, 0.90, 0.95):
            report_threshold(
                semantic_rows,
                "semantic_similarity",
                threshold,
                "_semantic_prediction",
            )
    else:
        print("Skipped: no semantic scores were requested or available.")

    print(
        "\nImportant: labels are synthetic and require review. "
        "Text-only scores are not the full production overlap score."
    )


if __name__ == "__main__":
    main()
