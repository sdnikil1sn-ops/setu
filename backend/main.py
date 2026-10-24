
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from psycopg import sql
from psycopg.rows import dict_row
from pydantic import BaseModel, Field
from institution_resolution import resolve_institution

from overlap_engine import find_overlap_candidates
from embedding_provider import semantic_similarity


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL")

app = FastAPI(
    title="SETU API",
    description="Institution complaint intelligence backend",
    version="0.2.0",
)

# Fixed table names only; never accept table names from API users.
COLLECTION_TABLES = {
    "regions": "regions",
    "institution_groups": "institution_groups",
    "bureaus": "bureaus",
    "institutions": "institutions",
    "institution_aliases": "institution_aliases",
    "profiles": "profiles",
    "complaint_cases": "complaint_cases",
    "case_actions": "case_actions",
    "case_links": "case_links",
    "coordination_notes": "coordination_notes",
    "alerts": "alerts",
    "sla_rules": "sla_rules",
    "audit_logs": "audit_logs",
    "ground_truth_pairs": "ground_truth_pairs",
    "ground_truth_clusters": "ground_truth_clusters",
    "institution_resolution_ground_truth":
        "institution_resolution_ground_truth",
}


def get_connection():
    """Open a short-lived connection to Supabase PostgreSQL."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing from backend/.env")

    return psycopg.connect(
        DATABASE_URL,
        connect_timeout=10,
        row_factory=dict_row,
    )


def fetch_page(
    table_name: str,
    conditions: list,
    values: list,
    limit: int,
    offset: int,
):
    """Return a filtered page and the total number of matching rows."""
    where_clause = sql.SQL("")

    if conditions:
        where_clause = sql.SQL(" WHERE ") + sql.SQL(" AND ").join(
            conditions
        )

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("SELECT count(*) AS total FROM {}").format(
                    sql.Identifier("public", table_name)
                ) + where_clause,
                values,
            )
            total = cur.fetchone()["total"]

            cur.execute(
                sql.SQL("SELECT * FROM {}").format(
                    sql.Identifier("public", table_name)
                )
                + where_clause
                + sql.SQL(" ORDER BY 1 LIMIT %s OFFSET %s"),
                values + [limit, offset],
            )
            items = cur.fetchall()

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": items,
    }


@app.get("/")
def home():
    return {
        "project": "SETU",
        "message": "Backend is running",
        "version": "0.2.0",
        "docs": "/docs",
    }


@app.get("/health")
def health():
    """Check database connectivity, not just server availability."""
    if not DATABASE_URL:
        return {
            "status": "unhealthy",
            "database": "DATABASE_URL is missing",
        }

    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 AS result")
                cur.fetchone()

        return {
            "status": "healthy",
            "database": "connected",
        }

    except Exception:
        # Do not return connection strings or database credentials.
        raise HTTPException(
            status_code=503,
            detail="Database connection failed",
        )


@app.get("/api/v1/summary")
def get_summary():
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                counts = {}

                for collection, table_name in COLLECTION_TABLES.items():
                    cur.execute(
                        sql.SQL("SELECT count(*) AS total FROM {}").format(
                            sql.Identifier("public", table_name)
                        )
                    )
                    counts[collection] = cur.fetchone()["total"]

                cur.execute(
                    "SELECT count(*) AS total "
                    "FROM public.setu_dataset_manifest"
                )
                counts["setu_dataset_manifest"] = (
                    cur.fetchone()["total"]
                )

        return {"actual_counts": counts}

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve database summary",
        )


@app.get("/api/v1/institutions")
def get_institutions(
    search: str | None = None,
    state: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    conditions = []
    values = []

    if search:
        conditions.append(
            sql.SQL(
                "(name ILIKE %s OR permanent_id ILIKE %s)"
            )
        )
        term = f"%{search}%"
        values.extend([term, term])

    if state:
        conditions.append(sql.SQL("state ILIKE %s"))
        values.append(state)

    return fetch_page(
        "institutions", conditions, values, limit, offset
    )


@app.get("/api/v1/cases")
def get_cases(
    status: str | None = None,
    bureau_id: str | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    conditions = []
    values = []

    if status:
        conditions.append(sql.SQL("status ILIKE %s"))
        values.append(status)

    if bureau_id:
        conditions.append(sql.SQL("current_bureau_id = %s"))
        values.append(bureau_id)

    return fetch_page(
        "complaint_cases", conditions, values, limit, offset
    )


@app.get("/api/v1/cases/{case_id}")
def get_case(case_id: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT *
                    FROM public.complaint_cases
                    WHERE case_id = %s
                    """,
                    (case_id,),
                )
                case = cur.fetchone()

        if case is None:
            raise HTTPException(
                status_code=404,
                detail="Case not found",
            )

        return case

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve case",
        )


