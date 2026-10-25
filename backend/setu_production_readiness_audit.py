"""Read-only SETU readiness audit; run from backend with its venv activated."""
import os, subprocess, sys, urllib.request, urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = os.getenv("SETU_AUDIT_BASE_URL", "http://127.0.0.1:8081").rstrip("/")
RESULTS = []

def report(name, status, detail=""):
    RESULTS.append((name, status, detail))
    print(f"[{status}] {name}" + (f" — {detail}" if detail else ""))

def run_tests():
    for name, cmd in [
        ("Full pytest suite", [sys.executable, "-m", "pytest", "-q"]),
        ("Read-only overlap smoke test", [sys.executable, "test_overlap_engine.py", "--live-db-smoke"]),
    ]:
        print(f"\\n--- {name} ---")
        try:
            p = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=900)
            out = (p.stdout + "\\n" + p.stderr).strip()
            if out: print(out[-10000:])
            report(name, "PASS" if p.returncode == 0 else "FAIL", f"exit code {p.returncode}")
        except Exception as e:
            report(name, "FAIL", f"{type(e).__name__}: {e}")

def database_audit():
    print("\\n--- Read-only database checks ---")
    try:
        # Discover Python modules that define get_connection() without regex.
        import ast
        import importlib
        import sys as _sys

        if str(ROOT) not in _sys.path:
            _sys.path.insert(0, str(ROOT))

        candidates = []
        preferred = ["main.py", "database.py", "db.py", "database_connection.py"]
        py_files = list(ROOT.glob("*.py"))
        ordered = sorted(
            py_files,
            key=lambda f: (preferred.index(f.name) if f.name in preferred else len(preferred), f.name),
        )
        for source_file in ordered:
            try:
                source_text = source_file.read_text(encoding="utf-8", errors="replace")
                tree = ast.parse(source_text, filename=str(source_file))
            except (OSError, SyntaxError):
                continue
            if any(
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "get_connection"
                for node in ast.walk(tree)
            ):
                candidates.append(source_file.stem)

        get_connection = None
        import_errors = []
        for module_name in candidates:
            try:
                module = importlib.import_module(module_name)
                possible = getattr(module, "get_connection", None)
                if callable(possible):
                    get_connection = possible
                    print(f"Database connection helper discovered in: {module_name}.py")
                    break
            except Exception as import_error:
                import_errors.append(f"{module_name}: {type(import_error).__name__}: {import_error}")

        if get_connection is None:
            raise RuntimeError(
                "Could not import get_connection() from a discovered module. "
                f"Candidates={candidates}; import errors={import_errors}"
            )

        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT current_user AS role_name, r.rolsuper AS superuser,
                           r.rolbypassrls AS bypasses_rls
                    FROM pg_roles r WHERE r.rolname = current_user
                """)
                role = cur.fetchone()
                safe = not role["superuser"] and not role["bypasses_rls"]
                report("API database role", "PASS" if safe else "FAIL",
                       f"role={role['role_name']}; superuser={role['superuser']}; bypasses_rls={role['bypasses_rls']}")

                cur.execute("""
                    SELECT c.relname AS table_name, c.relrowsecurity AS rls_enabled,
                           COALESCE(p.n, 0) AS policies
                    FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
                    LEFT JOIN (
                      SELECT tablename, COUNT(*) AS n FROM pg_policies
                      WHERE schemaname='public' GROUP BY tablename
                    ) p ON p.tablename=c.relname
                    WHERE n.nspname='public' AND c.relkind='r' ORDER BY c.relname
                """)
                tables = cur.fetchall()
                gaps = [r["table_name"] for r in tables if not r["rls_enabled"] or not r["policies"]]
                report("Public-table RLS/policy coverage", "PASS" if not gaps else "FAIL",
                       f"tables={len(tables)}; tables missing RLS or policies={gaps or 'none'}")

                cur.execute("""
                    SELECT tablename, policyname, permissive, roles, cmd, qual, with_check
                    FROM pg_policies WHERE schemaname='public'
                      AND tablename IN ('complaint_cases','ground_truth_pairs','audit_logs')
                    ORDER BY tablename, policyname
                """)
                policies = cur.fetchall()
                print("Sensitive-table policy definitions:")
                for p in policies:
                    print(f"  {p['tablename']}.{p['policyname']}: command={p['cmd']}, roles={p['roles']}, USING={p['qual']}, CHECK={p['with_check']}")
                found = {p["tablename"] for p in policies}
                missing = {"complaint_cases","ground_truth_pairs","audit_logs"} - found
                report("Sensitive-table policy inventory", "PASS" if not missing else "REVIEW",
                       f"missing policy inventory for={sorted(missing) if missing else 'none'}")

                cur.execute("""
                    SELECT COUNT(*) AS visible_cases,
                           COUNT(*) FILTER (WHERE COALESCE(is_restricted,FALSE)=FALSE) AS unrestricted,
                           COUNT(*) FILTER (WHERE institution_id IS NOT NULL AND COALESCE(is_restricted,FALSE)=FALSE) AS with_institution,
                           COUNT(*) FILTER (WHERE group_id IS NOT NULL AND COALESCE(is_restricted,FALSE)=FALSE) AS with_group
                    FROM public.complaint_cases
                """)
                print("Complaint counts (no complaint text):", cur.fetchone())

                cur.execute("""
                    SELECT COUNT(*) AS eligible_pairs
                    FROM public.complaint_cases a JOIN public.complaint_cases b
                      ON a.case_id < b.case_id
                     AND a.source_system <> b.source_system
                     AND ((a.institution_id IS NOT NULL AND a.institution_id=b.institution_id)
                       OR (a.group_id IS NOT NULL AND a.group_id=b.group_id))
                    WHERE COALESCE(a.is_restricted,FALSE)=FALSE
                      AND COALESCE(b.is_restricted,FALSE)=FALSE
                """)
                n = cur.fetchone()["eligible_pairs"]
                report("Eligible unrestricted cross-source pairs", "PASS" if n else "REVIEW",
                       f"count={n}; zero means live candidate detection is not demonstrated by current data")

                cur.execute("SELECT COUNT(*) AS n FROM public.complaint_cases WHERE COALESCE(is_restricted,FALSE)=TRUE")
                n = cur.fetchone()["n"]
                report("Restricted rows visible to API DB role", "REVIEW" if n else "PASS",
                       f"count={n}; visibility alone is not a leak, since the overlap query excludes them")
    except Exception as e:
        report("Database audit", "FAIL", f"{type(e).__name__}: {e}")

def config_audit():
    print("\\n--- Deployment configuration checks ---")
    envfile = ROOT / ".env"
    try:
        from dotenv import dotenv_values
        values = dotenv_values(envfile) if envfile.exists() else {}
    except Exception:
        values = {}
    report(".env file", "PASS" if envfile.exists() else "REVIEW",
           "present; secrets are not printed" if envfile.exists() else "not found; values may be injected externally")
    def has(k): return bool(os.getenv(k) or values.get(k))
    for k in ("SETU_API_DATABASE_URL", "SUPABASE_URL", "SETU_API_TOKEN"):
        report(f"Required setting {k}", "PASS" if has(k) else "FAIL",
               "configured" if has(k) else "missing")
    report("Separate importer credential", "PASS" if has("SETU_IMPORTER_DATABASE_URL") else "REVIEW",
           "configured" if has("SETU_IMPORTER_DATABASE_URL") else "not configured; do not run importer until configured")
    mainfile = ROOT / "main.py"
    if mainfile.exists():
        s = mainfile.read_text(encoding="utf-8", errors="replace")
        wildcard = "allow_origins=['*']" in s or 'allow_origins=["*"]' in s
        report("Simple CORS wildcard scan", "REVIEW" if wildcard else "PASS",
               "wildcard pattern found; review before production" if wildcard else "no simple wildcard pattern found")
    else: report("main.py present", "FAIL", "not found")

def http_check(path, expected):
    try:
        req = urllib.request.Request(BASE + path, method="GET")
        with urllib.request.urlopen(req, timeout=8) as r: code = r.status
    except urllib.error.HTTPError as e: code = e.code
    except Exception as e:
        report("HTTP " + path, "BLOCKED", f"{type(e).__name__}: {e}")
        return
    report("HTTP " + path, "PASS" if code in expected else "FAIL",
           f"status={code}; expected={sorted(expected)}")

def main():
    print("SETU READINESS AUDIT — READ ONLY")
    print(f"Backend: {ROOT}\\nAPI: {BASE}")
    run_tests()
    database_audit()
    config_audit()
    print("\\n--- HTTP end-to-end smoke checks ---")
    http_check("/health", {200})
    http_check("/", {200})
    http_check("/api/v1/summary", {401})
    http_check("/api/v1/cases", {401})
    print("\\n--- SUMMARY ---")
    for name, status, detail in RESULTS: print(f"{status:7} | {name} | {detail}")
    fails = sum(s == "FAIL" for _,s,_ in RESULTS)
    blocked = sum(s == "BLOCKED" for _,s,_ in RESULTS)
    review = sum(s == "REVIEW" for _,s,_ in RESULTS)
    print(f"\\nFAIL={fails}; BLOCKED={blocked}; REVIEW={review}")
    print("This audit is a diagnostic, not a production security certification.")
    return 1 if fails else 0

if __name__ == "__main__":
    raise SystemExit(main())
