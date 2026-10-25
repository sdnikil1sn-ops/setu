from __future__ import annotations

import getpass
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote
from uuid import UUID

import psycopg


PROFILE_ID = "TEST-PHASE6-REGIONAL-001"
EXPECTED_REGION = "REG-TA-chennai"


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise SystemExit(f"Could not find {path}. Run from your SETU backend folder.")
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> int:
    env = read_env(Path(".env"))
    raw_url = env.get("DATABASE_URL")
    if not raw_url:
        raise SystemExit("DATABASE_URL was not found in .env.")
    parsed = urlparse(raw_url)
    old_username = unquote(parsed.username or "")
    if not parsed.hostname or "." not in old_username:
        raise SystemExit("Could not derive the Supabase pooler project reference from DATABASE_URL.")

    project_ref = old_username.rsplit(".", 1)[1]
    login_username = f"setu_api_login.{project_ref}"
    auth_id_raw = input("Paste the Auth UUID for TEST-PHASE6-REGIONAL-001: ").strip()
    try:
        auth_id = str(UUID(auth_id_raw))
    except ValueError:
        raise SystemExit("That does not look like a valid UUID. Test cancelled.")

    print("\nSETU Phase 6 — Regional Officer authorization test")
    print(f"Host: {parsed.hostname}")
    print(f"Port: {parsed.port or 5432}")
    print(f"Database: {unquote(parsed.path.lstrip('/')) or 'postgres'}")
    print(f"Login role: {login_username}")
    password = getpass.getpass("Password for the setu_api_login database role: ")
    if not password:
        raise SystemExit("No password entered; test cancelled.")

    try:
        with psycopg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            dbname=unquote(parsed.path.lstrip("/")) or "postgres",
            user=login_username,
            password=password,
            sslmode="require",
            connect_timeout=12,
            autocommit=False,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT current_user, session_user, rolsuper, rolbypassrls,
                           pg_has_role(current_user, 'setu_api', 'MEMBER')
                    FROM pg_roles
                    WHERE rolname = current_user
                """)
                role = cur.fetchone()
                if not role:
                    raise RuntimeError("Could not inspect connected role.")
                current_user, session_user, is_superuser, bypasses_rls, is_member = role
                print("\nDatabase role:")
                print(f"  current_user = {current_user}")
                print(f"  session_user = {session_user}")
                print(f"  superuser = {is_superuser}")
                print(f"  bypasses RLS = {bypasses_rls}")
                print(f"  member of setu_api = {is_member}")
                if current_user != "setu_api_login" or session_user != "setu_api_login":
                    raise RuntimeError("Connected to a role other than setu_api_login.")
                if is_superuser or bypasses_rls or not is_member:
                    raise RuntimeError("Login role security attributes/membership are not as expected.")

                # Set request-scoped identity for this transaction only.
                cur.execute(
                    "SELECT set_config('setu.auth_user_id', %s, true), "
                    "set_config('setu.demo_mode', 'false', true)",
                    (auth_id,),
                )

                cur.execute("""
                    SELECT user_id, role, region_id, is_synthetic, demo_only,
                           auth_user_id = %s::uuid AS auth_link_matches
                    FROM public.profiles
                    WHERE user_id = %s
                """, (auth_id, PROFILE_ID))
                profile = cur.fetchone()
                print("\nLinked profile:")
                if profile is None:
                    print("  visible profile = none")
                    raise RuntimeError("Test profile is not visible; check Auth UUID and profile linking.")
                print(f"  user_id = {profile[0]}")
                print(f"  role = {profile[1]}")
                print(f"  region_id = {profile[2]}")
                print(f"  is_synthetic = {profile[3]}")
                print(f"  demo_only = {profile[4]}")
                print(f"  auth_link_matches = {profile[5]}")
                if profile[1] != "Regional Officer" or profile[2] != EXPECTED_REGION:
                    raise RuntimeError("Test profile role or region does not match the expected fixture.")
                if profile[3] is not False or profile[4] is not False or profile[5] is not True:
                    raise RuntimeError("Test profile is synthetic/demo or linked to a different Auth user.")

                cur.execute("SELECT count(*) FROM public.complaint_cases")
                visible_cases = cur.fetchone()[0]
                cur.execute("""
                    SELECT count(*)
                    FROM public.complaint_cases
                    WHERE region_id = %s AND is_restricted IS FALSE
                """, (EXPECTED_REGION,))
                eligible_region_cases = cur.fetchone()[0]
                cur.execute("""
                    SELECT count(*)
                    FROM public.complaint_cases
                    WHERE region_id <> %s OR is_restricted IS TRUE
                """, (EXPECTED_REGION,))
                out_of_scope_or_restricted_visible = cur.fetchone()[0]
                cur.execute("""
                    SELECT count(*)
                    FROM public.complaint_cases
                    WHERE region_id = %s
                """, (EXPECTED_REGION,))
                region_visible_cases = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM public.audit_logs")
                visible_audit_logs = cur.fetchone()[0]

                print("\nCase authorization:")
                print(f"  visible complaint cases = {visible_cases}")
                print(f"  visible cases in expected region = {region_visible_cases}")
                print(f"  visible cases outside region or restricted = {out_of_scope_or_restricted_visible}")
                print(f"  visible audit logs = {visible_audit_logs}")

                if visible_cases <= 0:
                    raise RuntimeError("Authorized regional user cannot see any cases.")
                if region_visible_cases != visible_cases:
                    raise RuntimeError("Some visible cases are outside the assigned region.")
                if out_of_scope_or_restricted_visible != 0:
                    raise RuntimeError("Out-of-region or restricted cases are visible.")
                # Audit logs are management-only in Phase 5 policy.
                if visible_audit_logs != 0:
                    raise RuntimeError("Regional Officer can read management-only audit logs.")

                conn.rollback()
                print("\nPASS: Regional Officer can read eligible regional cases only.")
                print("Transaction rolled back; no application rows were changed.")
                return 0
    except Exception as exc:
        print(f"\nFAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("No commit was issued. Review the error before retrying.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
