"""Phase 6 Desk Officer RLS test for SETU.

Connects using the restricted setu_api_login role. Uses SETU's own
transaction-local identity setting (setu.auth_user_id), not auth.uid().
The test performs SELECTs only and rolls back the transaction.
"""
from getpass import getpass
from urllib.parse import urlparse
import os
import sys
import uuid

import psycopg
from dotenv import load_dotenv

PROFILE_ID = "TEST-PHASE6-DESK-001"
ASSIGNED_CASE = "CASE-TEST-PH6-DESK-001"
UNASSIGNED_CASE = "CASE-TEST-PH6-DESK-002"
RESTRICTED_CASE = "CASE-TEST-PH6-DESK-003"
PROJECT_REF = "anfsjqkhmbgjefmgzzeb"


def main() -> int:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("FAIL: DATABASE_URL was not found in backend/.env")
        return 1

    auth_id_raw = input("Enter Auth UUID linked to TEST-PHASE6-DESK-001: ").strip()
    try:
        auth_id = str(uuid.UUID(auth_id_raw))
    except ValueError:
        print("FAIL: That is not a valid UUID.")
        return 1

    parsed = urlparse(database_url)
    if not parsed.hostname or not parsed.port or not parsed.path:
        print("FAIL: DATABASE_URL does not contain a usable host, port, and database.")
        return 1

    db_password = getpass("Enter password for the dedicated setu_api_login role: ")
    if not db_password:
        print("FAIL: A database role password is required.")
        return 1

    try:
        with psycopg.connect(
            host=parsed.hostname,
            port=parsed.port,
            dbname=parsed.path.lstrip("/"),
            user=f"setu_api_login.{PROJECT_REF}",
            password=db_password,
            sslmode="require",
            connect_timeout=15,
            options="-c application_name=setu_phase6_desk_officer_rls_test_v2",
            autocommit=False,
            row_factory=psycopg.rows.dict_row,
        ) as conn:
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT current_user AS role_name")
                    role_name = cur.fetchone()["role_name"]
                    if role_name != "setu_api_login":
                        raise AssertionError(f"Unexpected active role: {role_name}")

                    cur.execute(
                        "SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user"
                    )
                    role = cur.fetchone()
                    if role is None or role["rolsuper"] or role["rolbypassrls"]:
                        raise AssertionError("Database login is superuser or bypasses RLS")

                    # SETU's authorization helpers resolve this transaction-local setting.
                    cur.execute(
                        "SELECT set_config('setu.auth_user_id', %s, true)",
                        (auth_id,),
                    )
                    cur.execute(
                        "SELECT public.setu_current_auth_user_id() AS resolved_auth_user_id"
                    )
                    resolved = cur.fetchone()["resolved_auth_user_id"]
                    if str(resolved) != auth_id:
                        raise AssertionError(
                            f"SETU identity helper resolved {resolved!r}, expected {auth_id}"
                        )

                    cur.execute("SELECT * FROM public.setu_current_profile()")
                    profiles = cur.fetchall()
                    if len(profiles) != 1:
                        raise AssertionError(
                            f"Expected exactly one current profile, got {len(profiles)}"
                        )
                    profile = profiles[0]
                    if profile["user_id"] != PROFILE_ID or profile["role"] != "Desk Officer":
                        raise AssertionError(
                            "Identity resolved to an unexpected profile: "
                            f"{profile['user_id']!r}, role={profile['role']!r}"
                        )

                    cur.execute(
                        """SELECT case_id FROM public.complaint_cases
                           WHERE case_id = ANY(%s) ORDER BY case_id""",
                        ([ASSIGNED_CASE, UNASSIGNED_CASE, RESTRICTED_CASE],),
                    )
                    visible = {row["case_id"] for row in cur.fetchall()}
                    expected = {ASSIGNED_CASE}
                    if visible != expected:
                        raise AssertionError(
                            "Unexpected case visibility. "
                            f"Expected only {sorted(expected)}, got {sorted(visible)}"
                        )

                    cur.execute("SELECT count(*) AS n FROM public.audit_logs")
                    audit_count = cur.fetchone()["n"]
                    if audit_count != 0:
                        raise AssertionError(
                            f"Desk Officer unexpectedly sees {audit_count} audit log rows"
                        )

                    print("Database role: setu_api_login")
                    print("Superuser: false; BYPASSRLS: false")
                    print("SETU identity helper: matched to Desk Officer profile")
                    print("Assigned eligible case: visible")
                    print("Unassigned eligible case: hidden")
                    print("Assigned restricted case: hidden")
                    print("Audit log rows visible: 0")
                    print("PASS: Desk Officer can read the assigned eligible case only.")
            finally:
                conn.rollback()
    except Exception as exc:
        print(f"FAIL: {type(exc).__name__}: {exc}")
        print("No changes were committed by this test; the transaction was rolled back.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
