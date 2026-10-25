
"""Create an additional local synthetic benchmark for SETU.

No database access. No external API calls.
The labels are synthetic and should be reviewed before benchmarking.
"""

import csv
from pathlib import Path


OUTPUT_FILE = Path(__file__).resolve().parent / "ground_truth_expansion.csv"

PAIRS = [
    # Positive examples: same underlying issue
    {
        "pair_id": "EXP-P01",
        "is_true_overlap": True,
        "pair_type": "paraphrase",
        "text_a": "The college has not refunded my tuition fee after admission cancellation.",
        "text_b": "I cancelled my admission, but the institution still has not returned my tuition payment.",
        "label_rationale": "Same cancelled admission and outstanding tuition refund.",
    },
    {
        "pair_id": "EXP-P02",
        "is_true_overlap": True,
        "pair_type": "multilingual",
        "text_a": "My college has not returned the fee after I cancelled admission.",
        "text_b": "சேர்க்கையை ரத்து செய்த பிறகும் கல்லூரி கட்டணத்தைத் திருப்பித் தரவில்லை.",
        "label_rationale": "Same admission cancellation and fee-refund issue, expressed in different languages.",
    },
    {
        "pair_id": "EXP-P03",
        "is_true_overlap": True,
        "pair_type": "deposit_refund",
        "text_a": "The hostel has not returned my refundable security deposit after checkout.",
        "text_b": "I vacated the college hostel, but my security deposit is still pending.",
        "label_rationale": "Same hostel deposit not returned after leaving.",
    },
    {
        "pair_id": "EXP-P04",
        "is_true_overlap": True,
        "pair_type": "scholarship_delay",
        "text_a": "My approved scholarship amount has not reached my bank account.",
        "text_b": "Although my scholarship was approved, the payment has not been disbursed.",
        "label_rationale": "Same approved scholarship payment delay.",
    },
    {
        "pair_id": "EXP-P05",
        "is_true_overlap": True,
        "pair_type": "duplicate_charge",
        "text_a": "The examination portal charged me twice for the same examination fee.",
        "text_b": "I paid the exam fee once, but two transactions were deducted for that payment.",
        "label_rationale": "Same double charge for one examination fee.",
    },
    {
        "pair_id": "EXP-P06",
        "is_true_overlap": True,
        "pair_type": "facility",
        "text_a": "The required laboratory equipment has been unavailable to students for three weeks.",
        "text_b": "Students cannot complete practicals because the lab equipment is still not provided.",
        "label_rationale": "Same underlying lack of required laboratory equipment.",
    },
    {
        "pair_id": "EXP-P07",
        "is_true_overlap": True,
        "pair_type": "transport",
        "text_a": "The college bus assigned to our route has repeatedly failed to arrive in the morning.",
        "text_b": "Students on our route keep missing first period because the morning college bus does not arrive.",
        "label_rationale": "Same recurring failure of the morning bus service on one route.",
    },
    {
        "pair_id": "EXP-P08",
        "is_true_overlap": True,
        "pair_type": "document_delay",
        "text_a": "The college has not issued my original transfer certificate despite completing the process.",
        "text_b": "My transfer certificate is still being withheld by the institution after I submitted all required documents.",
        "label_rationale": "Same outstanding transfer certificate for the same student and process.",
    },
    {
        "pair_id": "EXP-P09",
        "is_true_overlap": True,
        "pair_type": "hostel_water",
        "text_a": "There has been no drinking water in our hostel block for several days.",
        "text_b": "Residents of the same hostel block still cannot access drinking water.",
        "label_rationale": "Same continuing drinking-water outage in one hostel block.",
    },
    {
        "pair_id": "EXP-P10",
        "is_true_overlap": True,
        "pair_type": "exam_schedule",
        "text_a": "The department announced two conflicting examination dates for the same subject.",
        "text_b": "Students received different exam dates for the same subject from the department.",
        "label_rationale": "Same subject and same conflicting examination schedule.",
    },

    # Negative examples: similar wording, different underlying issues
    {
        "pair_id": "EXP-N01",
        "is_true_overlap": False,
        "pair_type": "hard_negative_refund",
        "text_a": "My tuition fee has not been refunded after admission cancellation.",
        "text_b": "The hostel has not refunded my security deposit after checkout.",
        "label_rationale": "Different payments and different processes: tuition refund versus hostel deposit.",
    },
    {
        "pair_id": "EXP-N02",
        "is_true_overlap": False,
        "pair_type": "hard_negative_scholarship",
        "text_a": "My approved scholarship payment has not reached my bank account.",
        "text_b": "My scholarship application was rejected because I did not meet the eligibility rules.",
        "label_rationale": "One is a delayed approved payment; the other is an eligibility rejection.",
    },
    {
        "pair_id": "EXP-N03",
        "is_true_overlap": False,
        "pair_type": "hard_negative_transport",
        "text_a": "The morning college bus did not arrive on our route.",
        "text_b": "The college increased the annual bus transportation fee without notice.",
        "label_rationale": "Different issues: missing service versus an unexpected fee increase.",
    },
    {
        "pair_id": "EXP-N04",
        "is_true_overlap": False,
        "pair_type": "hard_negative_lab",
        "text_a": "Required laboratory equipment has not been provided for practical classes.",
        "text_b": "The laboratory is closed because its electrical wiring is under repair.",
        "label_rationale": "Different causes and remedies: missing equipment versus a temporary closure.",
    },
    {
        "pair_id": "EXP-N05",
        "is_true_overlap": False,
        "pair_type": "hard_negative_exam_fee",
        "text_a": "I was charged twice for one examination fee.",
        "text_b": "I paid the examination fee but the portal still blocks my hall ticket.",
        "label_rationale": "Different incidents: duplicate payment versus hall-ticket access.",
    },
    {
        "pair_id": "EXP-N06",
        "is_true_overlap": False,
        "pair_type": "hard_negative_certificate",
        "text_a": "My transfer certificate has not been issued after completing the required process.",
        "text_b": "My original degree certificate contains a spelling mistake in my name.",
        "label_rationale": "Different documents and different problems: delayed transfer certificate versus incorrect degree certificate.",
    },
    {
        "pair_id": "EXP-N07",
        "is_true_overlap": False,
        "pair_type": "hard_negative_hostel",
        "text_a": "Our hostel block has had no drinking water for several days.",
        "text_b": "The hostel mess has served unsafe food this week.",
        "label_rationale": "Different hostel services and underlying incidents.",
    },
    {
        "pair_id": "EXP-N08",
        "is_true_overlap": False,
        "pair_type": "hard_negative_schedule",
        "text_a": "The department published conflicting dates for the same subject examination.",
        "text_b": "The department changed the examination hall after the date was confirmed.",
        "label_rationale": "Different scheduling issues: conflicting dates versus a venue change.",
    },
    {
        "pair_id": "EXP-N09",
        "is_true_overlap": False,
        "pair_type": "hard_negative_admission",
        "text_a": "The institution has not refunded tuition after I cancelled admission.",
        "text_b": "The institution has not confirmed my admission because document verification is pending.",
        "label_rationale": "Different stages and issues: post-cancellation refund versus pending admission verification.",
    },
    {
        "pair_id": "EXP-N10",
        "is_true_overlap": False,
        "pair_type": "hard_negative_same_topic",
        "text_a": "A student was charged twice for the examination fee for Semester One.",
        "text_b": "A different student was charged twice for the examination fee for Semester Two.",
        "label_rationale": "Similar wording but deliberately different students and separate examination transactions.",
    },
]


def main():
    if len(PAIRS) != 20:
        raise ValueError("Expected exactly 20 benchmark pairs.")

    ids = [row["pair_id"] for row in PAIRS]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate pair IDs found.")

    positives = sum(row["is_true_overlap"] for row in PAIRS)
    negatives = len(PAIRS) - positives

    fieldnames = [
        "pair_id",
        "is_true_overlap",
        "pair_type",
        "text_a",
        "text_b",
        "label_rationale",
        "is_synthetic",
    ]

    with OUTPUT_FILE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for pair in PAIRS:
            writer.writerow({
                **pair,
                "is_synthetic": True,
            })

    print("Synthetic benchmark created successfully.")
    print("File:", OUTPUT_FILE)
    print("Total pairs:", len(PAIRS))
    print("Positive pairs:", positives)
    print("Negative pairs:", negatives)
    print("Database changes: none")
    print("External API calls: none")
    print("Encoding: UTF-8 with BOM")


if __name__ == "__main__":
    main()
