"""Read-only preflight for SETU's API database connection before RLS hardening."""
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Must match the URL selection used by backend/main.py.
DATABASE_URL = os.getenv("SETU_API_DATABASE_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise SystemExit(
        "Neither SETU_API_DATABASE_URL nor DATABASE_URL is configured in backend/.env."
    )

try:
    with psycopg.connect(DATABASE_URL, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    current_user AS database_role,
                    current_database() AS database_name,
                    r.rolsuper AS is_superuser,
                    r.rolbypassrls AS bypasses_rls,
                    has_schema_privilege(current_user, 'public', 'USAGE')
                        AS public_schema_usage
                FROM pg_roles AS r
                WHERE r.rolname = current_user;
            """)
            role = cur.fetchone()

            cur.execute("""
                SELECT
                    count(*) FILTER (WHERE c.relrowsecurity) AS rls_enabled_tables,
                    count(*) FILTER (
                        WHERE c.relrowsecurity AND NOT c.relforcerowsecurity
                    ) AS rls_enabled_not_forced_tables,
                    count(*) FILTER (
                        WHERE c.relrowsecurity AND c.relforcerowsecurity
                    ) AS forced_rls_tables
                FROM pg_class AS c
                JOIN pg_namespace AS n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public'
                  AND c.relkind = 'r';
            """)
            table_counts = cur.fetchone()

            cur.execute("""
                SELECT
                    count(*) AS policy_count,
                    count(DISTINCT schemaname || '.' || tablename)
                        AS tables_with_policies
                FROM pg_policies
                WHERE schemaname = 'public';
            """)
            policy_counts = cur.fetchone()

            cur.execute("""
                SELECT
                    c.relname AS table_name,
                    c.relrowsecurity AS rls_enabled,
                    c.relforcerowsecurity AS force_rls,
                    count(p.policyname) AS policy_count
                FROM pg_class AS c
                JOIN pg_namespace AS n ON n.oid = c.relnamespace
                LEFT JOIN pg_policies AS p
                  ON p.schemaname = n.nspname
                 AND p.tablename = c.relname
                WHERE n.nspname = 'public'
                  AND c.relkind = 'r'
                GROUP BY c.relname, c.relrowsecurity, c.relforcerowsecurity
                ORDER BY c.relname;
            """)
            table_rows = cur.fetchall()

    print("SETU API database preflight (read-only)")
    print("---------------------------------------")
    print(f"Database role: {role[0]}")
    print(f"Database name: {role[1]}")
    print(f"Superuser: {role[2]}")
    print(f"Bypasses RLS: {role[3]}")
    print(f"Can use public schema: {role[4]}")
    print(f"RLS-enabled public tables: {table_counts[0]}")
    print(f"RLS enabled but not forced: {table_counts[1]}")
    print(f"Forced-RLS tables: {table_counts[2]}")
    print(f"Public policies: {policy_counts[0]}")
    print(f"Public tables with policies: {policy_counts[1]}")
    print()
    print("Per-table RLS status:")
    for table_name, enabled, forced, policy_count in table_rows:
        print(
            f"  {table_name}: rls={enabled}, force_rls={forced}, "
            f"policies={policy_count}"
        )
    print()
    print("No data was modified. The database URL and credentials were not printed.")
except Exception as exc:
    # Avoid printing connection strings, which can contain credentials.
    print(f"Preflight failed: {type(exc).__name__}: {exc}")
    raise SystemExit(1)
