
import csv
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent / "ground_truth_expansion.csv"

NEW_CASES = [
    # Same underlying incident: positive
    {
        "pair_id": "EXP2-P01",
        "is_true_overlap": "True",
        "pair_type": "same_incident_different_students",
        "text_a": "Several students were charged twice for the same examination fee transaction batch on 12 August.",
        "text_b": "Our class received duplicate examination fee deductions from the college transaction batch dated 12 August.",
        "label_rationale": "Positive only if the shared batch and incident date identify the same underlying incident; multiple affected students do not automatically mean separate incidents.",
    },
    {
        "pair_id": "EXP2-P02",
        "is_true_overlap": "True",
        "pair_type": "same_incident_missing_reference",
        "text_a": "My admission cancellation refund for application ADM-2041 has not been processed.",
        "text_b": "The refund for my cancelled admission is still pending. My application number is ADM-2041.",
        "label_rationale": "Same application identifier and same pending refund incident.",
    },
    {
        "pair_id": "EXP2-P03",
        "is_true_overlap": "True",
        "pair_type": "same_incident_paraphrase",
        "text_a": "The college has not repaired the water supply failure reported in hostel block C on Monday.",
        "text_b": "The water outage in hostel C reported on Monday remains unresolved.",
        "label_rationale": "Same location, event, report date, and unresolved outage.",
    },
    {
        "pair_id": "EXP2-P04",
        "is_true_overlap": "True",
        "pair_type": "same_incident_different_language",
        "text_a": "The college has not returned the fee for admission application ADM-782 after cancellation.",
        "text_b": "சேர்க்கை விண்ணப்பம் ADM-782 ரத்து செய்யப்பட்டும் கட்டணம் திரும்ப வழங்கப்படவில்லை.",
        "label_rationale": "Same application identifier and refund incident expressed in English and Tamil.",
    },
    {
        "pair_id": "EXP2-P05",
        "is_true_overlap": "True",
        "pair_type": "same_incident_conflicting_wording",
        "text_a": "The examination hall allocation for seat group G12 was incorrect in the timetable published on 4 September.",
        "text_b": "The 4 September timetable assigned seat group G12 to the wrong examination hall.",
        "label_rationale": "Both describe the same allocation error in the same timetable release.",
    },

    # Shared systemic issue, but not necessarily the same individual incident
    {
        "pair_id": "EXP2-S01",
        "is_true_overlap": "False",
        "pair_type": "shared_systemic_issue",
        "text_a": "Student A's scholarship payment for the first semester is delayed.",
        "text_b": "Student B's scholarship payment for the first semester is delayed.",
        "label_rationale": "Separate student-level cases. They may share a systemic cause, so relate them for investigation rather than merge them as one incident.",
    },
    {
        "pair_id": "EXP2-S02",
        "is_true_overlap": "False",
        "pair_type": "shared_systemic_issue",
        "text_a": "The north campus bus was late on Monday because the route was understaffed.",
        "text_b": "The south campus bus was late on Tuesday because the route was understaffed.",
        "label_rationale": "Different campus routes and dates; potentially the same systemic staffing problem, not the same incident.",
    },
    {
        "pair_id": "EXP2-S03",
        "is_true_overlap": "False",
        "pair_type": "shared_systemic_issue",
        "text_a": "Three students cannot download certificates because the certificate portal is unavailable for their applications.",
        "text_b": "Another student cannot download a certificate because the same portal is unavailable for a different application.",
        "label_rationale": "Distinct application-level cases potentially linked to one portal outage. Keep separate and link to a shared issue if verified.",
    },

    # Similar topic, different underlying incidents: negative
    {
        "pair_id": "EXP2-N01",
        "is_true_overlap": "False",
        "pair_type": "same_topic_different_transactions",
        "text_a": "Student A was charged twice for the Semester One examination fee on transaction TX-101.",
        "text_b": "Student B was charged twice for the Semester Two examination fee on transaction TX-909.",
        "label_rationale": "Different students, semesters, and transaction references.",
    },
    {
        "pair_id": "EXP2-N02",
        "is_true_overlap": "False",
        "pair_type": "same_topic_different_events",
        "text_a": "The college bus did not arrive on route R4 on Monday morning.",
        "text_b": "The college bus did not arrive on route R4 on Friday evening.",
        "label_rationale": "Same route and failure type, but distinct dates and separate service events.",
    },
    {
        "pair_id": "EXP2-N03",
        "is_true_overlap": "False",
        "pair_type": "same_topic_different_applications",
        "text_a": "Admission refund for application ADM-110 was delayed after cancellation.",
        "text_b": "Admission refund for application ADM-782 was delayed after cancellation.",
        "label_rationale": "Different application identifiers indicate separate refund cases.",
    },
    {
        "pair_id": "EXP2-N04",
        "is_true_overlap": "False",
        "pair_type": "same_topic_different_exam_events",
        "text_a": "The department published the wrong date for the mathematics examination scheduled for 10 October.",
        "text_b": "The department published the wrong date for the physics examination scheduled for 18 October.",
        "label_rationale": "Different examinations and scheduled dates; similar administrative error type does not establish the same incident.",
    },

    # Missing or conflicting evidence: labels describe the supplied synthetic facts
    {
        "pair_id": "EXP2-U01",
        "is_true_overlap": "False",
        "pair_type": "missing_identifiers",
        "text_a": "My college has not refunded my admission fee after cancellation.",
        "text_b": "The admission fee refund is still pending after I cancelled my seat.",
        "label_rationale": "Insufficient identifiers to establish that these are the same case. Treat as unresolved for human review; False means not confirmed as the same incident, not proven unrelated.",
    },
    {
        "pair_id": "EXP2-U02",
        "is_true_overlap": "False",
        "pair_type": "conflicting_identifiers",
        "text_a": "Refund for admission application ADM-300 is pending.",
        "text_b": "Refund for admission application ADM-301 is pending.",
        "label_rationale": "Conflicting application identifiers suggest distinct cases. Verify identifiers before making a final decision.",
    },
    {
        "pair_id": "EXP2-U03",
        "is_true_overlap": "False",
        "pair_type": "same_topic_conflicting_dates",
        "text_a": "The hostel water outage was reported on 2 November in block A.",
        "text_b": "The hostel water outage was reported on 19 November in block D.",
        "label_rationale": "Different blocks and report dates; same topic alone is insufficient evidence of one incident.",
    },
]


