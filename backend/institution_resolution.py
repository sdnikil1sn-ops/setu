
import os
import re
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


def check_database_connection():
    """Check connectivity without modifying data."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 AS result")
            return cur.fetchone()["result"]


def normalize_name(name: str | None):
    """Standardize case, punctuation, and whitespace."""
    if name is None:
        return ""

    name = name.casefold()
    name = re.sub(r"[\W_]+", " ", name, flags=re.UNICODE)
    return " ".join(name.split())


def resolve_by_permanent_id(raw_permanent_id: str | None):
    """Find an institution using its exact Permanent ID."""
    if raw_permanent_id is None or not raw_permanent_id.strip():
        return {
            "institution": None,
            "resolution_method": None,
            "resolution_confidence": 0.0,
            "resolution_status": "unresolved",
            "reason": "Permanent ID is missing",
        }

    permanent_id = raw_permanent_id.strip()

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM public.institutions
                WHERE BTRIM(permanent_id) = %s
                LIMIT 2
                """,
                (permanent_id,),
            )
            matches = cur.fetchall()

    if len(matches) == 0:
        return {
            "institution": None,
            "resolution_method": "permanent_id",
            "resolution_confidence": 0.0,
            "resolution_status": "unresolved",
            "reason": "No institution matches this Permanent ID",
        }

    if len(matches) > 1:
        return {
            "institution": None,
            "resolution_method": "permanent_id",
            "resolution_confidence": 0.0,
            "resolution_status": "needs_review",
            "reason": "Multiple institutions share this Permanent ID",
        }

    return {
        "institution": matches[0],
        "resolution_method": "permanent_id",
        "resolution_confidence": 1.0,
        "resolution_status": "resolved",
        "reason": "Exact Permanent ID match",
    }


