
import csv
import re
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_CSV = BASE_DIR / "ground_truth_expansion.csv"
OUTPUT_CSV = BASE_DIR / "ground_truth_evidence_review.csv"

MONTHS = (
    "January|February|March|April|May|June|July|August|September|"
    "October|November|December"
)
WEEKDAYS = (
    "Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
)

STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "for", "to", "of",
    "in", "on", "at", "by", "from", "with", "after", "before",
    "my", "our", "their", "his", "her", "this", "that", "same",
    "different", "has", "have", "had", "was", "were", "is", "are",
    "not", "still", "because", "another", "student", "students",
    "college", "department", "reported", "issue", "problem",
}

# Broad topic indicators, not proof of a shared root cause.
SYSTEMIC_TERMS = {
    "scholarship", "payment", "refund", "fee", "admission",
    "examination", "exam", "timetable", "hall", "certificate",
    "portal", "hostel", "water", "bus", "route", "transport",
    "laboratory", "lab", "delay", "outage", "unavailable",
    "charged", "charge", "transaction", "semester", "schedule",
    "allocation", "staffing", "staffed", "application",
}


def extract_values(text, patterns):
    values = set()

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            values.add(match.group(1).casefold())

    return values


def extract_evidence(text):
    text = text or ""

    application_ids = extract_values(
        text,
        [r"\b(ADM-?\d+)\b"],
    )

    transaction_ids = extract_values(
        text,
        [r"\b(TX-?\d+)\b"],
    )
    
    batch_references = extract_values(
        text,
        [
            r"\b((?:transaction\s+)?batch(?:\s+(?:dated|on))?\s+"
            r"(?:\d{1,2}\s+(?:"
            + MONTHS
            + r")|(?:"
            + MONTHS
            + r")\s+\d{1,2}|\d{1,2}[/-]\d{1,2}"
            r"(?:[/-]\d{2,4})?))\b",
            r"\b(batch\s+(?:reference|ref|id)\s*[:#-]?\s*[a-z0-9-]+)\b",
        ],
    )

    batch_references = {
        re.sub(
            r"\b(?:transaction\s+)?batch\s+(?:dated|on)\s+",
            "batch ",
            value,
        )
        for value in batch_references
    }


    semesters = extract_values(
        text,
        [
            r"\b(semester\s+(?:one|two|three|four|1|2|3|4))\b",
            r"\b((?:first|second|third|fourth)\s+semester)\b",
        ],
    )

    dates = extract_values(
        text,
        [
            rf"\b({WEEKDAYS})\b",
            rf"\b(\d{{1,2}}\s+(?:{MONTHS}))\b",
            rf"\b((?:{MONTHS})\s+\d{{1,2}})\b",
            r"\b(\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?)\b",
        ],
    )

    
    
    locations = set()

    location_patterns = [
        # Explicit hostel identifiers: "hostel block C" or "hostel C"
        r"\bhostel\s+(?:block\s+)?([a-z]|\d{1,2})\b",

        # Explicit route identifiers: "route R4" or "route 4A"
        r"\broute\s+([a-z]?\d+[a-z]?|\d+[a-z])\b",

        # Named campus
        r"\b((?:north|south|east|west)\s+campus)\b",

        # Explicit seat-group identifier
        r"\b(seat\s+group\s+[a-z0-9]+)\b",
    ]

    for pattern in location_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            value = match.group(1).casefold()

            if pattern == location_patterns[0]:
                value = f"hostel block {value}"
            elif pattern == location_patterns[1]:
                value = f"route {value}"
            else:
                value = " ".join(value.split())

            locations.add(value)

    tokens = {
        token
        for token in re.findall(r"[a-z0-9]+", text.casefold())
        if len(token) > 2 and token not in STOPWORDS
    }

    topic_terms = tokens & SYSTEMIC_TERMS

    return {
        "application_ids": application_ids,
        "transaction_ids": transaction_ids,
        "semesters": semesters,
        "dates": dates,
        "locations": locations,
        "topic_terms": topic_terms,
        "tokens": tokens,
        "batch_references": batch_references,
    }

