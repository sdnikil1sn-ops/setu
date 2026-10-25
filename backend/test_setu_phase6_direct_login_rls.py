from __future__ import annotations

import getpass
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

import psycopg


def read_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        raise SystemExit(f"Could not find {path}. Run this script from your SETU backend folder.")
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> int:
    env = read_env(Path(".env"))
    current_url = env.get("DATABASE_URL")
    if not current_url:
        raise SystemExit("DATABASE_URL was not found in .env.")

    parsed = urlparse(current_url)
    if not parsed.hostname:
        raise SystemExit("Could not parse the host from DATABASE_URL.")

    # Supabase pooler usernames for custom roles normally use:
    # role_name.project_ref. Derive project_ref from the existing postgres.<ref> username.
    old_username = unquote(parsed.username or "")
    if "." not in old_username:
        raise SystemExit(
            "Could not derive the Supabase project reference from the current DATABASE_URL username. "
            "Do not print or share the full URL; tell me this message."
        )
    project_ref = old_username.rsplit(".", 1)[1]
    login_username = f"setu_api_login.{project_ref}"

    print("SETU Phase 6 — direct database login / RLS smoke test")
    print(f"Host: {parsed.hostname}")
    print(f"Port: {parsed.port or 5432}")
    print(f"Database: {unquote(parsed.path.lstrip('/')) or 'postgres'}")
    print(f"Login role: {login_username}")
    print("Password will be requested securely and will not be displayed or saved.")
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
                cur.execute(
                    """
                    SELECT current_user, session_user,
                           rolsuper, rolbypassrls, rolcanlogin,
                           pg_has_role(current_user, 'setu_api', 'MEMBER')
                    FROM pg_roles
                    WHERE rolname = current_user
                    """
                )
                role = cur.fetchone()
                if not role:
                    raise RuntimeError("Could not inspect the connected database role.")
                current_user, session_user, superuser, bypassrls, canlogin, member = role
                print("\nConnection identity:")
                print(f"  current_user = {current_user}")
                print(f"  session_user  = {session_user}")
                print(f"  superuser     = {superuser}")
                print(f"  bypasses RLS  = {bypassrls}")
                print(f"  can login     = {canlogin}")
                print(f"  member of setu_api = {member}")

                if current_user != "setu_api_login" or session_user != "setu_api_login":
                    raise RuntimeError("Connected role does not match the expected login role.")
                if superuser or bypassrls or not canlogin or not member:
                    raise RuntimeError("The login role's security attributes are not as expected.")

                # Keep both simulated request contexts in this transaction.
                cur.execute("SELECT set_config('setu.auth_user_id', '', true), set_config('setu.demo_mode', 'true', true)")
                cur.execute("SELECT count(*) FROM public.complaint_cases")
                demo_cases = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM public.profiles")
                demo_profiles = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM public.audit_logs")
                demo_audit = cur.fetchone()[0]
                cur.execute("SELECT count(*) FROM public.case_actions")
                demo_actions = cur.fetchone()[0]

                print("\nDemo context:")
                print(f"  complaint_cases = {demo_cases}")
                print(f"  profiles         = {demo_profiles}")
                print(f"  audit_logs       = {demo_audit}")
                print(f"  case_actions     = {demo_actions}")

                if any(v != 0 for v in (demo_cases, demo_profiles, demo_audit, demo_actions)):
                    raise RuntimeError("Demo context exposed protected rows.")

                fake_auth_id = "11111111-1111-4111-8111-111111111111"
                cur.execute(
                    "SELECT set_config('setu.auth_user_id', %s, true), set_config('setu.demo_mode', 'false', true)",
                    (fake_auth_id,),
                )
                table_queries = {
                    "profiles": "SELECT count(*) FROM public.profiles",
                    "complaint_cases": "SELECT count(*) FROM public.complaint_cases",
                    "restricted_cases": "SELECT count(*) FROM public.complaint_cases WHERE is_restricted IS TRUE",
                    "case_actions": "SELECT count(*) FROM public.case_actions",
                    "case_links": "SELECT count(*) FROM public.case_links",
                    "alerts": "SELECT count(*) FROM public.alerts",
                    "coordination_notes": "SELECT count(*) FROM public.coordination_notes",
                    "audit_logs": "SELECT count(*) FROM public.audit_logs",
                }
                unlinked_counts = {}
                for name, query in table_queries.items():
                    cur.execute(query)
                    unlinked_counts[name] = cur.fetchone()[0]

                print("\nUnlinked Auth identity context:")
                for name, count in unlinked_counts.items():
                    print(f"  {name} = {count}")

                if any(count != 0 for count in unlinked_counts.values()):
                    raise RuntimeError("An unlinked identity exposed protected rows.")

                # Never commit: this is an observation-only test.
                conn.rollback()
                print("\nPASS: direct login, role attributes, and RLS smoke assertions succeeded.")
                print("Transaction rolled back; no application rows were changed.")
                return 0

    except Exception as exc:
        print(f"\nFAIL: {type(exc).__name__}: {exc}", file=sys.stderr)
        print("The test transaction was not committed. Check the error before retrying.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
