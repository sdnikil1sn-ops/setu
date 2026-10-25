
import csv
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
GROUND_TRUTH_CSV = BASE_DIR / "ground_truth_expansion.csv"
REVIEW_CSV = BASE_DIR / "ground_truth_evidence_review.csv"

SUMMARY_CSV = BASE_DIR / "evidence_classification_summary.csv"
ERRORS_CSV = BASE_DIR / "evidence_classification_errors.csv"

POSITIVE_CATEGORY = "same_incident_candidate"


def parse_bool(value):
    normalized = str(value).strip().casefold()

    if normalized in {"true", "1", "yes"}:
        return True

    if normalized in {"false", "0", "no"}:
        return False

    raise ValueError(f"Unrecognized boolean label: {value!r}")


def read_csv(path):
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError(f"CSV contains no records: {path}")

    return rows


def safe_ratio(numerator, denominator):
    return numerator / denominator if denominator else 0.0


def main():
    ground_truth_rows = read_csv(GROUND_TRUTH_CSV)
    review_rows = read_csv(REVIEW_CSV)

    truth_by_id = {
        row["pair_id"]: parse_bool(row["is_true_overlap"])
        for row in ground_truth_rows
    }

    review_by_id = {
        row["pair_id"]: row
        for row in review_rows
    }

    if len(truth_by_id) != len(ground_truth_rows):
        raise ValueError("Duplicate pair_id found in ground-truth CSV.")

    if len(review_by_id) != len(review_rows):
        raise ValueError("Duplicate pair_id found in review CSV.")

    missing_reviews = set(truth_by_id) - set(review_by_id)
    missing_truth = set(review_by_id) - set(truth_by_id)

    if missing_reviews or missing_truth:
        raise ValueError(
            "CSV pair IDs do not match. "
            f"Missing review rows: {sorted(missing_reviews)}; "
            f"missing ground-truth rows: {sorted(missing_truth)}"
        )

    true_positive = 0
    false_positive = 0
    false_negative = 0
    true_negative = 0

    category_counts = Counter()
    category_truth_counts = Counter()
    error_rows = []
    summary_rows = []

    for pair_id, expected_same_incident in truth_by_id.items():
        review = review_by_id[pair_id]

        category = review["incident_relationship"].strip()
        predicted_candidate = category == POSITIVE_CATEGORY

        category_counts[category] += 1
        category_truth_counts[
            (category, expected_same_incident)
        ] += 1

        if expected_same_incident and predicted_candidate:
            true_positive += 1
            outcome = "true_positive"

        elif not expected_same_incident and predicted_candidate:
            false_positive += 1
            outcome = "false_positive"

        elif expected_same_incident and not predicted_candidate:
            false_negative += 1
            outcome = "missed_positive_candidate"

        else:
            true_negative += 1
            outcome = "not_flagged_negative_label"

        record = {
            "pair_id": pair_id,
            "expected_same_incident": str(
                expected_same_incident
            ),
            "incident_relationship": category,
            "candidate_flag": str(predicted_candidate),
            "evaluation_outcome": outcome,
            "evidence_level": review.get("evidence_level", ""),
            "evidence_signals": review.get("evidence_signals", ""),
            "incident_explanation": review.get(
                "incident_explanation", ""
            ),
        }

        summary_rows.append(record)

        if outcome in {
            "false_positive",
            "missed_positive_candidate",
        }:
            error_rows.append(record)

    precision = safe_ratio(
        true_positive,
        true_positive + false_positive,
    )

    recall = safe_ratio(
        true_positive,
        true_positive + false_negative,
    )

    f1 = safe_ratio(
        2 * precision * recall,
        precision + recall,
    )

    total = len(summary_rows)
    flagged = true_positive + false_positive
    labelled_positive = true_positive + false_negative

    # Write the per-pair evaluation report.
    fields = list(summary_rows[0].keys())

    with SUMMARY_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summary_rows)

    with ERRORS_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(error_rows)

    print("=== SETU Evidence Classification Evaluation ===")
    print(f"Pairs evaluated: {total}")
    print("Database access: none")
    print("Database changes: none")
    print("External API calls: none")

    print("\n=== Candidate-detection metrics ===")
    print(f"True positives: {true_positive}")
    print(f"False positives: {false_positive}")
    print(f"Missed positive candidates: {false_negative}")
    print(f"Negative-labelled pairs not flagged: {true_negative}")
    print(f"Precision: {precision:.3f}")
    print(f"Recall: {recall:.3f}")
    print(f"F1 score: {f1:.3f}")
    print(f"Candidate flags: {flagged}/{total}")
    print(f"Ground-truth positive pairs: {labelled_positive}/{total}")

    print("\n=== Incident category vs ground truth ===")
    for category in sorted(category_counts):
        positive = category_truth_counts[(category, True)]
        negative = category_truth_counts[(category, False)]

        print(
            f"{category}: "
            f"ground-truth positive={positive}, "
            f"ground-truth negative={negative}, "
            f"total={category_counts[category]}"
        )

    print("\n=== Output files ===")
    print(f"Per-pair report: {SUMMARY_CSV}")
    print(f"Error cases: {ERRORS_CSV}")

    print(
        "\nInterpretation: only same_incident_candidate counts as "
        "a positive prediction. Other categories count as not flagged "
        "for this metric; they are NOT treated as confirmed negatives. "
        "These results measure agreement with the current synthetic "
        "benchmark, not real-world production accuracy."
    )


if __name__ == "__main__":
    main()