def compare_evidence(text_a, text_b):
    a = extract_evidence(text_a)
    b = extract_evidence(text_b)

    shared_application_ids = (
        a["application_ids"] & b["application_ids"]
    )
    shared_transaction_ids = (
        a["transaction_ids"] & b["transaction_ids"]
    )
    shared_batch_references = (
        a["batch_references"] & b["batch_references"]
    )

    conflicting_application_ids = (
        bool(a["application_ids"])
        and bool(b["application_ids"])
        and not shared_application_ids
    )
    conflicting_transaction_ids = (
        bool(a["transaction_ids"])
        and bool(b["transaction_ids"])
        and not shared_transaction_ids
    )

    shared_semesters = a["semesters"] & b["semesters"]
    different_semesters = (
        bool(a["semesters"])
        and bool(b["semesters"])
        and not shared_semesters
    )

    shared_dates = a["dates"] & b["dates"]
    different_dates = (
        bool(a["dates"])
        and bool(b["dates"])
        and not shared_dates
    )

    shared_locations = a["locations"] & b["locations"]
    different_locations = (
        bool(a["locations"])
        and bool(b["locations"])
        and not shared_locations
    )

    shared_topic_terms = a["topic_terms"] & b["topic_terms"]

    # Explainable phrase-level support for common complaint patterns.
    # This is supporting evidence only, not proof of a shared incident.
    text_a_normalized = " ".join(text_a.casefold().split())
    text_b_normalized = " ".join(text_b.casefold().split())

    paraphrase_groups = {

        "admission_fee_refund": {
            "admission cancellation",
            "cancelled admission",
            "canceled admission",
            "fee refund",
            "tuition refund",
            "returned the fee",
            "returned my tuition",
            "tuition payment",
            "சேர்க்கையை ரத்து",
            "கட்டணத்தைத் திருப்பித் தர",
            "கட்டணத்தை திருப்பித் தர",
        },

        "scholarship_payment_delay": {
            "scholarship",
            "bank account",
            "payment has not been disbursed",
            "payment delay",
        },
        "laboratory_equipment_unavailable": {
            "laboratory equipment",
            "lab equipment",
            "not provided",
            "unavailable",
            "cannot complete practicals",
        },
        "college_bus_service_failure": {
            "college bus",
            "morning",
            "route",
            "does not arrive",
            "failed to arrive",
            "missing first period",
        },
        "transfer_certificate_delay": {
            "transfer certificate",
            "not issued",
            "still being withheld",
            "required documents",
        },
        "hostel_drinking_water": {
            "drinking water",
            "hostel block",
            "no drinking water",
            "cannot access drinking water",
        },
        "examination_schedule_conflict": {
            "examination dates",
            "exam dates",
            "same subject",
            "conflicting",
            "different exam dates",
        },
        "duplicate_examination_fee": {
            "examination fee",
            "exam fee",
            "charged twice",
            "two transactions",
            "deducted",
        },
        "hostel_deposit_refund": {
            "security deposit",
            "refundable security deposit",
            "refundable deposit",
            "deposit is still pending",
            "deposit has not been returned",
            "deposit not returned",
            "hostel deposit",
            "after checkout",
            "after vacating",
        },
    }

    text_a_combined = text_a_normalized
    text_b_combined = text_b_normalized

    matched_paraphrase_groups = []

    for group_name, phrases in paraphrase_groups.items():
        matches_a = any(phrase in text_a_combined for phrase in phrases)
        matches_b = any(phrase in text_b_combined for phrase in phrases)

        if matches_a and matches_b:
            matched_paraphrase_groups.append(group_name)

    paraphrase_support = bool(matched_paraphrase_groups)
    # Identify specific complaint intents for evidence reporting.
    # Intent matches describe subject matter, not incident identity.
    complaint_intents = {
        "admission_fee_refund": [
    "tuition fee",
    "tuition payment",
    "admission cancellation",
    "admission fee",
    "fee refund",
    "returned the fee",
    "சேர்க்கையை ரத்து",
    "கட்டணத்தைத் திருப்பித் தர",
    "கட்டணத்தை திருப்பித் தர",
],
        "hostel_deposit_refund": [
            "security deposit",
            "refundable deposit",
            "deposit is still pending",
        ],
        "scholarship_payment_delay": [
            "scholarship",
            "payment has not been disbursed",
            "payment has not reached",
            "bank account",
        ],
        "duplicate_examination_fee": [
            "examination fee",
            "exam fee",
            "charged twice",
            "two transactions",
        ],
        "laboratory_equipment_unavailable": [
            "laboratory equipment",
            "lab equipment",
            "not provided",
            "unavailable to students",
        ],
        "college_bus_service_failure": [
            "college bus",
            "bus service",
            "does not arrive",
            "failed to arrive",
        ],
        "transfer_certificate_delay": [
            "transfer certificate",
            "not issued",
            "being withheld",
        ],
        "hostel_drinking_water": [
            "drinking water",
            "water outage",
            "no drinking water",
        ],
        "examination_schedule_conflict": [
            "examination dates",
            "exam dates",
            "conflicting examination",
            "same subject",
        ],
    }

    intents_a = {
        intent
        for intent, phrases in complaint_intents.items()
        if any(phrase in text_a_normalized for phrase in phrases)
    }

    intents_b = {
        intent
        for intent, phrases in complaint_intents.items()
        if any(phrase in text_b_normalized for phrase in phrases)
    }

    shared_complaint_intents = intents_a & intents_b
    # Distinguish different complaint intents that share broad topic words.
    contrast_pairs = [
        (
            "scholarship_payment_delay",
            "scholarship_eligibility_rejection",
            [
                "payment has not reached",
                "payment has not been disbursed",
                "payment delay",
            ],
            [
                "application was rejected",
                "eligibility rules",
                "did not meet the eligibility",
            ],
        ),
        (
            "duplicate_fee_charge",
            "hall_ticket_access",
            [
                "charged twice",
                "two transactions",
                "deducted twice",
            ],
            [
                "hall ticket",
                "blocks my hall ticket",
                "hall-ticket access",
            ],
        ),
        (
            "hostel_water_outage",
            "hostel_food_safety",
            [
                "drinking water",
                "water outage",
                "no water",
            ],
            [
                "unsafe food",
                "hostel mess",
                "food safety",
            ],
        ),
    ]

    contrasting_contexts = []

    for name_a, name_b, phrases_a, phrases_b in contrast_pairs:
        a_matches_first = any(
            phrase in text_a_normalized for phrase in phrases_a
        )
        a_matches_second = any(
            phrase in text_a_normalized for phrase in phrases_b
        )
        b_matches_first = any(
            phrase in text_b_normalized for phrase in phrases_a
        )
        b_matches_second = any(
            phrase in text_b_normalized for phrase in phrases_b
        )

        if (
            a_matches_first and b_matches_second
        ) or (
            a_matches_second and b_matches_first
        ):
            contrasting_contexts.append(f"{name_a}_vs_{name_b}")
    shared_tokens = a["tokens"] & b["tokens"]

    signals = []

    if shared_application_ids:
        signals.append("shared_application_id")
    if shared_transaction_ids:
        signals.append("shared_transaction_id")
    if conflicting_application_ids:
        signals.append("different_application_ids")
    if conflicting_transaction_ids:
        signals.append("different_transaction_ids")
    if shared_semesters:
        signals.append("shared_semester")
    if different_semesters:
        signals.append("different_semesters")
    if shared_dates:
        signals.append("shared_date_or_weekday")
    if different_dates:
        signals.append("different_dates_or_weekdays")
    if shared_locations:
        signals.append("shared_location")
    if different_locations:
        signals.append("different_locations")
    if shared_topic_terms:
        signals.append("shared_topic_terms")
    if paraphrase_support:
        signals.append("paraphrase_support")
    if contrasting_contexts:
        signals.append("contrasting_context")
    if shared_batch_references:
        signals.append("shared_batch_reference")

    
    # Incident relationship: conservative evidence-based suggestions.
    shared_identifier = bool(
        shared_application_ids
        or shared_transaction_ids
        or shared_batch_references
    )

    conflicting_identifier = (
        conflicting_application_ids or conflicting_transaction_ids
    )

    if conflicting_identifier:
        incident_relationship = "conflicting_identifier_review"
        incident_explanation = (
            "Different application or transaction identifiers were found. "
            "Review whether these represent separate cases or a wider event."
        )

    elif contrasting_contexts:
        incident_relationship = "unresolved_human_review"
        incident_explanation = (
            "Contrasting complaint contexts were detected. Do not infer "
            "a shared incident from topic or paraphrase similarity alone; "
            "review the underlying events and any possible systemic link."
        )

    elif shared_identifier:
        incident_relationship = "same_incident_candidate"
        incident_explanation = (
            "An application, transaction, or batch identifier appears in "
            "both texts. Verify the identifier meaning and surrounding context."
        )

    elif (
        shared_dates
        and shared_locations
        and len(shared_topic_terms) >= 1
    ):
        incident_relationship = "same_incident_candidate"
        incident_explanation = (
            "Date, location, and topic evidence overlap. This is only a "
            "candidate; verify the actual event before linking cases."
        )

    elif (
        different_semesters
        or different_dates
        or different_locations
    ):
        incident_relationship = "possible_distinct_incidents"
        incident_explanation = (
            "At least one extracted context field differs. A shared "
            "systemic cause may still connect the complaints."
        )

    else:
        incident_relationship = "unresolved_human_review"
        incident_explanation = (
            "Available structured evidence does not establish whether "
            "these texts describe the same incident."
        )
    # Systemic relationship is separate from incident identity.
    # Shared topic words alone are insufficient to suggest a systemic cause.

    context_overlap = bool(
        shared_dates
        or shared_locations
        or shared_semesters
        or shared_application_ids
        or shared_transaction_ids
    )

    if len(shared_topic_terms) >= 2 and context_overlap:
        systemic_relationship = "potentially_shared_systemic_issue"
        systemic_explanation = (
            "Multiple topic terms and at least one contextual signal overlap. "
            "Investigate a possible common process or service; this does "
            "not establish a shared root cause."
        )

    elif len(shared_topic_terms) >= 2 or len(shared_tokens) >= 3:
        systemic_relationship = "similar_topic_only"
        systemic_explanation = (
            "The texts share subject matter, but the extracted evidence "
            "does not sufficiently support a common systemic cause."
        )

    elif not a["tokens"] or not b["tokens"]:
        systemic_relationship = "unresolved"
        systemic_explanation = (
            "Insufficient extracted text to assess a possible common cause."
        )

    else:
        systemic_relationship = "unresolved"
        systemic_explanation = (
            "No reliable systemic relationship can be inferred from "
            "the available evidence."
        )


    if shared_transaction_ids or shared_batch_references:
        evidence_level = "corroborated_reference_match"
    elif (
        shared_application_ids
        or (
            shared_dates
            and shared_locations
            and shared_topic_terms
        )
    ):
        evidence_level = "supporting_context"
    elif shared_topic_terms:
        evidence_level = "topic_overlap_only"
    elif shared_complaint_intents:
        evidence_level = "shared_intent_only"
    else:
        evidence_level = "insufficient_evidence"

    return {
        "incident_relationship": incident_relationship,
        "incident_explanation": incident_explanation,
        "systemic_relationship": systemic_relationship,
        "systemic_explanation": systemic_explanation,
        "evidence_signals": ";".join(signals) or "none_detected",
        "paraphrase_support": paraphrase_support,
        "matched_paraphrase_groups": ";".join(
            sorted(matched_paraphrase_groups)
        ),
        "shared_application_ids": ";".join(
            sorted(shared_application_ids)
        ),
        "application_ids_a": ";".join(sorted(a["application_ids"])),
        "application_ids_b": ";".join(sorted(b["application_ids"])),
        "shared_transaction_ids": ";".join(
            sorted(shared_transaction_ids)
        ),
        "transaction_ids_a": ";".join(sorted(a["transaction_ids"])),
        "transaction_ids_b": ";".join(sorted(b["transaction_ids"])),
        "shared_semesters": ";".join(sorted(shared_semesters)),
        "semesters_a": ";".join(sorted(a["semesters"])),
        "semesters_b": ";".join(sorted(b["semesters"])),
        "shared_dates": ";".join(sorted(shared_dates)),
        "dates_a": ";".join(sorted(a["dates"])),
        "dates_b": ";".join(sorted(b["dates"])),
        "shared_locations": ";".join(sorted(shared_locations)),
        "locations_a": ";".join(sorted(a["locations"])),
        "locations_b": ";".join(sorted(b["locations"])),
        "shared_topic_terms": ";".join(sorted(shared_topic_terms)),
                "shared_batch_references": ";".join(
            sorted(shared_batch_references)
        ),
        "complaint_intents_a": ";".join(sorted(intents_a)),
        "complaint_intents_b": ";".join(sorted(intents_b)),
        "shared_complaint_intents": ";".join(
            sorted(shared_complaint_intents)
        ),
        "batch_references_a": ";".join(
            sorted(a["batch_references"])
        ),
        "batch_references_b": ";".join(
            sorted(b["batch_references"])
        ),
        "evidence_level": evidence_level,
                "contrasting_contexts": ";".join(contrasting_contexts),
    }