def resolve_by_alias(raw_name: str | None):
    """Find an institution using an exact, case-insensitive alias."""
    if raw_name is None or not raw_name.strip():
        return {
            "institution": None,
            "resolution_method": None,
            "resolution_confidence": 0.0,
            "resolution_status": "unresolved",
            "reason": "Institution name is missing",
        }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT DISTINCT i.*
                FROM public.institution_aliases AS a
                JOIN public.institutions AS i
                  ON i.institution_id = a.institution_id
                WHERE LOWER(BTRIM(a.alias)) = LOWER(%s)
                LIMIT 2
                """,
                (raw_name.strip(),),
            )
            matches = cur.fetchall()

    if len(matches) == 0:
        return {
            "institution": None,
            "resolution_method": "alias",
            "resolution_confidence": 0.0,
            "resolution_status": "unresolved",
            "reason": "No institution matches this alias",
        }

    if len(matches) > 1:
        return {
            "institution": None,
            "resolution_method": "alias",
            "resolution_confidence": 0.0,
            "resolution_status": "needs_review",
            "reason": "Alias matches multiple institutions",
        }

    return {
        "institution": matches[0],
        "resolution_method": "alias",
        "resolution_confidence": 0.95,
        "resolution_status": "resolved",
        "reason": "Exact case-insensitive alias match",
    }


def resolve_by_normalized_name(raw_name: str | None):
    """Match a normalized name against existing institution names."""
    normalized_input = normalize_name(raw_name)

    if not normalized_input:
        return {
            "institution": None,
            "resolution_method": None,
            "resolution_confidence": 0.0,
            "resolution_status": "unresolved",
            "reason": "Institution name is missing",
        }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM public.institutions")
            institutions = cur.fetchall()

    matches = {}

    for institution in institutions:
        possible_names = [
            institution.get("name"),
            institution.get("normalized_name"),
        ]

        if any(
            normalize_name(name) == normalized_input
            for name in possible_names
            if name
        ):
            matches[institution["institution_id"]] = institution

    if len(matches) == 0:
        return {
            "institution": None,
            "resolution_method": "normalized_name",
            "resolution_confidence": 0.0,
            "resolution_status": "unresolved",
            "reason": "No institution matches the normalized name",
        }

    if len(matches) > 1:
        return {
            "institution": None,
            "resolution_method": "normalized_name",
            "resolution_confidence": 0.0,
            "resolution_status": "needs_review",
            "reason": "Normalized name matches multiple institutions",
        }

    return {
        "institution": next(iter(matches.values())),
        "resolution_method": "normalized_name",
        "resolution_confidence": 0.90,
        "resolution_status": "resolved",
        "reason": "Unique normalized-name match",
    }


def find_fuzzy_candidates(
    raw_name: str | None,
    limit: int = 5,
):
    """
    Rank similar institution names and aliases.
    Fuzzy results are suggestions, never automatic resolutions.
    """
    normalized_input = normalize_name(raw_name)

    if not normalized_input:
        return {
            "resolution_status": "unresolved",
            "resolution_method": "fuzzy_name",
            "resolution_confidence": 0.0,
            "candidates": [],
            "reason": "Institution name is missing",
        }

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    i.*,
                    a.alias AS matched_alias
                FROM public.institutions AS i
                LEFT JOIN public.institution_aliases AS a
                  ON a.institution_id = i.institution_id
                """
            )
            rows = cur.fetchall()

    candidates_by_id = {}

    for row in rows:
        institution_id = row["institution_id"]

        names_to_compare = [
            (row.get("name"), "institution_name"),
            (row.get("normalized_name"), "normalized_name"),
            (row.get("matched_alias"), "alias"),
        ]

        for candidate_name, matched_on in names_to_compare:
            normalized_candidate = normalize_name(candidate_name)

            if not normalized_candidate:
                continue

            score = fuzz.ratio(
                normalized_input,
                normalized_candidate,
            )

            # Ignore weak similarities to reduce irrelevant suggestions.
            if score < 65:
                continue

            previous = candidates_by_id.get(institution_id)

            if previous is None or score > previous["score"]:
                candidates_by_id[institution_id] = {
                    "institution_id": institution_id,
                    "name": row["name"],
                    "permanent_id": row["permanent_id"],
                    "score": round(score, 2),
                    "matched_on": matched_on,
                }

    candidates = sorted(
        candidates_by_id.values(),
        key=lambda item: item["score"],
        reverse=True,
    )[:limit]

    if not candidates or candidates[0]["score"] < 75:
        status = "unresolved"
        reason = "No sufficiently similar candidate found"
    else:
        status = "needs_review"
        reason = (
            "Fuzzy candidates require human verification; "
            "similarity alone cannot confirm identity"
        )

    return {
        "institution": None,
        "resolution_method": "fuzzy_name",
        "resolution_confidence": 0.0,
        "resolution_status": status,
        "candidates": candidates,
        "reason": reason,
    }


def resolve_institution(
    raw_permanent_id: str | None,
    raw_name: str | None,
):
    """Try reliable exact rules before suggesting fuzzy candidates."""
    id_result = resolve_by_permanent_id(raw_permanent_id)

    if id_result["resolution_status"] in ("resolved", "needs_review"):
        return id_result

    alias_result = resolve_by_alias(raw_name)

    if alias_result["resolution_status"] in ("resolved", "needs_review"):
        return alias_result

    name_result = resolve_by_normalized_name(raw_name)

    if name_result["resolution_status"] in ("resolved", "needs_review"):
        return name_result

    fuzzy_result = find_fuzzy_candidates(raw_name)

    if fuzzy_result["resolution_status"] == "needs_review":
        return fuzzy_result

    return {
        "institution": None,
        "resolution_method": None,
        "resolution_confidence": 0.0,
        "resolution_status": "unresolved",
        "reason": (
            "No unique match found using Permanent ID, alias, "
            "normalized name, or fuzzy candidate search"
        ),
        "candidates": fuzzy_result["candidates"],
    }