class InstitutionResolutionRequest(BaseModel):
    """Input for a read-only institution identity lookup."""

    raw_name: str | None = Field(default=None, max_length=300)
    raw_permanent_id: str | None = Field(default=None, max_length=100)


@app.post("/api/v1/institutions/resolve")
def resolve_institution_api(request: InstitutionResolutionRequest):
    """
    Propose an institution match without modifying database records.
    """
    try:
        result = resolve_institution(
            raw_permanent_id=request.raw_permanent_id,
            raw_name=request.raw_name,
        )

        institution = result.get("institution")

        # Return only the fields needed by the API consumer.
        institution_summary = None

        if institution:
            institution_summary = {
                "institution_id": institution["institution_id"],
                "name": institution["name"],
                "permanent_id": institution["permanent_id"],
                "state": institution["state"],
                "district": institution["district"],
            }

        return {
            "resolution_status": result["resolution_status"],
            "resolution_method": result["resolution_method"],
            "resolution_confidence": result["resolution_confidence"],
            "reason": result["reason"],
            "institution": institution_summary,
            "candidates": result.get("candidates", []),
            "review_required": (
                result["resolution_status"] == "needs_review"
            ),
        }

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Institution resolution could not be completed",
        )

@app.get("/api/v1/overlaps/candidates")
def get_overlap_candidates(
    limit: int = Query(default=20, ge=1, le=100),
    minimum_score: float = Query(default=50, ge=0, le=100),
):
    """
    Return ranked cross-bureau complaint candidates.
    This endpoint is read-only; all candidates require human review.
    """
    try:
        return find_overlap_candidates(
            limit=limit,
            minimum_score=minimum_score,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve overlap candidates",
        )
        

class SemanticCheckRequest(BaseModel):
    """Synthetic or explicitly authorized test texts only."""

    text_a: str = Field(min_length=1, max_length=3000)
    text_b: str = Field(min_length=1, max_length=3000)


@app.post("/api/v1/overlaps/semantic-check")
def semantic_check_api(request: SemanticCheckRequest):
    """
    Development-only semantic comparison.
    Does not access or modify the database.
    """
    if os.getenv("SETU_ENABLE_SEMANTIC_CHECK", "").lower() != "true":
        raise HTTPException(
            status_code=404,
            detail="Semantic check endpoint is disabled",
        )

    try:
        result = semantic_similarity(
            request.text_a,
            request.text_b,
        )

        return {
            **result,
            "review_required": True,
            "database_modified": False,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Semantic comparison could not be completed",
        )


@app.get("/api/v1/overlaps/candidates")
def get_overlap_candidates(
    limit: int = Query(default=20, ge=1, le=100),
    minimum_score: float = Query(default=50, ge=0, le=100),
):
    """
    Return ranked cross-bureau complaint candidates.
    This endpoint is read-only; all candidates require human review.
    """
    try:
        return find_overlap_candidates(
            limit=limit,
            minimum_score=minimum_score,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        )
    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Could not retrieve overlap candidates",
        )