def main():
    if not INPUT_CSV.exists():
        raise FileNotFoundError(
            f"Benchmark not found: {INPUT_CSV}"
        )

    with INPUT_CSV.open(
        "r", newline="", encoding="utf-8-sig"
    ) as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    required = {
        "pair_id",
        "is_true_overlap",
        "pair_type",
        "text_a",
        "text_b",
    }

    if not rows or not required.issubset(rows[0].keys()):
        raise ValueError(
            "Input CSV is empty or missing required columns."
        )

    output_rows = []

    incident_counts = Counter()
    systemic_counts = Counter()

    for row in rows:
        evidence = compare_evidence(
            row["text_a"],
            row["text_b"],
        )

        incident_counts[evidence["incident_relationship"]] += 1
        systemic_counts[evidence["systemic_relationship"]] += 1

        output_rows.append({
            "pair_id": row["pair_id"],
            "pair_type": row["pair_type"],
            "expected_same_incident": row["is_true_overlap"],
            **evidence,
        })

    fieldnames = list(output_rows[0].keys())

    with OUTPUT_CSV.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    print("=== SETU Two-Level Evidence Evaluation ===")
    print(f"Pairs evaluated: {len(output_rows)}")
    print("Database access: none")
    print("Database changes: none")
    print("External API calls: none")
    print(f"Output: {OUTPUT_CSV}")

    print("\n=== Incident relationship suggestions ===")
    for name, count in sorted(incident_counts.items()):
        print(f"{name}: {count}")

    print("\n=== Systemic relationship suggestions ===")
    for name, count in sorted(systemic_counts.items()):
        print(f"{name}: {count}")

    print(
        "\nThese are uncalibrated rule-based suggestions, "
        "not confirmed incident relationships."
    )


if __name__ == "__main__":
    main()