def main():
    if not CSV_PATH.exists():
        raise FileNotFoundError(
            f"Benchmark CSV not found: {CSV_PATH}"
        )

    with CSV_PATH.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames
        existing_rows = list(reader)

    required_columns = {
        "pair_id",
        "is_true_overlap",
        "pair_type",
        "text_a",
        "text_b",
        "label_rationale",
        "is_synthetic",
    }

    if not fieldnames or not required_columns.issubset(fieldnames):
        raise ValueError(
            "The existing CSV does not have the expected benchmark columns."
        )

    existing_ids = {row["pair_id"] for row in existing_rows}
    duplicates = [
        case["pair_id"]
        for case in NEW_CASES
        if case["pair_id"] in existing_ids
    ]

    if duplicates:
        raise ValueError(
            f"These pair IDs already exist; no changes made: {duplicates}"
        )

    for case in NEW_CASES:
        case["is_synthetic"] = "True"

    combined_rows = existing_rows + NEW_CASES

    with CSV_PATH.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(combined_rows)

    print("Ground-truth benchmark expanded successfully.")
    print(f"Original pairs: {len(existing_rows)}")
    print(f"Added pairs: {len(NEW_CASES)}")
    print(f"Total pairs: {len(combined_rows)}")
    print(f"Output: {CSV_PATH}")
    print("Database access: none")
    print("External API calls: none")
    print("Database changes: none")
    print("All added labels are synthetic and require review.")


if __name__ == "__main__":
    main()
