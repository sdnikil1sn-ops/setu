
import csv
import random
from collections import Counter, defaultdict
from pathlib import Path

from institution_resolution import get_connection
from overlap_engine import score_pair


OUTPUT_FILE = Path(__file__).parent / "overlap_review_sample.csv"
SAMPLE_PER_BUCKET_AND_SCOPE = 5
RANDOM_SEED = 42


def score_bucket(score):
    if score < 65:
        return "50-64"
    if score < 75:
        return "65-74"
    if score < 85:
        return "75-84"
    if score < 95:
        return "85-94"
    return "95-100"


def fetch_candidates():
    candidates = []

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.case_id AS id_a,
                    a.case_ref AS ref_a,
                    a.source_system AS source_a,
                    a.institution_id AS institution_a,
                    a.group_id AS group_a,
                    a.category AS category_a,
                    a.text AS text_a,
                    a.received_date AS date_a,
                    a.is_restricted AS restricted_a,

                    b.case_id AS id_b,
                    b.case_ref AS ref_b,
                    b.source_system AS source_b,
                    b.institution_id AS institution_b,
                    b.group_id AS group_b,
                    b.category AS category_b,
                    b.text AS text_b,
                    b.received_date AS date_b,
                    b.is_restricted AS restricted_b

                FROM public.complaint_cases AS a
                JOIN public.complaint_cases AS b
                  ON a.source_system <> b.source_system
                 AND a.case_id < b.case_id
                 AND (
                      (
                          a.institution_id IS NOT NULL
                          AND a.institution_id = b.institution_id
                      )
                      OR
                      (
                          a.group_id IS NOT NULL
                          AND a.group_id = b.group_id
                      )
                 )
                WHERE COALESCE(a.is_restricted, FALSE) = FALSE
                  AND COALESCE(b.is_restricted, FALSE) = FALSE
                """
            )

            rows = cur.fetchall()

    for row in rows:
        same_institution = (
            row["institution_a"] is not None
            and row["institution_a"] == row["institution_b"]
        )

        same_group = (
            row["group_a"] is not None
            and row["group_a"] == row["group_b"]
        )

        evidence = score_pair(
            {
                "institution_id": row["institution_a"],
                "group_id": row["group_a"],
                "category": row["category_a"],
                "text": row["text_a"],
                "received_date": row["date_a"],
            },
            {
                "institution_id": row["institution_b"],
                "group_id": row["group_b"],
                "category": row["category_b"],
                "text": row["text_b"],
                "received_date": row["date_b"],
            },
        )

        if evidence["score"] < 50:
            continue

        scope = "institution" if same_institution else "group"

        candidates.append({
            "case_a": row["ref_a"] or row["id_a"],
            "case_b": row["ref_b"] or row["id_b"],
            "source_a": row["source_a"],
            "source_b": row["source_b"],
            "scope": scope,
            "category_a": row["category_a"],
            "category_b": row["category_b"],
            "score": evidence["score"],
            "text_similarity": evidence["text_similarity"],
            "days_apart": evidence["days_apart"],
            "reasons": "; ".join(evidence["reasons"]),
            "text_a": row["text_a"] or "",
            "text_b": row["text_b"] or "",
            "human_label": "",
            "review_notes": "",
        })

    return candidates


def main():
    print("Reading eligible cross-bureau candidates...")
    candidates = fetch_candidates()

    print("Eligible candidates scoring at least 50:", len(candidates))

    buckets = defaultdict(list)

    for candidate in candidates:
        key = (
            candidate["scope"],
            score_bucket(candidate["score"]),
        )
        buckets[key].append(candidate)

    rng = random.Random(RANDOM_SEED)
    selected = []

    for key in sorted(buckets):
        group = buckets[key]
        count = min(SAMPLE_PER_BUCKET_AND_SCOPE, len(group))
        selected.extend(rng.sample(group, count))

    selected.sort(
        key=lambda item: (
            item["scope"],
            item["score"],
            item["case_a"],
            item["case_b"],
        )
    )

    fields = [
        "case_a",
        "case_b",
        "source_a",
        "source_b",
        "scope",
        "category_a",
        "category_b",
        "score",
        "text_similarity",
        "days_apart",
        "reasons",
        "text_a",
        "text_b",
        "human_label",
        "review_notes",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(selected)

    summary = Counter(
        (item["scope"], score_bucket(item["score"]))
        for item in selected
    )

    print("\n=== Review sample summary ===")
    print("Selected pairs:", len(selected))

    for (scope, bucket), count in sorted(summary.items()):
        print(f"{scope:12} | score {bucket:6} | {count} pairs")

    print("\nCSV created:", OUTPUT_FILE)
    print("Database changes: none")
    print("Google API requests: none")
    print(
        "\nReview labels: true_overlap, false_overlap, or uncertain."
    )
    print(
        "Only label a pair true_overlap when the complaint texts "
        "and available context support the same underlying issue."
    )
    print(
        "This sample is for human review, not a statistically "
        "representative estimate of production accuracy."
    )


if __name__ == "__main__":
    main()
