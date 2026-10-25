"""
SETU consolidated production-readiness runner.

Run from E:\\App\\Project\\setu\\backend with the project's virtualenv active:
    python .\\setu_full_readiness.py

Database operations are SELECT-only. Synthetic overlap cases are in-memory.
The runner never prints secret values and never creates/deletes database rows.
Optional authenticated E2E checks use tokens supplied via environment variables:
  SETU_AUDIT_TOKEN_ADMIN
  SETU_AUDIT_TOKEN_SENIOR
  SETU_AUDIT_TOKEN_BUREAU_HEAD
  SETU_AUDIT_TOKEN_REGIONAL_OFFICER
  SETU_AUDIT_TOKEN_DESK_OFFICER
Tokens must be valid Supabase access tokens for test users with matching profiles.
"""
from __future__ import annotations

import ast
import importlib
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = os.getenv("SETU_AUDIT_BASE_URL", "http://127.0.0.1:8081").rstrip("/")
RESULTS: list[tuple[str, str, str]] = []


def report(name: str, status: str, detail: str = "") -> None:
    RESULTS.append((name, status, detail))
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))


def run_cmd(name: str, args: list[str], timeout: int = 900) -> None:
    print(f"\n--- {name} ---")
    try:
        proc = subprocess.run(args, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
        output = (proc.stdout + "\n" + proc.stderr).strip()
        if output:
            print(output[-10000:])
        report(name, "PASS" if proc.returncode == 0 else "FAIL", f"exit code {proc.returncode}")
    except Exception as exc:
        report(name, "FAIL", f"{type(exc).__name__}: {exc}")


def request(path: str, token: str | None = None, demo: bool = False) -> tuple[int | None, str]:
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if demo:
        demo_token = get_setting("SETU_API_TOKEN")
        if demo_token:
            headers["X-SETU-API-TOKEN"] = demo_token
    req = urllib.request.Request(BASE + path, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.status, response.read(4096).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read(4096).decode("utf-8", "replace")
    except Exception as exc:
        return None, f"{type(exc).__name__}: {exc}"


def http_expect(label: str, path: str, expected: set[int], token: str | None = None,
                demo: bool = False) -> tuple[int | None, str]:
    code, body = request(path, token, demo)
    if code is None:
        report(label, "BLOCKED", body)
    else:
        report(label, "PASS" if code in expected else "FAIL",
               f"HTTP {code}; expected {sorted(expected)}")
    return code, body


def get_setting(key: str) -> str | None:
    value = os.getenv(key)
    if value:
        return value
    try:
        from dotenv import dotenv_values
        return dotenv_values(ROOT / ".env").get(key)
    except Exception:
        return None


def discover_connection():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    preferred = ["main.py", "database.py", "db.py", "database_connection.py"]
    files = sorted(ROOT.glob("*.py"),
                   key=lambda f: (preferred.index(f.name) if f.name in preferred else len(preferred), f.name))
    for file in files:
        try:
            tree = ast.parse(file.read_text(encoding="utf-8", errors="replace"), filename=str(file))
        except (OSError, SyntaxError):
            continue
        if any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == "get_connection"
               for n in ast.walk(tree)):
            try:
                mod = importlib.import_module(file.stem)
                fn = getattr(mod, "get_connection", None)
                if callable(fn):
                    print(f"Database helper: {file.name}")
                    return fn
            except Exception as exc:
                print(f"Could not import {file.name}: {type(exc).__name__}: {exc}")
    return None


def db_security_checks():
    print("\n--- 1. RLS and restricted-record isolation diagnostics (read-only) ---")
    connect = discover_connection()
    if connect is None:
        report("Database RLS inspection", "FAIL", "Could not discover get_connection()")
        return
    try:
        with connect() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT current_user AS role_name, r.rolsuper AS is_superuser,
                           r.rolbypassrls AS bypasses_rls
                    FROM pg_roles r WHERE r.rolname = current_user
                """)
                role = cur.fetchone()
                ok = not role["is_superuser"] and not role["bypasses_rls"]
                report("API DB role is non-privileged", "PASS" if ok else "FAIL",
                       f"role={role['role_name']}; superuser={role['is_superuser']}; bypasses_rls={role['bypasses_rls']}")

                cur.execute("""
                    SELECT c.relname AS table_name, c.relrowsecurity AS rls_enabled,
                           c.relforcerowsecurity AS rls_forced,
                           COALESCE(p.n,0) AS policy_count
                    FROM pg_class c JOIN pg_namespace ns ON ns.oid=c.relnamespace
                    LEFT JOIN (SELECT tablename, COUNT(*) AS n FROM pg_policies
                               WHERE schemaname='public' GROUP BY tablename) p
                      ON p.tablename=c.relname
                    WHERE ns.nspname='public' AND c.relkind='r'
                    ORDER BY c.relname
                """)
                tables = cur.fetchall()
                gaps = [r["table_name"] for r in tables if not r["rls_enabled"] or not r["policy_count"]]
                report("All public tables have RLS and policies", "PASS" if not gaps else "FAIL",
                       f"table_count={len(tables)}; gaps={gaps or 'none'}")

                cur.execute("""
                    SELECT tablename, policyname, permissive, roles, cmd, qual, with_check
                    FROM pg_policies WHERE schemaname='public'
                      AND tablename IN ('complaint_cases','ground_truth_pairs','audit_logs')
                    ORDER BY tablename, policyname
                """)
                rows = cur.fetchall()
                print("Sensitive policies:")
                for r in rows:
                    print(f"  {r['tablename']}.{r['policyname']} | {r['cmd']} | roles={r['roles']} | USING={r['qual']} | CHECK={r['with_check']}")
                got = {r["tablename"] for r in rows}
                needed = {"complaint_cases", "ground_truth_pairs", "audit_logs"}
                report("Sensitive-table policy inventory", "PASS" if needed <= got else "REVIEW",
                       f"missing={sorted(needed-got) or 'none'}; definitions printed for manual semantic review")

                cur.execute("""
                    SELECT COUNT(*) AS visible,
                           COUNT(*) FILTER (WHERE COALESCE(is_restricted,FALSE)=TRUE) AS restricted,
                           COUNT(*) FILTER (WHERE COALESCE(is_restricted,FALSE)=FALSE) AS unrestricted
                    FROM public.complaint_cases
                """)
                counts = cur.fetchone()
                print(f"Complaint counts only: visible={counts['visible']}, restricted={counts['restricted']}, unrestricted={counts['unrestricted']}")
                report("Restricted isolation against real rows", "REVIEW",
                       "not proven by counts alone; use role-specific RLS tests with controlled fixtures")

                cur.execute("""
                    SELECT COUNT(*) AS n
                    FROM public.complaint_cases a JOIN public.complaint_cases b
                      ON a.case_id < b.case_id AND a.source_system <> b.source_system
                     AND ((a.institution_id IS NOT NULL AND a.institution_id=b.institution_id)
                       OR (a.group_id IS NOT NULL AND a.group_id=b.group_id))
                    WHERE COALESCE(a.is_restricted,FALSE)=FALSE
                      AND COALESCE(b.is_restricted,FALSE)=FALSE
                """)
                n = cur.fetchone()["n"]
                report("Live overlap data availability", "PASS" if n else "REVIEW",
                       f"eligible_pairs={n}; zero means live data cannot prove candidate detection")
    except Exception as exc:
        report("Database RLS inspection", "FAIL", f"{type(exc).__name__}: {exc}")


def synthetic_overlap_checks():
    print("\n--- 2. Synthetic overlap detection checks (no DB writes) ---")
    try:
        from overlap_engine import score_pair
        a = {
            "institution_id": "AUDIT-INST-001", "group_id": "AUDIT-GROUP-001",
            "category": "Fees / Refund",
            "text": "The institution has not refunded the tuition fee.",
            "received_date": None,
        }
        b = {
            "institution_id": "AUDIT-INST-001", "group_id": "AUDIT-GROUP-001",
            "category": "Fees / Refund",
            "text": "Tuition fee refund from the institution is still pending.",
            "received_date": None,
        }
        unrelated = {
            "institution_id": "AUDIT-INST-999", "group_id": "AUDIT-GROUP-999",
            "category": "Other", "text": "A separate unrelated maintenance issue.",
            "received_date": None,
        }
        same = score_pair(a, b)
        different = score_pair(a, unrelated)
        checks = [
            ("Known shared institution recognized", bool(same["same_institution"])),
            ("Known shared group recognized", bool(same["same_group"])),
            ("Unrelated pair not falsely linked", not different["same_institution"] and not different["same_group"]),
            ("Scores within 0..100", 0 <= same["score"] <= 100 and 0 <= different["score"] <= 100),
        ]
        for name, ok in checks:
            report(name, "PASS" if ok else "FAIL")
        print(f"Synthetic scores: related={same['score']}; unrelated={different['score']} (no text is logged)")
    except Exception as exc:
        report("Synthetic overlap tests", "FAIL", f"{type(exc).__name__}: {exc}")


def error_and_deployment_checks():
    print("\n--- 3. Error handling and 4. deployment configuration ---")
    tests = sorted(ROOT.glob("test_*.py"))
    source_files = [ROOT / n for n in ("main.py", "auth.py", "db_context.py", "overlap_engine.py") if (ROOT / n).exists()]
    if source_files:
        combined = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in source_files)
        debug_pattern = bool(re.search(r"(?i)debug\s*=\s*True", combined))
        report("Simple debug=True scan", "REVIEW" if debug_pattern else "PASS",
               "debug=True pattern found; verify production configuration" if debug_pattern else "no simple debug=True pattern found")
        secret_response = bool(re.search(r"(?i)(detail|content)\s*=\s*(?:str\(exc\)|repr\(exc\)|traceback)", combined))
        report("Exception-detail exposure scan", "REVIEW" if secret_response else "PASS",
               "possible raw exception response found; inspect manually" if secret_response else "no simple raw-exception response pattern found")
        wildcard = bool(re.search(r"allow_origins\s*=\s*\[\s*['\"]\*['\"]\s*\]", combined))
        report("CORS wildcard scan", "FAIL" if wildcard else "PASS",
               "wildcard CORS origin pattern found" if wildcard else "no simple wildcard CORS origin pattern found")
    else:
        report("Source configuration scan", "FAIL", "expected source files missing")

    env_path = ROOT / ".env"
    report(".env presence", "PASS" if env_path.exists() else "REVIEW",
           "present; values withheld" if env_path.exists() else "not present; may be injected by deployment")
    for key in ("SETU_API_DATABASE_URL", "SUPABASE_URL", "SETU_API_TOKEN"):
        val = get_setting(key)
        report(f"Required setting {key}", "PASS" if val else "FAIL", "configured" if val else "missing")
    report("Importer credential", "PASS" if get_setting("SETU_IMPORTER_DATABASE_URL") else "REVIEW",
           "configured" if get_setting("SETU_IMPORTER_DATABASE_URL") else "not configured; keep importer disabled")
    migrations = ROOT.parent / "supabase" / "migrations"
    report("Migration folder", "PASS" if migrations.is_dir() and any(migrations.glob("*.sql")) else "REVIEW",
           "SQL migration files found" if migrations.is_dir() and any(migrations.glob("*.sql")) else "no migrations folder/files found at expected path")
    backup_path = get_setting("SETU_BACKUP_DIR")
    report("Backup configuration", "PASS" if backup_path and Path(backup_path).exists() else "REVIEW",
           "configured path exists" if backup_path and Path(backup_path).exists() else "SETU_BACKUP_DIR absent or path missing; backup restore not tested")
    log_path = get_setting("SETU_LOG_LEVEL")
    report("Log level configuration", "PASS" if log_path else "REVIEW",
           f"configured as {log_path}" if log_path else "SETU_LOG_LEVEL not set; inspect deployed logging setup")
    report("Role-specific E2E test files", "PASS" if any("phase6" in p.name for p in tests) else "REVIEW",
           f"found {sum('phase6' in p.name for p in tests)} phase6 test files; live authenticated checks are separate")


def role_e2e_checks():
    print("\n--- 5. Authenticated end-to-end checks (optional per-role tokens) ---")
    roles = {
        "ADMIN": "SETU_AUDIT_TOKEN_ADMIN",
        "SENIOR": "SETU_AUDIT_TOKEN_SENIOR",
        "BUREAU_HEAD": "SETU_AUDIT_TOKEN_BUREAU_HEAD",
        "REGIONAL_OFFICER": "SETU_AUDIT_TOKEN_REGIONAL_OFFICER",
        "DESK_OFFICER": "SETU_AUDIT_TOKEN_DESK_OFFICER",
    }
    available = [(role, key, os.getenv(key)) for role, key in roles.items() if os.getenv(key)]
    if not available:
        report("Authenticated role-by-role E2E", "REVIEW",
               "no optional SETU_AUDIT_TOKEN_* environment tokens supplied; no token values are requested or printed")
        return
    for role, key, token in available:
        code, _ = http_expect(f"{role} /api/v1/cases", "/api/v1/cases", {200, 403}, token=token)
        # Summary is intended for Admin/Senior Management only.
        expected = {200} if role in {"ADMIN", "SENIOR"} else {403}
        http_expect(f"{role} /api/v1/summary authorization", "/api/v1/summary", expected, token=token)
        if code == 200:
            http_expect(f"{role} institutions endpoint", "/api/v1/institutions", {200}, token=token)


def main():
    print("SETU CONSOLIDATED READINESS AUDIT")
    print(f"Backend: {ROOT}")
    print(f"API base: {BASE}")
    print("Database checks are SELECT-only. Synthetic scoring is in-memory. No secret values are printed.")
    run_cmd("Full test suite", [sys.executable, "-m", "pytest", "-q"])
    run_cmd("Focused RLS and role authorization tests", [
        sys.executable, "-m", "pytest", "-q",
        "test_rls_migration_contract.py", "test_setu_phase6_direct_login_rls.py",
        "test_db_context.py", "test_case_authorization.py",
        "test_single_case_scope.py", "test_sensitive_endpoint_authorization.py",
    ])
    db_security_checks()
    synthetic_overlap_checks()
    error_and_deployment_checks()

    print("\n--- Base API smoke checks ---")
    http_expect("Health endpoint", "/health", {200})
    http_expect("Root endpoint", "/", {200})
    http_expect("Unauthenticated summary denial", "/api/v1/summary", {401})
    http_expect("Unauthenticated cases denial", "/api/v1/cases", {401})
    demo = get_setting("SETU_API_TOKEN")
    if demo:
        http_expect("Demo token institution endpoint", "/api/v1/institutions", {200}, demo=True)
        http_expect("Demo token summary restriction", "/api/v1/summary", {401, 403}, demo=True)
    role_e2e_checks()

    print("\n--- FINAL SUMMARY ---")
    for name, status, detail in RESULTS:
        print(f"{status:7} | {name} | {detail}")
    fails = sum(s == "FAIL" for _, s, _ in RESULTS)
    blocked = sum(s == "BLOCKED" for _, s, _ in RESULTS)
    reviews = sum(s == "REVIEW" for _, s, _ in RESULTS)
    print(f"\nFAIL={fails}; BLOCKED={blocked}; REVIEW={reviews}")
    print("A zero-failure report is not a security certification. Review every REVIEW item.")
    return 1 if fails else 0

if __name__ == "__main__":
    raise SystemExit(main())
