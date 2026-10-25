"""SETU Phase 6 Admin and Senior Management RLS authorization test v2.

Connects as restricted setu_api_login and sets transaction-local SETU identity.
Tests actual RLS-filtered SELECTs for cases and audit logs. SELECT-only; rolls
back each transaction.
"""
from getpass import getpass
from urllib.parse import urlparse
import os
import uuid

import psycopg
from dotenv import load_dotenv

PROJECT_REF = "anfsjqkhmbgjefmgzzeb"
PROFILES = [
    ("Admin", "TEST-PHASE6-ADMIN-001"),
    ("Senior Management", "TEST-PHASE6-SENIOR-001"),
]
CASE_IDS = [
    "CASE-TEST-PH6-DESK-001",  # assigned and unrestricted
    "CASE-TEST-PH6-DESK-002",  # unassigned and unrestricted
    "CASE-TEST-PH6-DESK-003",  # assigned but restricted
]
EXPECTED_VISIBLE = {
    "CASE-TEST-PH6-DESK-001",
    "CASE-TEST-PH6-DESK-002",
}


def read_uuid(prompt: str) -> str:
    try:
        return str(uuid.UUID(input(prompt).strip()))
    except ValueError as exc:
        raise ValueError("That is not a valid UUID.") from exc


def main() -> int:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("FAIL: DATABASE_URL was not found in backend/.env")
        return 1

    try:
        auth_ids = [
            read_uuid("Enter Auth UUID linked to TEST-PHASE6-ADMIN-001: "),
            read_uuid("Enter Auth UUID linked to TEST-PHASE6-SENIOR-001: "),
        ]
    except ValueError as exc:
        print(f"FAIL: {exc}")
        return 1

    if auth_ids[0] == auth_ids[1]:
        print("FAIL: Admin and Senior Management must use separate Auth UUIDs.")
        return 1

    parsed = urlparse(database_url)
    if not parsed.hostname or not parsed.port or not parsed.path:
        print("FAIL: DATABASE_URL does not contain a usable host, port, and database.")
        return 1

    password = getpass("Enter password for the dedicated setu_api_login role: ")
    if not password:
        print("FAIL: A database role password is required.")
        return 1

    try:
        with psycopg.connect(
            host=parsed.hostname,
            port=parsed.port,
            dbname=parsed.path.lstrip("/"),
            user=f"setu_api_login.{PROJECT_REF}",
            password=password,
            sslmode="require",
            connect_timeout=15,
            options="-c application_name=setu_phase6_management_rls_test_v2",
            autocommit=False,
            row_factory=psycopg.rows.dict_row,
        ) as conn:
            for (role_name, profile_id), auth_id in zip(PROFILES, auth_ids):
                try:
                    with conn.cursor() as cur:
                        cur.execute("SELECT current_user AS role_name")
                        if cur.fetchone()["role_name"] != "setu_api_login":
                            raise AssertionError("Connected using unexpected database role")

                        cur.execute(
                            "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
                        )
                        role = cur.fetchone()
                        if role is None or role["rolsuper"] or role["rolbypassrls"]:
                            raise AssertionError("Login is superuser or bypasses RLS")

                        cur.execute(
                            "SELECT set_config('setu.auth_user_id', %s, true)",
                            (auth_id,),
                        )
                        cur.execute(
                            "SELECT public.setu_current_auth_user_id() AS uid"
                        )
                        if str(cur.fetchone()["uid"]) != auth_id:
                            raise AssertionError("SETU identity helper returned wrong Auth UUID")

                        cur.execute("SELECT * FROM public.setu_current_profile()")
                        profiles = cur.fetchall()
                        if len(profiles) != 1:
                            raise AssertionError(
                                f"Expected one profile, got {len(profiles)}"
                            )
                        p = profiles[0]
                        if p["user_id"] != profile_id or p["role"] != role_name:
                            raise AssertionError(
                                f"Wrong profile resolved: {p['user_id']!r}, {p['role']!r}"
                            )

                        cur.execute(
                            """SELECT case_id FROM public.complaint_cases
                               WHERE case_id = ANY(%s) ORDER BY case_id""",
                            (CASE_IDS,),
                        )
                        visible = {r["case_id"] for r in cur.fetchall()}
                        if visible != EXPECTED_VISIBLE:
                            raise AssertionError(
                                f"Unexpected case visibility: {sorted(visible)}"
                            )

                        # Policy explicitly allows management roles to read audit logs.
                        cur.execute("SELECT count(*) AS n FROM public.audit_logs")
                        audit_count = cur.fetchone()["n"]
                        if audit_count < 0:
                            raise AssertionError("Invalid audit log count")

                        print(f"\n{role_name} ({profile_id})")
                        print("  Database role: setu_api_login")
                        print("  Superuser: false; BYPASSRLS: false")
                        print("  Identity helper: correct profile")
                        print("  Assigned unrestricted case: visible")
                        print("  Unassigned unrestricted case: visible")
                        print("  Restricted case: hidden")
                        print(
                            "  Audit-log policy: management access permitted; "
                            f"{audit_count} row(s) visible"
                        )
                        print(f"  PASS: {role_name} case-authorization checks passed.")
                finally:
                    conn.rollback()

        print("\nPASS: Admin and Senior Management case-authorization checks passed.")
        print(
            "NOTE: Audit-log visibility was observed according to the existing "
            "management policy; this test does not validate audit-log row scoping."
        )
        return 0
    except Exception as exc:
        print(f"\nFAIL: {type(exc).__name__}: {exc}")
        print("No changes were committed; each test transaction was rolled back.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
