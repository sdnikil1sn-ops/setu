
import os
from datetime import date, datetime
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from rapidfuzz import fuzz
from psycopg.rows import dict_row


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    """Connect to the existing Supabase database."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing from backend/.env")

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
        row_factory=dict_row,
    )


def normalize_text(value):
    """Normalize text for similarity comparison."""
    if not value:
        return ""
    return " ".join(str(value).casefold().split())


def date_score(date_a, date_b):
    """Return points based on complaint-date proximity."""
    if not date_a or not date_b:
        return 0, None

    if isinstance(date_a, datetime):
        date_a = date_a.date()
    if isinstance(date_b, datetime):
        date_b = date_b.date()

    if not isinstance(date_a, date) or not isinstance(date_b, date):
        return 0, None

    days_apart = abs((date_a - date_b).days)

    if days_apart == 0:
        return 15, days_apart
    if days_apart <= 7:
        return 12, days_apart
    if days_apart <= 30:
        return 8, days_apart
    if days_apart <= 90:
        return 4, days_apart

    return 0, days_apart


def score_pair(case_a, case_b):
    """
    Score candidate evidence without claiming a match is confirmed.

    Same institution: up to 100 points.
    Same group, different campuses: up to 80 points.
    """
    reasons = []
    score = 0

    institution_a = case_a.get("institution_id")
    institution_b = case_b.get("institution_id")

    group_a = case_a.get("group_id")
    group_b = case_b.get("group_id")

    same_institution = (
        institution_a is not None
        and institution_a == institution_b
    )

    same_group = (
        group_a is not None
        and group_a == group_b
    )

    if same_institution:
        score += 35
        reasons.append("Same canonical institution")
    elif same_group:
        score += 15
        reasons.append("Same institution group; campuses may differ")
    else:
        reasons.append("No shared institution or group evidence")

    category_a = normalize_text(case_a.get("category"))
    category_b = normalize_text(case_b.get("category"))

    if category_a and category_a == category_b:
        score += 20
        reasons.append("Same complaint category")

    text_a = normalize_text(case_a.get("text"))
    text_b = normalize_text(case_b.get("text"))

    text_similarity = 0.0

    if text_a and text_b:
        text_similarity = fuzz.token_set_ratio(text_a, text_b)
        score += round(30 * text_similarity / 100, 2)

        if text_similarity >= 85:
            reasons.append("Very similar complaint text")
        elif text_similarity >= 65:
            reasons.append("Moderately similar complaint text")

    points, days_apart = date_score(
        case_a.get("received_date"),
        case_b.get("received_date"),
    )
    score += points

    if days_apart is not None:
        if days_apart == 0:
            reasons.append("Received on the same date")
        elif days_apart <= 7:
            reasons.append("Received within 7 days")
        elif days_apart <= 30:
            reasons.append("Received within 30 days")

    return {
        "score": round(min(score, 100), 2),
        "text_similarity": round(text_similarity, 2),
        "days_apart": days_apart,
        "same_institution": same_institution,
        "same_group": same_group,
        "reasons": reasons,
    }


def find_overlap_candidates(limit=50, minimum_score=50):
    """
    Rank cross-bureau candidate pairs sharing an institution
    or an institution group.

    Restricted complaints are excluded. No case links are written.
    """
    if not 1 <= limit <= 200:
        raise ValueError("limit must be between 1 and 200")

    if not 0 <= minimum_score <= 100:
        raise ValueError("minimum_score must be between 0 and 100")

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    a.case_id AS case_a_id,
                    a.case_ref AS case_a_ref,
                    a.source_system AS source_a,
                    a.institution_id AS institution_a_id,
                    a.group_id AS group_a_id,
                    a.category AS category_a,
                    a.text AS text_a,
                    a.received_date AS date_a,

                    b.case_id AS case_b_id,
                    b.case_ref AS case_b_ref,
                    b.source_system AS source_b,
                    b.institution_id AS institution_b_id,
                    b.group_id AS group_b_id,
                    b.category AS category_b,
                    b.text AS text_b,
                    b.received_date AS date_b

                FROM public.complaint_cases AS a
                JOIN public.complaint_cases AS b
                  ON a.case_id < b.case_id
                 AND a.source_system <> b.source_system
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

                ORDER BY a.case_id, b.case_id
                """
            )
            rows = cur.fetchall()

    candidates = []

    for row in rows:
        case_a = {
            "institution_id": row["institution_a_id"],
            "group_id": row["group_a_id"],
            "category": row["category_a"],
            "text": row["text_a"],
            "received_date": row["date_a"],
        }

        case_b = {
            "institution_id": row["institution_b_id"],
            "group_id": row["group_b_id"],
            "category": row["category_b"],
            "text": row["text_b"],
            "received_date": row["date_b"],
        }

        evidence = score_pair(case_a, case_b)

        if evidence["score"] < minimum_score:
            continue

        if evidence["same_institution"]:
            scope = "institution"
        elif evidence["same_group"]:
            scope = "group"
        else:
            continue

        candidates.append({
            "case_a": row["case_a_ref"],
            "case_b": row["case_b_ref"],
            "source_a": row["source_a"],
            "source_b": row["source_b"],
            "institution_a_id": row["institution_a_id"],
            "institution_b_id": row["institution_b_id"],
            "scope": scope,
            "category_a": row["category_a"],
            "category_b": row["category_b"],
            "score": evidence["score"],
            "text_similarity": evidence["text_similarity"],
            "days_apart": evidence["days_apart"],
            "reasons": evidence["reasons"],
            "review_required": True,
        })

    candidates.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "candidate_count": len(candidates),
        "returned_count": min(limit, len(candidates)),
        "minimum_score": minimum_score,
        "items": candidates[:limit],
        "note": (
            "Scores are heuristic rankings, not probabilities. "
            "Every candidate requires human review. Restricted "
            "complaints are excluded."
        ),
    }
